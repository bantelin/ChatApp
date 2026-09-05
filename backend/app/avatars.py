import io
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

AVATARS_DIR = Path(__file__).resolve().parent.parent / "uploads" / "avatars"
AVATARS_DIR.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD_BYTES = 2 * 1024 * 1024
MAX_DIMENSION = 512


def avatar_path(trip: str) -> Path:
    return AVATARS_DIR / f"{trip}.webp"


def avatar_url_for(trip: str | None) -> str | None:
    if trip and avatar_path(trip).exists():
        return f"/avatars/{trip}.webp"
    return None


async def save_avatar(trip: str, file: UploadFile) -> None:
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="画像は2MB以内にしてください")

    try:
        image = Image.open(io.BytesIO(content))
        image.verify()
        image = Image.open(io.BytesIO(content))
        image.load()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status_code=400, detail="画像として認識できませんでした")

    image = image.convert("RGB")
    image.thumbnail((MAX_DIMENSION, MAX_DIMENSION))
    image.save(avatar_path(trip), format="WEBP", quality=85)
