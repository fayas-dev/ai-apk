"""
Jarvis Settings & Voice Configuration Page
Control TTS voice properties, wake-phrase sensitivity, and VPS endpoints.
"""

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
    FONT_SUBHEADING,
    NEON_GREEN,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)


class SettingsPage(ctk.CTkFrame):
    def __init__(
        self,
        master,
        current_server: str,
        current_tts: bool,
        on_test_voice: Callable[[str], None],
        on_save_settings: Callable[[str, bool, int], None],
        **kwargs,
    ):
        super().__init__(master, fg_color=DARK_BG, **kwargs)
        self.current_server = current_server
        self.current_tts = current_tts
        self.on_test_voice = on_test_voice
        self.on_save_settings = on_save_settings

        self._setup_ui()

    def _setup_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(20, 10))

        ctk.CTkLabel(
            header,
            text="JARVIS SYSTEM & VOICE CONFIGURATION",
            font=FONT_HEADING,
            text_color=CYAN_ACCENT,
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Customize voice synthesis, wake-phrase detection, and VPS endpoints.",
            font=FONT_SMALL,
            text_color=TEXT_SECONDARY,
        ).pack(anchor="w")

        content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=30, pady=10)

        # Voice Settings Card
        voice_card = ctk.CTkFrame(content, fg_color=CARD_BG, corner_radius=14, border_width=1, border_color=BORDER_COLOR)
        voice_card.pack(fill="x", pady=8)

        ctk.CTkLabel(voice_card, text="TEXT-TO-SPEECH (TTS) SYNTHESIS", font=FONT_SUBHEADING, text_color=CYAN_ACCENT).pack(anchor="w", padx=16, pady=(14, 8))

        # Enable TTS Switch
        self.tts_switch = ctk.CTkSwitch(
            voice_card,
            text="Enable Spoken Voice Responses (TTS)",
            font=FONT_BODY_BOLD,
            text_color=TEXT_PRIMARY,
            progress_color=CYAN_ACCENT,
        )
        if self.current_tts:
            self.tts_switch.select()
        else:
            self.tts_switch.deselect()
        self.tts_switch.pack(anchor="w", padx=16, pady=8)

        # Speech Rate Slider
        ctk.CTkLabel(voice_card, text="Speech Speed (Words Per Minute):", font=FONT_SMALL, text_color=TEXT_SECONDARY).pack(anchor="w", padx=16, pady=(6, 2))
        self.speed_slider = ctk.CTkSlider(
            voice_card,
            from_=130,
            to=230,
            number_of_steps=10,
            progress_color=CYAN_ACCENT,
            button_color=CYAN_ACCENT,
            button_hover_color=CYAN_HOVER,
        )
        self.speed_slider.set(185)
        self.speed_slider.pack(fill="x", padx=16, pady=4)

        # Test Voice Button
        ctk.CTkButton(
            voice_card,
            text="🔊 Test Jarvis Voice",
            font=FONT_SMALL,
            fg_color="#18273A",
            hover_color="#243B55",
            text_color=CYAN_ACCENT,
            width=140,
            height=32,
            corner_radius=8,
            command=lambda: self.on_test_voice("All voice synthesis channels are calibrated and fully operational, sir."),
        ).pack(anchor="w", padx=16, pady=(8, 14))

        # Server Settings Card
        server_card = ctk.CTkFrame(content, fg_color=CARD_BG, corner_radius=14, border_width=1, border_color=BORDER_COLOR)
        server_card.pack(fill="x", pady=8)

        ctk.CTkLabel(server_card, text="CENTRALIZED VPS SERVER", font=FONT_SUBHEADING, text_color=CYAN_ACCENT).pack(anchor="w", padx=16, pady=(14, 8))

        ctk.CTkLabel(server_card, text="WebSocket Endpoint URL:", font=FONT_SMALL, text_color=TEXT_SECONDARY).pack(anchor="w", padx=16, pady=(4, 2))

        self.server_entry = ctk.CTkEntry(
            server_card,
            font=FONT_BODY,
            text_color=TEXT_PRIMARY,
            fg_color="#060A10",
            border_width=1,
            border_color=BORDER_COLOR,
            height=38,
        )
        self.server_entry.insert(0, self.current_server)
        self.server_entry.pack(fill="x", padx=16, pady=(0, 10))

        # Save Button
        ctk.CTkButton(
            server_card,
            text="💾 Save & Apply Settings",
            font=FONT_BODY_BOLD,
            fg_color=CYAN_ACCENT,
            hover_color=CYAN_HOVER,
            text_color="#000000",
            height=38,
            corner_radius=10,
            command=self._handle_save,
        ).pack(anchor="w", padx=16, pady=(0, 16))

    def _handle_save(self):
        new_url = self.server_entry.get().strip()
        tts_enabled = self.tts_switch.get() == 1
        speed = int(self.speed_slider.get())
        self.on_save_settings(new_url, tts_enabled, speed)
