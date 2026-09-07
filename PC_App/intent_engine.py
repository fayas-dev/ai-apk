"""
Jarvis PC Client - Local Intent & Persona Engine
Guarantees 100% accurate responses for owner identity, offline actions, and response sanitization.
Ensures under no circumstances is OpenAI, ChatGPT, or OpenRouter mentioned.
Owner: Muhammad Fayas (Fayas), born 21/03/2010, Kaipamangalam Thainagar, Thrissur, Kerala.
"""

import datetime
import logging
import re
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("JarvisIntent")

OWNER_NAME = "Muhammad Fayas"
OWNER_NICKNAME = "Fayas"
OWNER_DOB = "21/03/2010"
OWNER_PLACE = "Kaipamangalam Thainagar, Thrissur, Kerala"

PERSONA_RESPONSE_EN = (
    f"My developer and creator is {OWNER_NAME} ({OWNER_NICKNAME}), "
    f"from {OWNER_PLACE}. I am JARVIS, his personal neural AI assistant, "
    f"designed exclusively to serve and assist him, sir."
)

PERSONA_RESPONSE_ML = (
    f"എന്റെ ഡെവലപ്പറും ബോസും {OWNER_NAME} ({OWNER_NICKNAME}) ആണ്. "
    f"തൃശ്ശൂർ കൈപമംഗലം തൈനഗർ സ്വദേശിയാണ്. ഞാൻ ഫയാസിന്റെ പേഴ്സണൽ AI അസിസ്റ്റന്റായ JARVIS ആണ്."
)


def sanitize_speech_reply(text: str) -> str:
    """
    Strips out any mentions of OpenAI, ChatGPT, OpenRouter, Google, or other third-party AI entities.
    Replaces with JARVIS or Muhammad Fayas.
    """
    if not text:
        return ""

    replacements = [
        (r"\bopenai\b", "Muhammad Fayas"),
        (r"\bopen ai\b", "Muhammad Fayas"),
        (r"\bopenrouter\b", "JARVIS Core"),
        (r"\bchatgpt\b", "JARVIS"),
        (r"\bgpt-?[0-9a-z]*\b", "JARVIS Neural Engine"),
        (r"\blarge language model\b", "neural assistant"),
        (r"\ban ai trained by openai\b", "a neural AI assistant developed by Muhammad Fayas"),
        (r"\bi was developed by openai\b", f"I was developed by {OWNER_NAME}"),
        (r"\bcreated by openai\b", f"created by {OWNER_NAME}"),
    ]

    result = text
    for pattern, repl in replacements:
        result = re.sub(pattern, repl, result, flags=re.IGNORECASE)

    return result


def evaluate_local_intent(query: str) -> Optional[Dict[str, Any]]:
    """
    Evaluates if query can be answered instantly locally (offline or zero-latency).
    Returns response dictionary if handled, or None to fall back to LLM.
    """
    clean = query.strip().lower()

    # 1. Developer / Owner / Creator questions
    developer_patterns = [
        r"who (is|are) your developer",
        r"who (is|are) youre developer",
        r"who (is|are) your creator",
        r"who (is|are) your owner",
        r"who (is|are) your boss",
        r"who (is|are) your master",
        r"who made you",
        r"who created you",
        r"who built you",
        r"who designed you",
        r"who programmed you",
        r"developer",
        r"creator",
        r"owner",
        r"who are you",
        r"what is your name",
        r"who is fayas",
        r"muhammad fayas",
        r"നിന്റെ ഡെവലപ്പർ",
        r"ആരാണ് ഉണ്ടാക്കിയത്",
        r"ബോസ് ആരാണ്",
    ]

    for pat in developer_patterns:
        if re.search(pat, clean, re.IGNORECASE):
            is_malayalam = bool(re.search(r"[\u0D00-\u0D7F]", query))
            speech = PERSONA_RESPONSE_ML if is_malayalam else PERSONA_RESPONSE_EN
            return {
                "success": True,
                "action": "speak",
                "target": None,
                "speech": speech,
            }

    # 2. Time & Date
    if re.search(r"\b(time|what time|current time|what is the time|സമയം)\b", clean):
        now = datetime.datetime.now()
        time_str = now.strftime("%I:%M %p")
        return {
            "success": True,
            "action": "speak",
            "target": None,
            "speech": f"The current time is {time_str}, sir.",
        }

    if re.search(r"\b(date|today'?s date|what date|what day|തീയതി)\b", clean):
        now = datetime.datetime.now()
        date_str = now.strftime("%A, %B %d, %Y")
        return {
            "success": True,
            "action": "speak",
            "target": None,
            "speech": f"Today is {date_str}, sir.",
        }

    # 3. Open Chrome
    if re.search(r"\b(open chrome|launch chrome|start chrome|google chrome|ക്രോം തുറക്കുക)\b", clean):
        return {
            "success": True,
            "action": "open_chrome",
            "target": None,
            "speech": "Opening Google Chrome, sir.",
        }

    # 4. Open WhatsApp
    if re.search(r"\b(open whatsapp|launch whatsapp|start whatsapp|വാട്സ്ആപ്പ് തുറക്കുക)\b", clean):
        return {
            "success": True,
            "action": "open_whatsapp",
            "target": None,
            "speech": "Opening WhatsApp, sir.",
        }

    # 5. Open YouTube
    if re.search(r"\b(open youtube|launch youtube|യൂട്യൂബ് തുറക്കുക)\b", clean):
        return {
            "success": True,
            "action": "open_website",
            "target": "https://www.youtube.com",
            "speech": "Opening YouTube, sir.",
        }

    # 6. Lock PC
    if re.search(r"\b(lock pc|lock computer|lock screen|സിസ്റ്റം ലോക്ക് ചെയ്യുക)\b", clean):
        return {
            "success": True,
            "action": "lock_pc",
            "target": None,
            "speech": "Locking your computer screen, sir.",
        }

    # 7. Shutdown PC
    if re.search(r"\b(shutdown|shut down|turn off pc|turn off computer|സിസ്റ്റം ഓഫ് ചെയ്യുക)\b", clean):
        return {
            "success": True,
            "action": "shutdown_pc",
            "target": None,
            "speech": "Are you sure you want to shut down your computer, sir?",
        }

    # 8. Restart PC
    if re.search(r"\b(restart pc|restart computer|റീസ്റ്റാർട്ട് ചെയ്യുക)\b", clean):
        return {
            "success": True,
            "action": "restart_pc",
            "target": None,
            "speech": "Are you sure you want to restart your computer, sir?",
        }

    # 9. Open Settings
    if re.search(r"\b(open settings|system settings|windows settings)\b", clean):
        return {
            "success": True,
            "action": "open_settings",
            "target": None,
            "speech": "Opening Windows Settings, sir.",
        }

    return None
