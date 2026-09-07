"""
Jarvis PC Client - PyInstaller Executable Builder
Compiles the complete modern Jarvis GUI Desktop Application into dist/Jarvis.exe
Includes CustomTkinter UI themes, images, and speech assets.
"""

import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "images"
GUI_DIR = BASE_DIR / "gui"
LOGO_PNG = IMAGES_DIR / "logo.png"
LOGO_ICO = IMAGES_DIR / "logo.ico"
MAIN_PY = BASE_DIR / "main.py"
DIST_DIR = BASE_DIR / "dist"
BUILD_DIR = BASE_DIR / "build"


def ensure_ico_exists():
    """Generates logo.ico from logo.png if it does not already exist."""
    if LOGO_ICO.exists():
        print(f"[INFO] Using existing icon: {LOGO_ICO}")
        return

    if not LOGO_PNG.exists():
        raise FileNotFoundError(f"Source image not found: {LOGO_PNG}")

    print(f"[INFO] Generating {LOGO_ICO} from {LOGO_PNG}...")
    try:
        from PIL import Image
        img = Image.open(LOGO_PNG)
        img.save(
            LOGO_ICO,
            format="ICO",
            sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)],
        )
        print(f"[INFO] Successfully created {LOGO_ICO}")
    except Exception as e:
        print(f"[WARNING] Could not convert PNG to ICO: {e}")


def build_executable():
    """Runs PyInstaller to compile the modern Jarvis desktop app into Jarvis.exe."""
    ensure_ico_exists()

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name=Jarvis",
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR}",
        f"--specpath={BASE_DIR}",
        f"--add-data={IMAGES_DIR}{os.pathsep}images",
        f"--add-data={GUI_DIR}{os.pathsep}gui",
        "--collect-all=customtkinter",
        "--collect-all=pyttsx3",
        "--collect-all=pystray",
        "--hidden-import=pyttsx3",
        "--hidden-import=pyttsx3.drivers",
        "--hidden-import=pyttsx3.drivers.sapi5",
        "--hidden-import=pyttsx3.drivers.dummy",
        "--hidden-import=pystray",
        "--hidden-import=sounddevice",
        "--hidden-import=numpy",
        "--hidden-import=speech_recognition",
        "--hidden-import=PIL",
        "--hidden-import=PIL._tkinter_finder",
    ]

    if LOGO_ICO.exists():
        cmd.append(f"--icon={LOGO_ICO}")

    cmd.append(str(MAIN_PY))

    print("\n=======================================================")
    print("  BUILDING JARVIS MODERN DESKTOP APP (JARVIS.EXE)")
    print("=======================================================")
    print("Command:", " ".join(cmd))
    print(f"Working Directory: {BASE_DIR}\n")

    result = subprocess.run(cmd, cwd=str(BASE_DIR))
    if result.returncode == 0:
        exe_path = DIST_DIR / "Jarvis.exe"
        print("\n=======================================================")
        print("  BUILD COMPLETED SUCCESSFULLY!")
        print(f"  Modern Desktop Executable: {exe_path}")
        print("=======================================================")
    else:
        print(f"\n[ERROR] PyInstaller build failed with exit code {result.returncode}")
        sys.exit(result.returncode)


if __name__ == "__main__":
    build_executable()
