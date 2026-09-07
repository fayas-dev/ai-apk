"""
Jarvis PC Client - Remote Controller Engine
Executes remote mouse, keyboard, screen capture, and system actions
received from the Jarvis Mobile App via the VPS WebSocket bridge.
"""

import base64
import ctypes
import io
import logging
import os
import subprocess
from typing import Any, Dict, Optional, Tuple

import pyautogui
from PIL import Image

logger = logging.getLogger("JarvisRemote")

# PyAutoGUI configuration
pyautogui.FAILSAFE = False  # Avoid crashing if cursor touches screen corner
pyautogui.PAUSE = 0.01      # Low latency for smooth cursor movement


class RemoteController:
    """Handles real-time mobile-to-PC control commands."""

    @staticmethod
    def handle_mouse_move(dx: float, dy: float, sensitivity: float = 1.5):
        """Moves the PC cursor by a relative delta (dx, dy)."""
        try:
            cur_x, cur_y = pyautogui.position()
            new_x = cur_x + int(dx * sensitivity)
            new_y = cur_y + int(dy * sensitivity)
            pyautogui.moveTo(new_x, new_y)
        except Exception as e:
            logger.error("Failed to move mouse: %s", e)

    @staticmethod
    def handle_mouse_click(button: str = "left"):
        """Clicks left, right, or middle mouse button."""
        try:
            btn = button.lower().strip()
            if btn in ("left", "right", "middle"):
                pyautogui.click(button=btn)
        except Exception as e:
            logger.error("Failed to click mouse: %s", e)

    @staticmethod
    def handle_mouse_double_click():
        """Double clicks the left mouse button."""
        try:
            pyautogui.doubleClick()
        except Exception as e:
            logger.error("Failed to double click: %s", e)

    @staticmethod
    def handle_mouse_scroll(amount: int):
        """Scrolls the mouse wheel up (positive) or down (negative)."""
        try:
            pyautogui.scroll(amount)
        except Exception as e:
            logger.error("Failed to scroll: %s", e)

    @staticmethod
    def handle_keyboard_type(text: str):
        """Types string of text directly into the active window."""
        try:
            pyautogui.write(text, interval=0.01)
        except Exception as e:
            logger.error("Failed to type text: %s", e)

    @staticmethod
    def handle_key_press(key: str):
        """Presses a special key (e.g. enter, backspace, esc, tab, space)."""
        try:
            k = key.lower().strip()
            key_map = {
                "enter": "enter",
                "return": "enter",
                "backspace": "backspace",
                "delete": "delete",
                "tab": "tab",
                "escape": "esc",
                "esc": "esc",
                "space": "space",
                "up": "up",
                "down": "down",
                "left": "left",
                "right": "right",
            }
            if k in key_map:
                pyautogui.press(key_map[k])
            elif len(k) == 1:
                pyautogui.press(k)
        except Exception as e:
            logger.error("Failed to press key: %s", e)

    @staticmethod
    def capture_screen_base64(max_width: int = 960, quality: int = 60) -> Optional[str]:
        """
        Captures the current PC screen, resizes it for low-latency transmission,
        compresses it as JPEG, and returns a Base64-encoded data string.
        """
        try:
            from PIL import ImageDraw
            screenshot = pyautogui.screenshot()
            cur_x, cur_y = pyautogui.position()

            # Draw live visible PC mouse cursor pointer (cyan arrow with black border)
            try:
                draw = ImageDraw.Draw(screenshot)
                cursor_points = [
                    (cur_x, cur_y),
                    (cur_x, cur_y + 18),
                    (cur_x + 5, cur_y + 14),
                    (cur_x + 10, cur_y + 22),
                    (cur_x + 13, cur_y + 20),
                    (cur_x + 8, cur_y + 12),
                    (cur_x + 14, cur_y + 12),
                ]
                draw.polygon(cursor_points, fill="#00E5FF", outline="black")
            except Exception:
                pass

            # Scale down to maintain aspect ratio while keeping payload small
            width, height = screenshot.size
            if width > max_width:
                new_width = max_width
                new_height = int(height * (max_width / width))
                screenshot = screenshot.resize((new_width, new_height), Image.Resampling.BILINEAR)

            buffer = io.BytesIO()
            # Convert RGBA to RGB for JPEG
            if screenshot.mode in ("RGBA", "P"):
                screenshot = screenshot.convert("RGB")
            screenshot.save(buffer, format="JPEG", quality=quality, optimize=True)
            b64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
            return b64_str
        except Exception as e:
            logger.error("Screen capture failed: %s", e)
            return None

    @staticmethod
    def lock_pc() -> Tuple[bool, str]:
        """Locks the Windows PC immediately."""
        try:
            ctypes.windll.user32.LockWorkStation()
            return True, "PC locked."
        except Exception as e:
            return False, f"Failed to lock: {e}"

    @staticmethod
    def shutdown_pc() -> Tuple[bool, str]:
        """Immediately shuts down the PC."""
        try:
            subprocess.run(["shutdown", "/s", "/t", "0"], check=True)
            return True, "PC shutting down."
        except Exception as e:
            return False, f"Shutdown failed: {e}"

    @staticmethod
    def restart_pc() -> Tuple[bool, str]:
        """Immediately restarts the PC."""
        try:
            subprocess.run(["shutdown", "/r", "/t", "0"], check=True)
            return True, "PC restarting."
        except Exception as e:
            return False, f"Restart failed: {e}"

    @classmethod
    def execute_remote_command(cls, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for executing remote PC commands sent from Mobile.
        """
        cmd = command_data.get("command", "")
        logger.info("Executing remote control command: %s", cmd)

        if cmd == "mouse_move":
            dx = float(command_data.get("dx", 0))
            dy = float(command_data.get("dy", 0))
            sens = float(command_data.get("sensitivity", 1.5))
            cls.handle_mouse_move(dx, dy, sens)
            return {"status": "ok"}

        elif cmd == "mouse_click":
            button = command_data.get("button", "left")
            cls.handle_mouse_click(button)
            return {"status": "ok"}

        elif cmd == "mouse_double_click":
            cls.handle_mouse_double_click()
            return {"status": "ok"}

        elif cmd == "mouse_scroll":
            amount = int(command_data.get("amount", 0))
            cls.handle_mouse_scroll(amount)
            return {"status": "ok"}

        elif cmd == "key_type":
            text = command_data.get("text", "")
            cls.handle_keyboard_type(text)
            return {"status": "ok"}

        elif cmd == "key_press":
            key = command_data.get("key", "")
            cls.handle_key_press(key)
            return {"status": "ok"}

        elif cmd in ("get_screen", "view_pc_screen"):
            screen_b64 = cls.capture_screen_base64()
            return {
                "status": "ok",
                "screen": screen_b64,
            }

        elif cmd in ("shutdown_pc", "restart_pc"):
            # Destructive actions must use the shared action registry so the
            # confirmation safeguard is never bypassed by remote commands.
            from actions import execute_action
            success, msg = execute_action(cmd)
            return {"status": "confirmation_required" if success else "error", "message": msg}

        elif cmd == "lock_pc":
            success, msg = cls.lock_pc()
            return {"status": "ok" if success else "error", "message": msg}

        elif cmd == "open_chrome":
            from actions import open_chrome
            success, msg = open_chrome()
            return {"status": "ok" if success else "error", "message": msg}

        elif cmd == "open_whatsapp":
            from actions import open_whatsapp
            success, msg = open_whatsapp()
            return {"status": "ok" if success else "error", "message": msg}

        elif cmd in (
            "open_application",
            "open_website",
            "search_web",
            "open_url_in_chrome",
            "search_and_open_app",
        ):
            from actions import execute_action
            success, msg = execute_action(cmd, command_data.get("target"))
            return {"status": "ok" if success else "error", "message": msg}

        return {"status": "error", "message": f"Unknown command: {cmd}"}
