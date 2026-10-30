"""Ponte QWebChannel entre Python e o JS do wallpaper."""
from __future__ import annotations

import json
import logging
import os

from PyQt6.QtCore import QObject, pyqtSlot

from wallpaper.media_reader import AudioPeakReader, MediaReader
from wallpaper.system_monitor import SystemMonitor

log = logging.getLogger(__name__)


class Bridge(QObject):
    def __init__(self, window, cfg, parent=None):
        super().__init__(parent)
        self.window = window
        self.cfg = cfg
        self.sysmon = SystemMonitor()
        self.audio = AudioPeakReader()
        self.media = MediaReader(poll_ms=cfg.media_poll_ms)
        self.media.start()

    @pyqtSlot(result=str)
    def getSystemStats(self) -> str:
        try:
            cpu, ram = self.sysmon.sample()
            info = self.media.latest
            beat = 0.0
            if self.cfg.audio_beat_enabled and self.audio.available:
                beat = self.audio.peak()
            return json.dumps({
                "cpu": cpu,
                "ram": ram,
                "title": info.title or "AGUARDANDO M\u00cdDIA...",
                "artist": info.artist or "SYSTEM_STANDBY",
                "playing": info.playing,
                "beat": beat,
            }, ensure_ascii=False)
        except Exception:
            log.exception("getSystemStats falhou")
            return json.dumps({
                "cpu": 0, "ram": 0,
                "title": "AGUARDANDO M\u00cdDIA...",
                "artist": "SYSTEM_STANDBY",
                "playing": False, "beat": 0.0,
            })

    @pyqtSlot(result=str)
    def getImagesList(self) -> str:
        try:
            images_dir = os.path.join(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__))), "images")
            if os.path.isdir(images_dir):
                exts = (".png", ".jpg", ".jpeg", ".webp", ".gif")
                files = [
                    f"images/{f}"
                    for f in sorted(os.listdir(images_dir))
                    if f.lower().endswith(exts)
                ]
                return json.dumps(files)
        except Exception:
            log.exception("getImagesList falhou")
        return json.dumps([])

    @pyqtSlot()
    def nextImage(self) -> None:
        if self.window and self.window.web_view:
            self.window.web_view.page().runJavaScript(
                "if (window.forceNextImage) window.forceNextImage();"
            )

    @pyqtSlot()
    def densityUp(self) -> None:
        if self.window and self.window.web_view:
            self.window.web_view.page().runJavaScript(
                "if (window.__voxelEngine && window.__voxelEngine.densityUp) "
                "window.__voxelEngine.densityUp();"
            )

    @pyqtSlot()
    def densityDown(self) -> None:
        if self.window and self.window.web_view:
            self.window.web_view.page().runJavaScript(
                "if (window.__voxelEngine && window.__voxelEngine.densityDown) "
                "window.__voxelEngine.densityDown();"
            )

    def shutdown(self) -> None:
        self.media.stop()