"""
Robust wake-phrase matching for noisy speech-to-text.
Handles English, Malayalam, Manglish, and common STT mishears of "Jarvis".
"""

from __future__ import annotations

import re
from typing import Optional, Tuple

WAKE_PHRASES = [
    "hey jarvis",
    "okay jarvis",
    "ok jarvis",
    "hello jarvis",
    "hi jarvis",
    "yo jarvis",
    "jarvis",
]

_STT_FIXES = [
    (r"jar\s*vis+", "jarvis"),
    (r"jar\s*vice", "jarvis"),
    (r"jar\s*wis", "jarvis"),
    (r"jarv(?:is|ish|iz|es|as|us)", "jarvis"),
    (r"jervis", "jarvis"),
    (r"jarvice", "jarvis"),
    (r"jarwis", "jarvis"),
    (r"\bcharvis\b", "jarvis"),
    (r"\btravis\b", "jarvis"),
    (r"\bharvey'?s?\b", "jarvis"),
    (r"\bjar vis\b", "jarvis"),
    (r"\bhey service\b", "hey jarvis"),
    (r"\bok(?:ay)? service\b", "ok jarvis"),
    (r"\bhello service\b", "hello jarvis"),
    (r"\bhi service\b", "hi jarvis"),
    (r"ജാർവിസ്", "jarvis"),
    (r"ജാര്‍വിസ്", "jarvis"),
    (r"ജാർവിസ്", "jarvis"),
    (r"ഹേയ്?\s*ജാർവിസ്", "hey jarvis"),
    (r"ഹേയ്?\s*ജാർവിസ", "hey jarvis"),
    (r"ഹേയ്?\s*ജാർവിസ്", "hey jarvis"),
    (r"ഹായ്\s*ജാർവിസ്", "hi jarvis"),
]


def normalize_speech(text: str) -> str:
    if not text:
        return ""
    t = text.lower().strip()
    t = t.replace("’", "'").replace("`", "'")
    for pattern, repl in _STT_FIXES:
        t = re.sub(pattern, repl, t, flags=re.IGNORECASE)
    t = re.sub(r"[^\w\s\u0D00-\u0D7F]", " ", t, flags=re.UNICODE)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def parse_wake_phrase(text: str) -> Tuple[bool, Optional[str]]:
    """
    Returns (wake_detected, remaining_command_or_None).
    Remaining command is only returned when the user spoke the request in the same utterance.
    """
    original = (text or "").strip()
    if not original:
        return False, None

    normalized = normalize_speech(original)
    if not normalized:
        return False, None

    for phrase in sorted(WAKE_PHRASES, key=len, reverse=True):
        idx = normalized.find(phrase)
        if idx == -1:
            continue
        # Avoid matching "jarvis" inside unrelated longer tokens.
        before = normalized[:idx]
        after = normalized[idx + len(phrase) :]
        if before and before[-1].isalnum():
            continue
        if after and after[0].isalnum():
            continue
        command = after.strip(" ,.-")
        return True, command if command else None

    return False, None


def strip_wake_from_command(text: str) -> str:
    found, remainder = parse_wake_phrase(text)
    if found and remainder:
        return remainder
    if found:
        return ""
    return (text or "").strip()
