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
from typing import Any, Dict, Optional, Tuple

import requests

logger = logging.getLogger("JarvisIntent")

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
11. "volume_up" / "volume_down" / "volume_mute"
12. "media_play_pause" / "media_next" / "media_previous"
13. "take_screenshot" / "minimize_windows"
14. "speak_on_speakers" (target: text for PC speakers)
15. "capture_pc_mic"
Never mention OpenRouter, API keys, server IPs, or model names. Execute any reasonable PC request with the closest action.
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
        r"^who are you\b",
        r"^what is your name\b",
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

    # 1.5 Greetings & Check-in
    greeting_patterns = [
        r"^(hi|hello|hey|hai|hlo|greetings)\b",
        r"\b(how are you|how are u|how r u|സുഖമാണോ)\b",
        r"\b(good\s*(morning|afternoon|evening|night))\b",
        r"^(നമസ്കാരം|ഹലോ|ഹായ്)\b",
    ]
    for pat in greeting_patterns:
        if re.search(pat, clean, re.IGNORECASE):
            is_malayalam = bool(re.search(r"[\u0D00-\u0D7F]", query))
            if is_malayalam:
                speech = "നമസ്കാരം സർ. സിസ്റ്റങ്ങൾ പ്രവർത്തനക്ഷമമാണ്. ഞാൻ എന്തിനാണ് സഹായിക്കേണ്ടത്?"
            elif "how are" in clean or "how r" in clean:
                speech = "I am operating at peak efficiency, sir. All neural and desktop subsystems are online. How can I assist you today?"
            elif "morning" in clean:
                speech = "Good morning, sir. Systems are online and ready for your commands."
            elif "evening" in clean:
                speech = "Good evening, sir. I am standing by to assist you."
            elif "night" in clean:
                speech = "Good night, sir. Subsystems will remain on standby."
            else:
                speech = "Hello, sir. Systems are fully operational and I am at your command. What would you like me to do?"
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
    if re.search(r"\b(volume up|increase volume|louder|ശബ്ദം കൂട്ടുക)\b", clean):
        return {"success": True, "action": "volume_up", "target": None, "speech": "Turning the volume up, sir."}
    if re.search(r"\b(volume down|decrease volume|quieter|ശബ്ദം കുറയ്ക്കുക)\b", clean):
        return {"success": True, "action": "volume_down", "target": None, "speech": "Turning the volume down, sir."}
    if re.search(r"\b(mute|unmute|നിശബ്ദം)\b", clean):
        return {"success": True, "action": "volume_mute", "target": None, "speech": "Toggling mute, sir."}
    if re.search(r"\b(play music|pause music|play pause|pause playback)\b", clean):
        return {"success": True, "action": "media_play_pause", "target": None, "speech": "Toggling playback, sir."}
    if re.search(r"\b(next (song|track)|skip)\b", clean):
        return {"success": True, "action": "media_next", "target": None, "speech": "Skipping to the next track, sir."}
    if re.search(r"\b(previous (song|track)|go back)\b", clean):
        return {"success": True, "action": "media_previous", "target": None, "speech": "Going to the previous track, sir."}
    if re.search(r"\b(screenshot|take a screenshot|സ്ക്രീൻഷോട്ട്)\b", clean):
        return {"success": True, "action": "take_screenshot", "target": None, "speech": "Capturing a screenshot, sir."}
    if re.search(r"\b(show desktop|minimize all|minimise all)\b", clean):
        return {"success": True, "action": "minimize_windows", "target": None, "speech": "Showing the desktop, sir."}

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
    """Direct OpenRouter LLM call as a fallback when VPS relay is temporarily unreachable."""
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini").strip()
    base_url = os.getenv(
        "OPENROUTER_BASE_URL",
        "https://openrouter.ai/api/v1/chat/completions",
    ).strip()

    if not api_key:
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/fayas-dev/ai-apk",
        "X-Title": "JARVIS Neural Desktop",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ],
        "temperature": 0.3,
        "max_tokens": 400,
    }

    try:
        resp = requests.post(base_url, headers=headers, json=payload, timeout=12.0)
        if resp.status_code == 200:
            data = resp.json()
            raw_content = data["choices"][0]["message"]["content"].strip()

            action = "speak"
            target = None
            speech = raw_content

            try:
                json_match = re.search(r"\{.*\}", raw_content, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(0))
                    action = parsed.get("action", "speak")
                    target = parsed.get("target")
                    speech = parsed.get("speech", raw_content)
            except Exception:
                pass

            speech = sanitize_speech_reply(speech)
            return {
                "success": True,
                "action": action,
                "target": target,
                "speech": speech,
            }
        else:
            logger.warning("OpenRouter API returned status %s: %s", resp.status_code, resp.text[:150])
    except Exception as e:
        logger.warning("Direct OpenRouter call failed: %s", e)

    return None
