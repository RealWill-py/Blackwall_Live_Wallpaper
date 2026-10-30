Blackwall Cyberpunk Live Wallpaper
Live wallpaper interativo estilo Cyberpunk Blackwall para Windows.
Backend PyQt6/WebEngine + motor de renderização HTML5 Canvas (Linhas/Voxels).

O projeto foi refatorado para oferecer uma experiência imersiva e de alta performance, integrando-se nativamente à área de trabalho do Windows.

✨ Funcionalidades
Injeção Nativa no Desktop: O wallpaper roda atrás dos ícones da área de trabalho (camada WorkerW), agindo como um papel de parede real e não como uma janela flutuante.

Motor Blackwall (Linhas): Renderização baseada em linhas verticais cuja altura e brilho reagem à luminosidade da imagem, criando o efeito de "cortina de luz" cyberpunk.

Background Procedural: Textura de fundo dinâmica com grid de linhas, chuva digital (matrix rain), scanlines e efeitos de glitch sutis.

HUD Unificado: Painel estilo Cyber-Deck fixado na parte inferior da tela (acima da barra de tarefas), exibindo Relógio, Métricas do Sistema (CPU/RAM) e Informações de Mídia.

Media Reader Avançado: Leitura de mídia global (Spotify, YouTube, etc.) via API nativa do Windows (WinRT), com fallback para PowerShell.

Beat Detector: Efeitos visuais no HUD e nas linhas que pulsam de acordo com o áudio do sistema (via pycaw).

Controle de Densidade: Ajuste em tempo real da quantidade de linhas/voxels (5 níveis) diretamente pelo ícone na bandeja do sistema.

Multi-monitor Ready: A injeção e o dimensionamento são calculados com base no monitor primário, evitando distorções em setups com múltiplas telas.

Watchdog do Explorer: Se o explorer.exe reiniciar, o wallpaper é reinjetado automaticamente.

🚀 Instalação
Instale as dependências:

pip install -r requirements.txt

Coloque suas imagens (de preferência 1920x1080 - 16:9) na pasta images/.

Inicie o wallpaper:

python launcher.py

Ou clique duas vezes no arquivo play.vbs para iniciar sem a janela do terminal.

🎮 Controles
ESC: Fecha o wallpaper.

Tray Icon (Bandeja do Sistema):

Próxima Imagem: Avança manualmente a imagem.

Densidade de Voxels: Aumenta (+) ou diminui (-) a quantidade de linhas na tela.

Fechar Wallpaper: Encerra o processo.

🛠️ Estrutura do Projeto
launcher.py # Entry point (PyQt6, injeção WorkerW, sync)
config.py # Configurações persistentes (config.json)
index.html # Estrutura DOM (Canvas + HUD)
style.css # Estilização do Cyber-Deck e hover effects
script.js # Lógica do motor (Linhas, background, bridge)
wallpaper/
injector.py # API Win32 (WorkerW, watchdog, monitor primário)
bridge.py # Ponte QWebChannel Python <-> JS
media_reader.py # WinRT/PS + Beat Detector (pycaw)
system_monitor.py # Leitura de CPU/RAM (psutil)
tray.py # System Tray e menus
tests/ # Testes unitários (pytest)
images/ # Suas artes (.png, .jpg, .webp)

🧪 Testes e Build
Testes: Execute pytest -v para rodar a suíte de testes.

Build (.exe): Execute pyinstaller build.spec. O executável será gerado em dist/BlackwallWallpaper/.

📝 Notas Técnicas
Resolução Ideal: Para preencher a tela perfeitamente sem margens, use imagens com a mesma proporção do seu monitor (ex: 1920x1080).

Compatibilidade: Desenvolvido e testado em Windows 10/11. A injeção força a flag WS_CHILD antes do SetParent para garantir a renderização correta.

Fallbacks de Mídia: Se o winrt-runtime falhar na instalação, o leitor de mídia muda automaticamente para um script PowerShell em segundo plano.

Beat Audio: Se a API do pycaw não for reconhecida, o recurso de beat é desativado silenciosamente para não quebrar o wallpaper.