BASE = "https://raw.githubusercontent.com/sacuar/folder/b7af0f4ac2aa6a8894364d152d1c7a9b6276f770/optional_plugins/"
ROOT = ".folder_explorer/github_plugins"
CATALOG = {"three_mf":["3MF thumbnails and preview","52e4cc8220b6e1b5ab1b43ef4414db8ff12eaf7d"],"drive_tools":["Drive and storage tools","8eeafdddfde55b515eecc58d61744a6309edbbdd"],"image_tools":["Image conversion and resize","6fe24803c2cded416b34676fc57e2b47d9305de2"],"document_tools":["Office document conversion (LibreOffice required)","e8f22de913ba90893a55fc1b4abdfe33d4c1c412"],"media_tools":["Video conversion, trim and audio extraction","12f39d13d95770df4290e68951d9cbc15611d4a2"]}
"""Explicit opt-in plugin installs from an immutable GitHub revision."""
import hashlib,importlib.util,os,json,base64,urllib.request,urllib.error,ssl
from pathlib import Path
from PySide6.QtCore import QObject,Signal,QRunnable,QThreadPool,Qt
from PySide6.QtWidgets import QDialog,QVBoxLayout,QLabel,QListWidget,QListWidgetItem,QPushButton,QMessageBox,QFileDialog
PREVIEWS={};THUMBS={}
class API:
    def __init__(self,host,menu):self.host=host;self.menu=menu
    def action(self,label,fn):self.menu.addAction(label,lambda:fn(self.host))
    def preview(self,ext,widget,thumb):PREVIEWS[ext]=widget;THUMBS[ext]=thumb
MAX_BYTES=200000
def verify(key,data):
    return 0<len(data)<=MAX_BYTES and hashlib.sha1(('blob '+str(len(data))+'\0').encode()+data).hexdigest()==CATALOG[key][1]
def download_plugin(key):
    from urllib.parse import urlsplit
    ref=BASE.split('/')[5]
    sources=[(BASE+key+'.py',False),
             ('https://api.github.com/repos/sacuar/folder/contents/optional_plugins/'+key+'.py?ref='+ref,True)]
    errors=[]
    for url,encoded in sources:
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Folder-plugin-installer','Accept':'application/vnd.github+json' if encoded else 'application/octet-stream'})
            with urllib.request.urlopen(req,timeout=15) as response:
                final=urlsplit(response.geturl())
                if final.scheme!='https' or final.hostname not in ('raw.githubusercontent.com','api.github.com'):raise ValueError('Unexpected download destination')
                raw=response.read(MAX_BYTES*2+1)
            if encoded:
                if len(raw)>MAX_BYTES*2:raise ValueError('API reply too large')
                payload=json.loads(raw)
                if payload.get('encoding')!='base64' or payload.get('sha')!=CATALOG[key][1]:raise ValueError('GitHub API content identity mismatch')
                data=base64.b64decode(''.join(payload['content'].split()),validate=True)
            else:data=raw
            if not verify(key,data):raise ValueError('Downloaded file checksum differs from the verified catalogue')
            return data
        except Exception as exc:errors.append(('GitHub API' if encoded else 'Raw GitHub')+': '+str(exc))
    raise RuntimeError('\n'.join(errors))
class DownloadSignals(QObject):
    done=Signal(str,object);failed=Signal(str)
class Download(QRunnable):
    def __init__(self,key):
        super().__init__();self.key=key;self.signals=DownloadSignals()
    def run(self):
        try:self.signals.done.emit(self.key,download_plugin(self.key))
        except Exception as e:self.signals.failed.emit(str(e))
class Manager(QObject):
    def __init__(self,host):
        super().__init__(host);self.host=host;self.root=Path.home()/ROOT;self.job=None
        self.menu=host.menuBar().addMenu('Plugins');self.menu.addAction('Install available plugins…',self.show_catalog)
        self.menu.addAction('Manage installed plugins…',self.show_catalog);self.menu.addSeparator()
        self.actions=self.menu.addMenu('Installed tools');self.load()
    def valid(self,key,data):
        return verify(key,data)
    def load(self):
        for key in CATALOG:
            p=self.root/(key+'.py')
            if not p.is_file():continue
            try:
                data=p.read_bytes()
                if not self.valid(key,data):
                    self.host.statusBar().showMessage('Plugin '+key+' failed integrity verification. Reinstall it.',10000);continue
                spec=importlib.util.spec_from_file_location('optional_'+key,p);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);mod.register(API(self.host,self.actions))
            except Exception as e:self.host.statusBar().showMessage('Plugin '+key+': '+str(e),10000)
    def show_catalog(self):
        if getattr(self,'dialog',None) is not None and self.dialog.isVisible():self.dialog.raise_();return
        d=QDialog(self.host);self.dialog=d;d.setWindowTitle('Available plugins');d.resize(650,420);l=QVBoxLayout(d)
        l.addWidget(QLabel('Optional GitHub plugins. Install only what you need. Restart after changes.'))
        self.list=QListWidget();l.addWidget(self.list)
        self.refresh()
        for label,fn in [('Install selected',self.install),('Install from downloaded file…',self.manual),('Uninstall selected',self.remove),('Close',d.close)]:
            b=QPushButton(label);b.clicked.connect(fn);l.addWidget(b)
        d.show()
    def refresh(self):
        self.list.clear()
        for key,(label,sha) in CATALOG.items():
            p=self.root/(key+'.py');installed=p.is_file() and p.stat().st_size<=MAX_BYTES and self.valid(key,p.read_bytes())
            item=QListWidgetItem(label+' — '+('Installed' if installed else 'Needs reinstall' if p.is_file() else 'Available'));item.setData(256,key);self.list.addItem(item)
    def key(self):
        item=self.list.currentItem();return item.data(256) if item else None
    def install(self):
        key=self.key()
        if not key or self.job:return
        if QMessageBox.question(self.dialog,'Install plugin','Download this verified GitHub plugin? It runs with your permissions after restart.')!=QMessageBox.Yes:return
        self.job=Download(key);self.job.signals.done.connect(self.downloaded);self.job.signals.failed.connect(self.failed)
        self.dialog.setWindowTitle('Downloading '+CATALOG[key][0]+'…')
        QThreadPool.globalInstance().start(self.job)
    def store(self,key,data):
        if not self.valid(key,data):raise ValueError('Plugin file does not match the verified GitHub checksum.')
        self.root.mkdir(parents=True,exist_ok=True);p=self.root/(key+'.py');tmp=p.with_suffix('.tmp')
        tmp.write_bytes(data);os.replace(tmp,p)
        self.refresh();QMessageBox.information(self.host,'Plugins','Installed. Restart Folder to activate.')
    def downloaded(self,key,data):
        self.job=None;self.dialog.setWindowTitle('Available plugins')
        try:self.store(key,data)
        except Exception as e:QMessageBox.warning(self.host,'Plugin installation',str(e))
    def failed(self,error):
        self.job=None;self.dialog.setWindowTitle('Available plugins')
        QMessageBox.warning(self.host,'Plugin download failed',error+'\n\nYou may download the pinned file in your browser and use Install from downloaded file.')
    def manual(self):
        if self.job:return
        key=self.key()
        if not key:return
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        result=QMessageBox.question(self.host,'Manual plugin installation','Open the verified source download in your browser first?',QMessageBox.Yes|QMessageBox.No|QMessageBox.Cancel)
        if result==QMessageBox.Cancel:return
        if result==QMessageBox.Yes:QDesktopServices.openUrl(QUrl(BASE+key+'.py'))
        p,_=QFileDialog.getOpenFileName(self.dialog,'Choose downloaded '+key+'.py','','Python plugin (*.py)')
        if not p:return
        try:
            if Path(p).stat().st_size>MAX_BYTES:raise ValueError('Plugin file too large')
            if QMessageBox.question(self.host,'Trust plugin','Install this checksum-verified plugin? It executes code after restart.')!=QMessageBox.Yes:return
            self.store(key,Path(p).read_bytes())
        except Exception as e:QMessageBox.warning(self.host,'Plugin installation',str(e))
    def remove(self):
        key=self.key()
        if not key:return
        if QMessageBox.question(self.dialog,'Uninstall plugin','Remove the selected plugin? Restart to deactivate.')!=QMessageBox.Yes:return
        try:(self.root/(key+'.py')).unlink(missing_ok=True);self.refresh()
        except OSError as e:QMessageBox.warning(self.host,'Plugins',str(e))
