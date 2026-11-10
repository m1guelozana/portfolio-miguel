from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

RESUME_PATH = BASE_DIR / "files" / "curriculo.pdf"
DOWNLOAD_NAME = "Curriculo-Miguel-Ozana.pdf"
MAX_BYTES = 5 * 1024 * 1024  # 5 MB


def resume_exists() -> bool:
    return RESUME_PATH.is_file()
