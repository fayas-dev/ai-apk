"""
Jarvis Dashboard Page
Futuristic Arc Reactor animation, live voice indicators, transcripts, and quick action chips.
"""

import math
import tkinter as tk
from pathlib import Path
from typing import Callable, Optional

import customtkinter as ctk
from PIL import Image, ImageTk

from gui.theme import (
    BORDER_COLOR,
    CARD_BG,
    CYAN_ACCENT,
    CYAN_HOVER,
    DARK_BG,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_HEADING,
    FONT_SMALL,
    FONT_SUBHEADING,
    NEON_BLUE,
    NEON_GREEN,
    NEON_PURPLE,
    NEON_RED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)


class DashboardPage(ctk.CTkFrame):
    def __init__(
        self,
        master,
        logo_path: Path,
        on_talk_clicked: Callable[[], None],
        on_quick_action: Callable[[str], None],
        **kwargs,
    ):
        super().__init__(master, fg_color=DARK_BG, **kwargs)
        self.logo_path = logo_path
        self.on_talk_clicked = on_talk_clicked
        self.on_quick_action = on_quick_action

        self._anim_step = 0
        self._current_state = "STANDBY"
        self._anim_running = True

        self._setup_ui()
        self._start_arc_animation()

    def _setup_ui(self):
        # Top Header Bar
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=30, pady=(20, 10))

        title_col = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_col.pack(side="left")

        ctk.CTkLabel(
            title_col,
            text="NEURAL COMMAND CENTER",
            font=FONT_HEADING,
            text_color=CYAN_ACCENT,
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_col,
            text="MARK VII // AUTONOMOUS VOICE OPERATING SYSTEM",
            font=FONT_SMALL,
            text_color=TEXT_SECONDARY,
        ).pack(anchor="w")

        # Status Pill Badge
        self.status_badge = ctk.CTkLabel(
            header_frame,
            text="● STANDBY",
            font=FONT_BODY_BOLD,
            text_color=CYAN_ACCENT,
            fg_color="#08212D",
            corner_radius=16,
            padx=16,
            pady=6,
        )
        self.status_badge.pack(side="right")

        # Main Center Container
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=30, pady=10)

        # Left Column: Interactive Arc Reactor & Tap to Speak
        reactor_col = ctk.CTkFrame(content_frame, fg_color=CARD_BG, corner_radius=16, border_width=1, border_color=BORDER_COLOR)
        reactor_col.pack(side="left", fill="both", expand=True, padx=(0, 12), pady=0)

        ctk.CTkLabel(
            reactor_col,
            text="CORE ARC REACTOR",
            font=FONT_SUBHEADING,
            text_color=TEXT_SECONDARY,
        ).pack(pady=(16, 5))

        # Canvas for animated pulsing rings
        self.canvas_size = 230
        self.canvas = tk.Canvas(
            reactor_col,
            width=self.canvas_size,
            height=self.canvas_size,
            bg=CARD_BG,
            highlightthickness=0,
            cursor="hand2",
        )
        self.canvas.pack(pady=10)
        self.canvas.bind("<Button-1>", lambda e: self.on_talk_clicked())

        # Load logo image for reactor center
        self.logo_img_tk = None
        if self.logo_path.exists():
            try:
                pil_img = Image.open(self.logo_path).resize((90, 90), Image.Resampling.LANCZOS)
                self.logo_img_tk = ImageTk.PhotoImage(pil_img)
            except Exception:
                self.logo_img_tk = None

        # Tap to Speak Button
        self.talk_btn = ctk.CTkButton(
            reactor_col,
            text="🎤  TAP TO SPEAK",
            font=FONT_BODY_BOLD,
            text_color="#000000",
            fg_color=CYAN_ACCENT,
            hover_color=CYAN_HOVER,
            corner_radius=20,
            height=42,
            command=self.on_talk_clicked,
        )
        self.talk_btn.pack(pady=(10, 8), padx=40, fill="x")

        self.voice_hint_label = ctk.CTkLabel(
            reactor_col,
            text='Say "Hey Jarvis" or tap the reactor',
            font=FONT_SMALL,
            text_color=TEXT_SECONDARY,
        )
        self.voice_hint_label.pack(pady=(0, 16))

        # Right Column: Live Neural Feedback & Transcripts
        feedback_col = ctk.CTkFrame(content_frame, fg_color="transparent")
        feedback_col.pack(side="right", fill="both", expand=True, padx=(12, 0), pady=0)

        # User Spoken Transcript Card
        user_card = ctk.CTkFrame(feedback_col, fg_color=CARD_BG, corner_radius=14, border_width=1, border_color=BORDER_COLOR)
        user_card.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            user_card,
            text="VOICE INPUT (YOU)",
            font=FONT_SMALL,
            text_color=CYAN_ACCENT,
        ).pack(anchor="w", padx=16, pady=(12, 4))

        self.user_transcript_label = ctk.CTkLabel(
            user_card,
            text='Waiting for your voice command...',
            font=FONT_BODY,
            text_color=TEXT_PRIMARY,
            wraplength=450,
            justify="left",
        )
        self.user_transcript_label.pack(anchor="w", padx=16, pady=(0, 14))

        # Jarvis Spoken Reply Card
        reply_card = ctk.CTkFrame(feedback_col, fg_color=CARD_BG, corner_radius=14, border_width=1, border_color=BORDER_COLOR)
        reply_card.pack(fill="both", expand=True, pady=(0, 10))

        ctk.CTkLabel(
            reply_card,
            text="JARVIS NEURAL RESPONSE",
            font=FONT_SMALL,
            text_color=NEON_BLUE,
        ).pack(anchor="w", padx=16, pady=(12, 4))

        self.jarvis_reply_label = ctk.CTkLabel(
            reply_card,
            text="Greetings, sir. All core systems are operational. I am connected to the VPS at 45.131.64.32:2004.",
            font=FONT_BODY,
            text_color=TEXT_PRIMARY,
            wraplength=450,
            justify="left",
        )
        self.jarvis_reply_label.pack(anchor="w", padx=16, pady=(0, 14))

        # Bottom Quick Action Chips
        chips_frame = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=14, border_width=1, border_color=BORDER_COLOR)
        chips_frame.pack(fill="x", padx=30, pady=(0, 20))

        ctk.CTkLabel(
            chips_frame,
            text="QUICK COMMAND CHIPS:",
            font=FONT_SMALL,
            text_color=TEXT_SECONDARY,
        ).pack(side="left", padx=(16, 10), pady=12)

        quick_actions = [
            ("🌐 Chrome", "open chrome"),
            ("💬 WhatsApp", "open whatsapp"),
            ("📁 Files", "open file explorer"),
            ("⚙️ Settings", "open windows settings"),
            ("🔒 Lock PC", "lock my pc"),
        ]

        for label, cmd in quick_actions:
            btn = ctk.CTkButton(
                chips_frame,
                text=label,
                font=FONT_SMALL,
                fg_color="#060A10",
                hover_color="#1A2636",
                text_color=CYAN_ACCENT,
                border_width=1,
                border_color="#0E3342",
                corner_radius=12,
                height=28,
                command=lambda c=cmd: self.on_quick_action(c),
            )
            btn.pack(side="left", padx=4, pady=10)

    def _start_arc_animation(self):
        """Draws pulsing futuristic concentric rings."""
        if not self._anim_running:
            return

        self._anim_step += 1
        cx, cy = self.canvas_size / 2, self.canvas_size / 2
        self.canvas.delete("ring")

        # Color based on current state
        if self._current_state == "LISTENING":
            base_color = NEON_GREEN
        elif self._current_state == "PROCESSING":
            base_color = NEON_PURPLE
        elif self._current_state == "SPEAKING":
            base_color = NEON_BLUE
        else:
            base_color = CYAN_ACCENT

        pulse = math.sin(self._anim_step * 0.1) * 6

        # Concentric animated rings
        self.canvas.create_oval(
            cx - 100 - pulse, cy - 100 - pulse, cx + 100 + pulse, cy + 100 + pulse,
            outline="#0D2A38", width=1.5, tags="ring"
        )
        self.canvas.create_oval(
            cx - 85 + pulse, cy - 85 + pulse, cx + 85 - pulse, cy + 85 - pulse,
            outline=base_color, width=2, tags="ring"
        )
        self.canvas.create_oval(
            cx - 65, cy - 65, cx + 65, cy + 65,
            outline=base_color, width=3, tags="ring"
        )

        # Center logo
        if self.logo_img_tk:
            self.canvas.create_image(cx, cy, image=self.logo_img_tk, tags="ring")
        else:
            self.canvas.create_text(
                cx, cy, text="JARVIS", fill=base_color, font=("Segoe UI", 14, "bold"), tags="ring"
            )

        self.after(50, self._start_arc_animation)

    def set_state(self, state: str, message: Optional[str] = None):
        """Updates the state and badge colors."""
        self._current_state = state.upper()
        badge_bg = "#08212D"
        default_hint = 'Say "Hey Jarvis" or tap the reactor'

        if "IDLE" in self._current_state:
            color = "#666666"
            badge_bg = "#1A1A1A"
            badge_text = "○ LISTENING DISABLED"
            default_hint = "Voice listening is disabled in system tray"
            self.talk_btn.configure(text="🔇  VOICE DISABLED", fg_color="#444444", text_color="#AAAAAA", state="disabled")
        elif "LISTEN" in self._current_state:
            color = NEON_GREEN
            badge_bg = "#062618"
            badge_text = "● LISTENING..."
            default_hint = "Listening... Speak your command or tap to stop"
            self.talk_btn.configure(text="⏹  STOP LISTENING", fg_color="#D32F2F", hover_color="#B71C1C", text_color="#FFFFFF", state="normal")
        elif "PROCESS" in self._current_state:
            color = NEON_PURPLE
            badge_bg = "#220833"
            badge_text = "● PROCESSING AI..."
            default_hint = "Analyzing with VPS AI..."
            self.talk_btn.configure(text="⏳  PROCESSING...", fg_color=NEON_PURPLE, text_color="#FFFFFF", state="disabled")
        elif "SPEAK" in self._current_state:
            color = NEON_BLUE
            badge_bg = "#081E33"
            badge_text = "● SPEAKING..."
            default_hint = "Jarvis is speaking response..."
            self.talk_btn.configure(text="🔊  SPEAKING...", fg_color=NEON_BLUE, text_color="#000000", state="disabled")
        elif "DISCONNECT" in self._current_state or "OFFLINE" in self._current_state:
            color = NEON_RED
            badge_bg = "#2E0A12"
            badge_text = "○ VPS OFFLINE"
            default_hint = "Waiting for VPS reconnection at 45.131.64.32:2004"
            self.talk_btn.configure(text="🎤  TAP TO SPEAK", fg_color=CYAN_ACCENT, hover_color=CYAN_HOVER, text_color="#000000", state="normal")
        else:
            color = CYAN_ACCENT
            badge_bg = "#08212D"
            badge_text = "● STANDBY"
            default_hint = 'Say "Hey Jarvis" or tap the reactor'
            self.talk_btn.configure(text="🎤  TAP TO SPEAK", fg_color=CYAN_ACCENT, hover_color=CYAN_HOVER, text_color="#000000", state="normal")

        self.status_badge.configure(text=badge_text, text_color=color, fg_color=badge_bg)
        self.voice_hint_label.configure(text=message if message else default_hint)

    def update_transcript(self, user_text: str):
        self.user_transcript_label.configure(text=f'"{user_text}"')

    def update_reply(self, reply_text: str):
        self.jarvis_reply_label.configure(text=reply_text)
