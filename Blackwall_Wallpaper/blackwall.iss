; Script do Inno Setup para Blackwall Live Wallpaper

[Setup]
AppName=Blackwall
AppVersion=1.0
AppPublisher=RealWill
DefaultDirName={autopf}\Blackwall
DefaultGroupName=Blackwall
OutputDir=dist
OutputBaseFilename=Blackwall-Setup
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
SetupIconFile=icon.ico

[Files]
; Copia a pasta que o PyInstaller gerou
Source: "dist\BlackwallWallpaper\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
; Atalhos
Name: "{group}\Blackwall"; Filename: "{app}\BlackwallWallpaper.exe"
Name: "{userdesktop}\Blackwall"; Filename: "{app}\BlackwallWallpaper.exe"; Tasks: desktopicon

[Tasks]
; Opção de criar atalho na área de trabalho
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; GroupDescription: "Atalhos:"

[Run]
; Pergunta se quer rodar após instalar
Filename: "{app}\BlackwallWallpaper.exe"; Description: "Executar Blackwall"; Flags: nowait postinstall skipifsilent