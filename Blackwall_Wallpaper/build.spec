# build.spec -- PyInstaller
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

ROOT = Path(SPECPATH)

datas = [
    (str(ROOT / "index.html"), "."),
    (str(ROOT / "style.css"), "."),
    (str(ROOT / "script.js"), "."),
    (str(ROOT / "icon.ico"), "."),  # Inclui o ícone no bundle para o tray usar
]

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
        "tkinter", "matplotlib", "numpy", "pandas", "scipy", 
        "IPython", "pytest", "PyQt6.Qt3DCore", "PyQt6.QtMultimedia"
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
    strip=False,
    upx=False,
    console=False,
    icon="icon.ico",  # Define o ícone do .exe
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="BlackwallWallpaper",
)