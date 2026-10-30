"""Testes do SystemMonitor."""
from __future__ import annotations
from unittest.mock import patch
from wallpaper.system_monitor import SystemMonitor


def test_sample_in_range():
    cpu, ram = SystemMonitor().sample()
    assert 0.0 <= cpu <= 100.0
    assert 0.0 <= ram <= 100.0


def test_sample_uses_psutil():
    mon = SystemMonitor()
    fake_vm = type("VM", (), {"percent": 42.0})()
    with patch("wallpaper.system_monitor.psutil.cpu_percent", return_value=17.5), \
         patch("wallpaper.system_monitor.psutil.virtual_memory", return_value=fake_vm):
        cpu, ram = mon.sample()
    assert cpu == 17.5
    assert ram == 42.0
