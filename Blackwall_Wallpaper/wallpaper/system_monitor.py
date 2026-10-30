"""Leitura de CPU/RAM."""
from __future__ import annotations

import psutil


class SystemMonitor:
    def sample(self):
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent
        return cpu, ram
