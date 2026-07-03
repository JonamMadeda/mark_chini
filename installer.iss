; Script generated for mark_chini

[Setup]
AppName=mark_chini
AppVersion=1.0
AppPublisher=JonamMadeda
AppPublisherURL=https://github.com/JonamMadeda/mark_chini
DefaultDirName={autopf}\mark_chini
DefaultGroupName=mark_chini
UninstallDisplayIcon={app}\mark_chini.exe
Compression=lzma2
SolidCompression=yes
OutputDir=.\dist
OutputBaseFilename=mark_chini_setup
PrivilegesRequired=admin

[Files]
Source: "dist\mark_chini.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\mark_chini"; Filename: "{app}\mark_chini.exe"
Name: "{group}\Uninstall mark_chini"; Filename: "{uninstallexe}"
Name: "{autoprograms}\mark_chini"; Filename: "{app}\mark_chini.exe"
Name: "{autodesktop}\mark_chini"; Filename: "{app}\mark_chini.exe"

[Run]
Filename: "{app}\mark_chini.exe"; Description: "Launch mark_chini"; Flags: postinstall nowait skipifsilent
