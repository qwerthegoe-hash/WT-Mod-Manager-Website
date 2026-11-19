; WT Mod Manager branded Windows installer, beta 1.3.9.
; The installer itself NEVER silently pins the taskbar.
; Per-user mod files/settings live in %LOCALAPPDATA%\WTModManager and survive.
#ifndef MyAppVersion
  #define MyAppVersion "1.3.0-beta.9"
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
WizardSmallImageBackColor=#202B3A
WizardImageBackColor=#0D1625
SetupIconFile=..\build\installer\WTModManager.ico
InfoAfterFile=release-notes.txt
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
VersionInfoVersion=1.3.0.9
WizardResizable=yes
WizardKeepAspectRatio=yes
AllowNoIcons=yes

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\dist\WTModManager.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "wtmm.installed"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; DestName: "README.txt"; Flags: ignoreversion

[Icons]
Name: "{group}\WT Mod Manager"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"; IconFilename: "{app}\{#AppExe}"; AppUserModelID: "WTModManager.Desktop"
Name: "{group}\Удалить WT Mod Manager"; Filename: "{uninstallexe}"

[InstallDelete]
; Remove only old runtime from an existing installation belonging to this app.
; Original user data is stored separately under %LOCALAPPDATA%\WTModManager.
Type: filesandordirs; Name: "{app}\_internal"; Check: HasLegacyRuntime

[UninstallDelete]
Type: files; Name: "{autodesktop}\WT Mod Manager.lnk"
Type: files; Name: "{userstartup}\WT Mod Manager.lnk"

[Run]
Filename: "{app}\{#AppExe}"; Parameters: "{code:GetLaunchParams}"; Description: "Запустить WT Mod Manager"; Flags: postinstall nowait skipifsilent

[Code]
function HasLegacyRuntime(): Boolean;
begin
  Result := FileExists(ExpandConstant('{app}\wtmm.installed')) and
            DirExists(ExpandConstant('{app}\_internal'));
end;

var
  FinishDesktopShortcut: TNewCheckBox;
  FinishTaskbarPin: TNewCheckBox;
  FinishAutoStart: TNewCheckBox;
  FinishOptionsLaidOut: Boolean;
  ChannelPage: TInputOptionWizardPage;
  InstallModePage: TInputOptionWizardPage;
  PortableImportPage: TInputOptionWizardPage;
  PortablePathPage: TInputDirWizardPage;
  PreviousVersion: String;
  HasExistingInstall: Boolean;
  ClearCachesOnUninstall: Boolean;

function GetLaunchParams(Param: String): String;
begin
  Result := '';
  if Assigned(FinishTaskbarPin) and FinishTaskbarPin.Checked then
    Result := '--offer-taskbar-pin';
end;

procedure InitializeWizard();
var
  Path: String;
  Saved: AnsiString;
begin
  WizardForm.WelcomeLabel1.Caption := 'WT MOD MANAGER';
  WizardForm.WelcomeLabel2.Caption :=
    'Фирменный мастер установки WT Mod Manager.' + #13#10 + #13#10 +
    'Выбери папку, затем настрой ярлыки на экране «Готово».' + #13#10 +
    'Моды и настройки пользователя сохраняются при переустановке.';
  HasExistingInstall := RegQueryStringValue(HKCU,
       'Software\Microsoft\Windows\CurrentVersion\Uninstall\WTModManager_is1',
       'DisplayVersion', PreviousVersion);
  if HasExistingInstall then
  begin
    WizardForm.WelcomeLabel2.Caption :=
      WizardForm.WelcomeLabel2.Caption + #13#10 + #13#10 +
      'Обнаружена версия ' + PreviousVersion +
      '. Повторная установка обновит или восстановит файлы программы.';
  end;

  InstallModePage := CreateInputOptionPage(wpSelectDir,
    'Режим установки', 'Как установить WT Mod Manager?',
    'Обычная установка сохраняет пользовательские данные. '
    + 'В расширенном режиме можно выбрать канал обновлений и импортировать '
    + 'настройки из portable-версии.',
    True, False);
  InstallModePage.Add('Обычная — установить или обновить');
  InstallModePage.Add('Расширенная — выбрать дополнительные параметры');
  if HasExistingInstall then
    InstallModePage.Add('Восстановить — повторно установить файлы программы');
  InstallModePage.Values[0] := True;

  ChannelPage := CreateInputOptionPage(InstallModePage.ID,
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

  PortableImportPage := CreateInputOptionPage(ChannelPage.ID,
    'Импорт из portable', 'Импортировать прежние настройки и моды?',
    'Существующие пользовательские данные не перезаписываются.',
    False, False);
  PortableImportPage.Add('Импортировать данные из старой portable-папки');
  PortableImportPage.Values[0] := False;

  PortablePathPage := CreateInputDirPage(PortableImportPage.ID,
    'Папка portable-версии', 'Откуда импортировать данные?',
    'Выбери папку, содержащую data и mods прежней portable-версии.',
    False, '');
  PortablePathPage.Add('');
  PortablePathPage.Values[0] := ExpandConstant('{userdocs}');

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

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;
  if PageID = ChannelPage.ID then
    Result := not InstallModePage.Values[1];
  if PageID = PortableImportPage.ID then
    Result := not InstallModePage.Values[1];
  if PageID = PortablePathPage.ID then
    Result := (not InstallModePage.Values[1]) or
              (not PortableImportPage.Values[0]);
end;

procedure CopyPortableCategory(const SourceBase, TargetBase, Category: String);
var
  FromPath: String;
  ToPath: String;
  Entry: TFindRec;
begin
  FromPath := SourceBase + '\mods\' + Category;
  ToPath := TargetBase + '\mods\' + Category;
  if not DirExists(FromPath) then
    Exit;
  if not ForceDirectories(ToPath) then
    Exit;
  if FindFirst(FromPath + '\*', Entry) then
  begin
    try
      repeat
        if ((Entry.Attributes and FILE_ATTRIBUTE_DIRECTORY) = 0) and
           ((Entry.Attributes and FILE_ATTRIBUTE_REPARSE_POINT) = 0) and
           (not FileExists(ToPath + '\' + Entry.Name)) then
          FileCopy(FromPath + '\' + Entry.Name,
                   ToPath + '\' + Entry.Name, True);
      until not FindNext(Entry);
    finally
      FindClose(Entry);
    end;
  end;
end;

procedure ImportPortableData(const SourceBase, TargetBase: String);
begin
  if FileExists(SourceBase + '\data\settings.json') and
     not FileExists(TargetBase + '\settings.json') then
    FileCopy(SourceBase + '\data\settings.json',
             TargetBase + '\settings.json', True);
  CopyPortableCategory(SourceBase, TargetBase, 'sights');
  CopyPortableCategory(SourceBase, TargetBase, 'sounds');
  CopyPortableCategory(SourceBase, TargetBase, 'camouflages');
  CopyPortableCategory(SourceBase, TargetBase, 'configurations');
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
  Json: AnsiString;
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
      if (not WizardSilent()) and InstallModePage.Values[1] and
         PortableImportPage.Values[0] then
        ImportPortableData(PortablePathPage.Values[0], Path);
    end;
  end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  Shortcut: String;
begin
  Result := True;
  if (not WizardSilent()) and (CurPageID = PortablePathPage.ID) then
  begin
    if (not DirExists(PortablePathPage.Values[0])) or
       ((not FileExists(PortablePathPage.Values[0] + '\data\settings.json')) and
        (not DirExists(PortablePathPage.Values[0] + '\mods'))) then
    begin
      MsgBox('Выбери существующую portable-папку с data/settings.json '
        + 'или каталогом mods. Никакие данные ещё не изменены.',
        mbError, MB_OK);
      Result := False;
      Exit;
    end;
  end;
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

function InitializeUninstall(): Boolean;
begin
  Result := True;
  ClearCachesOnUninstall := False;
  if not UninstallSilent() then
    ClearCachesOnUninstall :=
      MsgBox('Удалить также временный кэш и скачанные обновления?'
        + #13#10 + 'Настройки, моды и профили сохранятся в любом случае.',
        mbConfirmation, MB_YESNO) = idYes;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if (CurUninstallStep = usPostUninstall) and ClearCachesOnUninstall then
  begin
    DelTree(ExpandConstant('{localappdata}\WTModManager\cache'), True, True, True);
    DelTree(ExpandConstant('{localappdata}\WTModManager\updates'), True, True, True);
  end;
end;
