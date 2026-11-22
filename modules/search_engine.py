"""Launch the bundled portable engine only on demand; never silently elevate Folder."""
import os,sys,subprocess
from pathlib import Path
def bundled():
    root=Path(sys.executable).parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parents[1]/'vendor'
    p=root/'everything'/'Everything.exe'
    return p if sys.platform=='win32' and p.is_file() else None
def start():
    p=bundled()
    if p:
        subprocess.Popen([str(p),'-startup','-first-instance'],cwd=str(p.parent))
        return True
    return False
def reindex():
    p=bundled()
    if p:subprocess.Popen([str(p),'-startup','-reindex'],cwd=str(p.parent));return True
    return False
def install_service():
    p=bundled()
    if p:
        # Windows handles elevation for the vendor's service installation option.
        import ctypes
        return ctypes.windll.shell32.ShellExecuteW(None,'runas',str(p),'-install-service',str(p.parent),1)>32
    return False
