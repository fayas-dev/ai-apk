"""
Jarvis PC Client - QR Code Pairing Generator
Generates a visual QR code image for Mobile-to-PC pairing.
"""

import json
import os
import socket
from pathlib import Path

import qrcode
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent
QR_CACHE_PATH = BASE_DIR / "images" / "pairing_qr.png"


def get_local_ip() -> str:
    """Retrieves current PC local network IP."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def generate_pairing_qr_code(
    vps_url: str = "ws://45.131.64.32:2004/ws/jarvis",
    pair_id: str = "JARVIS-FAYAS-2010",
) -> str:
    """
    Generates a QR code containing pairing configuration and saves to images/pairing_qr.png.
    Returns the absolute path to the generated image.
    """
    local_ip = get_local_ip()
    hostname = socket.gethostname()

    local_ws = f"ws://{local_ip}:8765"
    pairing_data = {
        "app": "JARVIS",
        "version": "2.0",
        "local_ws": local_ws,
        "local_ip": local_ip,
        "port": 8765,
        "vps": vps_url,
        "pc_name": hostname,
        "owner": "Muhammad Fayas",
        "pair_id": pair_id,
    }

    raw_payload = json.dumps(pairing_data)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=3,
    )
    qr.add_data(raw_payload)
    qr.make(fit=True)

    # Cyan on Dark Background for Jarvis Theme
    img = qr.make_image(fill_color="#00E5FF", back_color="#070B12")

    os.makedirs(QR_CACHE_PATH.parent, exist_ok=True)
    img.save(str(QR_CACHE_PATH))
    return str(QR_CACHE_PATH)


if __name__ == "__main__":
    path = generate_pairing_qr_code()
    print(f"QR code generated at: {path}")
