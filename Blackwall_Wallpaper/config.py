"""Configuracao persistente do wallpaper."""
from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


def get_app_dir() -> Path:
    """Diretorio gravavel do app.

    - Rodando via 'python launcher.py': pasta do projeto.
    - Rodando como .exe (PyInstaller): pasta onde o .exe esta.
    """
    if getattr(sys, "frozen", False):
        return Path(os.path.dirname(sys.executable))
    return Path(__file__).parent


APP_DIR = get_app_dir()
CONFIG_PATH = APP_DIR / "config.json"
IMAGES_DIR = APP_DIR / "images"


@dataclass
class Config:
    slide_interval_sec: int = 35
    z_depth_intensity: float = 1.0
    hud_enabled: bool = True
    media_poll_ms: int = 1000
    audio_beat_enabled: bool = True
    autostart: bool = False

    def save(self, path: Path | None = None) -> None:
        target = path or CONFIG_PATH
        try:
            target.write_text(
                json.dumps(asdict(self), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception:
            pass

    @classmethod
    def load(cls, path: Path | None = None) -> "Config":
        target = path or CONFIG_PATH
        if not target.exists():
            cfg = cls()
            cfg.save(target)
            return cfg
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
            valid = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
            return cls(**valid)
        except Exception:
            cfg = cls()
            cfg.save(target)
            return cfg
