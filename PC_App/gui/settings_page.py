"""
Jarvis Settings & Voice Configuration Page
Control TTS voice properties, wake-phrase sensitivity, VPS endpoints, and Mobile QR Pairing.
"""

import os
from pathlib import Path
from typing import Callable

import customtkinter as ctk
from PIL import Image

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
from qr_generator import generate_pairing_qr_code


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
        self.qr_image = None

        self._setup_ui()

    def _setup_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(20, 10))

        ctk.CTkLabel(
            header,
            text="JARVIS SYSTEM & MOBILE PAIRING CONFIGURATION",
            font=FONT_HEADING,
            text_color=CYAN_ACCENT,
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Pair your mobile device, calibrate voice synthesis, and view owner profile.",
            font=FONT_SMALL,
            text_color=TEXT_SECONDARY,
        ).pack(anchor="w")

        content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=30, pady=10)

        # 1. Owner Profile Card
        owner_card = ctk.CTkFrame(content, fg_color=CARD_BG, corner_radius=14, border_width=1, border_color=BORDER_COLOR)
        owner_card.pack(fill="x", pady=8)

        ctk.CTkLabel(owner_card, text="AUTHORIZED MASTER & OWNER", font=FONT_SUBHEADING, text_color=CYAN_ACCENT).pack(anchor="w", padx=16, pady=(14, 4))
        ctk.CTkLabel(owner_card, text="Owner: Muhammad Fayas  |  DOB: 21/03/2010", font=FONT_BODY_BOLD, text_color=TEXT_PRIMARY).pack(anchor="w", padx=16, pady=2)
        ctk.CTkLabel(owner_card, text="Origin: Kaipamangalam, Thainagar, Thrissur, Kerala", font=FONT_SMALL, text_color=TEXT_SECONDARY).pack(anchor="w", padx=16, pady=(0, 14))

        # 2. Mobile Device Pairing & QR Code Card
        qr_card = ctk.CTkFrame(content, fg_color=CARD_BG, corner_radius=14, border_width=1, border_color=BORDER_COLOR)
        qr_card.pack(fill="x", pady=8)

        ctk.CTkLabel(qr_card, text="📱 MOBILE DEVICE QR CODE PAIRING", font=FONT_SUBHEADING, text_color=CYAN_ACCENT).pack(anchor="w", padx=16, pady=(14, 4))
        ctk.CTkLabel(
            qr_card,
            text="Scan to identify this PC, then enter the private relay address and pairing code on your phone. Network addresses and credentials are not displayed here.",
            font=FONT_SMALL,
            text_color=TEXT_SECONDARY,
            wraplength=600,
        ).pack(anchor="w", padx=16, pady=(0, 10))

        qr_path = generate_pairing_qr_code(vps_url=self.current_server)
        if os.path.exists(qr_path):
            try:
                pil_img = Image.open(qr_path)
                self.qr_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(160, 160))
                qr_label = ctk.CTkLabel(qr_card, image=self.qr_image, text="")
                qr_label.pack(anchor="w", padx=20, pady=8)
            except Exception as e:
                ctk.CTkLabel(qr_card, text=f"Error loading QR: {e}", text_color="red").pack(padx=16, pady=8)

        # 3. Voice Settings Card
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
            command=lambda: self.on_test_voice("All neural systems and voice channels are calibrated and operational, sir."),
        ).pack(anchor="w", padx=16, pady=(8, 14))

        # 4. Server Settings Card (no IP / URL displayed)
        server_card = ctk.CTkFrame(content, fg_color=CARD_BG, corner_radius=14, border_width=1, border_color=BORDER_COLOR)
        server_card.pack(fill="x", pady=8)

        ctk.CTkLabel(server_card, text="SECURE NEURAL LINK", font=FONT_SUBHEADING, text_color=CYAN_ACCENT).pack(anchor="w", padx=16, pady=(14, 8))
        ctk.CTkLabel(
            server_card,
            text="Server address, ports, and API keys are stored privately and never shown on screen. Pair the phone with the QR code above.",
            font=FONT_SMALL,
            text_color=TEXT_SECONDARY,
            wraplength=620,
        ).pack(anchor="w", padx=16, pady=(0, 10))

        # Save Button
        ctk.CTkButton(
            server_card,
            text="💾 Save Voice Settings",
            font=FONT_BODY_BOLD,
            fg_color=CYAN_ACCENT,
            hover_color=CYAN_HOVER,
            text_color="#000000",
            height=38,
            corner_radius=10,
            command=self._handle_save,
        ).pack(anchor="w", padx=16, pady=(0, 16))

    def _handle_save(self):
        tts_enabled = self.tts_switch.get() == 1
        speed = int(self.speed_slider.get())
        self.on_save_settings(self.current_server, tts_enabled, speed)
