import base64
import dataclasses
import json
from dataclasses import dataclass
from pathlib import Path

BRANDS_FILE = Path(__file__).parent / "brands.json"
CONFIG_FILE = Path(__file__).parent / "config.json"
LOGOS_DIR = Path(__file__).parent / "logos"

_LOGO_EXTENSIONS = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}


@dataclass
class BrandConfig:
    id: str
    name: str
    primary_color: str | None = None
    logo_url: str | None = None
    secondary_color: str | None = None
    font_family: str | None = None
    brand_voice: str | None = None
    website_url: str | None = None
    tagline: str | None = None


_BRAND_FIELDS = {f.name for f in dataclasses.fields(BrandConfig)}


def load_brands(path: Path = BRANDS_FILE) -> list[BrandConfig]:
    if not path.exists():
        raise FileNotFoundError(f"Brand config not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}") from e
    return [BrandConfig(**{k: v for k, v in b.items() if k in _BRAND_FIELDS})
            for b in data["brands"]]


def find_logo_data_uri(brand_id: str, logos_dir: Path = LOGOS_DIR) -> str | None:
    for ext, mime in _LOGO_EXTENSIONS.items():
        path = logos_dir / f"{brand_id}{ext}"
        if path.exists():
            data = base64.b64encode(path.read_bytes()).decode()
            return f"data:{mime};base64,{data}"
    return None


def load_model(path: Path = CONFIG_FILE) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Model config not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}") from e
    if "model" not in data:
        raise KeyError(f"'model' key missing from config: {path}")
    return data["model"]
