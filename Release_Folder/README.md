# 🤖 JARVIS MARK VII - COMPLETE ECOSYSTEM RELEASE

**Owner & Master**: Muhammad Fayas (Fayas)  
**Date of Birth**: 21/03/2010  
**Location**: Kaipamangalam, Thainagar, Thrissur, Kerala  
**Release Build**: v18 (Latest)

---

## 📦 What's in this folder:

1. **`Jarvis-PC.exe`** (~86.9 MB)
   - High-tech Cyberpunk Arc Reactor Desktop OS application.
   - Built with PyInstaller and CustomTkinter.
   - System tray minimization, zero microphone audio collision, and local direct server on port `8765`.
   - **Continuous Wake Detection**: Say *"Hey Jarvis"* -> responds *"Yes, sir?"* -> processes your command cleanly without loop locks.
   - **OpenRouter AI Fallback**: Directly connected to OpenRouter API (`gpt-4o-mini`) from `.env` so Jarvis answers questions even if VPS is offline.
   - **Zero Third-Party AI Mentions**: Enforces Muhammad Fayas as the sole creator and developer.

2. **`Jarvis-Mobile.apk`** (~29.3 MB - Release v18)
   - Android APK built from latest code on GitHub Actions.
   - **Deep Male Voice**: Tuned masculine voice synthesis on Android.
   - **One-Tap Connection**: Automatically connects to VPS (`ws://45.131.64.32:2004/ws/jarvis`) or Direct PC on local Wi-Fi.
   - **Remote PC Control**: Live PC screen streaming with cyan mouse pointer, virtual trackpad, keyboard, and system control.
   - **Voice Commands**:
     - *"Who is your developer?"* / *"How is youre developer?"* -> Responds with Muhammad Fayas.
     - *"Open Chrome in my PC"* -> Launches Chrome on your PC.
     - *"Open YouTube"* -> Launches YouTube in Chrome.
     - *"Open Kiro"* / *"Search Kiro"* -> Searches Google for Kiro and opens in Chrome.

---

## 🔒 File Integrity (SHA-256):

| File | SHA-256 Hash |
| :--- | :--- |
| `Jarvis-Mobile.apk` | `9536C05D6A2BCDA678C95F8455BDB342F98B20107E3B154FF14DE0E4AA0C1CF3` |
| `Jarvis-PC.exe` | `663C1141B73F7C3ECC4200520A3DB294A90678B0F0472FB42D50D6D10E427F4D` |

---

## 🚀 Quick Setup Instructions:

### On Your PC:
1. Double click **`Jarvis-PC.exe`** to start the desktop app.
2. The Arc Reactor will turn on and begin listening for *"Hey Jarvis"*.
3. You can minimize the app to the system tray anytime.

### On Your Android Phone:
1. Copy **`Jarvis-Mobile.apk`** to your phone and install it (allow *Install Unknown Apps* if prompted).
2. Open **JARVIS**.
3. It will automatically link to the system. You can also open **Settings** -> tap **Default VPS** or enter your PC's local IP (`ws://<PC_IP>:8765`) to connect directly.
