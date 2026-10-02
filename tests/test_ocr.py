import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PIL import Image, ImageDraw, ImageFont
from core.ocr.ocr import preprocess, extract_text



def load_test_font(size=28):
    """Tries a few common font locations across platforms. Falls back to
    PIL's built-in font if none are found, but that one renders tiny, so
    we bump its size explicitly where the Pillow version supports it -
    otherwise our own upscale+blur preprocessing turns it to mush and
    OCR reads nothing.
    """
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",  
        "C:\\Windows\\Fonts\\consola.ttf",                       
        "C:\\Windows\\Fonts\\arial.ttf",                         
        "/System/Library/Fonts/Menlo.ttc",                       
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)

    try:
        return ImageFont.load_default(size=size)  
    except TypeError:
        return ImageFont.load_default()  


def make_test_image(text, path):
    img = Image.new("RGB", (700, 150), color="black")
    draw = ImageDraw.Draw(img)
    font = load_test_font(28)
    draw.text((20, 20), text, fill="white", font=font)
    img.save(path)
    return path


def test_preprocess_returns_grayscale_image():
    path = make_test_image("sample error text", "/tmp/test_preprocess.png")
    img = preprocess(path)
    assert img.mode == "L"


def test_preprocess_upscales_small_images():
    path = make_test_image("tiny", "/tmp/test_small.png")
    small = Image.open(path).resize((100, 50))
    small.save(path)

    img = preprocess(path)
    assert min(img.size) >= 800


def test_extract_text_reads_real_words():
    path = make_test_image("ConnectionError timeout", "/tmp/test_ocr.png")
    result = extract_text(path)

    text_lower = result["text"].lower()
    assert "connection" in text_lower or "timeout" in text_lower
    assert result["avg_confidence"] > 0
    assert isinstance(result["needs_review"], bool)


if __name__ == "__main__":
    print("run with: pytest tests/test_ocr.py -v")
    print("(takes a bit longer than the other test files, OCR has to load its model)")
