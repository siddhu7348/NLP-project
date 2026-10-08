"""Extract plain text from uploaded resume files (.txt or .pdf)."""
import io
from pathlib import Path

from pypdf import PdfReader


def text_from_bytes(filename: str, data: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(io.BytesIO(data))
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
    elif suffix in (".txt", ".md"):
        text = data.decode("utf-8", errors="ignore")
    else:
        raise ValueError("Unsupported file type. Use .pdf or .txt")
    text = text.strip()
    if not text:
        raise ValueError("No text could be extracted (scanned/image-only PDF?).")
    return text


def text_from_file(path) -> str:
    path = Path(path)
    return text_from_bytes(path.name, path.read_bytes())
