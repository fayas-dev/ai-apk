"""
Jarvis Conversational AI Chat Page
Scrollable message stream, text input, speech synthesis, and action chips.
"""

import datetime
from typing import Callable

import customtkinter as ctk

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
    NEON_BLUE,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)


class ChatPage(ctk.CTkFrame):
    def __init__(self, master, on_send_message: Callable[[str], None], on_mic_clicked: Callable[[], None], **kwargs):
        super().__init__(master, fg_color=DARK_BG, **kwargs)
        self.on_send_message = on_send_message
        self.on_mic_clicked = on_mic_clicked

        self._setup_ui()

    def _setup_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(20, 10))

        ctk.CTkLabel(
            header,
            text="AI VOICE & TEXT CONVERSATION",
            font=FONT_HEADING,
            text_color=CYAN_ACCENT,
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Interactive multi-turn dialogue with real-time speech and system control.",
            font=FONT_SMALL,
            text_color=TEXT_SECONDARY,
        ).pack(anchor="w")

        # Scrollable Message History Area
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=DARK_BG,
            border_width=1,
            border_color=BORDER_COLOR,
            corner_radius=14,
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=30, pady=10)

        # Bottom Input Bar
        input_container = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=14, border_width=1, border_color=BORDER_COLOR)
        input_container.pack(fill="x", padx=30, pady=(0, 20))

        self.input_entry = ctk.CTkEntry(
            input_container,
            placeholder_text="Type a message or command (e.g. 'What is quantum physics?', 'Open Chrome')...",
            font=FONT_BODY,
            fg_color="#060A10",
            border_width=1,
            border_color=BORDER_COLOR,
            text_color=TEXT_PRIMARY,
            height=42,
        )
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(14, 8), pady=10)
        self.input_entry.bind("<Return>", lambda e: self._handle_send())

        # Send Button
        self.send_btn = ctk.CTkButton(
            input_container,
            text="Send",
            font=FONT_BODY_BOLD,
            fg_color=CYAN_ACCENT,
            hover_color=CYAN_HOVER,
            text_color="#000000",
            width=75,
            height=42,
            corner_radius=10,
            command=self._handle_send,
        )
        self.send_btn.pack(side="left", padx=(0, 8), pady=10)

        # Mic Button
        self.mic_btn = ctk.CTkButton(
            input_container,
            text="🎤",
            font=("Segoe UI", 16),
            fg_color="#18273A",
            hover_color="#20334D",
            text_color=CYAN_ACCENT,
            width=46,
            height=42,
            corner_radius=10,
            command=self.on_mic_clicked,
        )
        self.mic_btn.pack(side="left", padx=(0, 14), pady=10)

        # Add initial greeting message
        self.add_message("JARVIS", "Greetings, sir. I am listening and ready to assist you. How can I help?", action="speak")

    def _handle_send(self):
        text = self.input_entry.get().strip()
        if text:
            self.input_entry.delete(0, "end")
            self.on_send_message(text)

    def add_message(self, sender: str, text: str, action: str = None):
        is_user = (sender == "You")
        timestamp = datetime.datetime.now().strftime("%H:%M")

        bubble_container = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        bubble_container.pack(fill="x", padx=10, pady=6)

        bubble = ctk.CTkFrame(
            bubble_container,
            fg_color="#142132" if is_user else CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color="#0E3342" if not is_user else BORDER_COLOR,
        )

        if is_user:
            bubble.pack(side="right", padx=(50, 0))
        else:
            bubble.pack(side="left", padx=(0, 50))

        # Title / Sender + Time
        info_row = ctk.CTkFrame(bubble, fg_color="transparent")
        info_row.pack(fill="x", padx=12, pady=(8, 2))

        ctk.CTkLabel(
            info_row,
            text=sender.upper(),
            font=FONT_SMALL,
            text_color=CYAN_ACCENT if not is_user else TEXT_SECONDARY,
        ).pack(side="left")

        ctk.CTkLabel(
            info_row,
            text=f" • {timestamp}",
            font=FONT_SMALL,
            text_color=TEXT_SECONDARY,
        ).pack(side="left")

        if action and action != "speak":
            action_tag = ctk.CTkLabel(
                info_row,
                text=f"[{action.upper()}]",
                font=FONT_SMALL,
                text_color=NEON_BLUE,
                fg_color="#091E30",
                corner_radius=6,
                padx=6,
            )
            action_tag.pack(side="left", padx=8)

        # Message Text
        ctk.CTkLabel(
            bubble,
            text=text,
            font=FONT_BODY,
            text_color=TEXT_PRIMARY,
            wraplength=480,
            justify="left",
        ).pack(anchor="w", padx=12, pady=(0, 10))

        # Scroll to bottom
        self.after(50, lambda: self.scroll_frame._parent_canvas.yview_moveto(1.0))
