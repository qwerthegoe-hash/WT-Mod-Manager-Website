; WT Mod Manager branded Windows installer, beta 1.3.6.
; The installer itself NEVER silently pins the taskbar.
; Per-user mod files/settings live in %LOCALAPPDATA%\WTModManager and survive.
#ifndef MyAppVersion
  #define MyAppVersion "1.3.0-beta.6"
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
WizardSmallImageBackColor=none
WizardImageBackColor=#0D1625
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
VersionInfoVersion=1.3.0.6
WizardResizable=yes
WizardKeepAspectRatio=yes
AllowNoIcons=yes

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\dist\WTModManager\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "wtmm.installed"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; DestName: "README.txt"; Flags: ignoreversion

[Icons]
Name: "{group}\WT Mod Manager"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"; IconFilename: "{app}\{#AppExe}"
Name: "{group}\Удалить WT Mod Manager"; Filename: "{uninstallexe}"

[UninstallDelete]
Type: files; Name: "{autodesktop}\WT Mod Manager.lnk"
Type: files; Name: "{userstartup}\WT Mod Manager.lnk"

[Run]
Filename: "{app}\{#AppExe}"; Parameters: "{code:GetLaunchParams}"; Description: "Запустить WT Mod Manager"; Flags: postinstall nowait skipifsilent

[Code]
var
  FinishDesktopShortcut: TNewCheckBox;
  FinishTaskbarPin: TNewCheckBox;
  FinishAutoStart: TNewCheckBox;
  FinishOptionsLaidOut: Boolean;
  ChannelPage: TInputOptionWizardPage;
  PreviousVersion: String;

function GetLaunchParams(Param: String): String;
begin
  Result := '';
  if Assigned(FinishTaskbarPin) and FinishTaskbarPin.Checked then
    Result := '--offer-taskbar-pin';
end;

procedure InitializeWizard();
var
  Path: String;
  Saved: String;
begin
  WizardForm.WelcomeLabel1.Caption := 'WT MOD MANAGER';
  WizardForm.WelcomeLabel2.Caption :=
    'Фирменный мастер установки WT Mod Manager.' + #13#10 + #13#10 +
    'Выбери папку, затем настрой ярлыки на экране «Готово».' + #13#10 +
    'Моды и настройки пользователя сохраняются при переустановке.';
  if RegQueryStringValue(HKCU,
       'Software\Microsoft\Windows\CurrentVersion\Uninstall\WTModManager_is1',
       'DisplayVersion', PreviousVersion) then
  begin
    WizardForm.WelcomeLabel2.Caption :=
      WizardForm.WelcomeLabel2.Caption + #13#10 + #13#10 +
      'Обнаружена версия ' + PreviousVersion +
      '. Повторная установка обновит или восстановит файлы программы.';
  end;

  ChannelPage := CreateInputOptionPage(wpSelectDir,
    'Канал обновлений',
    'Какую версию программы получать?',
    'Стабильная — проверенные выпуски. Beta — новые функции раньше, ' +
    'но возможны ошибки. Выбор можно изменить позднее.',
    True, False);
  ChannelPage.Add('Stable — проверенные версии');
  ChannelPage.Add('Beta — тестовые версии');
  ChannelPage.Values[1] := True;
  Path := ExpandConstant('{localappdata}\WTModManager\update-channel.json');
  if LoadStringFromFile(Path, Saved) then
  begin
    if Pos('"stable"', Saved) > 0 then
      ChannelPage.Values[0] := True;
  end;

  FinishDesktopShortcut := TNewCheckBox.Create(WizardForm);
  FinishDesktopShortcut.Parent := WizardForm.FinishedPage;
  FinishDesktopShortcut.Caption := 'Создать ярлык на рабочем столе';
  FinishDesktopShortcut.Checked := True;
  FinishDesktopShortcut.Height := ScaleY(23);

  FinishTaskbarPin := TNewCheckBox.Create(WizardForm);
  FinishTaskbarPin.Parent := WizardForm.FinishedPage;
  FinishTaskbarPin.Caption := 'Закрепить на панели задач (с подтверждением Windows)';
  FinishTaskbarPin.Checked := False;
  FinishTaskbarPin.Height := ScaleY(23);

  FinishAutoStart := TNewCheckBox.Create(WizardForm);
  FinishAutoStart.Parent := WizardForm.FinishedPage;
  FinishAutoStart.Caption := 'Запускать вместе с Windows';
  FinishAutoStart.Checked :=
    FileExists(ExpandConstant('{userstartup}\WT Mod Manager.lnk'));
  FinishAutoStart.Height := ScaleY(23);
  FinishOptionsLaidOut := False;
end;

procedure CurPageChanged(CurPageID: Integer);
var
  Position: Integer;
begin
  if (CurPageID = wpFinished) and (not FinishOptionsLaidOut) then
  begin
    Position := WizardForm.RunList.Top;
    FinishDesktopShortcut.Left := WizardForm.RunList.Left;
    FinishTaskbarPin.Left := WizardForm.RunList.Left;
    FinishAutoStart.Left := WizardForm.RunList.Left;
    FinishDesktopShortcut.Width := WizardForm.RunList.Width;
    FinishTaskbarPin.Width := WizardForm.RunList.Width;
    FinishAutoStart.Width := WizardForm.RunList.Width;
    FinishDesktopShortcut.Top := Position;
    FinishTaskbarPin.Top := Position + ScaleY(25);
    FinishAutoStart.Top := Position + ScaleY(50);
    WizardForm.RunList.Top := Position + ScaleY(78);
    WizardForm.RunList.Height := WizardForm.RunList.Height - ScaleY(78);
    FinishOptionsLaidOut := True;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  Path: String;
  Json: String;
begin
  if CurStep = ssPostInstall then
  begin
    Path := ExpandConstant('{localappdata}\WTModManager');
    if ForceDirectories(Path) then
    begin
      if ChannelPage.Values[0] then
        Json := '{"channel":"stable"}'
      else
        Json := '{"channel":"beta"}';
      SaveStringToFile(Path + '\update-channel.json', Json, False);
    end;
  end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  Shortcut: String;
begin
  Result := True;
  if (CurPageID = wpFinished) and (not WizardSilent()) then
  begin
    Shortcut := ExpandConstant('{autodesktop}\WT Mod Manager.lnk');
    if FinishDesktopShortcut.Checked then
    begin
      try
        CreateShellLink(Shortcut, 'WT Mod Manager',
          ExpandConstant('{app}\WTModManager.exe'), '',
          ExpandConstant('{app}'),
          ExpandConstant('{app}\WTModManager.exe'),
          0, SW_SHOWNORMAL);
      except
        MsgBox('Не удалось создать ярлык на рабочем столе.', mbInformation, MB_OK);
      end;
    end
    else if FileExists(Shortcut) then
      DeleteFile(Shortcut);

    Shortcut := ExpandConstant('{userstartup}\WT Mod Manager.lnk');
    if FinishAutoStart.Checked then
    begin
      try
        CreateShellLink(Shortcut, 'WT Mod Manager — автозапуск',
          ExpandConstant('{app}\WTModManager.exe'), '',
          ExpandConstant('{app}'),
          ExpandConstant('{app}\WTModManager.exe'),
          0, SW_SHOWNORMAL);
      except
        MsgBox('Не удалось добавить WT Mod Manager в автозапуск.', mbInformation, MB_OK);
      end;
    end
    else if FileExists(Shortcut) then
      DeleteFile(Shortcut);

    // A taskbar pin requires a foreground app and a second, explicit Windows
    // confirmation. The installer never silently changes the user's taskbar.
    if FinishTaskbarPin.Checked then
      WizardForm.RunList.Checked[0] := True;
  end;
end;
