#define BasePath      "C:\\Users\\Administrator\\Desktop\\wenzhou\\系统清理大师\\build\\python\\新exe"
#define MyAppName     "文洲系统清理大师"
#define MyAppPublisher "王文洲工作室"
;=========仅在此处手动改版本号，其余全部自动=========
#define MyAppVersion  "4.0.4"
#define MyAppExeName  "文洲系统清理大师_v" + MyAppVersion + ".exe"

[Setup]
AppId={{7F3A9D7C-1B2E-4C5A-8D9F-7E6B5A4C3D2E1F0A}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableDirPage=no
DisableProgramGroupPage=no
OutputDir=C:\Users\Administrator\Desktop\wenzhou\releases
OutputBaseFilename=Setup_文洲系统清理大师_v{#MyAppVersion}
Compression=lzma2/ultra
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
SetupIconFile={#BasePath}\icon.ico
UninstallDisplayIcon={app}\icon.ico

[Languages]
Name: "chinese"; MessagesFile: "compiler:Languages\Chinese.isl"

[Files]
Source: "{#BasePath}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#BasePath}\icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#BasePath}\local_version.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"
Name: "{commonprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "运行{#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
  if not IsAdminInstallMode then
  begin
    MsgBox('❌ 请右键安装包 → 以管理员身份运行！', mbCriticalError, MB_OK);
    Result := False;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    MsgBox('✅ 安装完成！' + #13#10 + '版本：{#MyAppVersion}' + #13#10 + '程序已安装到：' + ExpandConstant('{app}'), mbInformation, MB_OK);
  end;
end;
end;