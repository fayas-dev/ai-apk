"""
Jarvis PC Client - Centralized Configuration
Contains all environment settings, paths, server URL, and constants.
"""

import os
from pathlib import Path

# Base Paths (Independent of Current Working Directory)
BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "images"
LOGO_PNG = IMAGES_DIR / "logo.png"
LOGO_ICO = IMAGES_DIR / "logo.ico"

# VPS Server WebSocket URL (Single source of truth)
# Default is the dedicated VPS at 45.131.64.32:2004
JARVIS_SERVER_URL = os.getenv(
    "JARVIS_SERVER", "ws://45.131.64.32:2004/ws/jarvis"
).strip()

# Text-To-Speech Configuration
JARVIS_TTS_ENABLED = (
    os.getenv("JARVIS_TTS", "true").strip().lower() in ("true", "1", "yes")
)

# Speech Recognition & Wake Phrase Detection
WAKE_PHRASES = [
    "hey jarvis",
    "okay jarvis",
    "ok jarvis",
    "hello jarvis",
    "hi jarvis",
    "jarvis",
    "jervis",
    "travis",
]

# Client Metadata
CLIENT_TYPE = "pc"
RECONNECT_INITIAL_DELAY = 2.0  # seconds
RECONNECT_MAX_DELAY = 30.0    # seconds
REQUEST_TIMEOUT = 25.0         # seconds
