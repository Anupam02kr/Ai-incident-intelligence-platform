from pathlib import Path

import cv2
import numpy as np
import pytesseract
from PIL import Image

from config import get_settings


def _setup_tesseract():
    cmd = get_settings().tesseract_cmd
    if cmd:
        pytesseract.pytesseract.tesseract_cmd = cmd


def read_screenshot(path: Path) -> dict:
    _setup_tesseract()

    img = cv2.imread(str(path))
    if img is None:
        raise ValueError(f"bad image: {path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=1.4, fy=1.4, interpolation=cv2.INTER_CUBIC)
    gray = cv2.fastNlMeansDenoising(gray, h=8)
    _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    pil = Image.fromarray(bw)
    text = pytesseract.image_to_string(pil, config="--psm 6").strip()
    meta = pytesseract.image_to_data(pil, output_type=pytesseract.Output.DICT, config="--psm 6")

    conf = [int(c) for c in meta.get("conf", []) if str(c).isdigit() and int(c) > 0]
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    return {
        "text": text,
        "lines": lines,
        "line_count": len(lines),
        "avg_confidence": round(sum(conf) / len(conf), 1) if conf else 0,
    }
