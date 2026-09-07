"""
Jarvis PC Client - Centralized Configuration
Secrets stay in environment variables. UI never displays IPs or API keys.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

import sys

if getattr(sys, "frozen", False):
    EXE_DIR = Path(sys.executable).resolve().parent
    BASE_DIR = Path(__file__).resolve().parent
    load_dotenv(EXE_DIR / ".env")
    load_dotenv(Path.cwd() / ".env")
else:
    BASE_DIR = Path(__file__).resolve().parent
    load_dotenv(BASE_DIR / ".env")
    load_dotenv(BASE_DIR.parent / ".env")

IMAGES_DIR = BASE_DIR / "images"
LOGO_PNG = IMAGES_DIR / "logo.png"
LOGO_ICO = IMAGES_DIR / "logo.ico"

# Default to VPS server and pairing token if not explicitly overridden
JARVIS_SERVER_URL = os.getenv("JARVIS_SERVER", "ws://45.131.64.32:2004/ws/jarvis").strip() or "ws://45.131.64.32:2004/ws/jarvis"
JARVIS_DEVICE_TOKEN = os.getenv("JARVIS_DEVICE_TOKEN", "JARVIS-FAYAS-2010").strip() or "JARVIS-FAYAS-2010"
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
