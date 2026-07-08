' Launches ShotSweep silently (no console window).
' Assumes this file sits in the same folder as ShotSweep.py.

Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")
strFolder = objFSO.GetParentFolderName(WScript.ScriptFullName)
strScript = strFolder & "\ShotSweep.py"

objShell.Run "pythonw """ & strScript & """", 0, False
