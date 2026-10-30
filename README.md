<img width="1920" height="1080" alt="{76CB2620-CC5B-445A-B2F8-080E2B0CFED7}" src="https://github.com/user-attachments/assets/2c5c6fb9-a3a8-4d15-aca7-e320084a3471" />



# 🎴 Blackwall — Cyberpunk Live Wallpaper

> Live wallpaper nativo para Windows com renderização procedural estilo *Cyberpunk 2077*.
> PyQt6 + WebEngine no backend, Canvas 2D no frontend.

<p align="center">
  <img src="https://img.shields.io/badge/Windows-10%2F11-0078D6?style=flat-square&logo=windows&logoColor=white" alt="Windows">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/PyQt6-6.6%2B-41CD52?style=flat-square&logo=qt&logoColor=white" alt="PyQt6">
  <img src="https://img.shields.io/badge/license-MIT-ff003c?style=flat-square" alt="License">
</p>

---

## ✨ O que faz

| | Recurso |
|---|---|
| 🖥️ | **Injeção nativa no desktop** — roda atrás dos ícones da área de trabalho (camada `WorkerW`), como wallpaper real |
| 🌐 | **Motor Blackwall** — linhas verticais cuja altura e brilho reagem à luminosidade da imagem, criando uma "cortina de luz" cyberpunk |
| 🎨 | **Background procedural** — grid, chuva digital, scanlines e glitches sutis |
| 📊 | **HUD Cyber-Deck** — relógio, CPU/RAM e mídia atual, fixado acima da taskbar |
| 🎵 | **Media Reader nativo** — leitura global de mídia (Spotify, YouTube) via WinRT, com fallback PowerShell |
| 🔊 | **Beat detector** — HUD e linhas pulsam com o áudio do sistema (`pycaw`) |
| 🎚️ | **Densidade ajustável** — 5 níveis, trocados pelo menu da bandeja |
| 🖱️ | **Multi-monitor ready** — dimensiona para o monitor primário |
| 🔄 | **Watchdog do Explorer** — reinjeta automaticamente se `explorer.exe` reiniciar |

---

## 🚀 Instalação

### Requisitos

- **Windows 10/11**
- **Python 3.10+** ([download](https://www.python.org/downloads/))
- **2 GB** livres em disco

### Passo a passo

```bash
# 1. Clone ou baixe o projeto
git clone https://github.com/RealWill-py/Live_Wallpaper_Windows.git
cd Live_Wallpaper_Windows

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Adicione imagens em ./images/  (1920×1080 · PNG · JPG · WEBP)

# 4. Inicie
python launcher.py
