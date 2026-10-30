# build.spec -- PyInstaller
# Uso:  pyinstaller build.spec
# Saida: dist/BlackwallWallpaper/

from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

ROOT = Path(SPECPATH)

datas = [
    (str(ROOT / "index.html"), "."),
    (str(ROOT / "style.css"), "."),
    (str(ROOT / "script.js"), "."),
    (str(ROOT / "images"), "images"),
]

hiddenimports = (
    collect_submodules("winrt")
    + collect_submodules("pycaw")
    + ["comtypes", "comtypes.client"]
)

a = Analysis(
    ["launcher.py"],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="BlackwallWallpaper",
    debug=False, strip=False, upx=True, console=False,
)
coll = COLLECT(
    exe, a.binaries, a.datas,
    strip=False, upx=True, name="BlackwallWallpaper",
)
