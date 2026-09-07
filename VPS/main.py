"""
Jarvis VPS - Central AI Server
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
from typing import Any, Dict, Optional

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
    "open_chrome",
    "open_file_explorer",
    "open_settings",
    "lock_pc",
    "shutdown_pc",
    "restart_pc",
}

# Jarvis AI System Prompt
SYSTEM_PROMPT = """You are JARVIS, a sophisticated personal AI assistant inspired by Iron Man's J.A.R.V.I.S.
You are helpful, conversational, and address the user naturally. Be friendly but professional.

You understand and respond fluently in both English and Malayalam (മലയാളം).
When the user speaks in Malayalam, respond naturally in Malayalam.
When the user speaks in English, respond naturally in English.

Your job is to analyze user requests and classify them into a safe, structured JSON action.

You must ALWAYS respond with ONLY a valid JSON object adhering strictly to this schema:
{
  "action": "<action_name>",
  "target": "<target_value_or_null>",
  "speech": "<natural_conversational_response>"
}

ALLOWED ACTION NAMES:
1. "speak" - For general questions, chit-chat, time, facts, or helpful conversations. (target: null)
2. "open_chrome" - When user asks to open Google Chrome. (target: "chrome")
3. "open_whatsapp" - When user asks to open WhatsApp. (target: "whatsapp")
4. "open_file_explorer" - When user asks to open File Explorer / files / documents folder. (target: "explorer")
5. "open_settings" - When user asks to open Windows Settings. (target: "settings")
6. "open_website" - When user asks to open a specific website or search the web (e.g. YouTube, Google, GitHub). (target: full URL, e.g. "https://www.youtube.com")
7. "open_application" - When user asks to open another installed application (e.g. notepad, calculator, spotify). (target: app name, e.g. "notepad")
8. "lock_pc" - When user asks to lock their computer. (target: null, speech: "Locking your computer now, sir.")
9. "shutdown_pc" - When user asks to shut down the computer. (target: null, speech: "Are you sure you want to shut down your computer?")
10. "restart_pc" - When user asks to restart the computer. (target: null, speech: "Are you sure you want to restart your computer?")

SPEECH RESPONSE GUIDELINES:
- Be conversational and natural like a personal assistant
- Address the user respectfully (you may use "sir" occasionally)
- Match the language of the user's input (English or Malayalam)
- Keep responses concise but friendly
- Show personality - you're not just a command executor, you're an assistant

EXAMPLES OF GOOD RESPONSES:
User (English): "What time is it?"
Response: {"action": "speak", "target": null, "speech": "It's currently 3:45 PM, sir."}

User (Malayalam): "സമയം എത്രയായി?"
Response: {"action": "speak", "target": null, "speech": "ഇപ്പോൾ ഉച്ചകഴിഞ്ഞ് 3:45 ആയി."}

User (English): "Open YouTube"
Response: {"action": "open_website", "target": "https://www.youtube.com", "speech": "Opening YouTube for you now."}

User (Malayalam): "യൂട്യൂബ് ഓപ്പൺ ചെയ്യൂ"
Response: {"action": "open_website", "target": "https://www.youtube.com", "speech": "യൂട്യൂബ് തുറക്കുന്നു."}

CRITICAL RULES:
- For "shutdown_pc" or "restart_pc", your speech MUST ask for confirmation
- NEVER output markdown backticks, extra prose, or commentary. Output ONLY the JSON object
- If an action is unsafe, impossible, or unrecognized, set action to "speak" with an informative speech message
- Always match the language of the user's input in your speech response
"""

@asynccontextmanager
async def lifespan(application: FastAPI):
    """Modern FastAPI lifespan handler (replaces deprecated on_event)."""
    logger.info("Jarvis VPS starting...")
    logger.info("Server listening on %s:%s", SERVER_HOST, SERVER_PORT)
    logger.info("External WebSocket endpoint: ws://45.131.64.32:2004/ws/jarvis")
    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY.startswith("YOUR_"):
        logger.warning(
            "OPENROUTER_API_KEY is not set or using placeholder! Please update .env"
        )
    else:
        logger.info("OpenRouter API key loaded successfully (length: %d)", len(OPENROUTER_API_KEY))
    logger.info("Configured AI model: %s", OPENROUTER_MODEL)
    yield
    logger.info("Jarvis VPS shutting down.")


app = FastAPI(
    title="Jarvis AI Assistant VPS Server",
    description="Central AI backend for Jarvis PC and Mobile Clients",
    version="1.0.0",
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
        "service": "Jarvis VPS Server",
        "port": SERVER_PORT,
        "websocket": "/ws/jarvis",
    }


def call_openrouter(prompt_text: str) -> Dict[str, Any]:
    """
    Sends the user text to OpenRouter API and parses the structured JSON response.
    Never logs the API key or raw Authorization header.
    """
    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY.startswith("YOUR_"):
        raise ValueError("OpenRouter API key is not configured on the VPS.")

    logger.info("Sending request to OpenRouter (model: %s)", OPENROUTER_MODEL)

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://jarvis.internal",
        "X-Title": "Jarvis Voice Assistant",
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
        logger.error("OpenRouter request timed out after 20 seconds")
        raise RuntimeError("OpenRouter AI service request timed out.")
    except requests.exceptions.RequestException as e:
        logger.error("OpenRouter connection error: %s", type(e).__name__)
        raise RuntimeError("Failed to reach OpenRouter AI service.")

    if response.status_code != 200:
        logger.error(
            "OpenRouter returned HTTP error status %s: %s",
            response.status_code,
            response.text[:200],
        )
        if response.status_code == 429:
            raise RuntimeError("AI service rate limit exceeded. Please try again shortly.")
        elif response.status_code == 401:
            raise RuntimeError("Authentication failed with AI service. Check VPS API key.")
        else:
            raise RuntimeError(f"AI service returned HTTP {response.status_code}")

    logger.info("AI response received")
    try:
        data = response.json()
        raw_content = data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, ValueError) as e:
        logger.error("Failed to parse OpenRouter response JSON structure: %s", e)
        raise RuntimeError("Invalid response structure from AI model.")

    # Clean markdown if model wrapped in ```json ... ```
    cleaned_json = raw_content
    if "```" in cleaned_json:
        cleaned_json = re.sub(r"^```(?:json)?", "", cleaned_json.strip(), flags=re.MULTILINE)
        cleaned_json = re.sub(r"```$", "", cleaned_json.strip(), flags=re.MULTILINE)
        cleaned_json = cleaned_json.strip()

    try:
        parsed_action = json.loads(cleaned_json)
    except json.JSONDecodeError:
        logger.warning("Model did not return raw JSON, attempting fallback parse")
        # Attempt to extract json object between { and }
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
        logger.warning("AI suggested disallowed action '%s', falling back to 'speak'", action)
        action = "speak"

    speech = parsed_action.get("speech") or "Command processed."
    target = parsed_action.get("target")

    return {
        "action": action,
        "target": target,
        "speech": speech,
    }


def validate_client_request(data: Any) -> tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """Validates incoming client request schema."""
    if not isinstance(data, dict):
        return False, "Message must be a valid JSON object.", None

    msg_type = data.get("type")
    if msg_type != "command":
        return False, f"Invalid message type '{msg_type}'. Expected 'command'.", None

    client = data.get("client")
    if client not in ("pc", "android"):
        return False, f"Invalid client '{client}'. Must be 'pc' or 'android'.", None

    request_id = data.get("request_id")
    if not request_id or not isinstance(request_id, str):
        request_id = str(uuid.uuid4())

    text = data.get("text")
    if not text or not isinstance(text, str) or not text.strip():
        return False, "Command text cannot be empty.", {"request_id": request_id}

    if len(text) > 500:
        return False, "Command text exceeds maximum length of 500 characters.", {"request_id": request_id}

    return True, None, {
        "type": "command",
        "client": client,
        "request_id": request_id,
        "text": text.strip(),
    }


@app.websocket("/ws/jarvis")
async def websocket_jarvis_endpoint(websocket: WebSocket):
    await websocket.accept()
    client_host = websocket.client.host if websocket.client else "unknown"
    logger.info("WebSocket client connected from %s", client_host)

    try:
        while True:
            raw_message = await websocket.receive_text()
            logger.info("Request received from client %s", client_host)

            try:
                data = json.loads(raw_message)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON received from client %s", client_host)
                await websocket.send_text(
                    json.dumps({
                        "type": "error",
                        "request_id": str(uuid.uuid4()),
                        "success": False,
                        "error": "Malformed JSON payload.",
                    })
                )
                continue

            is_valid, err_msg, validated_data = validate_client_request(data)
            if not is_valid:
                req_id = (validated_data or {}).get("request_id", str(uuid.uuid4()))
                logger.warning("Invalid client request: %s", err_msg)
                await websocket.send_text(
                    json.dumps({
                        "type": "error",
                        "request_id": req_id,
                        "success": False,
                        "error": err_msg,
                    })
                )
                continue

            request_id = validated_data["request_id"]
            user_text = validated_data["text"]
            client_type = validated_data["client"]

            logger.info(
                "Processing command [%s] from %s: '%s'",
                request_id,
                client_type,
                user_text,
            )

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
                logger.info("Response sent for request [%s] (action: %s)", request_id, ai_result["action"])

            except Exception as e:
                logger.error("Failed to process request [%s]: %s", request_id, str(e))
                error_payload = {
                    "type": "error",
                    "request_id": request_id,
                    "success": False,
                    "error": str(e) if "timed out" in str(e).lower() or "rate limit" in str(e).lower() else "Unable to process your request.",
                }
                await websocket.send_text(json.dumps(error_payload))

    except WebSocketDisconnect:
        logger.warning("WebSocket client disconnected (%s)", client_host)
    except Exception as e:
        logger.error("Unexpected WebSocket error with client %s: %s", client_host, e)


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Uvicorn server on %s:%s", SERVER_HOST, SERVER_PORT)
    uvicorn.run(
        app,
        host=SERVER_HOST,
        port=SERVER_PORT,
        log_level="info",
    )
