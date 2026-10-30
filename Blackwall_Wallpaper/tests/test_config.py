"""Testes do Config."""
from __future__ import annotations
import json
from pathlib import Path
from config import Config


def test_defaults_saved_and_loaded(tmp_config_path: Path):
    cfg = Config.load(tmp_config_path)
    assert tmp_config_path.exists()
    assert cfg.slide_interval_sec == 35


def test_roundtrip_persists(tmp_config_path: Path):
    cfg = Config.load(tmp_config_path)
    cfg.slide_interval_sec = 120
    cfg.save(tmp_config_path)
    assert Config.load(tmp_config_path).slide_interval_sec == 120


def test_unknown_keys_ignored(tmp_config_path: Path):
    tmp_config_path.write_text(
        json.dumps({"slide_interval_sec": 60, "bogus": 1}), encoding="utf-8"
    )
    cfg = Config.load(tmp_config_path)
    assert cfg.slide_interval_sec == 60
    assert not hasattr(cfg, "bogus")


def test_corrupt_falls_back(tmp_config_path: Path):
    tmp_config_path.write_text("{{{ not json", encoding="utf-8")
    cfg = Config.load(tmp_config_path)
    assert cfg.slide_interval_sec == 35
