"""Folder Options: editable preferences, not Windows registry policy."""
from copy import deepcopy
import sys
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QTabWidget,QWidget,QCheckBox,QComboBox,QLabel,QPushButton,QDialogButtonBox,QListWidget,QListWidgetItem,QInputDialog,QFileDialog,QMessageBox,QLineEdit)
from PySide6.QtCore import Qt
from modules.create_items import TYPES,DEFAULT_TYPES
from modules.toolbar_layout import ToolbarEditor

CONTEXT=['Copy','Cut','Paste','Rename','Move to Recycle Bin','New','Extract archive…','Open with','Play with']
DEFAULTS={'view_mode':0,'toolbar_labels':False,'show_menu_bar':False,'theme':'Dark','thumbnails':True,'video_thumbnails':True,'show_hidden':False,'show_extensions':True,'single_click':False,'show_cloud':True,'show_email':True,'show_bookmarks':True,'show_web_search':True,'show_sidebar':True,'show_everything':True,'fetch_favicons':True,'show_preview':True,'new_types':DEFAULT_TYPES,'context_items':CONTEXT,'auto_update_check':True}
def options(host,initial_tab=None):
    prefs=deepcopy(host.prefs); prefs.setdefault('quick_photo_viewer',True); d=QDialog(host);d.setWindowTitle('Folder Options');d.resize(720,660)
    layout=QVBoxLayout(d);tabs=QTabWidget();layout.addWidget(tabs)
    controls={}
    def page(label):
        w=QWidget();l=QVBoxLayout(w);tabs.addTab(w,label);return l
    def check(l,key,label):
        b=QCheckBox(label);b.setChecked(prefs.get(key,DEFAULTS.get(key,False)));l.addWidget(b);controls[key]=b
    general=page('General')
    check(general,'single_click','Single-click to open items')
    check(general,'auto_update_check','Check for updates on startup')
    general.addWidget(QLabel('Default application associations are controlled by your operating system.'))
    if sys.platform == 'win32':
        b=QPushButton('Windows Default Apps');b.clicked.connect(lambda:__import__('PySide6.QtGui',fromlist=['QDesktopServices']).QDesktopServices.openUrl(__import__('PySide6.QtCore',fromlist=['QUrl']).QUrl('ms-settings:defaultapps')));general.addWidget(b);general.addStretch()
    view=page('Appearance & view')
    theme=QComboBox();theme.addItems(['Dark','Light']);theme.setCurrentText(prefs.get('theme','Dark'));view.addWidget(QLabel('Colour theme'));view.addWidget(theme)
    for key,label in [('thumbnails','Generate thumbnails'),('video_thumbnails','Generate video thumbnails'),('show_hidden','Show hidden files'),('show_sidebar','Show sidebar')]:check(view,key,label)
    check(view,'show_scribble','Show Scribble button (temporary notes and calculator)')
    check(view,'advanced_commands','Show advanced commands (administrator access)')
    view.addStretch()
    toolbar=page('Toolbar')
    check(toolbar,'toolbar_labels','Show text labels beside toolbar icons')
    check(toolbar,'show_menu_bar','Show full menu bar (otherwise use the three-dot menu)')
    editor=ToolbarEditor(prefs,d);toolbar.addWidget(editor,1)
    search=page('Search & indexing')
    if sys.platform == 'win32':
        search.addWidget(QLabel('Everything is bundled on Windows. Full NTFS indexing may need its service.'))
        for title,fn in [('Start search engine',lambda:__import__('modules.search_engine',fromlist=['start']).start()),('Rebuild index',lambda:__import__('modules.search_engine',fromlist=['reindex']).reindex()),('Enable Everything service (administrator)',lambda:__import__('modules.search_engine',fromlist=['install_service']).install_service())]:
            b=QPushButton(title);b.clicked.connect(fn);search.addWidget(b)
    else:
        search.addWidget(QLabel('Ubuntu search scans the chosen directory, without modifying system indexes.'))
        b=QPushButton('Search files…')
        b.clicked.connect(lambda:__import__('modules.linux_search',fromlist=['open_search']).open_search(host))
        search.addWidget(b)
    search.addStretch()
    new=page('New items'); items={}
    for key,label in TYPES.items():
        b=QCheckBox(label);b.setChecked(key in prefs.get('new_types',DEFAULT_TYPES));new.addWidget(b);items[key]=b
    new.addStretch()
    context=page('Context menu');menu_items={}
    for label in CONTEXT:
        b=QCheckBox(label);b.setChecked(label in prefs.get('context_items',CONTEXT));context.addWidget(b);menu_items[label]=b
    context.addStretch()
    links=page('Sidebar & web')
    for key,label in [('show_cloud','Cloud storage links'),('show_email','Email links'),('show_bookmarks','Bookmarks'),('fetch_favicons','Automatically fetch and cache website icons')]:check(links,key,label)
    links.addWidget(QLabel('Right-click sidebar items to Clip/Unclip or hide cloud and email shortcuts.'))
    def restore_services():prefs['hidden_links']=[]
    button=QPushButton('Restore cloud / email shortcuts');button.clicked.connect(restore_services);links.addWidget(button)
    def add_link():
        name,ok=QInputDialog.getText(d,'Bookmark','Name:')
        if not ok or not name.strip():return
        url,ok=QInputDialog.getText(d,'Bookmark','HTTPS URL:')
        if ok and url.startswith('https://'):prefs.setdefault('bookmarks',{})[name.strip()]=url
    def add_sync():
        path=QFileDialog.getExistingDirectory(d,'Choose local cloud sync folder')
        if path:
            from pathlib import Path
            prefs.setdefault('sync_folders',{})[Path(path).name or path]=path
    def remove_link():
        entries=list(prefs.get('bookmarks',{}))+list(prefs.get('sync_folders',{}))
        if not entries:return
        name,ok=QInputDialog.getItem(d,'Remove shortcut','Shortcut:',entries,0,False)
        if ok:
            for key in ('bookmarks','sync_folders'):prefs.get(key,{}).pop(name,None)
    for title,fn in [('Add browser bookmark',add_link),('Add local cloud sync folder',add_sync),('Remove shortcut',remove_link)]:
        b=QPushButton(title);b.clicked.connect(fn);links.addWidget(b)
    links.addStretch()
    troubleshoot=page('Troubleshoot')
    troubleshoot.addWidget(QLabel('Reset Folder preferences only. Your files and Windows associations are not changed.'))
    def reset():
        if QMessageBox.question(d,'Reset Folder','Reset all Folder preferences and restart Folder?')==QMessageBox.Yes:
            host.prefs.clear();host.prefs.update(deepcopy(DEFAULTS));host.save();d.reject();QMessageBox.information(host,'Reset','Preferences restored. Restart Folder to apply all settings.')
    b=QPushButton('Restore defaults');b.clicked.connect(reset);troubleshoot.addWidget(b)
    def clear_cache():
        for p in host.findChildren(__import__('modules.thumbnails',fromlist=['ThumbnailModel']).ThumbnailModel):p.cache.clear()
        QMessageBox.information(d,'Cache','In-memory thumbnail cache cleared.')
    b=QPushButton('Clear thumbnail cache');b.clicked.connect(clear_cache);troubleshoot.addWidget(b);troubleshoot.addStretch()
    buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel);buttons.accepted.connect(d.accept);buttons.rejected.connect(d.reject);layout.addWidget(buttons)
    if initial_tab:
        for i in range(tabs.count()):
            if tabs.tabText(i)==initial_tab:tabs.setCurrentIndex(i);break
    if d.exec()==QDialog.Accepted:
        prefs.update(editor.values())
        prefs['theme']=theme.currentText()
        for key,b in controls.items():prefs[key]=b.isChecked()
        prefs['new_types']=[k for k,b in items.items() if b.isChecked()]
        prefs['context_items']=[k for k,b in menu_items.items() if b.isChecked()]
        host.prefs.pop('photo_viewer_path',None)
        host.prefs.update(prefs);host.save();host.apply_options()
