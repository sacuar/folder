"""Optional drive tools: native Windows format UI; read-only duplicate and large-file reports."""
import os,sys,ctypes,hashlib,threading,heapq,time
from pathlib import Path
from PySide6.QtCore import QObject,QRunnable,QThreadPool,Signal,QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QDialog,QVBoxLayout,QLabel,QPushButton,QFileDialog,QPlainTextEdit,QMessageBox,QInputDialog
class Signals(QObject):done=Signal(str)
class Scan(QRunnable):
    def __init__(self,root,mode,stop):super().__init__();self.root=root;self.mode=mode;self.stop=stop;self.signals=Signals()
    def run(self):
        try:self.signals.done.emit(self.work())
        except Exception as e:self.signals.done.emit(str(e))
    def work(self):
        sizes={};large=[];count=0;budget=2*1024**3;start=time.monotonic()
        for base,dirs,files in os.walk(self.root,followlinks=False):
            if self.stop.is_set() or count>=100000 or time.monotonic()-start>120:break
            def safe(p):
                try:return not p.is_symlink() and not (getattr(p.lstat(),'st_file_attributes',0)&0x400)
                except OSError:return False
            dirs[:]=[d for d in dirs if d.lower() not in ('windows','system volume information','$recycle.bin') and safe(Path(base,d))]
            for name in files:
                if self.stop.is_set() or count>=100000:break
                p=Path(base,name)
                if not safe(p):continue
                try:n=p.stat().st_size
                except OSError:continue
                count+=1
                if self.mode=='large':
                    if n:heapq.heappush(large,(n,str(p)))
                    if len(large)>200:heapq.heappop(large)
                elif n:sizes.setdefault(n,[]).append(p)
        header=f'{count:,} accessible files examined; bounded scan. No deletion.\n\n'
        if self.mode=='large':return header+'\n'.join(f'{n/1048576:,.2f} MB  {p}' for n,p in sorted(large,reverse=True))
        groups={};skipped=0
        for size,paths in sizes.items():
            if len(paths)<2:continue
            for p in paths:
                if self.stop.is_set() or time.monotonic()-start>120:return header+'Scan stopped.'
                if size>budget:skipped+=1;continue
                budget-=size
                try:
                    h=hashlib.sha256()
                    with p.open('rb') as f:
                        for chunk in iter(lambda:f.read(1048576),b''):
                            if self.stop.is_set():return header+'Scan stopped.'
                            h.update(chunk)
                    groups.setdefault((size,h.hexdigest()),[]).append(str(p))
                except OSError:pass
        return header+f'{skipped} skipped for 2 GiB hashing budget.\n\n'+'\n\n'.join('\n'.join(v) for v in groups.values() if len(v)>1)
def report(host,mode):
    path=QFileDialog.getExistingDirectory(host,'Choose folder or drive to scan')
    if not path:return
    d=QDialog(host);d.setWindowTitle('Largest files' if mode=='large' else 'Duplicate files');d.resize(850,550);l=QVBoxLayout(d);text=QPlainTextEdit('Scanning…');text.setReadOnly(True);l.addWidget(text)
    stop=threading.Event();b=QPushButton('Close / cancel');b.clicked.connect(d.reject);l.addWidget(b)
    job=Scan(path,mode,stop);job.signals.done.connect(text.setPlainText);QThreadPool.globalInstance().start(job);d.exec();stop.set()
def format_drive(host):
    if sys.platform!='win32':return
    mask=ctypes.windll.kernel32.GetLogicalDrives()
    sysdrive=os.environ.get('SystemDrive','C:').upper()
    drives=[chr(i+65)+':' for i in range(26) if mask&(1<<i) and chr(i+65)+':'!=sysdrive and ctypes.windll.kernel32.GetDriveTypeW(chr(i+65)+':\\')==2]
    if not drives:QMessageBox.information(host,'Format removable drive','No removable drives detected. For fixed drives use Windows Disk Management.');return
    drive,ok=QInputDialog.getItem(host,'Format removable drive','Select removable drive:',drives,0,False)
    if not ok:return
    typed,ok=QInputDialog.getText(host,'Data loss warning','Formatting erases all files on '+drive+'. Type '+drive+' to open the Windows format dialog.')
    if not ok or typed.strip().upper()!=drive:return
    if ctypes.windll.kernel32.GetDriveTypeW(drive+'\\')!=2:return
    ctypes.windll.shell32.SHFormatDrive(int(host.winId()),ord(drive[0])-65,0xffff,0)
def register(api):
    api.action('Find largest files…',lambda host:report(host,'large'))
    api.action('Find duplicate files…',lambda host:report(host,'duplicates'))
    if sys.platform=='win32':
        api.action('Format removable drive…',format_drive)
        api.action('Windows Disk Management…',lambda host:__import__('subprocess').Popen(['mmc.exe','diskmgmt.msc']))
