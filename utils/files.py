"""Small helpers for handling real uploaded file bytes."""
import mimetypes


def guess_mime_type(filename: str) -> str:
    mime, _ = mimetypes.guess_type(filename)
    return mime or "application/octet-stream"
