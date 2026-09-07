"""
Jarvis System Actions & Whitelist Page
Catalog of safe actions with one-click test execution and real-time security audit log.
"""

import datetime
from typing import Callable

import customtkinter as ctk

from gui.theme import (
    BORDER_COLOR,
    CARD_BG,
    CYAN_ACCENT,
    DARK_BG,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_CODE,
    FONT_HEADING,
    FONT_SMALL,
    FONT_SUBHEADING,
    NEON_AMBER,
    NEON_GREEN,
    NEON_RED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)


class ActionsPage(ctk.CTkFrame):
    def __init__(self, master, on_execute_action: Callable[[str], None], **kwargs):
        super().__init__(master, fg_color=DARK_BG, **kwargs)
        self.on_execute_action = on_execute_action

        self._setup_ui()

    def _setup_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(20, 10))

        ctk.CTkLabel(
            header,
            text="SYSTEM ACTIONS & WHITELIST REGISTRY",
            font=FONT_HEADING,
            text_color=CYAN_ACCENT,
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Safe action whitelist enforced on Windows. Arbitrary shell commands are blocked.",
            font=FONT_SMALL,
            text_color=TEXT_SECONDARY,
        ).pack(anchor="w")

        content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=30, pady=10)

        # Action Catalog
        ctk.CTkLabel(content, text="APPROVED SYSTEM ACTIONS", font=FONT_SUBHEADING, text_color=TEXT_SECONDARY).pack(anchor="w", pady=(10, 8))

        actions = [
            ("🌐 Google Chrome", "open_chrome", "Opens Google Chrome browser via predefined launcher", NEON_GREEN, False),
            ("💬 WhatsApp", "open_whatsapp", "Launches WhatsApp Windows app or Web client", NEON_GREEN, False),
            ("📁 File Explorer", "open_file_explorer", "Opens Windows File Explorer safely", NEON_GREEN, False),
            ("⚙️ Windows Settings", "open_settings", "Opens Windows 10/11 System Settings panel", NEON_GREEN, False),
            ("🔒 Lock Workstation", "lock_pc", "Locks the computer immediately via Windows API", NEON_AMBER, False),
            ("🛑 Shutdown Computer", "shutdown_pc", "Requires 2-step user confirmation before execution", NEON_RED, True),
            ("🔄 Restart Computer", "restart_pc", "Requires 2-step user confirmation before execution", NEON_RED, True),
        ]

        for title, action_id, desc, color, protected in actions:
            card = ctk.CTkFrame(content, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
            card.pack(fill="x", pady=4)

            left = ctk.CTkFrame(card, fg_color="transparent")
            left.pack(side="left", padx=16, pady=10)

            title_row = ctk.CTkFrame(left, fg_color="transparent")
            title_row.pack(anchor="w")

            ctk.CTkLabel(title_row, text=title, font=FONT_BODY_BOLD, text_color=TEXT_PRIMARY).pack(side="left")
            if protected:
                ctk.CTkLabel(
                    title_row,
                    text="🔒 PROTECTED (CONFIRMATION REQUIRED)",
                    font=FONT_SMALL,
                    text_color=NEON_RED,
                    fg_color="#380C16",
                    corner_radius=6,
                    padx=6,
                ).pack(side="left", padx=10)

            ctk.CTkLabel(left, text=desc, font=FONT_SMALL, text_color=TEXT_SECONDARY).pack(anchor="w", pady=(2, 0))

            btn = ctk.CTkButton(
                card,
                text="Execute",
                font=FONT_SMALL,
                fg_color="#18273A",
                hover_color="#243B55",
                text_color=color,
                border_width=1,
                border_color="#1F3A4D",
                width=85,
                height=32,
                corner_radius=8,
                command=lambda a=action_id: self.on_execute_action(a),
            )
            btn.pack(side="right", padx=16, pady=10)

        # Audit Log Section
        ctk.CTkLabel(content, text="SECURITY AUDIT & EXECUTION LOG", font=FONT_SUBHEADING, text_color=TEXT_SECONDARY).pack(anchor="w", pady=(20, 8))

        self.log_container = ctk.CTkFrame(content, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        self.log_container.pack(fill="both", expand=True, pady=(0, 20))

        self.log_text = ctk.CTkTextbox(
            self.log_container,
            fg_color="#060A10",
            text_color=TEXT_PRIMARY,
            font=FONT_CODE,
            height=130,
            border_width=0,
        )
        self.log_text.pack(fill="both", expand=True, padx=12, pady=12)
        self.add_log_entry("SYSTEM_INIT", "Safe action whitelist registry initialized.")

    def add_log_entry(self, action_name: str, message: str, status: str = "SUCCESS"):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        entry = f"[{now}] [{status}] ACTION: {action_name.upper()} -> {message}\n"
        self.log_text.insert("end", entry)
        self.log_text.see("end")
