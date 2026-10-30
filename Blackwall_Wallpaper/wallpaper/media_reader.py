"""Leitor de midia: winrt nativo, fallback PowerShell, fallback psutil."""
from __future__ import annotations

import asyncio
import json
import logging
import subprocess
import sys
import threading
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass
class MediaInfo:
    title: str = ""
    artist: str = ""
    playing: bool = False
    source: str = ""


PS_SCRIPT = r"""
Add-Type -AssemblyName Windows.Foundation
[Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager, Windows.Media.Control, ContentType=WindowsRuntime] | Out-Null
$sessionManager = [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager]::RequestAsync().GetAwaiter().GetResult()
$session = $sessionManager.GetCurrentSession()
if ($session) {
    $props = $session.TryGetMediaPropertiesAsync().GetAwaiter().GetResult()
    [PSCustomObject]@{ Title = $props.Title; Artist = $props.Artist } | ConvertTo-Json
}
"""


class MediaReader(threading.Thread):
    def __init__(self, poll_ms: int = 1000):
        super().__init__(daemon=True, name="MediaReader")
        self._poll = max(poll_ms, 300) / 1000.0
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._latest = MediaInfo()
        self._backend = self._detect_backend()

    @staticmethod
    def _detect_backend() -> str:
        try:
            from winrt.windows.media.control import (  # noqa: F401
                GlobalSystemMediaTransportControlsSessionManager,
            )
            log.info("Media backend: winrt")
            return "winrt"
        except Exception:
            log.info("Media backend: powershell")
            return "powershell"

    @property
    def latest(self) -> MediaInfo:
        with self._lock:
            return self._latest

    def _set(self, info: MediaInfo) -> None:
        with self._lock:
            self._latest = info

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        if self._backend == "winrt":
            try:
                asyncio.run(self._run_winrt())
                return
            except Exception:
                log.exception("winrt falhou, caindo para PowerShell.")
                self._backend = "powershell"
        self._run_powershell()

    async def _run_winrt(self) -> None:
        from winrt.windows.media.control import (
            GlobalSystemMediaTransportControlsSessionManager as MediaManager,
        )
        manager = await MediaManager.request_async()
        while not self._stop_event.is_set():
            info = MediaInfo(source="winrt")
            try:
                session = manager.get_current_session()
                if session:
                    props = await session.try_get_media_properties_async()
                    if props:
                        info.title = props.title or ""
                        info.artist = props.artist or ""
                    pb = session.get_playback_info()
                    if pb:
                        info.playing = pb.playback_status.name == "PLAYING"
            except Exception:
                pass
            self._set(info)
            await asyncio.sleep(self._poll)

    def _run_powershell(self) -> None:
        si = None
        creationflags = 0
        if sys.platform == "win32":
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = 0
            creationflags = subprocess.CREATE_NO_WINDOW

        while not self._stop_event.is_set():
            info = MediaInfo(source="powershell")
            try:
                r = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", PS_SCRIPT],
                    capture_output=True, text=True, timeout=2,
                    startupinfo=si, creationflags=creationflags,
                )
                if r.stdout.strip():
                    data = json.loads(r.stdout)
                    if data.get("Title"):
                        info.title = data["Title"]
                        info.artist = data.get("Artist") or "STREAMING"
                        info.playing = True
                        self._set(info)
                        self._stop_event.wait(self._poll)
                        continue
            except Exception:
                pass

            try:
                import psutil
                for proc in psutil.process_iter(["name", "title"]):
                    pinfo = proc.info
                    name = (pinfo.get("name") or "").lower()
                    title = pinfo.get("title") or ""
                    if title and any(t in name for t in
                                     ("spotify", "chrome", "brave", "firefox", "msedge")):
                        if " - " in title and not any(
                            ign in title for ign in ("Visual Studio", "Google")
                        ):
                            parts = title.split(" - ")
                            info.title = parts[0].strip()
                            info.artist = (
                                parts[1]
                                .replace(" - YouTube Music", "")
                                .replace(" - Spotify", "")
                                .strip()
                            )
                            info.playing = True
                            self._set(info)
                            break
            except Exception:
                pass

            self._stop_event.wait(self._poll)


class AudioPeakReader:
    """Nivel de pico do audio (0.0-1.0) via pycaw.

    A API do pycaw muda entre versoes. Tentamos varias abordagens em
    ordem. Se todas falharem, loga os atributos do AudioDevice para
    diagnostico.
    """

    def __init__(self):
        self._meter = None
        try:
            from pycaw.pycaw import AudioUtilities
            device = AudioUtilities.GetSpeakers()
        except Exception as exc:
            log.info("pycaw indisponivel: %s", exc)
            return

        # Importa a interface uma vez
        try:
            from comtypes import CLSCTX_ALL
            try:
                from pycaw.pycaw import IAudioMeterInformation
            except ImportError:
                from pycaw.api.audiometer import IAudioMeterInformation  # type: ignore
        except Exception as exc:
            log.info("pycaw: nao foi possivel importar interfaces: %s", exc)
            return

        # 1) Atributo direto AudioMeterInformation
        try:
            meter = getattr(device, "AudioMeterInformation", None)
            if meter is not None:
                self._meter = meter
                log.info("pycaw: beat ativo (AudioMeterInformation direto).")
                return
        except Exception as exc:
            log.debug("pycaw AudioMeterInformation: %s", exc)

        # 2) Activate direto no AudioDevice
        try:
            iface = device.Activate(IAudioMeterInformation._iid_, CLSCTX_ALL, None)
            self._meter = iface.QueryInterface(IAudioMeterInformation)
            log.info("pycaw: beat ativo (Activate direto).")
            return
        except Exception as exc:
            log.debug("pycaw Activate direto: %s", exc)

        # 3) Atributo interno _dev (IMMDevice cru)
        try:
            raw = getattr(device, "_dev", None)
            if raw is not None:
                iface = raw.Activate(IAudioMeterInformation._iid_, CLSCTX_ALL, None)
                self._meter = iface.QueryInterface(IAudioMeterInformation)
                log.info("pycaw: beat ativo (via _dev.Activate).")
                return
        except Exception as exc:
            log.debug("pycaw _dev.Activate: %s", exc)

        # 4) IMMDeviceEnumerator manual
        try:
            from pycaw.pycaw import IMMDeviceEnumerator  # type: ignore
            from pycaw.constants import CLSID_MMDeviceEnumerator, EDataFlow, ERole  # type: ignore
            from comtypes import CoCreateInstance

            enumerator = CoCreateInstance(
                CLSID_MMDeviceEnumerator, IMMDeviceEnumerator, CLSCTX_ALL
            )
            raw = enumerator.GetDefaultAudioEndpoint(
                EDataFlow.eRender.value, ERole.eMultimedia.value
            )
            iface = raw.Activate(IAudioMeterInformation._iid_, CLSCTX_ALL, None)
            self._meter = iface.QueryInterface(IAudioMeterInformation)
            log.info("pycaw: beat ativo (IMMDeviceEnumerator).")
            return
        except Exception as exc:
            log.debug("pycaw IMMDeviceEnumerator: %s", exc)

        # Diagnostico
        try:
            attrs = [a for a in dir(device) if not a.startswith("_")][:15]
            log.info("pycaw: nenhuma API funcionou. Atributos publicos: %s", attrs)
        except Exception:
            pass
        log.info("pycaw: beat desativado.")

    @property
    def available(self) -> bool:
        return self._meter is not None

    def peak(self) -> float:
        if not self._meter:
            return 0.0
        try:
            return float(self._meter.GetMasterPeakValue())
        except Exception:
            return 0.0