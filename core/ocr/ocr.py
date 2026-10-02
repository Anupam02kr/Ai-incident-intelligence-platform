from PIL import Image, ImageOps, ImageFilter
import easyocr

_reader = None


def get_reader():
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(["en"], gpu=False)
    return _reader


def preprocess(image_path):
    img = Image.open(image_path)
    img = ImageOps.grayscale(img)
    img = ImageOps.autocontrast(img)
    img = img.filter(ImageFilter.MedianFilter(size=3))

    min_dimension = 800
    if min(img.size) < min_dimension:
        scale = min_dimension / min(img.size)
        new_size = (int(img.width * scale), int(img.height * scale))
        img = img.resize(new_size, Image.LANCZOS)

    return img


def extract_text(image_path, apply_preprocessing=True):
    reader = get_reader()

    if apply_preprocessing:
        img = preprocess(image_path)
        import numpy as np
        source = np.array(img)
    else:
        source = image_path

    results = reader.readtext(source)

    lines = []
    for bbox, text, confidence in results:
        lines.append({"text": text, "confidence": round(confidence, 3)})

    full_text = "\n".join(line["text"] for line in lines)
    avg_confidence = (
        round(sum(l["confidence"] for l in lines) / len(lines), 3) if lines else 0.0
    )

    return {
        "text": full_text,
        "lines": lines,
        "avg_confidence": avg_confidence,
        "needs_review": bool(avg_confidence < 0.6),
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("usage: python ocr.py path/to/screenshot.png")
    else:
        result = extract_text(sys.argv[1])
        print(f"avg confidence: {result['avg_confidence']}")
        print(f"needs review: {result['needs_review']}")
        print("\nextracted text:")
        print(result["text"])
