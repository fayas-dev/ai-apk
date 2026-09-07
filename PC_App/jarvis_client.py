"""
Jarvis PC Client - WebSocket Client & Remote Control Listener
Maintains a persistent authenticated connection to the private WSS relay.
Handles automatic reconnects, request UUIDs, and executes incoming remote control events.
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
    JARVIS_DEVICE_TOKEN,
    JARVIS_SERVER_URL,
    RECONNECT_INITIAL_DELAY,
    RECONNECT_MAX_DELAY,
    REQUEST_TIMEOUT,
)
from remote_controller import RemoteController

logger = logging.getLogger("JarvisClient")


class JarvisClient:
    def __init__(
        self,
        server_url: str = JARVIS_SERVER_URL,
        device_token: str = JARVIS_DEVICE_TOKEN,
        on_status_change: Optional[Callable[[str], None]] = None,
        on_remote_event: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        self.server_url = server_url
        self.device_token = device_token
        self.on_status_change = on_status_change
        self.on_remote_event = on_remote_event
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
            if not self.server_url or not self.device_token:
                self._notify_status("Secure relay not configured")
                await asyncio.sleep(RECONNECT_MAX_DELAY)
                continue
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

                    # Register as PC client with server
                    await ws.send(json.dumps({
                        "type": "register",
                        "client": "pc",
                        "pc_name": "Fayas-PC",
                        "pairing_token": self.device_token,
                    }))

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
                msg_type = data.get("type")

                # 1. Check for pending command replies
                req_id = data.get("request_id")
                if req_id and req_id in self._pending_requests:
                    fut = self._pending_requests.pop(req_id)
                    if not fut.done():
                        fut.set_result(data)
                    continue

                # 2. Check for Remote PC Control commands relayed from Mobile
                if msg_type == "remote_pc_command":
                    logger.info("Received mobile remote control command: %s", data.get("command"))
                    res = RemoteController.execute_remote_command(data)

                    # Notify GUI if callback registered
                    if self.on_remote_event:
                        try:
                            self.on_remote_event(data)
                        except Exception:
                            pass

                    # Relay the result for every authenticated remote action.
                    # This includes microphone-transcription and speaker control
                    # acknowledgements as well as screen frames.
                    if data.get("command") in ("get_screen", "view_pc_screen") and res.get("screen"):
                        screen_reply = {
                            "type": "remote_pc_response",
                            "command": "screen_data",
                            "screen": res["screen"],
                        }
                        await ws.send(json.dumps(screen_reply))
                    else:
                        await ws.send(json.dumps({
                            "type": "remote_pc_response",
                            "command": data.get("command", ""),
                            "result": res,
                        }))
                    continue

                logger.info("Received VPS broadcast: %s", data)

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
