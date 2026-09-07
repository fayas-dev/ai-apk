"""
Jarvis PC Client - Main Entrypoint
Launches the modern Mark VII Futuristic AI Desktop GUI Application.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging() -> Path:
    """
    Configures app-wide logging to a rotating file.

    This MUST run before any other Jarvis module is imported, because the
    compiled app runs with --windowed (no console window), so without a
    file handler every logger.info/warning/error() call in the whole
    codebase (jarvis_client, local_server, actions, speech_listener, the
    TTS worker, etc.) is silently discarded. This file is the only place
    to see what actually went wrong.
    """
    log_dir = Path(os.getenv("LOCALAPPDATA", str(Path.home()))) / "Jarvis"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "jarvis.log"

    handler = RotatingFileHandler(log_path, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)

    logging.getLogger("Jarvis").info("===== Jarvis starting up. Log file: %s =====", log_path)
    return log_path


LOG_FILE_PATH = setup_logging()

from gui.app import launch_gui  # noqa: E402  (import after logging is configured)

if __name__ == "__main__":
    try:
        launch_gui()
    except Exception:
        logging.getLogger("Jarvis").exception("Fatal crash on startup")
        raise
