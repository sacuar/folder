import os, sys, shutil, json
from pathlib import Path
from PySide6.QtCore import Qt, QDir, QUrl, QFileInfo, QTimer
from PySide6.QtGui import QPixmap, QPainter, QDesktopServices, QAction, QKeySequence
from PySide6.QtWidgets import *
from send2trash import send2trash
from modules.thumbnails import ThumbnailModel
from modules.preview import Preview
from modules.archives import extract
from modules.updates import Updater
from version import VERSION
from modules.workspace import apply_workspace_theme, configure_gallery, populate_places, configure_commands
from PySide6.QtCore import QSize
from addons import load_addons, manage_addons
from modules.icons import icon, FileIcons
from modules.photo_viewer import open_file
from modules.folder_options import options, CONTEXT
from modules.create_items import add_new_menu, create_item, TYPES, DEFAULT_TYPES
from modules.toolbar_layout import apply_layout
from modules.open_with import launch_cached, choose_app
from modules.web_links import populate_links, open_link, search_web
from modules.drives import sidebar_menu
from modules.favicons import Favicons
from modules.sidebar import populate, context, update_icon, clip_folder, clip_label, add_bookmark, manage_services
from modules.everything_search import open_search
from modules.maintenance import add_tools
from modules.web_popup import show_web
from modules.desktop_tools import properties,run_admin
from modules.scratchpad import toggle as toggle_scribble
from integration import register, unregister, IS_WINDOWS, STORE_BUILD

CONFIG = Path.home()/'.folder_explorer.json'
try: settings=json.loads(CONFIG.read_text())
except Exception: settings={}

class View(QTreeView):
    pass

class Pane(QWidget):
    def __init__(self,window,path):
        super().__init__(); self.host=window; self.history=[]; self.pos=-1
        layout=QVBoxLayout(self); layout.setContentsMargins(4,4,4,4)
        bar=QHBoxLayout(); bar.setSpacing(6); layout.addLayout(bar)
        for label,fn in [('←',lambda:self.travel(-1)),('→',lambda:self.travel(1)),('↑',lambda:self.go(str(Path(self.path).parent))),('↻',lambda:self.go(self.path,False))]:
            b=QToolButton(); b.setIcon(icon({'←':'back','→':'forward','↑':'up','↻':'refresh'}[label])); b.setToolTip({'←':'Back','→':'Forward','↑':'Up','↻':'Refresh'}[label]); b.setIconSize(QSize(18,18)); b.clicked.connect(fn); bar.addWidget(b)
        self.address=QLineEdit(); self.address.setClearButtonEnabled(True); self.address.returnPressed.connect(lambda:self.go(self.address.text())); bar.addWidget(self.address,1)
        self.search=QLineEdit(); self.search.setPlaceholderText('Search this folder'); self.search.setClearButtonEnabled(True); self.search.setMaximumWidth(210); self.search.textChanged.connect(self.filter); bar.addWidget(self.search)
        self.model=ThumbnailModel(self); self.model.prefs=window.prefs; self.model.setRootPath(''); self.model.setFilter(QDir.AllEntries|QDir.NoDotAndDotDot)
        self.view=View(); self.view.setModel(self.model); self.view.setIconSize(QSize(18,18)); self.view.setSelectionMode(QAbstractItemView.ExtendedSelection); self.view.setSortingEnabled(True); self.view.setUniformRowHeights(True); self.view.setColumnWidth(0,320); self.view.doubleClicked.connect(self.open); self.view.setContextMenuPolicy(Qt.CustomContextMenu); self.view.customContextMenuRequested.connect(self.menu); self.stack=QStackedWidget(); self.stack.addWidget(self.view)
        self.gallery=QListView(); configure_gallery(self.gallery); self.gallery.setModel(self.model); self.gallery.setViewMode(QListView.IconMode); self.gallery.setIconSize(QSize(112,112)); self.gallery.setGridSize(QSize(150,155)); self.gallery.setWordWrap(True); self.gallery.setResizeMode(QListView.Adjust); self.gallery.setSelectionMode(QAbstractItemView.ExtendedSelection); self.gallery.doubleClicked.connect(self.open); self.gallery.setContextMenuPolicy(Qt.CustomContextMenu); self.gallery.customContextMenuRequested.connect(self.menu); self.stack.addWidget(self.gallery); layout.addWidget(self.stack,1)
        mode=QComboBox();
        for label,key in [('Medium thumbnails','grid'),('Details / no thumbnails','details'),('Large thumbnails','large'),('Small thumbnails','small'),('List','details')]:mode.addItem(icon(key),label)
        mode.setToolTip('View size'); mode.setMinimumWidth(44); mode.setMaximumWidth(48 if not window.prefs.get('toolbar_labels',False) else 205); mode.setCurrentIndex(window.prefs.get('view_mode',0) if window.prefs.get('view_mode',0) in range(5) else 0); self.mode=mode; mode.currentIndexChanged.connect(self.change_mode); bar.addWidget(mode)
        self.preview_toggle=QToolButton(); self.preview_toggle.setText('Preview'); self.preview_toggle.setIcon(icon('split')); self.preview_toggle.setToolTip('Toggle preview pane'); self.preview_toggle.setToolButtonStyle(Qt.ToolButtonTextBesideIcon if window.prefs.get('toolbar_labels',False) else Qt.ToolButtonIconOnly); self.preview_toggle.setCheckable(True); self.preview_toggle.setChecked(window.prefs.get('preview_visible',True)); bar.addWidget(self.preview_toggle)
        self.pad_button=QToolButton();self.pad_button.setText('✎');self.pad_button.setToolTip('Temporary Scribble notes');self.pad_button.clicked.connect(lambda:toggle_scribble(self.host));self.pad_button.setVisible(window.prefs.get('show_scribble',False));bar.addWidget(self.pad_button)
        self.clip_button=QToolButton();self.clip_button.setIcon(icon('paperclip'));self.clip_button.setToolTip('Clip / Unclip this folder');self.clip_button.clicked.connect(lambda:clip_folder(self.host,self.path));bar.addWidget(self.clip_button)
        self.preview=Preview(); self.preview.prefs=window.prefs; self.preview_timer=QTimer(self); self.preview_timer.setSingleShot(True); self.preview_timer.setInterval(160); self.preview_timer.timeout.connect(self.load_preview); self.preview_toggle.toggled.connect(self.toggle_preview)
        layout.removeWidget(self.stack); split=QSplitter(); split.addWidget(self.stack); split.addWidget(self.preview); layout.addWidget(split,1); split.setStretchFactor(0,5); split.setStretchFactor(1,1); split.setSizes([900,250]); self.splitter=split
        self.preview.setVisible(self.preview_toggle.isChecked()); self.change_mode(mode.currentIndex(),persist=False)
        self.model.directoryLoaded.connect(lambda _:self.status())
        for v in (self.view,self.gallery):
            v.selectionModel().currentChanged.connect(self.show_preview)
            v.selectionModel().selectionChanged.connect(lambda *_:self.status())
        self.apply_options(); self.go(path)
    def apply_options(self):
        prefs=self.host.prefs
        self.pad_button.setVisible(prefs.get('show_scribble',False))
        self.mode.setMaximumWidth(205 if prefs.get('toolbar_labels',False) else 48); self.preview_toggle.setToolButtonStyle(Qt.ToolButtonTextBesideIcon if prefs.get('toolbar_labels',False) else Qt.ToolButtonIconOnly)
        self.model.setFilter(QDir.AllEntries|QDir.NoDotAndDotDot|(QDir.Hidden if prefs.get('show_hidden',False) else QDir.NoFilter))
        self.model.cache.clear(); self.gallery.viewport().update(); self.view.viewport().update()
        for v in (self.view,self.gallery):
            for signal in (v.clicked,v.doubleClicked):
                try:signal.disconnect(self.open)
                except (RuntimeError,TypeError):pass
            (v.clicked if prefs.get('single_click',False) else v.doubleClicked).connect(self.open)
    def change_mode(self,n,persist=True):
        self.stack.setCurrentIndex(0 if n==1 else 1); self.model.prefs=self.host.prefs; self.model.generate=(n not in (1,4))
        size={0:56,2:104,3:32}.get(n,56)
        self.gallery.setViewMode(QListView.ListMode if n==4 else QListView.IconMode); self.gallery.setIconSize(QSize(20,20) if n==4 else QSize(size,size)); self.gallery.setGridSize(QSize() if n==4 else QSize(size+40,size+34))
        if persist:
            self.host.prefs['view_mode']=n; self.host.save()
        self.status()

    def toggle_preview(self,enabled):
        self.preview.setVisible(enabled); self.host.prefs['preview_visible']=enabled; self.host.save()
        if enabled: self.show_preview(self.stack.currentWidget().currentIndex(),None)
        else: self.preview_timer.stop(); self.preview.show_file('')

    def status(self):
        if not hasattr(self,'path') or self.host.active() is not self:return
        count=self.model.rowCount(self.view.rootIndex()); selected=len(self.selected())
        self.host.statusBar().showMessage(f'{count} items     •     {selected} selected     •     {self.path}')

    def show_preview(self,index,previous):
        if self.preview_toggle.isChecked() and self.stack.currentWidget().currentIndex()==index:
            self.preview_timer.start()
        self.status()
    def load_preview(self):
        if not self.preview_toggle.isChecked():return
        index=self.stack.currentWidget().currentIndex()
        self.preview.show_file(self.model.filePath(index) if index.isValid() else '')

    def filter(self,s): self.model.setNameFilters(['*'+s+'*'] if s else ['*']); self.model.setNameFilterDisables(False)
    def go(self,path,record=True):
        path=os.path.abspath(os.path.expanduser(path.strip().strip('"')))
        if not os.path.isdir(path): return QMessageBox.warning(self,'Folder','Folder not found.')
        self.preview_timer.stop(); self.preview.show_file(''); self.path=path; self.address.setText(path); self.view.setRootIndex(self.model.setRootPath(path)); self.gallery.setRootIndex(self.view.rootIndex()); self.search.clear()
        if record: self.history=self.history[:self.pos+1]+[path]; self.pos=len(self.history)-1
        self.host.update_title(); self.view.viewport().update(); self.status()
    def travel(self,n):
        if 0<=self.pos+n<len(self.history): self.pos+=n; self.go(self.history[self.pos],False)
    def open(self,index):
        path=self.model.filePath(index)
        if os.path.isdir(path): self.go(path)
        else: launch_cached(path,self.host.prefs); self.host.save()
    def selected(self): return [self.model.filePath(i) for i in (self.view.selectionModel().selectedRows(0) if self.stack.currentIndex()==0 else self.gallery.selectionModel().selectedIndexes())]
    def extract_archive(self):
        files=self.selected()
        if len(files)!=1:return
        parent=QFileDialog.getExistingDirectory(self,'Extract to',self.path)
        if not parent:return
        try:extract(files[0],str(Path(parent)/Path(files[0]).stem))
        except Exception as e:QMessageBox.warning(self,'Extraction',str(e))
    def menu(self,point):
        v=self.stack.currentWidget(); index=v.indexAt(point)
        if index.isValid() and not v.selectionModel().isSelected(index):
            v.setCurrentIndex(index)
        v.setFocus(); m=QMenu(self)
        enabled=self.host.prefs.get('context_items',CONTEXT)
        for label,fn in [('Copy',lambda:self.host.capture(False)),('Cut',lambda:self.host.capture(True)),('Paste',self.host.paste),('Rename',self.host.rename),('Move to Recycle Bin',self.host.delete),('Extract archive…',self.extract_archive)]:
            if label in enabled:m.addAction(label,fn)
        if 'New' in enabled:add_new_menu(m,self)
        if index.isValid() and self.model.isDir(index):
            selected=self.model.filePath(index); m.addAction(icon('paperclip'),clip_label(self.host,selected),lambda:clip_folder(self.host,selected))
        elif not index.isValid():m.addAction(icon('paperclip'),clip_label(self.host,self.path),lambda:clip_folder(self.host,self.path))
        if index.isValid() and not self.model.isDir(index):
            path=self.model.filePath(index)
            if 'Open with' in enabled:m.addAction('Open with…',lambda:choose_app(self,path,self.host.prefs))
            if 'Play with' in enabled:m.addAction('Play with…',lambda:choose_app(self,path,self.host.prefs,True))
        sort=m.addMenu('Sort by')
        for title,col in [('Name',0),('Size',1),('Type',2),('Date modified',3)]:
            for direction,order in [('Ascending',Qt.AscendingOrder),('Descending',Qt.DescendingOrder)]:sort.addAction(title+' — '+direction,lambda checked=False,c=col,o=order:self.model.sort(c,o))
        if index.isValid():
            path=self.model.filePath(index);m.addAction('Properties…',lambda:properties(self,path))
            if self.host.prefs.get('advanced_commands',False) and IS_WINDOWS and Path(path).suffix.lower()=='.exe':m.addAction('Run as administrator…',lambda:run_admin(self,path))
        m.exec(self.stack.currentWidget().viewport().mapToGlobal(point))

class Explorer(QMainWindow):
    def __init__(self):
        super().__init__(); self.prefs=settings; self.clip=[]; self.cut=False; self.resize(1400,850); self.setMinimumSize(760,480); self.setWindowTitle('Folder'); self.setWindowIcon(icon('app')); self.last_pane=None
        root=QSplitter(); self.setCentralWidget(root); self.side=QListWidget(); nav=QWidget(); nl=QVBoxLayout(nav); nl.setContentsMargins(4,4,4,4); nl.setSpacing(8); self.places_toggle=QToolButton(); self.places_toggle.setText('Places / drives / shortcuts'); self.places_toggle.setCheckable(True);self.places_toggle.setChecked(True);nl.addWidget(self.places_toggle); self.nav_split=QSplitter(Qt.Vertical);nl.addWidget(self.nav_split,1);self.nav_split.addWidget(self.side);self.tree_toggle=QToolButton();self.tree_toggle.setText('Folder tree');self.tree_toggle.setCheckable(True);self.tree_toggle.setChecked(True);nl.addWidget(self.tree_toggle); self.tree=QTreeView(); self.tree_model=QFileSystemModel(self); self.tree_icons=FileIcons(); self.tree_model.setIconProvider(self.tree_icons); self.tree_model.setFilter(QDir.Dirs|QDir.NoDotAndDotDot|QDir.Drives); self.tree_model.setRootPath(''); self.tree.setModel(self.tree_model); self.tree.setHeaderHidden(True); self.tree.setAnimated(False); self.tree.setUniformRowHeights(True); self.tree.setIndentation(14); self.tree.setIconSize(QSize(16,16)); self.tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        for c in range(1,4): self.tree.hideColumn(c)
        self.tree.clicked.connect(lambda i:self.active().go(self.tree_model.filePath(i)) if self.tree_model.filePath(i) else None); self.tree.setContextMenuPolicy(Qt.CustomContextMenu); self.tree.customContextMenuRequested.connect(self.tree_menu); self.nav_split.addWidget(self.tree);self.nav_split.setSizes([300,400]);self.places_toggle.toggled.connect(self.side.setVisible);self.tree_toggle.toggled.connect(self.tree.setVisible);root.addWidget(nav); self.nav=nav; nav.setMinimumWidth(110);self.root_split=root
        self.favicons=Favicons(self); self.favicons.ready.connect(lambda origin,ic:update_icon(self,origin,ic)); self.refresh_sidebar()
        self.side.itemClicked.connect(self.open_place); self.side.setContextMenuPolicy(Qt.CustomContextMenu); self.side.customContextMenuRequested.connect(lambda point:context(self,point))
        self.tabs=QTabWidget(); self.tabs.setTabsClosable(True); self.tabs.setMovable(True); self.tabs.tabCloseRequested.connect(self.close_tab); root.addWidget(self.tabs); root.setSizes([190,1210]); root.setStretchFactor(0,0); root.setStretchFactor(1,1); self.tabs.currentChanged.connect(lambda _:self.update_title())
        toolbar=self.addToolBar('Commands'); self.commands=toolbar; toolbar.setMovable(False); toolbar.setObjectName('FolderCommands')
        self.command_actions={}
        for key,name,shortcut,fn in [('new_tab','New tab','Ctrl+T',self.new_tab),('split','Split','Ctrl+Shift+D',self.split),('new_folder','New folder','Ctrl+Shift+N',self.mkdir),('copy','Copy','Ctrl+C',lambda:self.capture(False)),('cut','Cut','Ctrl+X',lambda:self.capture(True)),('paste','Paste','Ctrl+V',self.paste),('rename','Rename','F2',self.rename),('recycle','Recycle','Delete',self.delete),('appearance','Appearance',None,self.appearance),('addons','Add-ons',None,lambda:manage_addons(self)),('options','Folder options',None,lambda:options(self)),('everything','Everything search','Ctrl+Shift+F',lambda:open_search(self)),('web','Web search',None,lambda:show_web(self))]:
            action=QAction(name,self); action.triggered.connect(fn); self.command_actions[key]=action
            if shortcut: action.setShortcut(QKeySequence(shortcut)); self.addAction(action)
        self.everything_action=self.command_actions['everything'];self.web_search=self.command_actions['web']
        new_file=QAction(icon('document'),'New file',self);new_file.setToolTip('Create a file in the active folder')
        file_menu=QMenu(self);new_file.setMenu(file_menu);file_menu.aboutToShow.connect(lambda:self.populate_new_files(file_menu));self.command_actions['new_file']=new_file
        self.tab_plus=QToolButton(self.tabs);self.tab_plus.setIcon(icon('plus'));self.tab_plus.setToolTip('New tab (Ctrl+T)');self.tab_plus.setAccessibleName('New tab');self.tab_plus.clicked.connect(self.new_tab)
        self.tabs.setCornerWidget(self.tab_plus,Qt.TopRightCorner)
        spacer=QWidget(toolbar);spacer.setMinimumWidth(0);spacer.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Preferred)
        space_action=QWidgetAction(self);space_action.setDefaultWidget(spacer);self.command_actions['space']=space_action
        toolbar.setContextMenuPolicy(Qt.CustomContextMenu);toolbar.customContextMenuRequested.connect(self.toolbar_menu)
        self.statusBar().setSizeGripEnabled(False)
        QApplication.instance().focusChanged.connect(self.remember_focus)
        self.new_tab(); self.apply_theme(); self.update_title()
        menu=self.menuBar().addMenu('Desktop integration'); menu.addAction('Register Open in Folder' if IS_WINDOWS else 'Register desktop launcher',lambda:self.registry(True)).setEnabled(not STORE_BUILD); menu.addAction('Remove registration',lambda:self.registry(False)).setEnabled(not STORE_BUILD); self.addon_menu=self.menuBar().addMenu('Add-ons'); self.addon_menu.addAction('Manage plugins…',lambda:manage_addons(self)); self.addon_menu.addAction('Load trusted add-ons…',lambda:load_addons(self)); self.addon_menu.addAction('Open add-on folder',self.addon_folder)
        self.updater=Updater(self,enabled=IS_WINDOWS and not STORE_BUILD); add_tools(self)
        view_menu=self.menuBar().addMenu('View');view_menu.addAction('Toggle sidebar',self.toggle_sidebar);view_menu.addAction('Scribble (temporary notes)',lambda:toggle_scribble(self));view_menu.addAction('Customise toolbar…',lambda:options(self,'Toolbar'));view_menu.addAction('Folder options…',lambda:options(self))
        from modules.plugin_catalog import Manager
        self.plugin_manager=Manager(self)
        menu_popup=QMenu(self)
        for action in self.menuBar().actions():
            if action.menu():menu_popup.addMenu(action.menu())
        menus=QAction(icon('more'),'Application menus',self);menus.setToolTip('Application menus');menus.setMenu(menu_popup);self.command_actions['menus']=menus
        self.apply_options()

    def toggle_sidebar(self):
        self.prefs['show_sidebar']=not self.nav.isVisible();self.nav.setVisible(self.prefs['show_sidebar']);self.save()
    def populate_new_files(self,menu):
        menu.clear()
        for key,label in TYPES.items():
            if key!='folder' and key in self.prefs.get('new_types',DEFAULT_TYPES):
                menu.addAction(label,lambda checked=False,k=key:self.create_new(k))
        if not menu.actions():menu.addAction('Enable file types in Folder Options').setEnabled(False)
    def create_new(self,kind):
        pane=self.active()
        if pane:create_item(pane,pane.path,kind)
    def toolbar_menu(self,point):
        menu=QMenu(self);menu.addAction('Customise toolbar…',lambda:options(self,'Toolbar'));menu.addAction('Folder options…',lambda:options(self));menu.exec(self.commands.mapToGlobal(point))

    def tree_menu(self,point):
        index=self.tree.indexAt(point)
        if not index.isValid():return
        path=self.tree_model.filePath(index);m=QMenu(self);m.addAction(icon('unclip' if clip_label(self,path).startswith('Unclip') else 'paperclip'),clip_label(self,path),lambda:clip_folder(self,path));m.addAction('Open',lambda:self.active().go(path));m.exec(self.tree.viewport().mapToGlobal(point))
    def open_place(self,item):
        value=item.data(Qt.UserRole)
        if not isinstance(value,str):return
        if value.startswith(('https://','http://')):open_link(value)
        else:self.active().go(value)
    def choose_search(self):
        provider,ok=QInputDialog.getItem(self,'Web search','Search with:',['Google','ChatGPT','DeepSeek'],0,False)
        if ok:search_web(self,provider)
    def apply_options(self):
        self.apply_theme(); self.menuBar().setVisible(self.prefs.get('show_menu_bar',False)); apply_layout(self); configure_commands(self.commands,self.prefs.get('toolbar_labels',False)); self.nav.setVisible(self.prefs.get('show_sidebar',True))
        self.refresh_sidebar()
        for pane in self.findChildren(Pane):pane.apply_options()
    def refresh_sidebar(self):
        self.side.clear(); populate_places(self.side); populate(self)
    def addon_folder(self):
        from addons import ADDON_DIR
        ADDON_DIR.mkdir(parents=True,exist_ok=True); QDesktopServices.openUrl(QUrl.fromLocalFile(str(ADDON_DIR)))
    def registry(self,enable):
        try:
            (register if enable else unregister)(); QMessageBox.information(self,'Desktop integration','Registration updated. Your default file manager is unchanged.')
        except Exception as e: QMessageBox.warning(self,'Windows integration',str(e))
    def remember_focus(self,old,new):
        if not new:return
        for p in self.tabs.currentWidget().findChildren(Pane) if self.tabs.currentWidget() else []:
            if p==new or p.isAncestorOf(new):
                if self.last_pane is not p:
                    self.last_pane=p; self.update_title()
                break

    def active(self):
        tab=self.tabs.currentWidget(); panes=tab.findChildren(Pane) if tab else []
        focus=QApplication.focusWidget()
        return next((p for p in panes if focus and (focus==p or p.isAncestorOf(focus))),self.last_pane if self.last_pane in panes else panes[0] if panes else None)
    def update_title(self):
        p=self.active()
        if p and hasattr(p,'path'):
            self.tabs.setTabText(self.tabs.currentIndex(),Path(p.path).name or p.path)
            i=self.tree_model.index(p.path)
            if i.isValid(): self.tree.setCurrentIndex(i); self.tree.scrollTo(i)
            p.status()
    def new_tab(self):
        p=self.active(); path=p.path if p else (sys.argv[1] if self.tabs.count()==0 and len(sys.argv)>1 and os.path.isdir(sys.argv[1]) else str(Path.home())); tab=QSplitter(); tab.addWidget(Pane(self,path)); self.tabs.addTab(tab,Path(path).name); self.tabs.setCurrentWidget(tab)
    def close_tab(self,i):
        if self.tabs.count()>1: w=self.tabs.widget(i); self.tabs.removeTab(i); w.deleteLater()
    def split(self):
        t=self.tabs.currentWidget()
        if t.count()==1: t.addWidget(Pane(self,self.active().path))
        else:
            w=t.widget(1); w.setParent(None); w.deleteLater(); self.last_pane=None; self.update_title()
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
    def save(self):
        tmp=CONFIG.with_suffix('.tmp'); tmp.write_text(json.dumps(self.prefs,indent=2),encoding='utf-8'); tmp.replace(CONFIG)
    def background(self,folder=False):
        path,_=QFileDialog.getOpenFileName(self,'Background image','','Images (*.png *.jpg *.jpeg *.bmp *.webp)')
        if path:
            if folder:self.prefs.setdefault('folders',{})[self.active().path]=path
            else:self.prefs['image']=path
            self.save()
    def appearance(self):
        d=QDialog(self);d.setWindowTitle('Appearance');l=QVBoxLayout(d)
        l.addWidget(QLabel('Application theme'))
        theme=QComboBox();theme.addItems(['Dark','Light']);theme.setCurrentText(self.prefs.get('theme','Dark'));l.addWidget(theme)
        l.addWidget(QLabel('Changes apply to gallery, file list, menus and sidebar.'))
        reset=QCheckBox('Remove existing decorative folder backgrounds');reset.setChecked(False);l.addWidget(reset)
        buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel);buttons.accepted.connect(d.accept);buttons.rejected.connect(d.reject);l.addWidget(buttons)
        if d.exec()==QDialog.Accepted:
            self.prefs['theme']=theme.currentText()
            if reset.isChecked():self.prefs.pop('image',None);self.prefs.pop('folders',None)
            self.save();self.apply_theme()
    def apply_theme(self):
        apply_workspace_theme(self, self.prefs, IS_WINDOWS)

if __name__=='__main__':
    if IS_WINDOWS:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('sacuar.Folder.Desktop')
    app=QApplication(sys.argv); app.setApplicationName('Folder'); app.setWindowIcon(icon('app')); app.setApplicationVersion(VERSION); app.setStyle('Fusion'); w=Explorer(); w.show()
    if '--smoke-test' in sys.argv: QTimer.singleShot(1200,app.quit)
    sys.exit(app.exec())
