"""Non-destructive maintenance with bounded local scans in background threads."""
import os,sys,shutil,hashlib,subprocess
from pathlib import Path
from collections import defaultdict
from PySide6.QtCore import QObject,Signal,QRunnable,QThreadPool,QUrl,QProcess
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QDialog,QVBoxLayout,QLabel,QPlainTextEdit,QPushButton,QFileDialog,QMessageBox
from modules.everything_search import count
DOC={'.txt','.md','.doc','.docx','.pdf','.xls','.xlsx','.ppt','.pptx','.odt','.csv','.rtf'}
class Signals(QObject):
    done=Signal(str)
class Job(QRunnable):
    def __init__(self,fn):super().__init__();self.fn=fn;self.signals=Signals()
    def run(self):
        try:result=self.fn()
        except Exception as exc:result=str(exc)
        self.signals.done.emit(result)
def dialog(host,title,fn):
    d=QDialog(host);d.setWindowTitle(title);d.resize(700,480);l=QVBoxLayout(d);l.addWidget(QLabel('Read-only report. Your files will not be modified.'))
    out=QPlainTextEdit('Scanning…');out.setReadOnly(True);l.addWidget(out,1);b=QPushButton('Close');b.clicked.connect(d.accept);l.addWidget(b)
    j=Job(fn);j.signals.done.connect(out.setPlainText);QThreadPool.globalInstance().start(j);d.exec()
def paths(root):
    n=0
    for base,dirs,files in os.walk(root,followlinks=False):
        dirs[:]=[x for x in dirs if not os.path.islink(os.path.join(base,x)) and x not in ('.git','node_modules','System Volume Information','$Recycle.Bin')]
        for name in files:
            p=Path(base,name)
            if p.is_symlink():continue
            yield p;n+=1
            if n>=100000:return
def storage(host):
    path=host.active().path
    prefs=dict(host.prefs)
    def work():
        use=shutil.disk_usage(path);free=100*use.free/max(use.total,1)
        lines=[f'Drive of {path}',f'Total: {use.total/1024**3:.2f} GiB',f'Used: {use.used/1024**3:.2f} GiB',f'Free: {use.free/1024**3:.2f} GiB ({free:.1f}%)']
        if free<10:lines.append('Warning: less than 10% free space.')
        try:lines.extend([f'Everything indexed files: {count(prefs,"file:"):,}',f'Everything indexed documents: {count(prefs,"file: ext:txt;md;doc;docx;pdf;xls;xlsx;ppt;pptx;odt;csv;rtf"):,}','Counts are across the Everything index, not just this folder.'])
        except Exception:
            n=docs=0
            for p in paths(path):n+=1;docs+=p.suffix.lower() in DOC
            lines.extend([f'Files in selected folder tree: {n:,}',f'Documents: {docs:,}','Fallback scan limited to 100,000 accessible files.'])
        return '\n'.join(lines)
    dialog(host,'File count and drive usage',work)
def duplicates(host):
    root=QFileDialog.getExistingDirectory(host,'Choose folder to check for duplicates',host.active().path)
    if not root:return
    def work():
        sizes=defaultdict(list);groups=defaultdict(list);budget=1024**3;skipped=0
        for p in paths(root):
            try:s=p.stat().st_size
            except OSError:continue
            if s:sizes[s].append(p)
        for size,items in sizes.items():
            if len(items)<2:continue
            for p in items:
                if size>budget:skipped+=1;continue
                budget-=size
                try:
                    h=hashlib.sha256()
                    with p.open('rb') as f:
                        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
                    groups[(size,h.hexdigest())].append(str(p))
                except OSError:pass
        result=[v for v in groups.values() if len(v)>1]
        return f'{len(result)} matching groups. No files deleted. Scan limited to 100,000 files and 1 GiB of hashing; {skipped} candidates skipped for budget.\n\n'+'\n\n'.join('\n'.join(x) for x in result[:1000])
    dialog(host,'Duplicate file report (SHA-256)',work)
def clear_cache(host):
    from modules.thumbnails import ThumbnailModel
    for model in host.findChildren(ThumbnailModel):model.cache.clear()
    host.favicons.clear();host.refresh_sidebar()
    QMessageBox.information(host,'Clear cache','Folder thumbnail and website-icon caches cleared. No Windows or personal files removed.')
def windows_settings(url):
    if sys.platform=='win32':QDesktopServices.openUrl(QUrl(url))
def installation_maintenance(host):
    root=Path(sys.executable).parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parents[1]
    script=root/'maintenance.ps1'
    if not script.is_file():
        QMessageBox.information(host,'Installation maintenance','Available in the Windows installer or source directory.');return
    previous=getattr(host,'maintenance_process',None)
    if previous and previous.state()!=QProcess.NotRunning:return
    proc=QProcess(host);host.maintenance_process=proc
    proc.setProgram('powershell.exe')
    proc.setArguments(['-NoProfile','-STA','-ExecutionPolicy','Bypass','-File',str(script),'-App','Folder','-ProtectPath',str(root)])
    def finished(code,status):
        if code or status!=QProcess.NormalExit:
            error=bytes(proc.readAllStandardError()).decode(errors='replace').strip()
            QMessageBox.warning(host,'Installation maintenance failed',error[-4000:] or f'Exit code: {code}')
    proc.finished.connect(finished)
    proc.errorOccurred.connect(lambda _:QMessageBox.warning(host,'Installation maintenance',proc.errorString()))
    proc.start()
def add_tools(host):
    menu=host.menuBar().addMenu('Tools')
    from modules.build_manager import open_manager
    menu.addAction('Old Build Manager…',lambda:open_manager(host))
    menu.addAction('Installer maintenance (legacy)…',lambda:installation_maintenance(host)).setEnabled(sys.platform=='win32')
    menu.addAction('Everything search…',lambda:__import__('modules.everything_search',fromlist=['open_search']).open_search(host))
    menu.addAction('File count and drive usage…',lambda:storage(host))
    menu.addAction('Find duplicate files…',lambda:duplicates(host))
    menu.addAction('Clear Folder cache…',lambda:clear_cache(host));menu.addSeparator()
    for label,url in [('Installed apps / uninstall','ms-settings:appsfeatures'),('Windows Update','ms-settings:windowsupdate'),('Default apps','ms-settings:defaultapps')]:
        menu.addAction(label,lambda u=url:windows_settings(u)).setEnabled(sys.platform=='win32')
