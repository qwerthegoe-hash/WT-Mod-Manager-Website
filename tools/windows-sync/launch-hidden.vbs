' WTMM: optional hidden launcher. Configure Task Scheduler to run wscript.exe with
' this .vbs path as the argument, instead of opening powershell.exe on screen.
' Keep the repository in the folder containing this file's tools/windows-sync parent.
Option Explicit
Dim fso, shell, folder, repo, ps, command
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")
folder = fso.GetParentFolderName(WScript.ScriptFullName)
repo = fso.GetAbsolutePathName(fso.BuildPath(folder, "..\.."))
ps = fso.BuildPath(folder, "sync-github-safe.ps1")
command = "powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy RemoteSigned -File """ & ps & """ -RepositoryPath """ & repo & """"
shell.Run command, 0, True
