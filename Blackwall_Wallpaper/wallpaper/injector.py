"""Injecao na camada WorkerW do Windows + watchdog do explorer."""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import logging
import threading

log = logging.getLogger(__name__)

user32 = ctypes.windll.user32

# --- constantes Win32 ---
HWND_BOTTOM = 1
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
SWP_FRAMECHANGED = 0x0020
SWP_NOZORDER = 0x0004
SMTO_NORMAL = 0x0000
GWL_STYLE = -16
WS_CHILD = 0x40000000
WS_POPUP = 0x80000000
WM_SPAWN_WORKER = 0x052C
MONITOR_DEFAULTTOPRIMARY = 1

# --- prototipos (evitam truncamento de HWND em 64-bit) ---
user32.EnumWindows.argtypes = [ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM), wt.LPARAM]
user32.EnumWindows.restype = wt.BOOL
user32.FindWindowW.argtypes = [wt.LPCWSTR, wt.LPCWSTR]
user32.FindWindowW.restype = wt.HWND
user32.FindWindowExW.argtypes = [wt.HWND, wt.HWND, wt.LPCWSTR, wt.LPCWSTR]
user32.FindWindowExW.restype = wt.HWND
user32.SetParent.argtypes = [wt.HWND, wt.HWND]
user32.SetParent.restype = wt.HWND
user32.GetParent.argtypes = [wt.HWND]
user32.GetParent.restype = wt.HWND
user32.SendMessageTimeoutW.argtypes = [
    wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM, wt.UINT, wt.UINT, ctypes.POINTER(wt.DWORD)
]
user32.SendMessageTimeoutW.restype = wt.LPARAM
user32.ShowWindow.argtypes = [wt.HWND, ctypes.c_int]
user32.SetWindowPos.argtypes = [
    wt.HWND, wt.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wt.UINT
]
user32.GetClientRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
user32.GetClientRect.restype = wt.BOOL
user32.GetWindowRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
user32.GetWindowRect.restype = wt.BOOL
user32.GetClassNameW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
user32.GetWindowTextW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
user32.SetWindowLongW.argtypes = [wt.HWND, ctypes.c_int, ctypes.c_long]
user32.SetWindowLongW.restype = ctypes.c_long
user32.GetWindowLongW.argtypes = [wt.HWND, ctypes.c_int]
user32.GetWindowLongW.restype = ctypes.c_long


# --- Monitor primario ---
class _POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class _MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wt.DWORD),
        ("rcMonitor", wt.RECT),
        ("rcWork", wt.RECT),
        ("dwFlags", wt.DWORD),
    ]


user32.MonitorFromPoint.argtypes = [_POINT, wt.DWORD]
user32.MonitorFromPoint.restype = wt.HMONITOR
user32.GetMonitorInfoW.argtypes = [wt.HMONITOR, ctypes.POINTER(_MONITORINFO)]
user32.GetMonitorInfoW.restype = wt.BOOL


def get_primary_monitor_rect() -> tuple[int, int, int, int]:
    """Retorna (x, y, w, h) do monitor primario em pixels fisicos."""
    pt = _POINT(0, 0)
    hmon = user32.MonitorFromPoint(pt, MONITOR_DEFAULTTOPRIMARY)
    if not hmon:
        log.warning("MonitorFromPoint falhou; usando fallback 1920x1080.")
        return (0, 0, 1920, 1080)
    mi = _MONITORINFO()
    mi.cbSize = ctypes.sizeof(_MONITORINFO)
    if not user32.GetMonitorInfoW(hmon, ctypes.byref(mi)):
        log.warning("GetMonitorInfoW falhou; usando fallback 1920x1080.")
        return (0, 0, 1920, 1080)
    r = mi.rcMonitor
    return (r.left, r.top, r.right - r.left, r.bottom - r.top)


# =====================================================================
#  Descoberta do WorkerW
# =====================================================================
def _spawn_workerw() -> int | None:
    """Envia 0x052C ao Progman para garantir que o WorkerW exista."""
    progman = user32.FindWindowW("Progman", None)
    if not progman:
        log.warning("Progman nao encontrado.")
        return None

    result = wt.DWORD()
    for wparam, lparam in ((0xD, 0x1), (0xD, 0x0)):
        user32.SendMessageTimeoutW(
            progman, WM_SPAWN_WORKER, wparam, lparam,
            SMTO_NORMAL, 1000, ctypes.byref(result),
        )
    return progman


def _find_target_workerw() -> int | None:
    """Retorna o HWND do WorkerW que fica ATRAS dos icones."""
    progman = _spawn_workerw()
    if not progman:
        return None

    shell = user32.FindWindowExW(progman, None, "SHELLDLL_DefView", None)
    if shell:
        worker = user32.FindWindowExW(progman, shell, "WorkerW", None)
        if worker:
            log.debug("WorkerW dentro do Progman (hwnd=0x%08x).", worker)
            return worker

    found: list[int | None] = [None]

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def enum_cb(hwnd, _):
        sh = user32.FindWindowExW(hwnd, None, "SHELLDLL_DefView", None)
        if sh:
            worker = user32.FindWindowExW(None, hwnd, "WorkerW", None)
            if worker:
                found[0] = worker
                return False
        return True

    user32.EnumWindows(enum_cb, 0)
    if found[0]:
        log.debug("WorkerW top-level (hwnd=0x%08x).", found[0])
    return found[0]


# =====================================================================
#  Injecao
# =====================================================================
def inject(hwnd: int) -> bool:
    """Injeta hwnd no WorkerW, dimensionado para o monitor primario."""
    if not hwnd:
        log.error("inject(): hwnd invalido (0).")
        return False

    worker = _find_target_workerw()
    if not worker:
        log.warning("WorkerW nao encontrado — desktop ainda nao pronto.")
        return False

    # 1) Forcar WS_CHILD ANTES do SetParent
    style = user32.GetWindowLongW(hwnd, GWL_STYLE)
    new_style = (style & ~WS_POPUP) | WS_CHILD
    if new_style != style:
        user32.SetWindowLongW(hwnd, GWL_STYLE, new_style)
        user32.SetWindowPos(
            hwnd, 0, 0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED,
        )

    # 2) SetParent
    user32.SetParent(hwnd, worker)

    # 3) Verificar
    actual = user32.GetParent(hwnd)
    if actual != worker:
        log.error(
            "SetParent falhou (esperado=0x%08x, obtido=0x%08x).",
            worker, actual or 0,
        )
        return False

    # 4) Dimensionar para o monitor primario
    mon_x, mon_y, mon_w, mon_h = get_primary_monitor_rect()

    worker_rect = wt.RECT()
    user32.GetWindowRect(worker, ctypes.byref(worker_rect))
    rel_x = mon_x - worker_rect.left
    rel_y = mon_y - worker_rect.top

    user32.SetWindowPos(
        hwnd, HWND_BOTTOM, rel_x, rel_y, mon_w, mon_h,
        SWP_NOACTIVATE | SWP_SHOWWINDOW,
    )
    user32.ShowWindow(hwnd, 5)

    worker_rect2 = wt.RECT()
    user32.GetWindowRect(worker, ctypes.byref(worker_rect2))
    worker_w = worker_rect2.right - worker_rect2.left
    worker_h = worker_rect2.bottom - worker_rect2.top

    log.info(
        "Injecao confirmada: hwnd=0x%08x -> WorkerW=0x%08x (worker=%dx%d, "
        "renderizando no monitor primario %dx%d em offset (%d,%d)).",
        hwnd, worker, worker_w, worker_h, mon_w, mon_h, rel_x, rel_y,
    )
    return True


# =====================================================================
#  Diagnostico
# =====================================================================
def dump_window_tree() -> str:
    """Despeja a arvore Progman/WorkerW — para debug quando injecao falha."""
    lines: list[str] = []

    def _walk(hwnd, depth=0):
        if not hwnd or depth > 3:
            return
        cls = ctypes.create_unicode_buffer(256)
        title = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls, 256)
        user32.GetWindowTextW(hwnd, title, 256)
        lines.append("  " * depth + f"{cls.value} '{title.value}' hwnd=0x{hwnd:08x}")
        child = user32.FindWindowExW(hwnd, None, None, None)
        while child:
            _walk(child, depth + 1)
            child = user32.FindWindowExW(hwnd, child, None, None)

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def _enum(hwnd, _):
        cls = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls, 256)
        if cls.value in ("Progman", "WorkerW"):
            _walk(hwnd)
        return True

    user32.EnumWindows(_enum, 0)
    return "\n".join(lines) or "(vazio)"


# =====================================================================
#  Watchdog do Explorer
# =====================================================================
class ExplorerWatchdog(threading.Thread):
    def __init__(self, get_hwnd, reapply, interval: float = 3.0):
        super().__init__(daemon=True, name="ExplorerWatchdog")
        self._get_hwnd = get_hwnd
        self._reapply = reapply
        self._interval = interval
        self._stop = threading.Event()
        self._last_pid = self._explorer_pid()

    @staticmethod
    def _explorer_pid():
        import psutil
        for p in psutil.process_iter(["name", "pid"]):
            if p.info.get("name", "").lower() == "explorer.exe":
                return p.info["pid"]
        return None

    def run(self) -> None:
        while not self._stop.wait(self._interval):
            pid = self._explorer_pid()
            if pid and pid != self._last_pid:
                log.warning("explorer reiniciou (pid %s -> %s); reinjetando...",
                            self._last_pid, pid)
                self._last_pid = pid
                try:
                    self._reapply(self._get_hwnd())
                except Exception:
                    log.exception("Falha ao reinjetar.")

    def stop(self) -> None:
        self._stop.set()