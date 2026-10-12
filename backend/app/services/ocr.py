from pathlib import Path
from PIL import Image
import pytesseract

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}

def extract_text(file_path: str) -> tuple[str, str]:
    path = Path(file_path)
    try:
        if path.suffix.lower() in IMAGE_EXTENSIONS:
            text = pytesseract.image_to_string(Image.open(path)).strip()
            return text, "completed" if text else "no_text_detected"
        if path.suffix.lower() == ".pdf":
            from pdf2image import convert_from_path
            pages = convert_from_path(str(path), dpi=220)
            text = "\n\n".join(pytesseract.image_to_string(page) for page in pages).strip()
            return text, "completed" if text else "no_text_detected"
        return "", "unsupported_file_type"
    except pytesseract.TesseractNotFoundError:
        return "", "tesseract_not_installed"
    except Exception:
        if path.suffix.lower() == ".pdf":
            return "", "pdf_ocr_unavailable_check_poppler_and_tesseract"
        return "", "ocr_failed_check_tesseract_installation"
