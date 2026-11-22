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
DefaultDirName={autopf}\Folder
DefaultGroupName=Folder
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog commandline
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=..\..\installer
OutputBaseFilename=Folder-{#AppVersion}-Setup-x64
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
WizardImageFile=..\..\assets\wizard.bmp
WizardSmallImageFile=..\..\assets\wizard-small.bmp
DisableWelcomePage=no
CloseApplications=yes
RestartApplications=no
UninstallDisplayIcon={app}\Folder.exe
SetupIconFile=..\..\assets\folder.ico
LicenseFile=..\..\LICENSE
[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked
[Files]
Source: "..\..\maintenance.ps1"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\maintenance.ps1"; DestName: "Setup-Maintenance.ps1"; Flags: dontcopy
Source: "..\..\dist\Folder\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\THIRD_PARTY_NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{autoprograms}\Folder maintenance"; Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\maintenance.ps1"" -App Folder -ProtectPath ""{app}"""; IconFilename: "{app}\Folder.exe"
Name: "{autoprograms}\Folder"; Filename: "{app}\Folder.exe"; IconFilename: "{app}\Folder.exe"
Name: "{autodesktop}\Folder"; Filename: "{app}\Folder.exe"; IconFilename: "{app}\Folder.exe"; Tasks: desktopicon
[Registry]
Root: HKCU; Subkey: "Software\FolderExplorer"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletevalue uninsdeletekeyifempty
[Run]
Filename: "{app}\Folder.exe"; Description: "Launch Folder"; Flags: nowait postinstall skipifsilent
[UninstallDelete]
Type: files; Name: "{app}\Folder.exe"

[Code]
procedure OpenMaintenance(Sender: TObject);
var Code: Integer;
begin
  ExtractTemporaryFile('Setup-Maintenance.ps1');
  if not Exec(ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe'), '-NoProfile -ExecutionPolicy Bypass -File "' + ExpandConstant('{tmp}\Setup-Maintenance.ps1') + '" -App Folder -ProtectPath "' + WizardDirValue + '"', '', SW_SHOWNORMAL, ewWaitUntilTerminated, Code) then
    MsgBox('Unable to open installation maintenance.', mbError, MB_OK);
end;
procedure InitializeWizard;
var Page: TWizardPage; Info: TNewStaticText; Button: TNewButton;
begin
  Page := CreateCustomPage(wpSelectDir, 'Review previous builds', 'Optional maintenance before installation');
  Info := TNewStaticText.Create(Page); Info.Parent := Page.Surface; Info.Width := Page.SurfaceWidth; Info.WordWrap := True; Info.Caption := 'Find previous Folder builds, installation paths and startup entries. Review results; nothing is removed automatically.';
  Button := TNewButton.Create(Page); Button.Parent := Page.Surface; Button.Top := ScaleY(66); Button.Width := ScaleX(235); Button.Caption := 'Scan and review old builds...'; Button.OnClick := @OpenMaintenance;
end;
