# JARVIS Neural AI // Mark VII

An autonomous personal AI assistant and remote workstation controller ecosystem engineered for **Muhammad Fayas** (Fayas).

## Project Ecosystem & Directory Structure

This repository contains the complete full-stack suite:

```
├── Mobile_App/            # Flutter Android Application (Voice Assistant & Remote Trackpad APK)
│   ├── lib/               # Dart source (Arc Reactor HUD, WebSockets, STT/TTS, Trackpad)
│   ├── android/           # Android native Gradle project configuration
│   ├── images/            # App icons and graphics
│   └── pubspec.yaml       # Flutter dependencies
│
├── PC_App/                # Python Desktop Agent & Workstation Controller
│   ├── actions.py         # OS automation (Chrome, YouTube, WhatsApp, Shutdown, Volume)
│   ├── jarvis_client.py   # WebSocket client connecting PC to VPS/Cloud relay
│   ├── remote_controller.py # Mouse and keyboard hardware emulation via PyAutoGUI
│   ├── speech_listener.py # Local speech recognition and wake-word listener
│   ├── intent_engine.py   # Local natural language parsing & AI routing
│   ├── local_server.py    # Local HTTP/WS fallback server
│   ├── gui/               # CustomTkinter & PyQt desktop interface
│   ├── build_exe.py       # PyInstaller executable builder
│   └── requirements.txt   # Python dependencies
│
├── VPS/                   # Standalone Python Relay Server (FastAPI + WebSocket)
│   ├── main.py            # High-performance FastAPI WebSocket relay & AI backend
│   ├── requirements.txt   # Server dependencies (FastAPI, Uvicorn, WebSockets, etc.)
│   └── .env.example       # Server environment variable templates
│
├── push_and_build_apk.bat # Automation script to commit, push & trigger GitHub APK builds
├── .github/workflows/     # CI/CD workflows for building Android APK releases
│
├── src/                   # React 18 + Vite Web Application & Cloud Control Center
│   ├── components/        # Arc Reactor, Voice Assistant, PC Trackpad, Diagnostics
│   ├── types.ts           # Unified TypeScript definitions
│   └── App.tsx            # Main application layout
├── server.ts              # Node.js Express + WebSocket relay server (Port 3000)
└── package.json           # Web applet configuration and scripts
```

## Features Across Platforms

### 1. Mobile App (`/Mobile_App`)
- Built with **Flutter / Dart** for Android.
- Interactive glowing Arc Reactor interface with voice commands in English & Malayalam.
- Remote PC Trackpad for controlling mouse cursor, buttons, and typing from your phone.
- QR scanner to connect instantly to the VPS or Cloud relay server.

### 2. PC Workstation Agent (`/PC_App`)
- Built with **Python 3**.
- Listens for remote commands from the Mobile App and Web Console.
- Hardware-level automation via `pyautogui` (mouse gestures, keyboard text injection, media keys).
- System control: Shutdown, Restart, Lock PC, Volume adjustments, App launching (Chrome, YouTube, WhatsApp, Explorer).
- Screen streaming and capture to feed PC display to mobile/web clients.

### 3. VPS Relay Server (`/VPS`)
- Built with **FastAPI** and asynchronous WebSockets.
- Routes commands between Mobile, Web, and PC clients seamlessly over the internet.
- Integrated AI reasoning and fallback rule engine honoring creator **Muhammad Fayas**.

### 4. Cloud Web Console (`/`)
- Responsive React + Tailwind + Vite web dashboard running on port 3000.
- Serves as a full cloud control center with WebSocket relay (`/ws/jarvis`), live diagnostics, system telemetry, and virtual trackpad.

