import secrets
from pathlib import Path

from fastapi import UploadFile


_BASE_DIR = Path(__file__).resolve().parents[2]
_AVATAR_DIR = _BASE_DIR / "uploads" / "avatars"
_MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5 MB
_HEADER_BYTES = 1024
_CHUNK_SIZE = 1024 * 1024


def _ensure_avatar_dir() -> None:
    _AVATAR_DIR.mkdir(parents=True, exist_ok=True)


def _generate_avatar_name(original_name: str | None) -> str:
    suffix = Path(original_name or "").suffix
    return f"{secrets.token_hex(16)}{suffix}"


def _is_allowed_image(header: bytes) -> bool:
    if header.startswith(b"\xff\xd8\xff"):  # JPEG
        return True
    if header.startswith(b"\x89PNG\r\n\x1a\n"):  # PNG
        return True
    if header.startswith(b"GIF8"):  # GIF
        return True
    if header.startswith(b"BM"):  # BMP
        return True
    if len(header) >= 12 and header.startswith(b"RIFF") and header[8:12] == b"WEBP":  # WEBP
        return True
    return False


async def save_avatar_file(upload: UploadFile) -> str:
    _ensure_avatar_dir()
    filename = _generate_avatar_name(upload.filename)
    destination = _AVATAR_DIR / filename
    total_bytes = 0

    header = await upload.read(_HEADER_BYTES)
    if not header:
        raise ValueError("Empty file upload.")
    if not _is_allowed_image(header):
        raise ValueError("Invalid image upload.")

    total_bytes = len(header)

    try:
        with destination.open("wb") as buffer:
            buffer.write(header)
            while True:
                remaining = _MAX_AVATAR_SIZE - total_bytes
                if remaining <= 0:
                    extra = await upload.read(1)
                    if extra:
                        raise ValueError("Avatar file is too large.")
                    break
                chunk = await upload.read(min(_CHUNK_SIZE, remaining))
                if not chunk:
                    break
                buffer.write(chunk)
                total_bytes += len(chunk)
    except Exception:
        destination.unlink(missing_ok=True)
        raise

    return destination.relative_to(_BASE_DIR).as_posix()


def delete_avatar_file(path_str: str) -> None:
    candidate = (_BASE_DIR / path_str).resolve()
    avatar_root = _AVATAR_DIR.resolve()
    try:
        candidate.relative_to(avatar_root)
    except ValueError:
        return
    if candidate.exists():
        candidate.unlink()
