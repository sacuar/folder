"""Compact asynchronous Everything ES bridge. No local index or automatic service installation."""
import os,sys,shutil,tempfile,subprocess
from pathlib import Path
from PySide6.QtCore import Qt,QTimer,QProcess,QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLineEdit,QListWidget,QListWidgetItem,QLabel,QPushButton,QFileDialog,QDockWidget
from modules.open_with import launch_cached
from modules.search_engine import start,reindex,install_service

DOWNLOAD='https://www.voidtools.com/downloads/'
def locate(prefs):
    root=Path(sys.executable).parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parents[1]/'vendor'
    options=[prefs.get('everything_es',''),str(root/'everything'/'es.exe'),shutil.which('es.exe') or '',str(Path(os.environ.get('ProgramFiles','C:/Program Files'))/'Everything'/'es.exe')]
    return next((str(Path(p).resolve()) for p in options if p and Path(p).is_file() and Path(p).name.lower()=='es.exe'),None)
def count(prefs,query):
    exe=locate(prefs)
    if not exe:raise RuntimeError('Everything CLI not configured')
    p=subprocess.run([exe,'-timeout','1500','-get-result-count','-no-digit-grouping',query],capture_output=True,timeout=5,creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=='win32' else 0)
    if p.returncode:raise RuntimeError('Everything is not running or indexing')
    return int(p.stdout.decode('ascii').strip())
class SearchDock(QDockWidget):
    def __init__(self,host):
        super().__init__('Everything search',host);self.host=host;self.setObjectName('EverythingSearch');self.setAllowedAreas(Qt.BottomDockWidgetArea|Qt.RightDockWidgetArea)
        w=QWidget();l=QVBoxLayout(w);l.setContentsMargins(6,6,6,6);self.setWidget(w)
        row=QHBoxLayout();l.addLayout(row);self.query=QLineEdit();self.query.setPlaceholderText('Search indexed files and folders…');self.query.setClearButtonEnabled(True);row.addWidget(self.query,1)
        for text,fn in [('Start index',lambda:(start(),self.timer.start(1500))),('Reindex',lambda:(reindex(),self.timer.start(1500)))]:
            b=QPushButton(text);b.clicked.connect(fn);row.addWidget(b)
        self.status=QLabel('Search local files. Start index if the engine is not running.');l.addWidget(self.status)
        self.results=QListWidget();self.results.setUniformItemSizes(True);l.addWidget(self.results,1);self.results.itemDoubleClicked.connect(self.open_result)
        self.results.setContextMenuPolicy(Qt.CustomContextMenu);self.results.customContextMenuRequested.connect(self.context)
        self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.setInterval(280);self.timer.timeout.connect(self.search);self.query.textChanged.connect(lambda _:self.timer.start())
        self.proc=QProcess(self);self.proc.finished.connect(self.finished);self.proc.errorOccurred.connect(self.failed)
        self.timeout=QTimer(self);self.timeout.setSingleShot(True);self.timeout.timeout.connect(self.proc.kill);self.file=None;self.running_query=''
        self.visibilityChanged.connect(lambda on:self.stop() if not on else None)
    def failed(self,error):
        self.timeout.stop();self.status.setText('Unable to run Everything CLI.')
        if self.file:self.file.unlink(missing_ok=True);self.file=None
    def choose(self):
        p,_=QFileDialog.getOpenFileName(self,'Select official Everything CLI (es.exe)','','Everything CLI (es.exe)')
        if p and Path(p).name.lower()=='es.exe':self.host.prefs['everything_es']=p;self.host.save();self.search()
    def stop(self):
        self.timer.stop()
        if self.proc.state()!=QProcess.NotRunning:self.proc.kill()
    def search(self):
        if self.proc.state()!=QProcess.NotRunning:
            self.proc.kill();return
        self.results.clear();q=self.query.text().strip()
        if not q:return
        exe=locate(self.host.prefs)
        if not exe:self.status.setText('Bundled search component missing. Reinstall Folder or use the official ES CLI.');return
        fd,name=tempfile.mkstemp(suffix='.txt');os.close(fd);self.file=Path(name);self.running_query=q
        self.proc.setProgram(exe);self.proc.setArguments(['-timeout','1500','-n','200','-full-path-and-name','-export-txt',name,q]);self.status.setText('Searching…');self.proc.start();self.timeout.start(7000)
    def finished(self,code,status):
        self.timeout.stop();p=self.file;self.file=None
        try:
            if not self.isVisible():return
            if self.running_query!=self.query.text().strip():self.timer.start();return
            if code or status!=QProcess.NormalExit:self.status.setText('Index not ready. Select Start index. For full NTFS indexing, enable its service in Settings. ');return
            for path in p.read_text(encoding='utf-8-sig',errors='replace').splitlines()[:200] if p else []:
                if os.path.isabs(path):
                    i=QListWidgetItem(path);i.setData(Qt.UserRole,path);self.results.addItem(i)
            self.status.setText(f'{self.results.count()} displayed (maximum 200). Double-click to open.')
        finally:
            if p:p.unlink(missing_ok=True)
    def open_result(self,item):
        path=item.data(Qt.UserRole)
        if os.path.isdir(path):self.host.active().go(path)
        elif os.path.isfile(path):launch_cached(path,self.host.prefs)
    def context(self,point):
        item=self.results.itemAt(point)
        if not item:return
        from PySide6.QtWidgets import QMenu
        m=QMenu(self);m.addAction('Open',lambda:self.open_result(item));m.addAction('Open containing folder',lambda:self.host.active().go(str(Path(item.data(Qt.UserRole)).parent)));m.exec(self.results.viewport().mapToGlobal(point))
def open_search(host):
    if sys.platform != 'win32':
        from modules.linux_search import open_search as linux_open_search
        return linux_open_search(host)
    if not hasattr(host,'everything_dock'):
        host.everything_dock=SearchDock(host);host.addDockWidget(Qt.BottomDockWidgetArea,host.everything_dock)
    start(); host.everything_dock.show();host.everything_dock.query.setFocus()
