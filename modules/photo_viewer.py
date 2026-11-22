"""Open images in the separately installed Quick Photo Viewer when available."""
import os, sys, subprocess
from pathlib import Path
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
IMAGE_EXTENSIONS={'.jpg','.jpeg','.png','.webp','.bmp','.gif','.tif','.tiff','.ico'}

def locate_viewer(prefs):
    custom=prefs.get('photo_viewer_path','')
    candidates=[Path(custom)] if custom else []
    if sys.platform=='win32':
        import winreg
        key=r'Software\Microsoft\Windows\CurrentVersion\App Paths\QuickPhotoViewer.exe'
        for hive in (winreg.HKEY_CURRENT_USER,winreg.HKEY_LOCAL_MACHINE):
            try:
                with winreg.OpenKey(hive,key) as k:
                    candidates.append(Path(winreg.QueryValueEx(k,'')[0].strip('"')))
            except OSError:pass
        for var in ('ProgramFiles','ProgramW6432','LOCALAPPDATA'):
            if os.environ.get(var):
                base=Path(os.environ[var]); candidates.extend([base/'Quick Photo Viewer'/'QuickPhotoViewer.exe',base/'Programs'/'Quick Photo Viewer'/'QuickPhotoViewer.exe'])
    return next((p for p in candidates if p.is_file() and p.suffix.lower()=='.exe'),None)

def open_file(path,prefs):
    if sys.platform=='win32' and Path(path).suffix.lower() in IMAGE_EXTENSIONS and prefs.get('quick_photo_viewer',True):
        exe=locate_viewer(prefs)
        if exe:
            try:
                subprocess.Popen([str(exe),str(Path(path).resolve())],cwd=str(exe.parent)); return True
            except OSError:pass
    return QDesktopServices.openUrl(QUrl.fromLocalFile(path))
