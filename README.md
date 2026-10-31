<div align="center">

# 🌆 BLACKWALL


[![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://microsoft.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.6+-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://pypi.org/project/PyQt6/)
[![License](https://img.shields.io/badge/License-MIT-ff003c?style=for-the-badge)](LICENSE)

<br>

<!-- Substitua o link abaixo por um GIF ou Print do seu wallpaper -->
<img width="1920" height="1080" alt="{76CB2620-CC5B-445A-B2F8-080E2B0CFED7}" src="https://github.com/user-attachments/assets/2c5c6fb9-a3a8-4d15-aca7-e320084a3471" />
</div>

---

## ⚡ Sobre o Projeto

O **Blackwall** não é apenas um vídeo em loop. É um motor de renderização que se injeta nativamente na camada `WorkerW` do Windows, rodando **atrás dos seus ícones**. Ele lê suas imagens, transforma a luminosidade em linhas verticais e cria uma experiência viva que reage ao seu mouse, à sua música e às métricas do seu PC.

---

## ✨ Recursos

<table>
  <tr>
    <td width="50%">
      <h3>🖥️ Injeção Nativa</h3>
      <p>Roda atrás dos ícones da área de trabalho. Sem janelas flutuantes, sem sobreposição na barra de tarefas. É um wallpaper de verdade.</p>
    </td>
    <td width="50%">
      <h3>🌐 Motor Blackwall</h3>
      <p>Renderização em linhas verticais. Partes claras da imagem geram linhas altas e brilhantes, criando o efeito de "cortina de luz".</p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>🎵 Media & Beat Detector</h3>
      <p>Leitura global do que está tocando (Spotify, YouTube) via WinRT. O HUD pulsa no ritmo da sua música usando a API de áudio do Windows.</p>
    </td>
    <td width="50%">
      <h3>📊 HUD Cyber-Deck</h3>
      <p>Painel unificado na base da tela exibindo Relógio, uso de CPU/RAM em tempo real e informações da faixa atual.</p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>🎚️ Densidade Ajustável</h3>
      <p>5 níveis de detalhamento (voxels). Troque direto pelo ícone na bandeja do sistema para deixar o efeito mais denso ou mais limpo.</p>
    </td>
    <td width="50%">
      <h3>🔄 Watchdog & Multi-Monitor</h3>
      <p>Se o Explorer do Windows reiniciar, o wallpaper se reinjeta sozinho. Dimensionamento inteligente focado no monitor primário.</p>
    </td>
  </tr>
</table>

---

## 🚀 Instalação Rápida

### Opção 1: Instalador (Recomendado)
1. Baixe o arquivo **`Blackwall-Setup.exe`** na aba de Releases.
2. Execute e siga as instruções na tela.
3. Coloque suas imagens (`.png`, `.jpg`, `.webp`) na pasta `images` criada ao lado do executável.
4. Abra o atalho **Blackwall** no seu Desktop.

### Opção 2: Rodando via código (Dev)
```bash
# Clone o repositório
git clone https://github.com/RealWill-py/Live_Wallpaper_Windows.git
cd Live_Wallpaper_Windows

# Instale as dependências
pip install -r requirements.txt

# Inicie
python launcher.py
