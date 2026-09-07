"""
Jarvis PC Client - Centralized Configuration
Secrets stay in environment variables. UI never displays IPs or API keys.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")

IMAGES_DIR = BASE_DIR / "images"
LOGO_PNG = IMAGES_DIR / "logo.png"
LOGO_ICO = IMAGES_DIR / "logo.ico"

# No production address is compiled into the desktop client. Configure a WSS
# endpoint privately in .env / the operating-system environment.
JARVIS_SERVER_URL = os.getenv("JARVIS_SERVER", "").strip()
JARVIS_DEVICE_TOKEN = os.getenv("JARVIS_DEVICE_TOKEN", "").strip()
JARVIS_ENABLE_LOCAL_DIRECT = os.getenv("JARVIS_ENABLE_LOCAL_DIRECT", "false").strip().lower() in ("1", "true", "yes")

JARVIS_TTS_ENABLED = (
    os.getenv("JARVIS_TTS", "true").strip().lower() in ("true", "1", "yes")
)

CLIENT_TYPE = "pc"
RECONNECT_INITIAL_DELAY = 2.0
RECONNECT_MAX_DELAY = 30.0
REQUEST_TIMEOUT = 25.0

# Keep WAKE_PHRASES for any callers; matching lives in wake_phrase.py
from wake_phrase import WAKE_PHRASES  # noqa: E402
