"""System tray do wallpaper."""
from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon


def _get_icon_path() -> Path:
    """Retorna o caminho do ícone, tanto rodando .py quanto .exe"""
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    else:
        base = Path(__file__).parent.parent
    return base / "icon.ico"


def _make_icon(color: str = "#ff003c") -> QIcon:
    ico_path = _get_icon_path()
    if ico_path.exists():
        return QIcon(str(ico_path))

    # Fallback: círculo vermelho (caso o icon.ico não exista)
    pm = QPixmap(32, 32)
    pm.fill(QColor("transparent"))
    p = QPainter(pm)
    p.setBrush(QColor(color))
    p.setPen(QColor("#000000"))
    p.drawEllipse(2, 2, 28, 28)
    p.end()
    return QIcon(pm)


def build_tray(parent, on_next, on_quit,
               on_density_up=None, on_density_down=None) -> QSystemTrayIcon:
    tray = QSystemTrayIcon(_make_icon(), parent)
    menu = QMenu()

    act_next = QAction("Pr\u00f3xima Imagem \u2794", parent)
    act_next.triggered.connect(on_next)
    menu.addAction(act_next)

    if on_density_up is not None or on_density_down is not None:
        menu.addSeparator()
        dens_menu = menu.addMenu("Densidade de Voxels")
        if on_density_up is not None:
            act_up = QAction("Mais voxels  (+)", parent)
            act_up.triggered.connect(on_density_up)
            dens_menu.addAction(act_up)
        if on_density_down is not None:
            act_down = QAction("Menos voxels  (-)", parent)
            act_down.triggered.connect(on_density_down)
            dens_menu.addAction(act_down)

    menu.addSeparator()
    act_quit = QAction("Fechar Wallpaper", parent)
    act_quit.triggered.connect(on_quit)
    menu.addAction(act_quit)

    tray.setContextMenu(menu)
    tray.setToolTip("Blackwall Voxel Live Wallpaper")
    tray.show()
    return tray