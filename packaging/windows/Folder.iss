#ifndef AppVersion
  #define AppVersion "0.5.0"
#endif
[Setup]
AppId={{14A42BC4-8AA3-4D97-AC72-58004C7EE1EB}
AppName=Folder
AppVersion={#AppVersion}
AppPublisher=Folder contributors
AppPublisherURL=https://github.com/sacuar/folder
AppSupportURL=https://github.com/sacuar/folder/issues
AppUpdatesURL=https://github.com/sacuar/folder/releases
DefaultDirName={localappdata}\Programs\Folder
DefaultGroupName=Folder
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=..\..\installer
OutputBaseFilename=Folder-{#AppVersion}-Setup-x64
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
UninstallDisplayIcon={app}\Folder.exe
LicenseFile=..\..\LICENSE
[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked
[Files]
Source: "..\..\dist\Folder\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\THIRD_PARTY_NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{autoprograms}\Folder"; Filename: "{app}\Folder.exe"
Name: "{autodesktop}\Folder"; Filename: "{app}\Folder.exe"; Tasks: desktopicon
[Registry]
Root: HKCU; Subkey: "Software\FolderExplorer"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletevalue uninsdeletekeyifempty
[Run]
Filename: "{app}\Folder.exe"; Description: "Launch Folder"; Flags: nowait postinstall skipifsilent
[UninstallDelete]
Type: files; Name: "{app}\Folder.exe"
