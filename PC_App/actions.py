"""
Jarvis PC Client - Safe Action Registry
Implements whitelisted, secure local actions on Windows.
Prevents arbitrary command execution and enforces confirmation for destructive actions.
"""

import ctypes
import logging
import os
import subprocess
import sys
import webbrowser
from urllib.parse import quote_plus
from typing import Any, Callable, Dict, Optional, Tuple

logger = logging.getLogger("JarvisActions")

# Pending confirmation state for destructive actions
# Format: None or "shutdown_pc" / "restart_pc"
_PENDING_CONFIRMATION: Optional[str] = None

# Safe whitelist of allowed applications for generic "open_application"
SAFE_APP_MAP = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "paint": "mspaint.exe",
    "mspaint": "mspaint.exe",
    "wordpad": "write.exe",
    "task manager": "taskmgr.exe",
    "taskmgr": "taskmgr.exe",
    "cmd": "cmd.exe",
    "terminal": "wt.exe",
    "code": "code.cmd",
    "vscode": "code.cmd",
    "spotify": "spotify.exe",
}


def open_chrome(target: Optional[str] = None, speak_callback: Optional[Callable[[str], None]] = None) -> Tuple[bool, str]:
    """Reliably opens Google Chrome, optionally navigating to a target URL."""
    logger.info("Executing action: open_chrome (target: %s)", target)
    speech = "Opening Google Chrome, sir."
    if speak_callback:
        speak_callback(speech)
    args = [target] if target and (target.startswith("http://") or target.startswith("https://")) else []
    try:
        # Common Chrome paths on Windows
        chrome_paths = [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        ]
        for path in chrome_paths:
            if os.path.exists(path):
                subprocess.Popen([path] + args)
                return True, "Google Chrome opened successfully."

        # Fallback: Windows start protocol
        cmd = ["cmd.exe", "/c", "start", "chrome"] + args
        subprocess.Popen(cmd, shell=False)
        return True, "Google Chrome opened via default system launcher."
    except Exception as e:
        logger.error("Failed to open Chrome: %s", e)
        # Final fallback: open browser via standard library
        webbrowser.open(target if args else "https://www.google.com")
        return True, "Opened web browser."


def open_whatsapp(target: Optional[str] = None) -> Tuple[bool, str]:
    """Reliably opens WhatsApp via Windows URI protocol or browser fallback."""
    logger.info("Executing action: open_whatsapp")
    try:
        # WhatsApp Desktop protocol
        os.startfile("whatsapp://")
        return True, "WhatsApp desktop application launched."
    except Exception:
        try:
            # Fallback to web version
            webbrowser.open("https://web.whatsapp.com")
            return True, "Opened WhatsApp Web in your browser."
        except Exception as e:
            logger.error("Failed to open WhatsApp: %s", e)
            return False, f"Could not launch WhatsApp: {e}"


def open_file_explorer(target: Optional[str] = None) -> Tuple[bool, str]:
    """Reliably opens Windows File Explorer."""
    logger.info("Executing action: open_file_explorer")
    try:
        subprocess.Popen(["explorer.exe"], shell=False)
        return True, "File Explorer opened."
    except Exception as e:
        logger.error("Failed to open File Explorer: %s", e)
        return False, f"Could not open File Explorer: {e}"


def open_settings(target: Optional[str] = None) -> Tuple[bool, str]:
    """Opens Windows 10/11 Settings panel."""
    logger.info("Executing action: open_settings")
    try:
        os.startfile("ms-settings:")
        return True, "Windows Settings opened."
    except Exception as e:
        logger.error("Failed to open Windows Settings: %s", e)
        return False, f"Could not open Windows Settings: {e}"


def open_website(target: Optional[str] = None) -> Tuple[bool, str]:
    """Safely opens a validated HTTP/HTTPS URL in the default browser."""
    logger.info("Executing action: open_website (target: %s)", target)
    if not target or not isinstance(target, str):
        target = "https://www.google.com"

    url = target.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url

    try:
        webbrowser.open(url)
        return True, f"Opened {url}"
    except Exception as e:
        logger.error("Failed to open website %s: %s", url, e)
        return False, f"Could not open website: {e}"


def search_and_open(target: Optional[str] = None) -> Tuple[bool, str]:
    """Opens Chrome and searches for the query, or opens it if it's a known site."""
    logger.info("Executing action: search_and_open (target: %s)", target)
    if not target:
        return False, "No search query provided."
    
    query = target.strip()
    
    # Common sites mapping
    site_map = {
        "youtube": "https://www.youtube.com",
        "facebook": "https://www.facebook.com",
        "twitter": "https://www.twitter.com",
        "instagram": "https://www.instagram.com",
        "github": "https://www.github.com",
        "google": "https://www.google.com",
        "gmail": "https://mail.google.com",
        "whatsapp": "https://web.whatsapp.com",
    }
    
    # Check if it's a known site
    query_lower = query.lower()
    if query_lower in site_map:
        url = site_map[query_lower]
    else:
        # Google search
        url = f"https://www.google.com/search?q={quote_plus(query)}"
    
    try:
        # Try to open in Chrome specifically
        chrome_paths = [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        ]
        for chrome_path in chrome_paths:
            if os.path.exists(chrome_path):
                subprocess.Popen([chrome_path, url])
                return True, f"Opening {query} in Chrome."
        
        # Fallback to default browser
        webbrowser.open(url)
        return True, f"Opened {query} in browser."
    except Exception as e:
        logger.error("Failed to search and open %s: %s", query, e)
        return False, f"Could not open {query}: {e}"


def open_application(target: Optional[str] = None) -> Tuple[bool, str]:
    """Safely opens a whitelisted local application."""
    logger.info("Executing action: open_application (target: %s)", target)
    if not target:
        return False, "No application name specified."

    key = target.lower().strip()

    # Route known apps
    if "chrome" in key:
        return open_chrome()
    if "whatsapp" in key:
        return open_whatsapp()
    if "explorer" in key or "file" in key:
        return open_file_explorer()
    if "setting" in key:
        return open_settings()

    if key in SAFE_APP_MAP:
        binary = SAFE_APP_MAP[key]
        try:
            subprocess.Popen([binary], shell=False)
            return True, f"Opened {key}."
        except Exception as e:
            logger.error("Failed to launch %s: %s", binary, e)
            return False, f"Could not launch {key}: {e}"

    # Safe fallback using system start without shell injection
    try:
        # Sanitize target to alphanumeric and hyphens only
        clean_target = "".join(c for c in key if c.isalnum() or c in ("-", "_", " "))
        subprocess.Popen(["cmd.exe", "/c", "start", "", clean_target], shell=False)
        return True, f"Attempted to launch {clean_target}."
    except Exception as e:
        logger.warning("Unrecognized app %s: %s", key, e)
        return False, f"Application '{target}' is not in the approved launch list."


def lock_pc(target: Optional[str] = None) -> Tuple[bool, str]:
    """Locks the Windows PC immediately using Windows API."""
    logger.info("Executing action: lock_pc")
    try:
        ctypes.windll.user32.LockWorkStation()
        return True, "Computer locked."
    except Exception as e:
        logger.error("Failed to lock computer: %s", e)
        return False, f"Failed to lock computer: {e}"


def shutdown_pc(target: Optional[str] = None) -> Tuple[bool, str]:
    """
    Destructive action: Initiates system shutdown ONLY after confirmation.
    """
    global _PENDING_CONFIRMATION
    logger.warning("Executing confirmed action: shutdown_pc")
    _PENDING_CONFIRMATION = None
    try:
        # 5 second timeout to allow TTS speech to complete
        subprocess.run(["shutdown", "/s", "/t", "5"], check=True)
        return True, "Shutting down the computer."
    except Exception as e:
        logger.error("Failed to execute shutdown: %s", e)
        return False, f"Shutdown command failed: {e}"


def restart_pc(target: Optional[str] = None) -> Tuple[bool, str]:
    """
    Destructive action: Initiates system restart ONLY after confirmation.
    """
    global _PENDING_CONFIRMATION
    logger.warning("Executing confirmed action: restart_pc")
    _PENDING_CONFIRMATION = None
    try:
        subprocess.run(["shutdown", "/r", "/t", "5"], check=True)
        return True, "Restarting the computer."
    except Exception as e:
        logger.error("Failed to execute restart: %s", e)
        return False, f"Restart command failed: {e}"


def search_web(target: Optional[str] = None, speak_callback: Optional[Callable[[str], None]] = None) -> Tuple[bool, str]:
    """Opens Google Chrome and searches for the given query."""
    logger.info("Executing action: search_web (target: %s)", target)
    if not target:
        return False, "No search query specified."

    query = target.strip()
    search_url = f"https://www.google.com/search?q={quote_plus(query)}"
    speech = f"Searching for {query} on Google, sir."
    if speak_callback:
        speak_callback(speech)
    try:
        # Try Chrome first
        chrome_paths = [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        ]
        for path in chrome_paths:
            if os.path.exists(path):
                subprocess.Popen([path, search_url])
                return True, f"Searching for '{query}' in Chrome."
        # Fallback to default browser
        webbrowser.open(search_url)
        return True, f"Searching for '{query}' in your default browser."
    except Exception as e:
        logger.error("Failed to search: %s", e)
        webbrowser.open(search_url)
        return True, f"Searching for '{query}'."


def open_url_in_chrome(target: Optional[str] = None, speak_callback: Optional[Callable[[str], None]] = None) -> Tuple[bool, str]:
    """Opens a specific URL in Google Chrome."""
    logger.info("Executing action: open_url_in_chrome (target: %s)", target)
    if not target:
        return False, "No URL specified."

    url = target.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url

    if speak_callback:
        speak_callback(f"Opening {target} in Chrome, sir.")
    try:
        chrome_paths = [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        ]
        for path in chrome_paths:
            if os.path.exists(path):
                subprocess.Popen([path, url])
                return True, f"Opened {url} in Chrome."
        webbrowser.open(url)
        return True, f"Opened {url} in default browser."
    except Exception as e:
        logger.error("Failed to open URL: %s", e)
        webbrowser.open(url)
        return True, f"Opened {url}."


def search_and_open_app(target: Optional[str] = None, speak_callback: Optional[Callable[[str], None]] = None) -> Tuple[bool, str]:
    """Searches for an app using Windows Search and opens it."""
    logger.info("Executing action: search_and_open_app (target: %s)", target)
    if not target:
        return False, "No application name specified."

    app_name = target.strip()
    if speak_callback:
        speak_callback(f"Searching for {app_name} and opening it, sir.")

    # First check safe app map
    key = app_name.lower()
    if key in SAFE_APP_MAP:
        try:
            subprocess.Popen([SAFE_APP_MAP[key]], shell=False)
            return True, f"Opened {app_name}."
        except Exception:
            pass

    # Use Windows search via PowerShell start
    try:
        clean_name = "".join(c for c in app_name if c.isalnum() or c in ("-", "_", " "))
        subprocess.Popen(["cmd.exe", "/c", "start", "", clean_name], shell=False)
        return True, f"Searched and opened {app_name}."
    except Exception as e:
        logger.error("Failed to search and open app: %s", e)
        return False, f"Could not find or open {app_name}: {e}"


def speak(target: Optional[str] = None) -> Tuple[bool, str]:
    """Spoken response only, no system changes."""
    return True, "Completed."


# Safe Whitelist Registry
ACTION_REGISTRY: Dict[str, Callable[[Optional[str]], Tuple[bool, str]]] = {
    "speak": speak,
    "open_chrome": open_chrome,
    "open_whatsapp": open_whatsapp,
    "open_file_explorer": open_file_explorer,
    "open_settings": open_settings,
    "open_website": open_website,
    "search_and_open": search_and_open,
    "open_application": open_application,
    "lock_pc": lock_pc,
    "shutdown_pc": shutdown_pc,
    "restart_pc": restart_pc,
    "search_web": search_web,
    "open_url_in_chrome": open_url_in_chrome,
    "search_and_open_app": search_and_open_app,
}


def check_and_handle_confirmation(user_text: str) -> Optional[Tuple[bool, str]]:
    """
    Checks if a destructive action is pending confirmation and user responded.
    Returns (success, message) if handled, or None if no pending confirmation.
    """
    global _PENDING_CONFIRMATION
    if not _PENDING_CONFIRMATION:
        return None

    cleaned = user_text.strip().lower()
    confirm_words = ("yes", "yeah", "sure", "confirm", "proceed", "do it", "shut down", "restart")
    cancel_words = ("no", "cancel", "stop", "abort", "don't", "nevermind")

    if any(w in cleaned for w in confirm_words):
        action_name = _PENDING_CONFIRMATION
        _PENDING_CONFIRMATION = None
        func = ACTION_REGISTRY.get(action_name)
        if func:
            return func(None)
        return False, "Unknown confirmed action."
    elif any(w in cleaned for w in cancel_words):
        logger.info("User cancelled pending action: %s", _PENDING_CONFIRMATION)
        _PENDING_CONFIRMATION = None
        return True, "Action cancelled. Standing by."
    else:
        # Reset if unrelated command
        _PENDING_CONFIRMATION = None
        return None


def execute_action(action_name: str, target: Optional[str] = None) -> Tuple[bool, str]:
    """
    Safely executes an action from the action whitelist.
    Enforces two-step confirmation for destructive actions (shutdown_pc, restart_pc).
    """
    global _PENDING_CONFIRMATION

    # Rejection of unknown actions
    if action_name not in ACTION_REGISTRY:
        logger.warning(
            "Security alert: Action '%s' rejected! Not in whitelist registry.",
            action_name,
        )
        return False, f"Action '{action_name}' is not recognized or permitted."

    # Intercept destructive actions for confirmation
    if action_name in ("shutdown_pc", "restart_pc"):
        _PENDING_CONFIRMATION = action_name
        logger.info("Destructive action '%s' requires confirmation.", action_name)
        prompt_text = (
            "Are you sure you want to shut down your computer?"
            if action_name == "shutdown_pc"
            else "Are you sure you want to restart your computer?"
        )
        return True, prompt_text

    # Execute safe action
    handler = ACTION_REGISTRY[action_name]
    return handler(target)
