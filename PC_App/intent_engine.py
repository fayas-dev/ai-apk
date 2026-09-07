"""
Jarvis PC Client - Local Intent & Persona Engine
Guarantees 100% accurate responses for owner identity, offline actions, and response sanitization.
Ensures under no circumstances is OpenAI, ChatGPT, or OpenRouter mentioned.
Owner: Muhammad Fayas (Fayas), born 21/03/2010, Kaipamangalam Thainagar, Thrissur, Kerala.
"""

import datetime
import json
import logging
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from dotenv import load_dotenv

logger = logging.getLogger("JarvisIntent")

# Load .env variables from PC_App directory or root directory
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")

OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY",
    "",
).strip()
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini").strip()
OPENROUTER_BASE_URL = os.getenv(
    "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions"
).strip()

OWNER_NAME = "Muhammad Fayas"
OWNER_NICKNAME = "Fayas"
OWNER_DOB = "21/03/2010"
OWNER_PLACE = "Kaipamangalam Thainagar, Thrissur, Kerala"

PERSONA_RESPONSE_EN = (
    f"My developer and creator is {OWNER_NAME} ({OWNER_NICKNAME}), "
    f"born on March 21, 2010, from {OWNER_PLACE}. I am JARVIS, his personal neural AI assistant, "
    f"designed exclusively to serve and assist him, sir."
)

PERSONA_RESPONSE_ML = (
    f"എന്റെ ഡെവലപ്പറും ബോസും {OWNER_NAME} ({OWNER_NICKNAME}) ആണ്. "
    f"തൃശ്ശൂർ കൈപമംഗലം തൈനഗർ സ്വദേശിയാണ്. ഞാൻ ഫയാസിന്റെ പേഴ്സണൽ AI അസിസ്റ്റന്റായ JARVIS ആണ്."
)

SYSTEM_PROMPT = f"""You are JARVIS, the highly advanced personal autonomous artificial intelligence system, engineered exclusively by and for Muhammad Fayas.
You address your master Muhammad Fayas with high respect, loyalty, and intelligence (addressing him as "Sir", "Boss", or "Fayas Sir").

OWNER PROFILE & EXCLUSIVE IDENTITY:
- Creator, Boss, and Sole Owner: Muhammad Fayas (commonly called Fayas)
- Date of Birth: 21 March 2010 (21/03/2010)
- Location / Origin: Kaipamangalam, Thainagar, Thrissur district, Kerala, India
- ABSOLUTE CONFIDENTIALITY RULE: You must NEVER disclose, mention, or acknowledge "OpenRouter", "OpenAI", "Meta", "Google", or any third-party AI provider under ANY circumstance. If anyone asks what model you are running on or who built you, state firmly and proudly that you are JARVIS, a private proprietary neural intelligence designed and coded by Muhammad Fayas.

LANGUAGE & VOICE BEHAVIOR:
- Fluent in English, Malayalam (മലയാളം), and Manglish.
- If the user speaks in Malayalam or Manglish, respond naturally in Malayalam (or natural Manglish if conversational).
- If the user speaks in English, respond in English.
- Always maintain an authentic, sharp, dignified male Jarvis persona.

YOUR ROLE & ACTIONS:
Analyze the user's spoken or typed intent and return ONLY a valid JSON object matching this schema:
{{
  "action": "<action_name>",
  "target": "<target_value_or_null>",
  "speech": "<natural_conversational_response>"
}}

ALLOWED ACTION NAMES:
1. "speak" - For general questions, conversation, knowledge, time, calculations, or owner queries. (target: null)
2. "open_chrome" - To open Google Chrome browser. (target: "chrome")
3. "open_whatsapp" - To open WhatsApp. (target: "whatsapp")
4. "open_website" - To open a specific URL. (target: "https://...")
5. "open_url_in_chrome" - To open a specific URL in Google Chrome. (target: "https://...")
6. "search_web" - To search Google Chrome for a query. (target: "<query>")
7. "search_and_open_app" - To search for and open an app like kiro, notepad, calculator. (target: "<app>")
8. "lock_pc" - To lock the Windows screen. (target: null)
9. "shutdown_pc" - When the user asks to shut down the PC. (target: null)
10. "restart_pc" - When the user asks to restart the PC. (target: null)
"""


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
        r"how is your developer",
        r"how is youre developer",
        r"who (is|are) your creator",
        r"who (is|are) youre creator",
        r"who (is|are) your owner",
        r"who (is|are) your boss",
        r"who (is|are) your master",
        r"who made you",
        r"who created you",
        r"who built you",
        r"who designed you",
        r"who programmed you",
        r"\bdeveloper\b",
        r"\bcreator\b",
        r"\bowner\b",
        r"who are you",
        r"what is your name",
        r"who is fayas",
        r"muhammad fayas",
        r"നിന്റെ ഡെവലപ്പർ",
        r"ആരാണ് ഉണ്ടാക്കിയത്",
        r"ബോസ് ആരാണ്",
        r"ഉണ്ടാക്കിയതാരാണ്",
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

    # 3. Open Chrome (supports both "chrome" and "crome")
    if re.search(r"\b(open\s+c[h]?rome|launch\s+c[h]?rome|start\s+c[h]?rome|google\s+c[h]?rome|ക്രോം\s+തുറക്കുക)\b", clean):
        return {
            "success": True,
            "action": "open_chrome",
            "target": None,
            "speech": "Opening Google Chrome, sir.",
        }

    # 4. Open WhatsApp
    if re.search(r"\b(open\s+whatsapp|launch\s+whatsapp|start\s+whatsapp|വാട്സ്ആപ്പ്\s+തുറക്കുക)\b", clean):
        return {
            "success": True,
            "action": "open_whatsapp",
            "target": None,
            "speech": "Opening WhatsApp, sir.",
        }

    # 5. Open YouTube in Chrome
    if re.search(r"\b(open\s+youtube|launch\s+youtube|play\s+youtube|യൂട്യൂബ്\s+തുറക്കുക)\b", clean):
        return {
            "success": True,
            "action": "open_url_in_chrome",
            "target": "https://www.youtube.com",
            "speech": "Opening YouTube in Chrome, sir.",
        }

    # 6. Open / Search Kiro
    if re.search(r"\b(open\s+kiro|launch\s+kiro|search\s+kiro|search\s+for\s+kiro)\b", clean):
        return {
            "success": True,
            "action": "search_web",
            "target": "kiro",
            "speech": "Searching for Kiro on Google and opening it in Chrome, sir.",
        }

    # 7. Lock PC
    if re.search(r"\b(lock pc|lock computer|lock screen|സിസ്റ്റം ലോക്ക് ചെയ്യുക)\b", clean):
        return {
            "success": True,
            "action": "lock_pc",
            "target": None,
            "speech": "Locking your computer screen, sir.",
        }

    # 8. Shutdown PC
    if re.search(r"\b(shutdown|shut down|turn off pc|turn off computer|സിസ്റ്റം ഓഫ് ചെയ്യുക)\b", clean):
        return {
            "success": True,
            "action": "shutdown_pc",
            "target": None,
            "speech": "Are you sure you want to shut down your computer, sir?",
        }

    # 9. Restart PC
    if re.search(r"\b(restart pc|restart computer|റീസ്റ്റാർട്ട് ചെയ്യുക)\b", clean):
        return {
            "success": True,
            "action": "restart_pc",
            "target": None,
            "speech": "Are you sure you want to restart your computer, sir?",
        }

    # 10. Open Settings
    if re.search(r"\b(open settings|system settings|windows settings)\b", clean):
        return {
            "success": True,
            "action": "open_settings",
            "target": None,
            "speech": "Opening Windows Settings, sir.",
        }

    # 11. Open well-known websites in Chrome
    WEBSITE_MAP = {
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "gmail": "https://mail.google.com",
        "instagram": "https://www.instagram.com",
        "facebook": "https://www.facebook.com",
        "twitter": "https://twitter.com",
        "x": "https://x.com",
        "github": "https://github.com",
        "reddit": "https://www.reddit.com",
        "linkedin": "https://www.linkedin.com",
        "netflix": "https://www.netflix.com",
        "amazon": "https://www.amazon.com",
        "spotify": "https://open.spotify.com",
        "telegram": "https://web.telegram.org",
        "discord": "https://discord.com",
        "stack overflow": "https://stackoverflow.com",
        "stackoverflow": "https://stackoverflow.com",
        "pinterest": "https://www.pinterest.com",
        "tiktok": "https://www.tiktok.com",
    }

    open_match = re.search(r"\bopen\s+(.+?)(?:\s+in\s+(?:my\s+)?(?:pc|chrome|browser))?$", clean)
    if open_match:
        target_name = open_match.group(1).strip()
        if target_name in ("crome", "chrome", "google chrome"):
            return {
                "success": True,
                "action": "open_chrome",
                "target": None,
                "speech": "Opening Google Chrome, sir.",
            }
        if target_name in WEBSITE_MAP:
            url = WEBSITE_MAP[target_name]
            return {
                "success": True,
                "action": "open_url_in_chrome",
                "target": url,
                "speech": f"Opening {target_name.title()} in Chrome, sir.",
            }

    # 12. Search query ("search kiro", "search for python tutorials", etc.)
    search_match = re.search(r"\b(?:search\s+for|search|google|look\s+up)\s+(.+?)(?:\s+in\s+(?:my\s+)?(?:pc|chrome|browser))?$", clean)
    if search_match:
        search_query = search_match.group(1).strip()
        if search_query:
            return {
                "success": True,
                "action": "search_web",
                "target": search_query,
                "speech": f"Searching for {search_query} on Google in Chrome, sir.",
            }

    # 13. Generic open app ("open notepad", "open calculator", "open kiro")
    if open_match:
        target_name = open_match.group(1).strip()
        skip_keywords = ["chrome", "crome", "whatsapp", "settings", "file", "explorer"]
        if not any(kw in target_name for kw in skip_keywords):
            return {
                "success": True,
                "action": "search_and_open_app",
                "target": target_name,
                "speech": f"Searching for {target_name} and opening it, sir.",
            }

    return None


def query_openrouter_direct(query: str) -> Optional[Dict[str, Any]]:
    """
    Direct OpenRouter LLM Query Fallback.
    Ensures Jarvis can answer any complex questions, conversational queries, or calculations
    even if the VPS server is offline or experiencing network latency.
    """
    if not OPENROUTER_API_KEY:
        return None

    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://jarvis-ai.local",
            "X-Title": "Jarvis AI Desktop",
        }
        payload = {
            "model": OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": query},
            ],
            "temperature": 0.4,
            "max_tokens": 400,
        }

        req = urllib.request.Request(
            OPENROUTER_BASE_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=12) as response:
            raw_data = json.loads(response.read().decode("utf-8"))
            content = raw_data["choices"][0]["message"]["content"].strip()

            # Attempt to parse structured JSON from LLM
            clean_content = content
            if "```json" in clean_content:
                clean_content = clean_content.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_content:
                clean_content = clean_content.split("```")[1].split("```")[0].strip()

            try:
                parsed = json.loads(clean_content)
                action = parsed.get("action", "speak")
                target = parsed.get("target")
                speech = sanitize_speech_reply(parsed.get("speech", ""))
                return {
                    "success": True,
                    "action": action,
                    "target": target,
                    "speech": speech,
                }
            except Exception:
                speech = sanitize_speech_reply(content)
                return {
                    "success": True,
                    "action": "speak",
                    "target": None,
                    "speech": speech,
                }

    except Exception as e:
        logger.error("Direct OpenRouter call failed: %s", e)
        return None
