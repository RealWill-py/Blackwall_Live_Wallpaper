<img width="1920" height="1080" alt="{76CB2620-CC5B-445A-B2F8-080E2B0CFED7}" src="https://github.com/user-attachments/assets/2c5c6fb9-a3a8-4d15-aca7-e320084a3471" />



════════════════════════════════════════════════════════════════════

B L A C K W A L L
Cyberpunk Live Wallpaper for Windows
"Uma cortina de luz atrás do seu desktop"

════════════════════════════════════════════════════════════════════

SOBRE
─────

O Blackwall é um live wallpaper interativo para Windows inspirado no
universo de Cyberpunk 2077. Ao contrário de wallpapers animados comuns,
ele é injetado diretamente na camada WorkerW do Windows — ou seja, roda
de verdade atrás dos ícones da área de trabalho, como um papel de parede
nativo.

A renderização é feita em linhas verticais que reagem à luminosidade das
suas imagens: partes claras geram linhas longas e brilhantes, partes
escuras geram linhas curtas e discretas. O resultado é uma "cortina de
luz" que pulsa com a música e reage ao mouse.

Backend em Python (PyQt6 + WebEngine), frontend em HTML5 Canvas.

RECURSOS
────────

• Injeção nativa no desktop
O wallpaper vive atrás dos ícones, na camada WorkerW do Windows.

• Motor Blackwall
Linhas verticais reativas à luminosidade da imagem, com efeito de
profundidade e oscilação sutil.

• Background procedural
Grid de linhas, chuva digital estilo Matrix, scanlines e glitches
ocasionais — tudo gerado em tempo real.

• HUD Cyber-Deck
Painel unificado com relógio, métricas de CPU/RAM e informações da
mídia atual, fixado acima da barra de tarefas.

• Leitor de mídia nativo
Detecta o que está tocando (Spotify, YouTube, etc.) via WinRT, com
fallback automático para PowerShell.

• Beat detector
O ícone do álbum pulsa em sincronia com o áudio do sistema.

• Densidade ajustável
5 níveis de voxels, alterados pelo menu da bandeja sem reiniciar.

• Watchdog do Explorer
Se o explorer.exe reiniciar, o wallpaper se reinjeta sozinho.

• Multi-monitor ready
Dimensiona e posiciona automaticamente no monitor primário.

REQUISITOS
──────────

• Windows 10 ou 11
• Python 3.10 ou superior (marcar "Add to PATH" na instalação)
• 2 GB de espaço livre em disco

INSTALAÇÃO
──────────

Clone ou baixe o projeto:

git clone https://github.com/RealWill-py/Live_Wallpaper_Windows.git
cd Live_Wallpaper_Windows

Instale as dependências:

pip install -r requirements.txt

Coloque suas imagens na pasta "images/"
Resolução recomendada: 1920x1080 (16:9) — PNG, JPG ou WEBP.

Inicie o wallpaper:

python launcher.py

Prefere sem terminal? Clique duas vezes em "play.vbs".

CONTROLES
─────────

Encerrar ESC ou bandeja → "Fechar Wallpaper"
Próxima imagem bandeja → "Próxima Imagem"
Aumentar densidade bandeja → "Densidade" → "Mais voxels (+)"
Diminuir densidade bandeja → "Densidade" → "Menos voxels (−)"

ESTRUTURA DO PROJETO
────────────────────

Blackwall_Wallpaper/
│
├── launcher.py Entry point · injeção · sync
├── config.py Configurações persistidas
├── build.spec PyInstaller
├── play.vbs Launcher silencioso
│
├── index.html DOM (Canvas + HUD)
├── style.css Estilo do Cyber-Deck
├── script.js Motor de render + bridge
│
├── wallpaper/
│ ├── injector.py Win32 · WorkerW · watchdog
│ ├── bridge.py QWebChannel Python ↔ JS
│ ├── media_reader.py WinRT · PowerShell · pycaw
│ ├── system_monitor.py CPU / RAM
│ └── tray.py System tray
│
├── tests/ pytest
└── images/ Suas artes

GERAR EXECUTÁVEL (.EXE)
───────────────────────

pip install pyinstaller
python -m PyInstaller build.spec --clean --noconfirm

O resultado fica em "dist/BlackwallWallpaper/".
Distribua a pasta inteira — não apague a subpasta "_internal/".

IMPORTANTE: depois de compilar, crie a pasta "images/" dentro de
"dist/BlackwallWallpaper/" e coloque suas imagens lá. O .exe não
lê imagens empacotadas — só as que estão ao lado dele.

TESTES
──────

pytest -v

NOTAS TÉCNICAS
──────────────

Resolução ideal das imagens
───────────────────────────
Use imagens com a mesma proporção do seu monitor. 1920x1080 é o
ideal para preencher a tela sem margens. Qualquer arquivo maior é
reduzido internamente para uma grade de 380 a 680px — imagens
gigantes não trazem ganho visual, só peso extra.

Compatibilidade com Windows
───────────────────────────
A injeção força a flag WS_CHILD antes do SetParent. Sem isso, a
janela fica na hierarquia do WorkerW mas o Windows a renderiza como
popup flutuante — o famoso "efeito de app em tela cheia". Também
há um sync_qt_geometry que propaga WM_SIZE para o QWebEngineView,
senão o canvas mantém o viewport antigo (2944px em vez de 1920px
em multi-monitor).

Leitor de mídia
───────────────
Três camadas, em ordem de preferência:

WinRT (winrt-runtime) — nativo, assíncrono

PowerShell — Windows.Media.Control em subprocesso oculto

psutil — varredura de títulos de janela

Se o pycaw falhar, o beat detector é desativado silenciosamente.

PALETA
──────

Blackwall Red #ff003c Borda, glow principal
Neon Magenta #ff007f Hover, topo das linhas
Neon Yellow #fcee0a LED de alerta
Neon Green #00ff88 LED de status
Background #010204 Fundo do canvas

LICENÇA
───────

MIT — use, modifique e redistribua à vontade.
Contribuições são muito bem-vindas.

════════════════════════════════════════════════════════════════════

// NIGHT CITY // ONLINE

════════════════════════════════════════════════════════════════════

