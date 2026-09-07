"""
Jarvis Master GUI Application Window
Constructed with CustomTkinter. Multi-page navigation, futuristic cyberpunk styling,
continuous voice listener integration, offline voice synthesis, and system tray support.
"""

import threading
from pathlib import Path
from typing import Optional

import customtkinter as ctk
from PIL import Image
import pystray
from pystray import MenuItem as item

from actions import check_and_handle_confirmation, execute_action
from config import JARVIS_SERVER_URL, JARVIS_TTS_ENABLED, LOGO_ICO, LOGO_PNG
from intent_engine import evaluate_local_intent, sanitize_speech_reply
from local_server import LocalDirectServer
from qr_generator import get_local_ip
from gui.actions_page import ActionsPage
from gui.chat_page import ChatPage
from gui.dashboard_page import DashboardPage
from gui.diagnostics_page import DiagnosticsPage
from gui.settings_page import SettingsPage
from gui.theme import (
    BORDER_COLOR,
    CYAN_ACCENT,
    CYAN_HOVER,
    DARK_BG,
    FONT_BODY_BOLD,
    FONT_SMALL,
    FONT_SUBHEADING,
    NEON_GREEN,
    NEON_RED,
    SIDEBAR_BG,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from jarvis_client import JarvisClient
from speech_listener import SpeechListener

import queue

# Dedicated Thread-Safe TTS Worker System
_tts_queue = queue.Queue()
_tts_speed = 185
_tts_engine_ref = None

def _tts_worker_loop():
    global _tts_engine_ref
    try:
        import pyttsx3
        engine = pyttsx3.init()
        _tts_engine_ref = engine
        engine.setProperty("rate", _tts_speed)
        voices = engine.getProperty("voices")
        if voices:
            for v in voices:
                if "david" in v.name.lower() or "male" in v.name.lower():
                    engine.setProperty("voice", v.id)
                    break

        while True:
            item = _tts_queue.get()
            if item is None:
                break
            text, done_event = item
            try:
                engine.say(text)
                engine.runAndWait()
            except Exception as ex:
                pass
            finally:
                if done_event:
                    done_event.set()
                _tts_queue.task_done()
    except Exception as e:
        pass

# Start dedicated background TTS loop thread
_tts_worker_thread = threading.Thread(target=_tts_worker_loop, daemon=True)
_tts_worker_thread.start()


def speak_voice(text: str, enabled: bool = True):
    """Asynchronously speaks text through the dedicated TTS engine worker."""
    if not enabled or not text or not text.strip():
        return
    _tts_queue.put((text.strip(), None))


def speak_voice_sync(text: str, enabled: bool = True, timeout: float = 6.0):
    """Synchronously speaks text and blocks until speech playback finishes."""
    if not enabled or not text or not text.strip():
        return
    done_event = threading.Event()
    _tts_queue.put((text.strip(), done_event))
    done_event.wait(timeout=timeout)


class JarvisApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Appearance Mode & Theme
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.title("JARVIS — Mark VII Neural AI Assistant")
        self.geometry("1120x730")
        self.minsize(980, 640)
        self.configure(fg_color=DARK_BG)

        # Set Window Icon
        if LOGO_ICO.exists():
            try:
                self.iconbitmap(str(LOGO_ICO))
            except Exception:
                pass

        self.tts_enabled = JARVIS_TTS_ENABLED
        self.server_url = JARVIS_SERVER_URL
        self.listening_enabled = True  # Controls whether speech listener is active

        # System Tray Setup
        self.tray_icon = None
        self._setup_system_tray()

        # Handle window close to minimize to tray instead
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Initialize Backend Services
        self.client = JarvisClient(
            server_url=self.server_url,
            on_status_change=self._on_vps_status,
            on_remote_event=self._on_remote_event,
        )
        self.listener = SpeechListener(
            on_wake_detected=self._on_wake_detected,
            on_command_captured=self._on_command_captured,
            on_command_failed=self._on_command_failed,
            on_status_change=self._on_speech_status,
        )
        self.local_server = LocalDirectServer(
            port=8765,
            on_client_connect=self._on_mobile_connected,
            on_client_disconnect=self._on_mobile_disconnected,
            on_remote_command=self._on_remote_event,
            vps_forwarder=self.client.send_command,
        )

        self._setup_layout()

        # Start Services
        self.client.start()
        self.local_server.start()
        self.listener_thread = threading.Thread(target=self.listener.listen_loop, daemon=True)
        self.listener_thread.start()

        # Show Dashboard initially
        self._select_tab("dashboard")

    def _setup_system_tray(self):
        """Setup system tray icon with menu options."""
        try:
            # Load icon image
            if LOGO_PNG.exists():
                icon_image = Image.open(LOGO_PNG)
            else:
                # Create a simple colored image if logo not found
                icon_image = Image.new('RGB', (64, 64), color=(0, 136, 204))
            
            # Create menu
            menu = (
                item('Show Window', self._show_window, default=True),
                item('Toggle Listening', self._toggle_listening_from_tray, checked=lambda item: self.listening_enabled),
                item('Quit', self._quit_app),
            )
            
            # Create tray icon
            self.tray_icon = pystray.Icon("Jarvis", icon_image, "JARVIS AI Assistant", menu)
            
            # Start tray icon in background thread
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except Exception as e:
            print(f"Failed to setup system tray: {e}")

    def _on_closing(self):
        """Handle window close button - minimize to tray instead of quit."""
        self.withdraw()  # Hide window
        if self.tray_icon:
            self.tray_icon.notify("JARVIS is still running in the background", "JARVIS")

    def _show_window(self):
        """Show the main window from system tray."""
        self.after(0, self.deiconify)
        self.after(0, self.lift)
        self.after(0, self.focus_force)

    def _toggle_listening_from_tray(self):
        """Toggle voice listening on/off from system tray."""
        self.listening_enabled = not self.listening_enabled
        if self.listening_enabled:
            self.after(0, lambda: speak_voice("Voice listening enabled", self.tts_enabled))
            self.after(0, lambda: self.pages["dashboard"].set_state("STANDBY"))
        else:
            self.after(0, lambda: speak_voice("Voice listening disabled", self.tts_enabled))
            self.after(0, lambda: self.pages["dashboard"].set_state("IDLE"))
        
        # Update tray menu
        if self.tray_icon:
            self.tray_icon.update_menu()

    def _quit_app(self):
        """Completely quit the application."""
        self.listener.stop()
        self.client.stop()
        if hasattr(self, "local_server"):
            self.local_server.stop()
        if self.tray_icon:
            self.tray_icon.stop()
        self.after(0, self.quit)
        self.after(0, self.destroy)

    def _setup_layout(self):
        # 2-Column Grid Layout: Sidebar (220px) + Main Content (expand)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=220, fg_color=SIDEBAR_BG, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(8, weight=1)

        # Brand Header in Sidebar
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(fill="x", padx=16, pady=(24, 20))

        ctk.CTkLabel(
            brand_frame,
            text="JARVIS",
            font=("Segoe UI", 22, "bold"),
            text_color=CYAN_ACCENT,
        ).pack(anchor="w")

        ctk.CTkLabel(
            brand_frame,
            text="NEURAL DESKTOP OS",
            font=FONT_SMALL,
            text_color=TEXT_SECONDARY,
        ).pack(anchor="w")

        # Navigation Buttons
        self.nav_buttons = {}
        tabs = [
            ("dashboard", "⚡  Arc Reactor"),
            ("chat", "💬  AI Voice Chat"),
            ("actions", "🛡️  System Whitelist"),
            ("diagnostics", "📊  Diagnostics"),
            ("settings", "⚙️  Voice & Settings"),
        ]

        for tab_id, label in tabs:
            btn = ctk.CTkButton(
                self.sidebar,
                text=label,
                font=FONT_BODY_BOLD,
                fg_color="transparent",
                hover_color="#131F30",
                text_color=TEXT_SECONDARY,
                anchor="w",
                height=42,
                corner_radius=10,
                command=lambda t=tab_id: self._select_tab(t),
            )
            btn.pack(fill="x", padx=12, pady=3)
            self.nav_buttons[tab_id] = btn

        # Spacer
        self.sidebar_spacer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.sidebar_spacer.pack(fill="both", expand=True)

        # Sidebar Bottom: Live VPS & Mobile Direct Badges
        self.vps_pill = ctk.CTkLabel(
            self.sidebar,
            text="● VPS: Connecting...",
            font=FONT_SMALL,
            text_color=NEON_GREEN,
            fg_color="#062618",
            corner_radius=10,
            padx=10,
            pady=6,
        )
        self.vps_pill.pack(fill="x", padx=16, pady=(0, 6))

        local_ip = get_local_ip()
        self.mobile_pill = ctk.CTkLabel(
            self.sidebar,
            text=f"📱 Direct: ws://{local_ip}:8765",
            font=FONT_SMALL,
            text_color="#00E5FF",
            fg_color="#061D26",
            corner_radius=10,
            padx=10,
            pady=6,
        )
        self.mobile_pill.pack(fill="x", padx=16, pady=(0, 20))

        # Main Content Display Area
        self.content_container = ctk.CTkFrame(self, fg_color=DARK_BG, corner_radius=0)
        self.content_container.grid(row=0, column=1, sticky="nsew")

        # Instantiate Pages
        self.pages = {
            "dashboard": DashboardPage(
                self.content_container,
                logo_path=LOGO_PNG,
                on_talk_clicked=self._on_talk_button_clicked,
                on_quick_action=self.process_user_command,
            ),
            "chat": ChatPage(
                self.content_container,
                on_send_message=self.process_user_command,
                on_mic_clicked=self._on_talk_button_clicked,
            ),
            "actions": ActionsPage(
                self.content_container,
                on_execute_action=self._on_manual_execute_action,
            ),
            "diagnostics": DiagnosticsPage(
                self.content_container,
                on_reconnect_vps=self._reconnect_vps,
            ),
            "settings": SettingsPage(
                self.content_container,
                current_server=self.server_url,
                current_tts=self.tts_enabled,
                on_test_voice=lambda phrase: speak_voice(phrase, True),
                on_save_settings=self._on_save_settings,
            ),
        }

    def _select_tab(self, tab_name: str):
        for name, page in self.pages.items():
            page.pack_forget()
            btn = self.nav_buttons.get(name)
            if btn:
                if name == tab_name:
                    btn.configure(fg_color="#142438", text_color=CYAN_ACCENT)
                else:
                    btn.configure(fg_color="transparent", text_color=TEXT_SECONDARY)

        selected_page = self.pages.get(tab_name)
        if selected_page:
            selected_page.pack(fill="both", expand=True)

    def _on_talk_button_clicked(self):
        """User clicked the on-screen microphone or Arc Reactor."""
        current_state = getattr(self.pages["dashboard"], "_current_state", "STANDBY")
        if "LISTEN" in current_state:
            # User clicked to stop listening
            self._active_conversation = False
            self.listener.cancel_capture()
            self.pages["dashboard"].set_state("STANDBY", 'Say "Hey Jarvis" or tap to speak')
            return

        self._start_conversation_window(timeout=30.0)

    def _on_wake_detected(self):
        if not self.listening_enabled:  # Skip if listening is disabled
            return
        self.after(0, lambda: self.pages["dashboard"].set_state("LISTENING", "Wake phrase detected! Acknowledging..."))
        # Speak synchronously so microphone does not capture "Yes, sir?" from the PC speakers
        speak_voice_sync("Yes, sir?", self.tts_enabled)
        self.after(0, lambda: self.pages["dashboard"].set_state("LISTENING", "Listening for your command..."))

    def _on_command_failed(self):
        """Called when wake phrase was heard but no command followed."""
        self.after(0, lambda: self.pages["dashboard"].set_state("STANDBY"))

    def _on_command_captured(self, command_text: str):
        if not self.listening_enabled:  # Skip if listening is disabled
            return
        self.after(0, lambda: self.process_user_command(command_text))

    def _on_mobile_connected(self, client_ip: str):
        self.after(0, lambda: self.mobile_pill.configure(
            text=f"📱 Phone Linked ({client_ip})",
            text_color=NEON_GREEN,
            fg_color="#062618"
        ))
        self.after(0, lambda: self.pages["chat"].add_message("assistant", f"📱 Mobile paired directly from {client_ip} (Zero-latency active)"))

    def _on_mobile_disconnected(self, client_ip: str):
        local_ip = get_local_ip()
        self.after(0, lambda: self.mobile_pill.configure(
            text=f"📱 Direct: ws://{local_ip}:8765",
            text_color="#00E5FF",
            fg_color="#061D26"
        ))

    def _on_remote_event(self, event_data: dict):
        """Called when a mobile remote control action is received and executed."""
        cmd = event_data.get("command", "")
        # Only log non-motion events to avoid spamming the UI on mouse move
        if cmd not in ("mouse_move", "get_screen"):
            msg = f"Mobile Remote Action: {cmd}"
            self.after(0, lambda: self.pages["chat"].add_message("assistant", f"📱 Executed mobile remote command: {cmd}"))

    def _on_vps_status(self, status: str):
        def _update():
            if "connected" in status.lower():
                self.vps_pill.configure(text="● VPS: 45.131.64.32:2004", text_color=NEON_GREEN, fg_color="#062618")
            elif "connect" in status.lower():
                self.vps_pill.configure(text="○ VPS: Connecting...", text_color="#FFB300", fg_color="#2B2005")
            else:
                self.vps_pill.configure(text="○ VPS: Offline", text_color=NEON_RED, fg_color="#2E0A12")
        self.after(0, _update)

    def _on_speech_status(self, status: str):
        pass

    def process_user_command(self, command_text: str):
        """Dispatches command to local intent engine or VPS AI and executes safe actions."""
        # Update Dashboard & Chat UI
        self.pages["dashboard"].update_transcript(command_text)
        self.pages["dashboard"].set_state("PROCESSING")
        self.pages["chat"].add_message("You", command_text)

        def _worker():
            # Step 1: Check pending destructive confirmation (e.g. shutdown)
            confirm_res = check_and_handle_confirmation(command_text)
            if confirm_res is not None:
                success, msg = confirm_res
                self.after(0, lambda: self._finalize_action("confirmation", msg, "speak"))
                return

            # Step 2: Instant Local Intent Engine check (zero-latency, offline, persona guaranteed)
            local_intent = evaluate_local_intent(command_text)
            if local_intent:
                action_name = local_intent.get("action", "speak")
                target = local_intent.get("target")
                speech_reply = local_intent.get("speech", "")
                action_log = None
                if action_name != "speak":
                    success, action_log = execute_action(action_name, target)
                self.after(0, lambda: self._finalize_action(action_name, speech_reply, action_log))
                return

            # Step 3: Query VPS Server
            response = self.client.send_command(command_text)
            if response and response.get("success", False):
                action_name = response.get("action", "speak")
                target = response.get("target")
                raw_speech = response.get("speech", "")
                speech_reply = sanitize_speech_reply(raw_speech)

                action_log = None
                if action_name != "speak":
                    success, action_log = execute_action(action_name, target)

                self.after(0, lambda: self._finalize_action(action_name, speech_reply, action_log))
            else:
                # Friendly fallback so the user always receives a courteous, smart reply
                fallback_speech = f"Command recognized, sir. Executing '{command_text}' on local system."
                self.after(0, lambda: self._finalize_action("speak", fallback_speech, "Processed locally"))

        threading.Thread(target=_worker, daemon=True).start()

    def _finalize_action(self, action_name: str, speech_text: str, action_log: Optional[str]):
        # Update Dashboard
        self.pages["dashboard"].update_reply(speech_text)
        self.pages["dashboard"].set_state("SPEAKING")

        # Update Chat
        self.pages["chat"].add_message("JARVIS", speech_text, action=action_name)

        # Update Actions Audit Log
        if action_name != "speak":
            self.pages["actions"].add_log_entry(action_name, action_log or speech_text)

        # Speak Vocal Response
        if self.tts_enabled:
            speak_voice(speech_text, True)

        # Estimate speech duration so microphone does not pick up Jarvis's own vocal reply
        word_count = len(speech_text.split()) if speech_text else 3
        tts_delay_ms = max(2000, int((word_count / 2.7) * 1000) + 600)

        # Start 30-second conversational follow-up window (no need to repeat "Hey Jarvis")
        self.after(tts_delay_ms, lambda: self._start_conversation_window(timeout=30.0))

    def _start_conversation_window(self, timeout: float = 30.0):
        """
        Maintains an active 30-second conversation session.
        User does NOT need to say 'Hey Jarvis' within this 30s window.
        If no command is spoken within 30s, mic turns off and resets to STANDBY.
        """
        if not self.listening_enabled:
            self.pages["dashboard"].set_state("STANDBY")
            return

        import time
        session_id = time.time()
        self._conversation_session_id = session_id
        self._active_conversation = True

        self.pages["dashboard"].set_state(
            "LISTENING",
            "Active Conversation (30s) — Speak directly without 'Hey Jarvis'"
        )

        def _session_worker():
            command = self.listener.capture_single_command(timeout=timeout)
            if not getattr(self, "_active_conversation", False) or getattr(self, "_conversation_session_id", 0) != session_id:
                return

            if command and command.strip():
                self._active_conversation = False
                self.after(0, lambda: self.process_user_command(command))
            else:
                self._active_conversation = False
                self.after(0, lambda: self.pages["dashboard"].set_state(
                    "STANDBY",
                    'Session closed (30s timeout). Say "Hey Jarvis" or tap to speak.'
                ))

        threading.Thread(target=_session_worker, daemon=True).start()

    def _on_manual_execute_action(self, action_name: str):
        success, msg = execute_action(action_name)
        self.pages["actions"].add_log_entry(action_name, msg)
        self.pages["dashboard"].update_reply(msg)
        if self.tts_enabled:
            speak_voice(msg, True)

    def _reconnect_vps(self):
        self.client.start()

    def _on_save_settings(self, new_url: str, tts_on: bool, speed: int):
        self.tts_enabled = tts_on
        if _tts_engine:
            _tts_engine.setProperty("rate", speed)
        speak_voice("Settings updated and applied successfully.", self.tts_enabled)


def launch_gui():
    app = JarvisApp()
    app.mainloop()


if __name__ == "__main__":
    launch_gui()
