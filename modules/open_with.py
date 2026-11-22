"""Local application preferences, no shell command interpolation."""
import os,sys,subprocess
from pathlib import Path
from PySide6.QtWidgets import QFileDialog,QMessageBox
from modules.photo_viewer import open_file, IMAGE_EXTENSIONS, is_qpv, complete_package
def launch_cached(path,prefs):
    exe=prefs.get('open_apps',{}).get(Path(path).suffix.lower(),'')
    if Path(path).suffix.lower() in IMAGE_EXTENSIONS and exe and is_qpv(exe):
        prefs.get('open_apps',{}).pop(Path(path).suffix.lower(),None)
        return open_file(path,prefs)
    if exe and Path(exe).is_file():
        try:subprocess.Popen([exe,path]);return
        except OSError:pass
    open_file(path,prefs)
def choose_app(host,path,prefs,play=False):
    if not Path(path).is_file():return
    exe,_=QFileDialog.getOpenFileName(host,'Play with' if play else 'Open with','','Applications (*.exe)' if sys.platform=='win32' else 'All files (*)')
    if not exe:return
    if is_qpv(exe) and not complete_package(exe):
        QMessageBox.warning(host,'Open with','This Quick Photo Viewer build is incomplete or obsolete. Install the current Windows package instead.');return
    try:
        subprocess.Popen([exe,path])
        if QMessageBox.question(host,'Remember application','Use this application for this file type inside Folder?')==QMessageBox.Yes:
            prefs.setdefault('open_apps',{})[Path(path).suffix.lower()]=exe;host.window().save()
    except OSError as exc:QMessageBox.warning(host,'Open with',str(exc))
