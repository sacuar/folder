import os, sys, shutil, json
from pathlib import Path
from PySide6.QtCore import Qt, QDir, QUrl
from PySide6.QtGui import QPixmap, QPainter, QDesktopServices, QAction, QKeySequence
from PySide6.QtWidgets import *
from send2trash import send2trash
from modules.thumbnails import ThumbnailModel
from modules.preview import Preview
from modules.archives import extract
from PySide6.QtCore import QSize
from addons import load_addons
from integration import register, unregister, IS_WINDOWS, STORE_BUILD

CONFIG = Path.home()/'.folder_explorer.json'
try: settings=json.loads(CONFIG.read_text())
except Exception: settings={}

class View(QTreeView):
    def paintEvent(self,event):
        super().paintEvent(event)
        path=self.window().prefs.get('folders',{}).get(self.model().filePath(self.rootIndex()), self.window().prefs.get('image',''))
        pix=QPixmap(path or '')
        if not pix.isNull():
            p=QPainter(self.viewport()); p.setOpacity(self.window().prefs.get('opacity',20)/100)
            pix=pix.scaled(self.viewport().size(),Qt.KeepAspectRatioByExpanding,Qt.SmoothTransformation)
            p.drawPixmap((self.viewport().width()-pix.width())//2,(self.viewport().height()-pix.height())//2,pix)

class Pane(QWidget):
    def __init__(self,window,path):
        super().__init__(); self.host=window; self.history=[]; self.pos=-1
        layout=QVBoxLayout(self); layout.setContentsMargins(4,4,4,4)
        bar=QHBoxLayout(); layout.addLayout(bar)
        for label,fn in [('←',lambda:self.travel(-1)),('→',lambda:self.travel(1)),('↑',lambda:self.go(str(Path(self.path).parent))),('↻',lambda:self.go(self.path,False))]:
            b=QPushButton(label); b.clicked.connect(fn); bar.addWidget(b)
        self.address=QLineEdit(); self.address.returnPressed.connect(lambda:self.go(self.address.text())); bar.addWidget(self.address,1)
        self.search=QLineEdit(); self.search.setPlaceholderText('Filter folder'); self.search.textChanged.connect(self.filter); bar.addWidget(self.search)
        self.model=ThumbnailModel(self); self.model.setRootPath(''); self.model.setFilter(QDir.AllEntries|QDir.NoDotAndDotDot)
        self.view=View(); self.view.setModel(self.model); self.view.setSelectionMode(QAbstractItemView.ExtendedSelection); self.view.setSortingEnabled(True); self.view.setColumnWidth(0,320); self.view.doubleClicked.connect(self.open); self.view.setContextMenuPolicy(Qt.CustomContextMenu); self.view.customContextMenuRequested.connect(self.menu); self.stack=QStackedWidget(); self.stack.addWidget(self.view)
        self.gallery=QListView(); self.gallery.setModel(self.model); self.gallery.setViewMode(QListView.IconMode); self.gallery.setIconSize(QSize(112,112)); self.gallery.setGridSize(QSize(150,155)); self.gallery.setResizeMode(QListView.Adjust); self.gallery.setSelectionMode(QAbstractItemView.ExtendedSelection); self.gallery.doubleClicked.connect(self.open); self.gallery.setContextMenuPolicy(Qt.CustomContextMenu); self.gallery.customContextMenuRequested.connect(self.menu); self.stack.addWidget(self.gallery); layout.addWidget(self.stack,1)
        mode=QComboBox(); mode.addItems(['Details','Thumbnails']); mode.currentIndexChanged.connect(self.stack.setCurrentIndex); bar.addWidget(mode)
        self.preview=Preview()
        layout.removeWidget(self.stack); split=QSplitter(); split.addWidget(self.stack); split.addWidget(self.preview); layout.addWidget(split,1)
        for v in (self.view,self.gallery): v.selectionModel().currentChanged.connect(self.show_preview)
        self.go(path)
    def show_preview(self,index,previous):
        self.preview.show_file(self.model.filePath(index))

    def filter(self,s): self.model.setNameFilters(['*'+s+'*'] if s else ['*']); self.model.setNameFilterDisables(False)
    def go(self,path,record=True):
        path=os.path.abspath(os.path.expanduser(path.strip().strip('"')))
        if not os.path.isdir(path): return QMessageBox.warning(self,'Folder','Folder not found.')
        self.preview.show_file(''); self.path=path; self.address.setText(path); self.view.setRootIndex(self.model.setRootPath(path)); self.gallery.setRootIndex(self.view.rootIndex()); self.search.clear()
        if record: self.history=self.history[:self.pos+1]+[path]; self.pos=len(self.history)-1
        self.host.update_title(); self.view.viewport().update()
    def travel(self,n):
        if 0<=self.pos+n<len(self.history): self.pos+=n; self.go(self.history[self.pos],False)
    def open(self,index):
        path=self.model.filePath(index)
        if os.path.isdir(path): self.go(path)
        else: QDesktopServices.openUrl(QUrl.fromLocalFile(path))
    def selected(self): return [self.model.filePath(i) for i in (self.view.selectionModel().selectedRows(0) if self.stack.currentIndex()==0 else self.gallery.selectionModel().selectedIndexes())]
    def extract_archive(self):
        files=self.selected()
        if len(files)!=1:return
        parent=QFileDialog.getExistingDirectory(self,'Extract to',self.path)
        if not parent:return
        try:extract(files[0],str(Path(parent)/Path(files[0]).stem))
        except Exception as e:QMessageBox.warning(self,'Extraction',str(e))
    def menu(self,point):
        m=QMenu(self)
        for label,fn in [('Copy',lambda:self.host.capture(False)),('Cut',lambda:self.host.capture(True)),('Paste',self.host.paste),('Rename',self.host.rename),('Move to Recycle Bin',self.host.delete),('New folder',self.host.mkdir),('Extract archive…',self.extract_archive),('Folder background',lambda:self.host.background(True))]: m.addAction(label,fn)
        m.exec(self.stack.currentWidget().viewport().mapToGlobal(point))

class Explorer(QMainWindow):
    def __init__(self):
        super().__init__(); self.prefs=settings; self.clip=[]; self.cut=False; self.resize(1150,720); self.setWindowTitle('Folder')
        root=QSplitter(); self.setCentralWidget(root); self.side=QListWidget(); nav=QWidget(); nl=QVBoxLayout(nav); nl.setContentsMargins(4,4,4,4); nl.addWidget(QLabel('QUICK ACCESS')); nl.addWidget(self.side,1); nl.addWidget(QLabel('FOLDERS')); self.tree=QTreeView(); self.tree_model=QFileSystemModel(self); self.tree_model.setFilter(QDir.Dirs|QDir.NoDotAndDotDot|QDir.Drives); self.tree_model.setRootPath(''); self.tree.setModel(self.tree_model); self.tree.setHeaderHidden(True)
        for c in range(1,4): self.tree.hideColumn(c)
        self.tree.clicked.connect(lambda i:self.active().go(self.tree_model.filePath(i)) if self.tree_model.filePath(i) else None); nl.addWidget(self.tree,3); root.addWidget(nav); nav.setMinimumWidth(160)
        for name,path in [('Home',Path.home()),('Desktop',Path.home()/'Desktop'),('Downloads',Path.home()/'Downloads'),('Documents',Path.home()/'Documents'),('Pictures',Path.home()/'Pictures')]+[(d.absolutePath(),d.absolutePath()) for d in QDir.drives()]:
            item=QListWidgetItem(name); item.setData(Qt.UserRole,str(path)); self.side.addItem(item)
        self.side.itemClicked.connect(lambda i:self.active().go(i.data(Qt.UserRole)))
        self.tabs=QTabWidget(); self.tabs.setTabsClosable(True); self.tabs.setMovable(True); self.tabs.tabCloseRequested.connect(self.close_tab); root.addWidget(self.tabs); root.setSizes([190,960]); self.tabs.currentChanged.connect(lambda _:self.update_title())
        toolbar=self.addToolBar('Commands'); toolbar.setMovable(False)
        for name,shortcut,fn in [('New tab','Ctrl+T',self.new_tab),('Split','Ctrl+Shift+D',self.split),('New folder','Ctrl+Shift+N',self.mkdir),('Copy','Ctrl+C',lambda:self.capture(False)),('Cut','Ctrl+X',lambda:self.capture(True)),('Paste','Ctrl+V',self.paste),('Rename','F2',self.rename),('Recycle','Delete',self.delete),('Appearance',None,self.appearance)]:
            a=QAction(name,self); a.triggered.connect(fn); toolbar.addAction(a)
            if shortcut: a.setShortcut(QKeySequence(shortcut))
        self.new_tab(); self.apply_theme()
        menu=self.menuBar().addMenu('Desktop integration'); menu.addAction('Register Open in Folder' if IS_WINDOWS else 'Register desktop launcher',lambda:self.registry(True)).setEnabled(not STORE_BUILD); menu.addAction('Remove registration',lambda:self.registry(False)).setEnabled(not STORE_BUILD); self.addon_menu=self.menuBar().addMenu('Add-ons'); self.addon_menu.addAction('Load trusted add-ons…',lambda:load_addons(self)); self.addon_menu.addAction('Open add-on folder',self.addon_folder)
    def addon_folder(self):
        from addons import ADDON_DIR
        ADDON_DIR.mkdir(parents=True,exist_ok=True); QDesktopServices.openUrl(QUrl.fromLocalFile(str(ADDON_DIR)))
    def registry(self,enable):
        try:
            (register if enable else unregister)(); QMessageBox.information(self,'Desktop integration','Registration updated. Your default file manager is unchanged.')
        except Exception as e: QMessageBox.warning(self,'Windows integration',str(e))
    def active(self):
        tab=self.tabs.currentWidget(); panes=tab.findChildren(Pane) if tab else []
        focus=QApplication.focusWidget()
        return next((p for p in panes if focus and (focus==p or p.isAncestorOf(focus))),panes[0] if panes else None)
    def update_title(self):
        p=self.active()
        if p and hasattr(p,'path'): self.tabs.setTabText(self.tabs.currentIndex(),Path(p.path).name or p.path)
    def new_tab(self):
        p=self.active(); path=p.path if p else (sys.argv[1] if self.tabs.count()==0 and len(sys.argv)>1 and os.path.isdir(sys.argv[1]) else str(Path.home())); tab=QSplitter(); tab.addWidget(Pane(self,path)); self.tabs.addTab(tab,Path(path).name); self.tabs.setCurrentWidget(tab)
    def close_tab(self,i):
        if self.tabs.count()>1: w=self.tabs.widget(i); self.tabs.removeTab(i); w.deleteLater()
    def split(self):
        t=self.tabs.currentWidget()
        if t.count()==1: t.addWidget(Pane(self,self.active().path))
        else: t.widget(1).setParent(None)
    def capture(self,cut): self.clip=self.active().selected(); self.cut=cut
    def paste(self):
        for src in self.clip[:]:
            dst=os.path.join(self.active().path,os.path.basename(src))
            if os.path.exists(dst): QMessageBox.warning(self,'Conflict',f'Skipped existing item: {dst}'); continue
            try:
                if self.cut: shutil.move(src,dst); self.clip.remove(src)
                elif os.path.isdir(src): shutil.copytree(src,dst)
                else: shutil.copy2(src,dst)
            except Exception as e: QMessageBox.warning(self,'Error',str(e))
    def name(self,title,default=''):
        s,ok=QInputDialog.getText(self,title,'Name:',text=default)
        return s if ok and s and s not in ('.','..') and not any(c in s for c in '/\\:') else None
    def mkdir(self):
        s=self.name('New folder')
        if s:
            try: os.mkdir(os.path.join(self.active().path,s))
            except Exception as e: QMessageBox.warning(self,'Error',str(e))
    def rename(self):
        files=self.active().selected()
        if len(files)!=1:return
        s=self.name('Rename',os.path.basename(files[0]))
        if s:
            try: os.rename(files[0],os.path.join(os.path.dirname(files[0]),s))
            except Exception as e: QMessageBox.warning(self,'Error',str(e))
    def delete(self):
        files=self.active().selected()
        if files and QMessageBox.question(self,'Recycle Bin',f'Move {len(files)} item(s) to Recycle Bin?')==QMessageBox.Yes:
            for f in files:
                try: send2trash(f)
                except Exception as e: QMessageBox.warning(self,'Error',str(e))
    def save(self): CONFIG.write_text(json.dumps(self.prefs,indent=2)); self.apply_theme(); [v.viewport().update() for v in self.findChildren(View)]
    def background(self,folder=False):
        path,_=QFileDialog.getOpenFileName(self,'Background image','','Images (*.png *.jpg *.jpeg *.bmp *.webp)')
        if path:
            if folder:self.prefs.setdefault('folders',{})[self.active().path]=path
            else:self.prefs['image']=path
            self.save()
    def appearance(self):
        d=QDialog(self); d.setWindowTitle('Appearance'); l=QVBoxLayout(d); theme=QComboBox(); theme.addItems(['Dark','Light']); theme.setCurrentText(self.prefs.get('theme','Dark')); l.addWidget(theme); theme.currentTextChanged.connect(lambda s:(self.prefs.update(theme=s),self.save())); l.addWidget(QLabel('Background opacity')); slider=QSlider(Qt.Horizontal); slider.setRange(0,70); slider.setValue(self.prefs.get('opacity',20)); slider.valueChanged.connect(lambda n:(self.prefs.update(opacity=n),self.save())); l.addWidget(slider)
        for name,fn in [('Choose global image',lambda:self.background()),('Choose folder image',lambda:self.background(True)),('Clear global image',lambda:(self.prefs.pop('image',None),self.save())),('Clear folder image',lambda:(self.prefs.get('folders',{}).pop(self.active().path,None),self.save()))]:
            b=QPushButton(name); b.clicked.connect(fn); l.addWidget(b)
        d.exec()
    def apply_theme(self):
        accent='#356ca5' if IS_WINDOWS else '#a83e17'; dark=self.prefs.get('theme','Dark')=='Dark'; bg,fg,panel,edge=('#171b20','#e8edf3','#222831','#3b4654') if dark else ('#f5f7fa','#17212e','#ffffff','#ccd4df'); self.setStyleSheet(f'QWidget {{background:{bg};color:{fg};font-size:13px;}} QTreeView,QListView,QListWidget,QLineEdit,QMenu {{background:{panel};border:1px solid {edge};}} QPushButton,QToolButton,QTabBar::tab {{padding:8px;border:1px solid {edge};border-radius:5px;}} QHeaderView::section {{background:{panel};color:{fg};padding:7px;}} QTreeView::item {{height:29px;}} QTreeView::item:selected,QListView::item:selected,QListWidget::item:selected,QTabBar::tab:selected {{background:{accent};color:white;}}')

if __name__=='__main__':
    app=QApplication(sys.argv); app.setStyle('Fusion'); w=Explorer(); w.show(); sys.exit(app.exec())
