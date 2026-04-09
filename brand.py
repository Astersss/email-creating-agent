import json
from dataclasses import dataclass
from pathlib import Path

BRANDS_FILE = Path(__file__).parent / "brands.json"
CONFIG_FILE = Path(__file__).parent / "config.json"


@dataclass
class BrandConfig:
    id: str
    name: str
    primary_color: str | None = None
    logo_url: str | None = None


def load_brands(path: Path = BRANDS_FILE) -> list[BrandConfig]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [BrandConfig(**b) for b in data["brands"]]


def load_model(path: Path = CONFIG_FILE) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["model"]
