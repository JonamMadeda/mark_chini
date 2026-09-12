; Script generated for mark_chini
; NOTE: AppId is intentionally "mark_chini" (not a GUID) to preserve the
; upgrade path for installs made by earlier installers that had no explicit
; AppId (Inno defaults AppId to AppName). Do NOT change it, or existing
; users will end up with two entries instead of an in-place upgrade.

[Setup]
AppId=mark_chini
AppName=mark_chini
AppVersion=1.3.0
AppPublisher=JonamMadeda
AppPublisherURL=https://github.com/JonamMadeda/mark_chini
DefaultDirName={autopf}\mark_chini
DefaultGroupName=mark_chini
UsePreviousAppDir=yes
DirExistsWarning=auto
UninstallDisplayIcon={app}\mark_chini.exe
SetupIconFile=app\icon.ico
WizardStyle=modern
Compression=lzma2
SolidCompression=yes
OutputDir=.\dist
OutputBaseFilename=mark_chini_setup
PrivilegesRequired=admin
CloseApplications=yes
RestartApplications=no

[Files]
Source: "dist\mark_chini.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\mark_chini"; Filename: "{app}\mark_chini.exe"; IconFilename: "{app}\mark_chini.exe"
Name: "{group}\Uninstall mark_chini"; Filename: "{uninstallexe}"
Name: "{autoprograms}\mark_chini"; Filename: "{app}\mark_chini.exe"; IconFilename: "{app}\mark_chini.exe"
Name: "{autodesktop}\mark_chini"; Filename: "{app}\mark_chini.exe"; IconFilename: "{app}\mark_chini.exe"

[Run]
Filename: "{app}\mark_chini.exe"; Description: "Launch mark_chini"; Flags: postinstall nowait skipifsilent

[Code]
procedure SHChangeNotify(wEventId: Longint; uFlags: Cardinal; dwItem1: Longint; dwItem2: Longint);
  external 'SHChangeNotify@shell32.dll stdcall';

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    { Recreate shortcuts with the new IconFilename above, then tell Explorer
      to refresh its icon cache so existing users see the custom icon
      immediately instead of the old generic one. }
    SHChangeNotify($08000000, 0, 0, 0);
  end;
end;
