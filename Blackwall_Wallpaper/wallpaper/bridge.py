"""Ponte QWebChannel entre Python e o JS do wallpaper."""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from urllib.parse import quote

from PyQt6.QtCore import QObject, pyqtSlot

from config import IMAGES_DIR
from wallpaper.media_reader import AudioPeakReader, MediaReader
from wallpaper.system_monitor import SystemMonitor

log = logging.getLogger(__name__)

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp")


class Bridge(QObject):
    def __init__(self, window, cfg, parent=None):
        super().__init__(parent)
        self.window = window
        self.cfg = cfg
        self.sysmon = SystemMonitor()
        self.audio = AudioPeakReader()
        self.media = MediaReader(poll_ms=cfg.media_poll_ms)
        self.media.start()
        log.info("Pasta de imagens: %s (existe=%s)",
                 IMAGES_DIR, IMAGES_DIR.exists())

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
        """Retorna lista de URLs absolutas 'file:///...' das imagens.

        Usa IMAGES_DIR do config.py (ao lado do .exe quando congelado).
        Retorna URL absoluta para o navegador nao tentar resolver
        caminhos relativos em _internal/.
        """
        try:
            if not IMAGES_DIR.exists():
                log.warning("Pasta images/ nao existe: %s", IMAGES_DIR)
                return json.dumps([])

            files = sorted(
                f for f in os.listdir(IMAGES_DIR)
                if f.lower().endswith(IMAGE_EXTS)
            )

            if not files:
                log.warning("Pasta images/ vazia: %s", IMAGES_DIR)
                return json.dumps([])

            # Converte para file:/// URL absoluta
            urls = []
            for f in files:
                full = (Path(IMAGES_DIR) / f).resolve()
                # quote() escapa espacos e caracteres especiais na URL
                urls.append(full.as_uri())

            log.info("getImagesList: %d imagem(ns) encontrada(s).", len(urls))
            for u in urls:
                log.info("  - %s", u)
            return json.dumps(urls)

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