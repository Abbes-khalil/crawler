; Inno Setup script for AS Biz Dev Web Intelligence (per-user, no admin).
; Compile:  iscc /DAppVersion=0.1.0 packaging\windows\installer.iss
; Expects the PyInstaller onefile at: dist\AS Biz Dev Web Intelligence.exe

#ifndef AppVersion
  #define AppVersion "0.1.0"
#endif

#define AppName "AS Biz Dev Web Intelligence"
#define AppExe "AS Biz Dev Web Intelligence.exe"

[Setup]
AppId={{7C4B2E90-2C1A-4E7F-9E2B-ASBIZDEVWEB01}}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=AS Biz Dev
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\{#AppExe}
; {#SourcePath} is this .iss file's directory (packaging\windows\).
OutputDir={#SourcePath}\..\..\dist
OutputBaseFilename=AS-Biz-Dev-Web-Intelligence-{#AppVersion}-setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; On upgrade, close a running instance so its files can be replaced.
CloseApplications=yes
RestartApplications=no

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; Flags: unchecked
Name: "autostart"; Description: "Start {#AppName} automatically when I sign in to Windows"; Flags: unchecked

[Files]
Source: "..\..\dist\{#AppExe}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Registry]
; Per-user autostart (no admin). Only created if the task is selected;
; uninstalldeletevalue removes it on uninstall.
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
  ValueType: string; ValueName: "{#AppName}"; ValueData: """{app}\{#AppExe}"""; \
  Flags: uninstalldeletevalue; Tasks: autostart

[Run]
; Launch at the end of setup (checkbox, ticked by default on non-silent installs).
Filename: "{app}\{#AppExe}"; Description: "Launch {#AppName} now"; \
  Flags: nowait postinstall skipifsilent runasoriginaluser

[UninstallRun]
; Stop a running instance before removing files.
Filename: "{sys}\taskkill.exe"; Parameters: "/F /IM ""{#AppExe}"""; \
  Flags: runhidden skipifdoesntexist; RunOnceId: "StopApp"
