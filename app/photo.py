from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

BASE_DIR = Path(__file__).resolve().parent

PHOTO_PATH = BASE_DIR / "files" / "foto.jpg"
MAX_BYTES = 8 * 1024 * 1024  # 8 MB de upload
SIZE = 640  # lado do quadrado final, em pixels
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}

# proteção contra imagens "bomba" (dimensões absurdas)
Image.MAX_IMAGE_PIXELS = 50_000_000


def photo_url() -> str | None:
    """URL versionada pela data do arquivo, para o navegador não servir foto antiga."""
    if not PHOTO_PATH.is_file():
        return None
    return f"/foto?v={int(PHOTO_PATH.stat().st_mtime)}"


def process_photo(data: bytes) -> bytes:
    """Valida, corrige a rotação, recorta em quadrado e regrava como JPEG sem metadados."""
    try:
        with Image.open(BytesIO(data)) as img:
            if img.format not in ALLOWED_FORMATS:
                raise ValueError("formato não suportado")
            img = ImageOps.exif_transpose(img)
            img = img.convert("RGB")
            img = ImageOps.fit(
                img,
                (SIZE, SIZE),
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.35),
            )
            out = BytesIO()
            img.save(out, format="JPEG", quality=88, optimize=True)  # imagem nova: sem EXIF
            return out.getvalue()
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError) as exc:
        raise ValueError("imagem inválida") from exc