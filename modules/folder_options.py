"""Folder Options: editable preferences, not Windows registry policy."""
from copy import deepcopy
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QTabWidget,QWidget,QCheckBox,QComboBox,QLabel,QPushButton,QDialogButtonBox,QListWidget,QListWidgetItem,QInputDialog,QFileDialog,QMessageBox,QLineEdit)
from PySide6.QtCore import Qt
from modules.create_items import TYPES,DEFAULT_TYPES

CONTEXT=['Copy','Cut','Paste','Rename','Move to Recycle Bin','New','Extract archive…','Folder background','Open with','Play with']
DEFAULTS={'view_mode':0,'theme':'Dark','thumbnails':True,'video_thumbnails':True,'show_hidden':False,'show_extensions':True,'single_click':False,'show_cloud':True,'show_email':True,'show_bookmarks':True,'show_web_search':True,'show_sidebar':True,'show_preview':True,'new_types':DEFAULT_TYPES,'context_items':CONTEXT,'auto_update_check':True}
def options(host):
    prefs=deepcopy(host.prefs); d=QDialog(host);d.setWindowTitle('Folder Options');d.resize(620,570)
    layout=QVBoxLayout(d);tabs=QTabWidget();layout.addWidget(tabs)
    controls={}
    def page(label):
        w=QWidget();l=QVBoxLayout(w);tabs.addTab(w,label);return l
    def check(l,key,label):
        b=QCheckBox(label);b.setChecked(prefs.get(key,DEFAULTS.get(key,False)));l.addWidget(b);controls[key]=b
    general=page('General')
    check(general,'single_click','Single-click to open items')
    check(general,'auto_update_check','Check for updates on startup')
    general.addWidget(QLabel('Default file associations are controlled by Windows Settings.'))
    b=QPushButton('Windows Default Apps');b.clicked.connect(lambda:__import__('PySide6.QtGui',fromlist=['QDesktopServices']).QDesktopServices.openUrl(__import__('PySide6.QtCore',fromlist=['QUrl']).QUrl('ms-settings:defaultapps')));general.addWidget(b);general.addStretch()
    view=page('View')
    for key,label in [('thumbnails','Generate thumbnails'),('video_thumbnails','Generate video thumbnails'),('show_hidden','Show hidden files'),('show_sidebar','Show sidebar')]:check(view,key,label)
    view.addStretch()
    new=page('New items'); items={}
    for key,label in TYPES.items():
        b=QCheckBox(label);b.setChecked(key in prefs.get('new_types',DEFAULT_TYPES));new.addWidget(b);items[key]=b
    new.addStretch()
    context=page('Context menu');menu_items={}
    for label in CONTEXT:
        b=QCheckBox(label);b.setChecked(label in prefs.get('context_items',CONTEXT));context.addWidget(b);menu_items[label]=b
    context.addStretch()
    links=page('Sidebar & web')
    for key,label in [('show_cloud','Cloud storage links'),('show_email','Email links'),('show_bookmarks','Bookmarks'),('show_web_search','Google / ChatGPT / DeepSeek search')]:check(links,key,label)
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
    if d.exec()==QDialog.Accepted:
        for key,b in controls.items():prefs[key]=b.isChecked()
        prefs['new_types']=[k for k,b in items.items() if b.isChecked()]
        prefs['context_items']=[k for k,b in menu_items.items() if b.isChecked()]
        host.prefs.update(prefs);host.save();host.apply_options()
