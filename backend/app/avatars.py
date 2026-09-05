import io
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

AVATARS_DIR = Path(__file__).resolve().parent.parent / "uploads" / "avatars"
AVATARS_DIR.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD_BYTES = 2 * 1024 * 1024
MAX_DIMENSION = 512
# 展開後の画像サイズに独自の上限を設ける(「画像爆弾」対策)。
# 圧縮率の高い形式(PNG/GIF等)は、数MBのファイルが数億ピクセルに
# 展開されることがあり、サーバーのメモリ・CPUを消費させられる恐れがある。
MAX_PIXELS = 30_000_000  # 例: 6000x5000相当


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

        # verify()/load()でデコードする前に、展開後の解像度を確認する。
        # ここでの拒否はデコード自体が走る前なので、実際のメモリ確保は発生しない。
        width, height = image.size
        if width * height > MAX_PIXELS:
            raise HTTPException(
                status_code=400, detail="画像の解像度が大きすぎます"
            )

        image.load()
    except HTTPException:
        raise
    except Image.DecompressionBombError:
        raise HTTPException(
            status_code=400, detail="画像の解像度が大きすぎます"
        )
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status_code=400, detail="画像として認識できませんでした")

    image = image.convert("RGB")
    image.thumbnail((MAX_DIMENSION, MAX_DIMENSION))
    image.save(avatar_path(trip), format="WEBP", quality=85)
