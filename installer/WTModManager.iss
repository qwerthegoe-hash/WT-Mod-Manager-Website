; WT Mod Manager — branded Windows setup
; Compiled with Inno Setup >=6.6 on Windows GitHub Actions.
; Installer is per-user (no admin UAC), upgradable and uninstallable.
; It never changes %LOCALAPPDATA%\WTModManager account settings or saved mods.

#ifndef MyAppVersion
  #define MyAppVersion "1.3.0-beta.5"
#endif

#define AppName "WT Mod Manager"
#define AppExe "WTModManager.exe"
#define AppSite "https://qwerthegoe-hash.github.io/WT-Mod-Manager-Website/"

[Setup]
AppId=WTModManager
AppName={#AppName}
AppVersion={#MyAppVersion}
AppVerName={#AppName} {#MyAppVersion}
AppPublisher=WT Mod Manager Community
AppPublisherURL={#AppSite}
AppSupportURL={#AppSite}
AppUpdatesURL={#AppSite}updates.html
DefaultDirName={localappdata}\Programs\WT Mod Manager
DefaultGroupName=WT Mod Manager
DisableProgramGroupPage=yes
DisableDirPage=no
UsePreviousAppDir=yes
UsePreviousGroup=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
MinVersion=10.0
WizardStyle=modern dark polar includetitlebar
WizardImageFile=..\build\installer\wizard.png
WizardSmallImageFile=..\build\installer\wizard-small.png
WizardImageBackColor=#0D1625
WizardSmallImageBackColor=#0D1625
SetupIconFile=..\build\installer\WTModManager.ico
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
OutputDir=..\dist
OutputBaseFilename=WTModManager-Setup
Compression=lzma2
SolidCompression=yes
CloseApplications=yes
CloseApplicationsFilter=WTModManager.exe
RestartApplications=no
SetupLogging=yes
ShowLanguageDialog=auto
VersionInfoCompany=WT Mod Manager Community
VersionInfoDescription=WT Mod Manager Windows Installer
VersionInfoProductName=WT Mod Manager
VersionInfoCopyright=WT Mod Manager Community
VersionInfoVersion=1.3.0.5
WizardResizable=yes
WizardKeepAspectRatio=yes

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык WT Mod Manager на рабочем столе"; GroupDescription: "Дополнительные параметры"; Flags: checkedonce

[Files]
Source: "..\dist\WTModManager\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "wtmm.installed"; DestDir: "{app}"; Flags: ignoreversion
Source: "Pin-to-taskbar.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; DestName: "README.txt"; Flags: ignoreversion

[Icons]
Name: "{group}\WT Mod Manager"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"; IconFilename: "{app}\{#AppExe}"
Name: "{group}\Удалить WT Mod Manager"; Filename: "{uninstallexe}"
Name: "{autodesktop}\WT Mod Manager"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"; IconFilename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "Запустить WT Mod Manager"; Flags: postinstall nowait skipifsilent
Filename: "{sys}\notepad.exe"; Parameters: """{app}\Pin-to-taskbar.txt"""; Description: "Показать, как закрепить WT Mod Manager на панели задач"; Flags: postinstall nowait skipifsilent unchecked

[Code]
// Give the installer its own concise brand message, while keeping the
// native accessibility, keyboard navigation, and Windows setup behavior.
procedure InitializeWizard();
begin
  WizardForm.WelcomeLabel1.Caption := 'WT MOD MANAGER';
  WizardForm.WelcomeLabel2.Caption :=
    'Мастер установки WT Mod Manager.' + #13#10 + #13#10 +
    'Выберите папку установки, затем настройте ярлык.' + #13#10 +
    'Пользовательские моды и настройки не будут удалены при обновлении.';
end;
