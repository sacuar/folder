import sys, subprocess
from pathlib import Path
KEY=r'Software\Classes\Directory\shell\FolderExplorer'
def register():
    import winreg
    args=[sys.executable] if getattr(sys,'frozen',False) else [sys.executable,str(Path(__file__).resolve().parents[1] / 'explorer.py')]
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER,KEY) as k: winreg.SetValueEx(k,'',0,winreg.REG_SZ,'Open in Folder')
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER,KEY+r'\command') as k: winreg.SetValueEx(k,'',0,winreg.REG_SZ,subprocess.list2cmdline(args)+' "%1"')
def unregister():
    import winreg
    for k in (KEY+r'\command',KEY):
        try:winreg.DeleteKey(winreg.HKEY_CURRENT_USER,k)
        except FileNotFoundError:pass
