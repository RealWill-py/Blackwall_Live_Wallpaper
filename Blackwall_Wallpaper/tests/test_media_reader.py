"""Testes do MediaReader."""
from __future__ import annotations
from wallpaper.media_reader import MediaInfo, MediaReader


def test_media_info_defaults():
    m = MediaInfo()
    assert m.title == ""
    assert m.artist == ""
    assert m.playing is False


def test_backend_detect_returns_known():
    assert MediaReader._detect_backend() in {"winrt", "powershell"}


def test_latest_initialised():
    reader = MediaReader()
    assert reader.latest.title == ""
    assert reader.latest.source == ""


def test_stop_sets_event():
    reader = MediaReader()
    assert not reader._stop_event.is_set()
    reader.stop()
    assert reader._stop_event.is_set()
