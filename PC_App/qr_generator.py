"""
Jarvis PC Client - QR Code Pairing Generator
Generates a visual QR code image for Mobile-to-PC pairing.
"""

import json
import os
from pathlib import Path

import qrcode
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent
QR_CACHE_PATH = BASE_DIR / "images" / "pairing_qr.png"


def generate_pairing_qr_code(
    vps_url: str = "",
    pair_id: str = "JARVIS-FAYAS-2010",
) -> str:
    """
    Generates a QR code containing pairing configuration and saves to images/pairing_qr.png.
    Returns the absolute path to the generated image.
    """
    # The QR is deliberately metadata only. It contains no LAN IP, VPS IP,
    # port, or credential; pairing details are entered privately on the phone.
    pairing_data = {
        "app": "JARVIS",
        "version": "2.0",
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
