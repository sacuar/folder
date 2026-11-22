"""Local application preferences, no shell command interpolation."""
import os,sys,subprocess
from pathlib import Path
from PySide6.QtWidgets import QFileDialog,QMessageBox
from modules.photo_viewer import open_file
def launch_cached(path,prefs):
    exe=prefs.get('open_apps',{}).get(Path(path).suffix.lower(),'')
    if exe and Path(exe).is_file():
        try:subprocess.Popen([exe,path]);return
        except OSError:pass
    open_file(path,prefs)
def choose_app(host,path,prefs,play=False):
    if not Path(path).is_file():return
    exe,_=QFileDialog.getOpenFileName(host,'Play with' if play else 'Open with','','Applications (*.exe)' if sys.platform=='win32' else 'All files (*)')
    if not exe:return
    try:
        subprocess.Popen([exe,path])
        if QMessageBox.question(host,'Remember application','Use this application for this file type inside Folder?')==QMessageBox.Yes:
            prefs.setdefault('open_apps',{})[Path(path).suffix.lower()]=exe;host.window().save()
    except OSError as exc:QMessageBox.warning(host,'Open with',str(exc))
