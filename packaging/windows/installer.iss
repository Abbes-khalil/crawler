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
OutputDir=dist
OutputBaseFilename=AS-Biz-Dev-Web-Intelligence-{#AppVersion}-setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; Flags: unchecked

[Files]
Source: "..\..\dist\{#AppExe}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{userdesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent
