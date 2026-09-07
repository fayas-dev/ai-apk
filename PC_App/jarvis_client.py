"""
Jarvis PC Client - WebSocket Client
Maintains a persistent connection to the VPS at ws://45.131.64.32:2004/ws/jarvis
Handles automatic reconnects with exponential backoff, request UUIDs, and timeout handling.
"""

import asyncio
import json
import logging
import threading
import uuid
from typing import Any, Callable, Dict, Optional

import websockets
from websockets.exceptions import ConnectionClosed

from config import (
    CLIENT_TYPE,
    JARVIS_SERVER_URL,
    RECONNECT_INITIAL_DELAY,
    RECONNECT_MAX_DELAY,
    REQUEST_TIMEOUT,
)

logger = logging.getLogger("JarvisClient")


class JarvisClient:
    def __init__(
        self,
        server_url: str = JARVIS_SERVER_URL,
        on_status_change: Optional[Callable[[str], None]] = None,
    ):
        self.server_url = server_url
        self.on_status_change = on_status_change
        self.is_connected = False
        self._running = False
        self._websocket: Optional[websockets.WebSocketClientProtocol] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None

        # Pending requests map: request_id -> asyncio.Future
        self._pending_requests: Dict[str, asyncio.Future] = {}

    def _notify_status(self, status: str):
        if self.on_status_change:
            try:
                self.on_status_change(status)
            except Exception:
                pass

    def start(self):
        """Starts the background WebSocket client loop."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._thread.start()

    def _run_event_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._connection_manager())

    async def _connection_manager(self):
        retry_delay = RECONNECT_INITIAL_DELAY
        while self._running:
            try:
                self._notify_status("Connecting to VPS...")
                logger.info("Connecting to Jarvis VPS at %s", self.server_url)

                async with websockets.connect(
                    self.server_url,
                    ping_interval=20,
                    ping_timeout=15,
                    close_timeout=5,
                ) as ws:
                    self._websocket = ws
                    self.is_connected = True
                    retry_delay = RECONNECT_INITIAL_DELAY
                    self._notify_status("VPS connected")
                    logger.info("Successfully connected to Jarvis VPS")

                    await self._receive_loop(ws)

            except (ConnectionClosed, OSError, Exception) as e:
                self.is_connected = False
                self._websocket = None
                self._notify_status("Disconnected")
                logger.warning("WebSocket disconnected: %s. Reconnecting in %.1fs...", e, retry_delay)

                # Fail pending requests
                for req_id, fut in list(self._pending_requests.items()):
                    if not fut.done():
                        fut.set_exception(ConnectionError("VPS connection lost during request."))
                self._pending_requests.clear()

                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 1.5, RECONNECT_MAX_DELAY)

    async def _receive_loop(self, ws: websockets.WebSocketClientProtocol):
        async for raw_msg in ws:
            try:
                data = json.loads(raw_msg)
                req_id = data.get("request_id")
                if req_id and req_id in self._pending_requests:
                    fut = self._pending_requests.pop(req_id)
                    if not fut.done():
                        fut.set_result(data)
                else:
                    logger.info("Received unsolicited or broadcast message: %s", data)
            except Exception as e:
                logger.error("Error processing message from VPS: %s", e)

    def send_command(self, text: str, timeout: float = REQUEST_TIMEOUT) -> Dict[str, Any]:
        """
        Synchronous helper to send a command text to the VPS and wait for response.
        Thread-safe and callable from any thread.
        """
        if not self._running or not self._loop:
            raise RuntimeError("JarvisClient is not running. Call start() first.")

        future = asyncio.run_coroutine_threadsafe(
            self._send_command_async(text, timeout), self._loop
        )
        try:
            return future.result(timeout=timeout + 2.0)
        except Exception as e:
            logger.error("Command '%s' failed: %s", text, e)
            return {
                "type": "error",
                "request_id": "",
                "success": False,
                "error": f"VPS communication error: {e}",
            }

    async def _send_command_async(self, text: str, timeout: float) -> Dict[str, Any]:
        if not self.is_connected or not self._websocket:
            raise ConnectionError("Jarvis VPS is currently offline. Please wait for reconnection.")

        request_id = str(uuid.uuid4())
        loop = asyncio.get_running_loop()
        future: asyncio.Future = loop.create_future()
        self._pending_requests[request_id] = future

        payload = {
            "type": "command",
            "client": CLIENT_TYPE,
            "request_id": request_id,
            "text": text,
        }

        try:
            await self._websocket.send(json.dumps(payload))
            logger.info("Sent command [%s] to VPS: '%s'", request_id, text)
            result = await asyncio.wait_for(future, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            self._pending_requests.pop(request_id, None)
            raise TimeoutError(f"Jarvis VPS did not respond within {timeout} seconds.")
        except Exception as e:
            self._pending_requests.pop(request_id, None)
            raise e

    def stop(self):
        """Stops the client and cleans up."""
        self._running = False
        if self._websocket and self._loop:
            asyncio.run_coroutine_threadsafe(self._websocket.close(), self._loop)
