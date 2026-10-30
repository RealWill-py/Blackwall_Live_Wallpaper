# build.spec -- PyInstaller
# Uso: pyinstaller build.spec --clean
# Saida: dist/BlackwallWallpaper/

from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

ROOT = Path(SPECPATH)

# Empacota UI (HTML/CSS/JS). As imagens do usuario NAO entram no exe:
# elas ficam ao lado do .exe, em ./images/
datas = [
    (str(ROOT / "index.html"), "."),
    (str(ROOT / "style.css"), "."),
    (str(ROOT / "script.js"), "."),
]

# winrt tem modulos carregados dinamicamente que o PyInstaller nao ve
hiddenimports = (
    collect_submodules("winrt")
    + collect_submodules("pycaw")
    + collect_submodules("comtypes")
    + [
        "comtypes.client",
        "PyQt6.QtWebEngineCore",
        "PyQt6.QtWebEngineWidgets",
        "PyQt6.QtWebChannel",
    ]
)

# QtWebEngine precisa dos arquivos de dados (locales, resources, etc.)
datas += collect_data_files("PyQt6.Qt6", subdir="resources")

a = Analysis(
    ["launcher.py"],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        # Remove peso morto
        "tkinter",
        "matplotlib",
        "numpy",
        "pandas",
        "scipy",
        "IPython",
        "pytest",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="BlackwallWallpaper",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,           # WebEngine nao gosta de UPX
    console=False,       # sem janela de terminal
    disable_windowed_traceback=False,
    icon=None,           # coloque "icon.ico" aqui se quiser icone
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="BlackwallWallpaper",
)
