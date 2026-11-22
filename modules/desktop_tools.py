"""Reversible folder opening and native Windows file properties."""
import os,sys,ctypes
from pathlib import Path
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QMessageBox
WIN=sys.platform=='win32'
ROOT=r'Software\Classes\Directory\shell'
BACKUP=r'Software\FolderExplorer\DefaultBackup'
VERB='FolderExplorer'
def default_folders(enable):
    import winreg
    h=winreg.HKEY_CURRENT_USER
    def read(k,n):
        try:return winreg.QueryValueEx(k,n)
        except FileNotFoundError:return None
    if enable:
        p=Path(sys.executable).resolve()
        if not getattr(sys,'frozen',False) or p.name.lower()!='folder.exe':raise RuntimeError('Install Folder first.')
        with winreg.CreateKey(h,ROOT) as k,winreg.CreateKey(h,BACKUP) as b:
            previous=read(k,'')
            if read(b,'Saved') is None:
                if previous and previous[0]==VERB:raise RuntimeError('Existing default has no backup.')
                winreg.SetValueEx(b,'Present',0,winreg.REG_DWORD,int(previous is not None))
                if previous:winreg.SetValueEx(b,'Previous',0,previous[1],previous[0])
                winreg.SetValueEx(b,'Saved',0,winreg.REG_DWORD,1)
            with winreg.CreateKey(h,ROOT+'\\'+VERB) as v:winreg.SetValueEx(v,'',0,winreg.REG_SZ,'Open in Folder')
            with winreg.CreateKey(h,ROOT+'\\'+VERB+r'\command') as c:winreg.SetValueEx(c,'',0,winreg.REG_SZ,'"'+str(p)+'" "%1"')
            winreg.SetValueEx(k,'',0,winreg.REG_SZ,VERB)
    else:
        with winreg.OpenKey(h,ROOT,0,winreg.KEY_READ|winreg.KEY_SET_VALUE) as k,winreg.OpenKey(h,BACKUP,0,winreg.KEY_READ) as b:
            current=read(k,'')
            if current and current[0]==VERB:
                if read(b,'Present')[0]:
                    value,typ=read(b,'Previous');winreg.SetValueEx(k,'',0,typ,value)
                else:winreg.DeleteValue(k,'')
        winreg.DeleteKey(h,BACKUP)
    ctypes.windll.shell32.SHChangeNotify(0x08000000,0,None,None)
def set_default(host,enable):
    if not WIN:return
    if enable and QMessageBox.question(host,'Default folder opening','Use Folder for ordinary directory opening? Desktop, taskbar, Win+E and system locations may still use Explorer. Restore the previous default before uninstalling.')!=QMessageBox.Yes:return
    try:default_folders(enable);QMessageBox.information(host,'Windows integration','Folder-opening preference updated.')
    except Exception as e:QMessageBox.warning(host,'Windows integration',str(e))
def properties(host,path):
    if not WIN:
        p = Path(path)
        try:
            st = p.stat()
            from datetime import datetime
            details = (f'Name: {p.name}\nPath: {p}\n'
                       f'Type: {"Directory" if p.is_dir() else "File"}\n'
                       f'Size: {st.st_size:,} bytes\n'
                       f'Modified: {datetime.fromtimestamp(st.st_mtime):%Y-%m-%d %H:%M}\n'
                       f'Permissions: {oct(st.st_mode & 0o777)}')
            QMessageBox.information(host,'File properties',details)
        except OSError as exc:
            QMessageBox.warning(host,'Properties',str(exc))
        return
    from ctypes import wintypes
    class Info(ctypes.Structure):
        _fields_=[('cbSize',wintypes.DWORD),('fMask',ctypes.c_ulong),('hwnd',wintypes.HWND),('lpVerb',wintypes.LPCWSTR),('lpFile',wintypes.LPCWSTR),('lpParameters',wintypes.LPCWSTR),('lpDirectory',wintypes.LPCWSTR),('nShow',ctypes.c_int),('hInstApp',wintypes.HINSTANCE),('lpIDList',ctypes.c_void_p),('lpClass',wintypes.LPCWSTR),('hkeyClass',wintypes.HKEY),('dwHotKey',wintypes.DWORD),('hIcon',wintypes.HANDLE),('hProcess',wintypes.HANDLE)]
    i=Info();i.cbSize=ctypes.sizeof(i);i.fMask=0x0000000c;i.hwnd=int(host.winId());i.lpVerb='properties';i.lpFile=str(path);i.nShow=1
    if not ctypes.windll.shell32.ShellExecuteExW(ctypes.byref(i)):QMessageBox.warning(host,'Properties','Windows could not open the properties dialog.')
def run_admin(host,path):
    p=Path(path)
    if not WIN or p.suffix.lower()!='.exe' or not p.is_file():return
    if QMessageBox.question(host,'Run as administrator','Request elevation for:\n'+str(p))!=QMessageBox.Yes:return
    fn=ctypes.windll.shell32.ShellExecuteW;fn.restype=ctypes.c_void_p
    result=fn(int(host.winId()),'runas',str(p),None,str(p.parent),1)
    if not result or result<=32:QMessageBox.warning(host,'Run as administrator','Cancelled or failed.')
