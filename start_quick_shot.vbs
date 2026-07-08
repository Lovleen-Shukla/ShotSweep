' Launches Quick Shot silently (no console window).
' Assumes this file sits in the same folder as quick_shot.py.

Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")
strFolder = objFSO.GetParentFolderName(WScript.ScriptFullName)
strScript = strFolder & "\quick_shot.py"

objShell.Run "pythonw """ & strScript & """", 0, False
