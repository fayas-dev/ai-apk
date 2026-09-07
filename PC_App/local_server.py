"""
Jarvis PC Client - Local Direct WebSocket Server
Listens on port 8765 on 0.0.0.0 for direct, high-speed, zero-latency
connections from the Jarvis Mobile App on the local network (LAN / Wi-Fi).
Enables trackpad mouse control, keyboard input, live PC screen mirroring,
and direct voice/chat command processing.
"""

import asyncio
import hmac
import json
import logging
import threading
from typing import Any, Callable, Dict, Optional, Set

import websockets

from actions import check_and_handle_confirmation, execute_action
from config import JARVIS_DEVICE_TOKEN
from intent_engine import evaluate_local_intent, sanitize_speech_reply
from remote_controller import RemoteController

logger = logging.getLogger("JarvisLocalServer")


class LocalDirectServer:
    def __init__(
        self,
        port: int = 8765,
        on_client_connect: Optional[Callable[[str], None]] = None,
        on_client_disconnect: Optional[Callable[[str], None]] = None,
        on_remote_command: Optional[Callable[[Dict[str, Any]], None]] = None,
        vps_forwarder: Optional[Callable[[str], Dict[str, Any]]] = None,
        device_token: str = JARVIS_DEVICE_TOKEN,
    ):
        self.port = port
        self.on_client_connect = on_client_connect
        self.on_client_disconnect = on_client_disconnect
        self.on_remote_command = on_remote_command
        self.vps_forwarder = vps_forwarder
        self.device_token = device_token

        self._running = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._server = None
        self.connected_clients: Set[websockets.WebSocketServerProtocol] = set()

    def start(self):
        """Starts the local server in a daemon background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_server, daemon=True)
        self._thread.start()
        logger.info("Direct Local WebSocket Server thread started on port %d", self.port)

    def _run_server(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._serve())

    async def _serve(self):
        try:
            async with websockets.serve(
                self._handler,
                "0.0.0.0",
                self.port,
                ping_interval=20,
                ping_timeout=20,
            ) as server:
                self._server = server
                logger.info("Jarvis Direct Local Server started with paired-device access only")
                while self._running:
                    await asyncio.sleep(1)
        except Exception as e:
            logger.error("Error in Direct Local Server: %s", e)

    async def _handler(self, websocket):
        client_ip = websocket.remote_address[0]
        # A LAN address is not a security boundary.  Pair before exposing any
        # remote-control capability.
        if not self.device_token:
            await websocket.close(code=1008, reason="Pairing is not configured")
            return
        try:
            raw_auth = await asyncio.wait_for(websocket.recv(), timeout=10)
            auth = json.loads(raw_auth)
            supplied = str(auth.get("pairing_token", ""))
            if auth.get("type") != "register" or not hmac.compare_digest(supplied, self.device_token):
                await websocket.close(code=1008, reason="Pairing failed")
                return
        except (asyncio.TimeoutError, json.JSONDecodeError, websockets.ConnectionClosed):
            await websocket.close(code=1008, reason="Pairing required")
            return

        logger.info("Paired mobile device connected")
        self.connected_clients.add(websocket)
        if self.on_client_connect:
            try:
                self.on_client_connect(client_ip)
            except Exception:
                pass

        # Send welcome handshake
        try:
            await websocket.send(
                json.dumps({
                    "type": "pong",
                    "server": "JARVIS-Direct-PC",
                    "status": "connected",
                })
            )
        except Exception:
            pass

        try:
            async for raw_message in websocket:
                try:
                    data = json.loads(raw_message)
                    await self._process_incoming(websocket, data)
                except json.JSONDecodeError:
                    pass
                except Exception as ex:
                    logger.error("Error processing mobile message: %s", ex)
        except websockets.ConnectionClosed:
            pass
        finally:
            self.connected_clients.discard(websocket)
            logger.info("Mobile device disconnected: %s", client_ip)
            if self.on_client_disconnect:
                try:
                    self.on_client_disconnect(client_ip)
                except Exception:
                    pass

    async def _process_incoming(self, ws, data: Dict[str, Any]):
        msg_type = data.get("type", "")

        # 1. Remote PC commands (mouse, keyboard, power, screen)
        if msg_type in ("remote_pc_command", "remote_command"):
            cmd = data.get("command", "")

            # Handle browser/search commands directly via action registry
            if cmd in ("search_web", "open_url_in_chrome", "search_and_open_app", "open_youtube"):
                target = data.get("target", data.get("query", ""))
                if cmd == "open_youtube":
                    cmd = "open_url_in_chrome"
                    target = "https://www.youtube.com"
                success, msg = execute_action(cmd, target)
                await ws.send(
                    json.dumps({
                        "type": "remote_pc_response",
                        "command": cmd,
                        "result": {"success": success, "message": msg},
                    })
                )
                return

            res = RemoteController.execute_remote_command(data)

            if self.on_remote_command:
                try:
                    self.on_remote_command(data)
                except Exception:
                    pass

            # If screen was requested, reply with screen JPEG
            if cmd in ("get_screen", "view_pc_screen") and res.get("screen"):
                await ws.send(
                    json.dumps({
                        "type": "remote_pc_response",
                        "command": "screen_data",
                        "screen": res["screen"],
                    })
                )
            else:
                await ws.send(
                    json.dumps({
                        "type": "remote_pc_response",
                        "command": cmd,
                        "result": res,
                    })
                )
            return

        # 2. Direct AI Command / Chat from Mobile
        if msg_type == "command":
            request_id = data.get("request_id", "")
            text = data.get("text", "")

            # 0. Check for a pending destructive-action confirmation
            # (e.g. shutdown/restart asked for a "yes"/"no" from this same
            # paired device) before anything else.
            confirm_res = check_and_handle_confirmation(text)
            if confirm_res is not None:
                success, msg = confirm_res
                await ws.send(
                    json.dumps({
                        "type": "response",
                        "request_id": request_id,
                        "success": success,
                        "action": "speak",
                        "target": None,
                        "speech": msg,
                    })
                )
                return

            # Check local intent first
            local_res = evaluate_local_intent(text)
            if local_res:
                action_name = local_res.get("action", "speak")
                target = local_res.get("target")
                if action_name != "speak":
                    execute_action(action_name, target)

                await ws.send(
                    json.dumps({
                        "type": "response",
                        "request_id": request_id,
                        "success": True,
                        "action": action_name,
                        "target": target,
                        "speech": local_res["speech"],
                    })
                )
                return

            # Forward to the private VPS relay if available. The desktop never
            # falls back to a provider API locally, so its credentials stay on
            # the server only.
            response = None
            if self.vps_forwarder:
                try:
                    response = self.vps_forwarder(text)
                except Exception as ve:
                    logger.warning("VPS forward failed: %s", ve)

            if response and response.get("success"):
                cleaned_speech = sanitize_speech_reply(response.get("speech", ""))
                action_name = response.get("action", "speak")
                target = response.get("target")
                if action_name != "speak":
                    execute_action(action_name, target)

                await ws.send(
                    json.dumps({
                        "type": "response",
                        "request_id": request_id,
                        "success": True,
                        "action": action_name,
                        "target": target,
                        "speech": cleaned_speech,
                    })
                )
            else:
                await ws.send(
                    json.dumps({
                        "type": "response",
                        "request_id": request_id,
                        "success": False,
                        "action": "speak",
                        "target": None,
                        "speech": "The secure neural relay is unavailable. Please reconnect and try again.",
                    })
                )
            return

    def stop(self):
        self._running = False
