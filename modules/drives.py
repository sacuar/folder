"""Drive labels and safe removal through the Windows shell UI."""
import ctypes,sys,subprocess
from PySide6.QtCore import QDir,Qt
from PySide6.QtWidgets import QMessageBox,QMenu
def drive_kind(path):
    if sys.platform!='win32':return ''
    kind=ctypes.windll.kernel32.GetDriveTypeW(str(path).replace('/','\\'))
    return {2:'Removable',3:'Local',4:'Network',5:'Optical',6:'RAM'}.get(kind,'Drive')
def safe_removal(host):
    if sys.platform!='win32':return
    try:subprocess.Popen(['rundll32.exe','shell32.dll,Control_RunDLL','hotplug.dll'])
    except OSError as exc:QMessageBox.warning(host,'Safely remove hardware',str(exc))
def sidebar_menu(host,point):
    item=host.side.itemAt(point)
    if not item:return
    path=item.data(Qt.UserRole)
    if path not in [d.absolutePath() for d in QDir.drives()]:return
    menu=QMenu(host)
    menu.addAction('Open',lambda:host.open_place(item))
    if sys.platform=='win32':menu.addAction('Safely remove hardware…',lambda:safe_removal(host))
    menu.exec(host.side.viewport().mapToGlobal(point))
