"""Entry point do Blackwall Voxel Live Wallpaper."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

from PyQt6.QtCore import QTimer, QUrl, Qt
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QApplication, QMainWindow

from config import Config, IMAGES_DIR
from wallpaper.bridge import Bridge
from wallpaper.injector import (
    ExplorerWatchdog,
    dump_window_tree,
    get_primary_monitor_rect,
    inject,
)
from wallpaper.tray import build_tray

LOG_PATH = Path(__file__).parent / "blackwall.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8", mode="a"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("launcher")


class WallpaperWindow(QMainWindow):
    MAX_INJECT_ATTEMPTS = 10
    RETRY_DELAY_MS = 500

    def __init__(self, cfg: Config):
        super().__init__()
        self.cfg = cfg
        self._inject_attempts = 0

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )
        self.setStyleSheet("background: #010204;")
        self.setGeometry(QGuiApplication.primaryScreen().geometry())

        self.web_view = QWebEngineView(self)
        self.setCentralWidget(self.web_view)
        self.web_view.settings().setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True
        )

        self.bridge = Bridge(self, cfg)
        self.channel = QWebChannel()
        self.channel.registerObject("bridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)

        html_path = Path(__file__).parent / "index.html"
        self.web_view.setUrl(QUrl.fromLocalFile(str(html_path)))

        self.tray = build_tray(
            self,
            on_next=self.bridge.nextImage,
            on_quit=QApplication.instance().quit,
            on_density_up=self.bridge.densityUp,
            on_density_down=self.bridge.densityDown,
        )

        QTimer.singleShot(300, self._try_inject)

        self.watchdog = ExplorerWatchdog(
            get_hwnd=lambda: int(self.winId()),
            reapply=self._reinject_from_watchdog,
        )
        self.watchdog.start()

    def _try_inject(self) -> None:
        self._inject_attempts += 1
        hwnd = int(self.winId())
        success = inject(hwnd)

        if success:
            log.info("Wallpaper ativo atras dos icones do desktop.")
            QTimer.singleShot(300, self._sync_qt_geometry)
            return

        if self._inject_attempts < self.MAX_INJECT_ATTEMPTS:
            log.warning(
                "Injecao falhou (tentativa %d/%d); retry em %dms.",
                self._inject_attempts, self.MAX_INJECT_ATTEMPTS,
                self.RETRY_DELAY_MS,
            )
            QTimer.singleShot(self.RETRY_DELAY_MS, self._try_inject)
        else:
            log.error(
                "Injecao falhou apos %d tentativas. A janela continuara como "
                "top-level (vai parecer um app em tela cheia).",
                self.MAX_INJECT_ATTEMPTS,
            )
            log.error("Arvore de janelas atual:\n%s", dump_window_tree())

    def _sync_qt_geometry(self) -> None:
        try:
            _, _, mon_w, mon_h = get_primary_monitor_rect()

            screen = QGuiApplication.primaryScreen()
            dpr = screen.devicePixelRatio() if screen else 1.0
            logical_w = int(mon_w / dpr)
            logical_h = int(mon_h / dpr)

            log.info(
                "Sync Qt geometry: physical=%dx%d dpr=%.2f logical=%dx%d",
                mon_w, mon_h, dpr, logical_w, logical_h,
            )

            self.resize(max(1, logical_w - 1), max(1, logical_h - 1))
            self.resize(logical_w, logical_h)
            if self.web_view:
                self.web_view.resize(logical_w, logical_h)

            QTimer.singleShot(200, self._dispatch_js_resize)
            log.info("Qt geometry sincronizada com HWND.")
        except Exception:
            log.exception("Falha em _sync_qt_geometry")

    def _dispatch_js_resize(self) -> None:
        try:
            self.web_view.page().runJavaScript(
                "window.dispatchEvent(new Event('resize'));"
            )
            log.info("JS resize event disparado.")
        except Exception:
            log.exception("Falha ao disparar JS resize")

    def _reinject_from_watchdog(self, hwnd: int) -> None:
        if not inject(hwnd):
            log.warning("Reinjecao apos restart do Explorer falhou.")
            return
        QTimer.singleShot(300, self._sync_qt_geometry)

    def closeEvent(self, event):  # noqa: N802
        try:
            self.watchdog.stop()
            self.bridge.shutdown()
        finally:
            super().closeEvent(event)

    def keyPressEvent(self, event):  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            QApplication.instance().quit()
        else:
            super().keyPressEvent(event)


def _setup_autostart(enable: bool) -> None:
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE,
        )
        exe = f'"{sys.executable}" "{Path(__file__).resolve()}"'
        if enable:
            winreg.SetValueEx(key, "BlackwallWallpaper", 0, winreg.REG_SZ, exe)
        else:
            try:
                winreg.DeleteValue(key, "BlackwallWallpaper")
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except Exception:
        log.exception("Falha ao configurar autostart.")


def main() -> int:
    cfg = Config.load()
    IMAGES_DIR.mkdir(exist_ok=True)
    if not any(IMAGES_DIR.iterdir()):
        log.warning("Pasta images/ vazia — adicione .png/.jpg/.webp")

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    window = WallpaperWindow(cfg)
    window.show()
    _setup_autostart(cfg.autostart)

    try:
        return app.exec()
    finally:
        cfg.save()


if __name__ == "__main__":
    sys.exit(main())