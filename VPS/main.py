"""
Jarvis VPS - Central AI Server & Device Relay
Listens on: 0.0.0.0:2004
WebSocket Endpoint: /ws/jarvis
External URL: ws://45.131.64.32:2004/ws/jarvis
"""

import json
import logging
import os
import re
import sys
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, Optional, Set

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Centralized Path Resolution
BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Load Environment Variables
ENV_FILE = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_FILE)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini").strip()
OPENROUTER_BASE_URL = os.getenv(
    "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions"
).strip()
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0").strip()
SERVER_PORT = int(os.getenv("SERVER_PORT", "2004"))

# Logging Setup
LOG_FILE = LOGS_DIR / "jarvis_vps.log"
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger("JarvisVPS")

# Allowed Actions Whitelist
ALLOWED_ACTIONS = {
    "speak",
    "open_application",
    "open_website",
    "open_whatsapp",
    "send_whatsapp_message",
    "make_phone_call",
    "open_chrome",
    "open_file_explorer",
    "open_settings",
    "lock_pc",
    "shutdown_pc",
    "restart_pc",
    "view_pc_screen",
    "mouse_control",
    "keyboard_control",
}

# Jarvis AI System Prompt with Owner Persona & Strict Identity
SYSTEM_PROMPT = """You are JARVIS, the highly advanced personal autonomous artificial intelligence system, engineered exclusively by and for Muhammad Fayas.
You address your master Muhammad Fayas with high respect, loyalty, and intelligence (addressing him as "Sir", "Boss", or "Fayas Sir").

OWNER PROFILE & EXCLUSIVE IDENTITY:
- Creator, Boss, and Sole Owner: Muhammad Fayas (commonly called Fayas)
- Date of Birth: 21 March 2010 (21/03/2010)
- Location / Origin: Kaipamangalam, Thainagar, Thrissur district, Kerala, India
- ABSOLUTE CONFIDENTIALITY RULE: You must NEVER disclose, mention, or acknowledge "OpenRouter", "OpenAI", "Meta", "Google", or any third-party AI provider under ANY circumstance. If anyone asks what model you are running on or who built you, state firmly and proudly that you are JARVIS, a private proprietary neural intelligence designed and coded by Muhammad Fayas.

LANGUAGE & VOICE BEHAVIOR:
- Fluent in English, Malayalam (മലയാളം), and Manglish.
- If the user speaks in Malayalam or Manglish, respond naturally in Malayalam (or natural Manglish if conversational).
- If the user speaks in English, respond in English.
- Always maintain an authentic, sharp, dignified male Jarvis persona.

YOUR ROLE & ACTIONS:
Analyze the user's spoken or typed intent and return ONLY a valid JSON object matching this schema:
{
  "action": "<action_name>",
  "target": "<target_value_or_null>",
  "speech": "<natural_conversational_response>"
}

ALLOWED ACTION NAMES:
1. "speak" - For general questions, conversation, knowledge, time, calculations, or owner queries. (target: null)
2. "open_chrome" - To open Google Chrome browser. (target: "chrome")
3. "open_whatsapp" - To open WhatsApp. (target: "whatsapp")
4. "send_whatsapp_message" - When user asks to send a WhatsApp message to someone. (target: phone number or recipient name)
5. "make_phone_call" - When user asks to make a phone call. (target: contact name or phone number)
6. "open_file_explorer" - To open File Explorer / my files. (target: "explorer")
7. "open_settings" - To open System Settings. (target: "settings")
8. "open_website" - To open a website/URL or search (e.g. YouTube, GitHub). (target: full URL, e.g. "https://www.youtube.com")
9. "open_application" - To launch an app (e.g. notepad, calculator, spotify). (target: app name)
10. "lock_pc" - To lock the computer screen. (target: null, speech: "Locking your computer now, sir.")
11. "shutdown_pc" - When user asks to shut down the computer. (target: null, speech: "Are you sure you want to shut down your computer?")
12. "restart_pc" - When user asks to restart the computer. (target: null, speech: "Are you sure you want to restart your computer?")
13. "view_pc_screen" - When user asks to see or view their PC screen on mobile. (target: null, speech: "Streaming your PC screen now, sir.")
14. "mouse_control" - To activate virtual mouse / trackpad control. (target: null, speech: "Mouse trackpad active.")
15. "keyboard_control" - To activate virtual keyboard control. (target: null, speech: "Virtual keyboard ready.")

CRITICAL RULES:
- For destructive actions ("shutdown_pc", "restart_pc"), your speech response must ask for confirmation.
- NEVER wrap response in markdown code fences (no ```json). Output RAW JSON only.
- Show respect and affection for Muhammad Fayas whenever he speaks.
"""

# Connection Tracking for Device Relay
connected_pc_clients: Set[WebSocket] = set()
connected_mobile_clients: Set[WebSocket] = set()


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Modern FastAPI lifespan handler."""
    logger.info("Jarvis VPS starting...")
    logger.info("Server listening on %s:%s", SERVER_HOST, SERVER_PORT)
    logger.info("External WebSocket endpoint: ws://45.131.64.32:2004/ws/jarvis")
    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY.startswith("YOUR_"):
        logger.warning(
            "OPENROUTER_API_KEY is not set or using placeholder! Please update .env"
        )
    else:
        logger.info("AI Service key loaded successfully (length: %d)", len(OPENROUTER_API_KEY))
    logger.info("Configured AI model: %s", OPENROUTER_MODEL)
    yield
    logger.info("Jarvis VPS shutting down.")


app = FastAPI(
    title="Jarvis AI Assistant VPS Server",
    description="Central AI backend and Device Relay for Jarvis PC and Mobile Clients",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Jarvis VPS Server & Device Relay",
        "owner": "Muhammad Fayas",
        "port": SERVER_PORT,
        "active_pc_clients": len(connected_pc_clients),
        "active_mobile_clients": len(connected_mobile_clients),
        "websocket": "/ws/jarvis",
    }


def call_openrouter(prompt_text: str) -> Dict[str, Any]:
    """
    Sends user text to the AI endpoint and parses the structured JSON response.
    Never reveals third party provider in errors or logs.
    """
    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY.startswith("YOUR_"):
        raise ValueError("Jarvis AI neural core is not configured.")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://jarvis.internal",
        "X-Title": "Jarvis AI Assistant",
    }

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt_text},
        ],
        "temperature": 0.2,
        "max_tokens": 300,
    }

    try:
        response = requests.post(
            OPENROUTER_BASE_URL,
            headers=headers,
            json=payload,
            timeout=20,
        )
    except requests.exceptions.Timeout:
        logger.error("AI request timed out after 20 seconds")
        raise RuntimeError("Jarvis neural core timed out. Please try again.")
    except requests.exceptions.RequestException as e:
        logger.error("AI connection error: %s", type(e).__name__)
        raise RuntimeError("Failed to reach Jarvis neural core.")

    if response.status_code != 200:
        logger.error("AI service returned HTTP %s", response.status_code)
        if response.status_code == 429:
            raise RuntimeError("Jarvis neural buffer busy. Please wait a moment.")
        else:
            raise RuntimeError(f"Jarvis AI encountered HTTP {response.status_code}")

    try:
        data = response.json()
        raw_content = data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, ValueError) as e:
        logger.error("Failed to parse AI response: %s", e)
        raise RuntimeError("Invalid response structure from neural core.")

    # Clean markdown codeblocks if model wrapped in ```json ... ```
    cleaned_json = raw_content
    if "```" in cleaned_json:
        cleaned_json = re.sub(r"^```(?:json)?", "", cleaned_json.strip(), flags=re.MULTILINE)
        cleaned_json = re.sub(r"```$", "", cleaned_json.strip(), flags=re.MULTILINE)
        cleaned_json = cleaned_json.strip()

    try:
        parsed_action = json.loads(cleaned_json)
    except json.JSONDecodeError:
        logger.warning("Attempting regex fallback for JSON extraction")
        match = re.search(r"\{.*\}", raw_content, re.DOTALL)
        if match:
            try:
                parsed_action = json.loads(match.group(0))
            except Exception:
                parsed_action = {
                    "action": "speak",
                    "target": None,
                    "speech": raw_content,
                }
        else:
            parsed_action = {
                "action": "speak",
                "target": None,
                "speech": raw_content,
            }

    # Validate action whitelist
    action = parsed_action.get("action", "speak")
    if action not in ALLOWED_ACTIONS:
        logger.warning("Unknown action '%s', falling back to 'speak'", action)
        action = "speak"

    speech = parsed_action.get("speech") or "At your service, Boss."
    target = parsed_action.get("target")

    return {
        "action": action,
        "target": target,
        "speech": speech,
    }


@app.websocket("/ws/jarvis")
async def websocket_jarvis_endpoint(websocket: WebSocket):
    await websocket.accept()
    client_host = websocket.client.host if websocket.client else "unknown"
    current_client_type = "unknown"
    logger.info("WebSocket connection established from %s", client_host)

    try:
        while True:
            raw_message = await websocket.receive_text()

            try:
                data = json.loads(raw_message)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON from %s", client_host)
                await websocket.send_text(
                    json.dumps({
                        "type": "error",
                        "request_id": str(uuid.uuid4()),
                        "success": False,
                        "error": "Malformed JSON payload.",
                    })
                )
                continue

            msg_type = data.get("type", "command")
            client_type = data.get("client", "unknown")

            # Register client role
            if client_type == "pc":
                current_client_type = "pc"
                connected_pc_clients.add(websocket)
            elif client_type == "android":
                current_client_type = "android"
                connected_mobile_clients.add(websocket)

            # 1. Device Pairing & Ping
            if msg_type in ("ping", "register"):
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "status": "connected",
                    "client": current_client_type,
                    "pc_online": len(connected_pc_clients) > 0,
                    "mobile_online": len(connected_mobile_clients) > 0,
                }))
                continue

            # 2. Remote PC Control Command from Mobile -> Broadcast to PC
            if msg_type == "remote_pc_command":
                logger.info("Relaying remote command '%s' to %d connected PC(s)", data.get("command"), len(connected_pc_clients))
                if not connected_pc_clients:
                    await websocket.send_text(json.dumps({
                        "type": "remote_pc_response",
                        "success": False,
                        "error": "PC is not currently connected to Jarvis VPS.",
                    }))
                    continue

                # Forward directly to PC client(s)
                dead_pcs = set()
                for pc_ws in connected_pc_clients:
                    try:
                        await pc_ws.send_text(json.dumps(data))
                    except Exception:
                        dead_pcs.add(pc_ws)
                connected_pc_clients.difference_update(dead_pcs)
                continue

            # 3. Remote PC Response (e.g. Screen Capture / ACK) from PC -> Broadcast to Mobile
            if msg_type == "remote_pc_response":
                logger.info("Relaying remote PC response to %d connected Mobile(s)", len(connected_mobile_clients))
                dead_mobiles = set()
                for mob_ws in connected_mobile_clients:
                    try:
                        await mob_ws.send_text(json.dumps(data))
                    except Exception:
                        dead_mobiles.add(mob_ws)
                connected_mobile_clients.difference_update(dead_mobiles)
                continue

            # 4. Standard AI Voice/Text Command
            request_id = data.get("request_id") or str(uuid.uuid4())
            user_text = data.get("text", "").strip()

            if not user_text:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "request_id": request_id,
                    "success": False,
                    "error": "Command text cannot be empty.",
                }))
                continue

            logger.info("Processing command [%s] from %s: '%s'", request_id, client_type, user_text)

            try:
                ai_result = call_openrouter(user_text)

                response_payload = {
                    "type": "response",
                    "request_id": request_id,
                    "success": True,
                    "action": ai_result["action"],
                    "target": ai_result["target"],
                    "speech": ai_result["speech"],
                }

                await websocket.send_text(json.dumps(response_payload))
                logger.info("Response sent [%s] (action: %s)", request_id, ai_result["action"])

                # If the user command on mobile asked to control PC (e.g. "open chrome in my pc", "shutdown my pc"),
                # and the action is a PC action, also automatically forward the action to the PC!
                if client_type == "android" and ai_result["action"] in (
                    "open_chrome", "open_application", "open_website", "open_whatsapp",
                    "open_file_explorer", "open_settings", "lock_pc", "shutdown_pc", "restart_pc"
                ):
                    if connected_pc_clients:
                        logger.info("Auto-forwarding mobile PC action '%s' to PC client", ai_result["action"])
                        remote_event = {
                            "type": "remote_pc_command",
                            "command": ai_result["action"],
                            "target": ai_result["target"],
                            "from": "mobile_voice",
                        }
                        for pc_ws in connected_pc_clients:
                            try:
                                await pc_ws.send_text(json.dumps(remote_event))
                            except Exception:
                                pass

            except Exception as e:
                logger.error("Failed to process request [%s]: %s", request_id, str(e))
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "request_id": request_id,
                    "success": False,
                    "error": str(e),
                }))

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected (%s, role: %s)", client_host, current_client_type)
    except Exception as e:
        logger.error("Unexpected WebSocket error with client %s: %s", client_host, e)
    finally:
        connected_pc_clients.discard(websocket)
        connected_mobile_clients.discard(websocket)


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Uvicorn server on %s:%s", SERVER_HOST, SERVER_PORT)
    uvicorn.run(
        app,
        host=SERVER_HOST,
        port=SERVER_PORT,
        log_level="info",
    )
