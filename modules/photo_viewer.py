"""Resolve only installed, complete Quick Photo Viewer packages; never launch old build trees."""
import os,sys,re,subprocess
from pathlib import Path
from PySide6.QtCore import QUrl,Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication,QDialog,QVBoxLayout,QLabel,QMessageBox
IMAGE_EXTENSIONS={'.jpg','.jpeg','.png','.webp','.bmp','.gif','.tif','.tiff','.ico','.svg','.psd'}
def is_qpv(path):
    name=re.sub(r'[^a-z0-9]','',str(path).casefold())
    return 'quickphotoviewer' in name or 'quickpicviewer' in name
def complete_package(path):
    try:
        p=Path(path)
        if not p.is_absolute() or p.name.casefold()!='quickphotoviewer.exe' or not p.is_file():return False
        if any(x.casefold() in ('build','dist','source','.venv') or 'upgrade' in x.casefold() for x in p.parts[:-1]):return False
        roots=[p.parent,p.parent/'_internal']
        for root in roots:
            if not any(x.is_file() and re.fullmatch(r'python3\d+\.dll',x.name,re.I) for x in root.glob('python3*.dll')):continue
            if any(x.is_file() for x in (root/'Qt6Core.dll',root/'PySide6'/'Qt6Core.dll',root/'PySide6'/'Qt'/'bin'/'Qt6Core.dll')):return True
        return False
    except (OSError,ValueError):return False
def registry_viewers():
    if sys.platform!='win32':return []
    import winreg
    paths=[]
    # Stable integration registration first. Do not consult old per-user App Paths.
    for key,value in ((r'Software\BANGTools\QuickPhotoViewer','Executable'),(r'Software\Microsoft\Windows\CurrentVersion\App Paths\QuickPhotoViewer.exe','')):
        for hive in (winreg.HKEY_LOCAL_MACHINE,):
            for view in (winreg.KEY_WOW64_64KEY,winreg.KEY_WOW64_32KEY):
                try:
                    with winreg.OpenKey(hive,key,0,winreg.KEY_READ|view) as k:paths.append(Path(str(winreg.QueryValueEx(k,value)[0]).strip('"')))
                except OSError:pass
    return paths
def locate_viewer(prefs):
    if sys.platform!='win32':return None
    candidates=[]
    for var in ('ProgramW6432','ProgramFiles','ProgramFiles(x86)','LOCALAPPDATA'):
        if os.environ.get(var):
            base=Path(os.environ[var]);candidates.extend([base/'Quick Photo Viewer'/'QuickPhotoViewer.exe',base/'Programs'/'Quick Photo Viewer'/'QuickPhotoViewer.exe'])
    candidates.extend(registry_viewers())
    custom=prefs.get('photo_viewer_path','')
    if custom:candidates.append(Path(custom))
    return next((p for p in candidates if complete_package(p)),None)
def reset_image_choices(prefs):
    prefs.pop('photo_viewer_path',None)
    apps=prefs.get('open_apps',{})
    if isinstance(apps,dict):
        for ext in list(apps):
            if ext.lower() in IMAGE_EXTENSIONS and is_qpv(apps[ext]):apps.pop(ext,None)
def internal_view(path):
    from modules.fit_preview import FitPreview
    parent=QApplication.activeWindow()
    try:
        widget=FitPreview(path,Path(path).suffix.lower()=='.svg')
        dialog=QDialog(parent);dialog.setWindowTitle(Path(path).name+' — Folder image viewer')
        dialog.setAttribute(Qt.WA_DeleteOnClose);dialog.resize(950,700);layout=QVBoxLayout(dialog);layout.addWidget(widget,1);dialog.show()
        # Keep the Python wrapper until the Qt dialog is closed.
        app=QApplication.instance()
        dialogs=getattr(app,'_image_dialogs',[])
        app._image_dialogs=dialogs;dialogs.append(dialog)
        dialog.destroyed.connect(lambda *_:dialogs.remove(dialog) if dialog in dialogs else None)
        return True
    except Exception as e:
        QMessageBox.warning(parent,'Open image',str(e));return False
def open_file(path,prefs):
    if Path(path).suffix.lower() in IMAGE_EXTENSIONS:
        if prefs.get('quick_photo_viewer',True):
            exe=locate_viewer(prefs)
            if exe:
                try:
                    subprocess.Popen([str(exe),str(Path(path).resolve())],cwd=str(exe.parent));return True
                except OSError:pass
        # Do not delegate to a possibly stale Windows image association.
        return internal_view(path)
    return QDesktopServices.openUrl(QUrl.fromLocalFile(path))
