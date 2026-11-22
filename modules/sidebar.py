"""Manage clipped folders and web shortcuts without touching actual files."""
import os
from pathlib import Path
from urllib.parse import urlsplit
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidgetItem,QMenu,QInputDialog,QFileDialog,QMessageBox
from modules.icons import icon
from modules.web_links import CLOUD,EMAIL,open_link
from modules.drives import safe_removal
ROLE=Qt.UserRole+1
def add_item(host,name,value,kind):
    ic=icon('paperclip' if kind=='clipped' else 'folder' if kind=='sync_folders' else 'document')
    if kind in ('cloud','email','bookmarks'):
        cached=host.favicons.get(value,host.prefs.get('fetch_favicons',True))
        if not cached.isNull():ic=cached
    item=QListWidgetItem(ic,name);item.setData(Qt.UserRole,value);item.setData(ROLE,kind);item.setToolTip(value);host.side.addItem(item)
def heading(host,title):
    item=QListWidgetItem(title);item.setFlags(Qt.NoItemFlags);host.side.addItem(item)
def populate(host):
    prefs=host.prefs;hidden=prefs.get('hidden_links',[])
    for key,title,items in [('clipped','CLIPPED',prefs.get('clipped',{})),('cloud','CLOUD STORAGE',CLOUD),('email','EMAIL',EMAIL),('bookmarks','BOOKMARKS',prefs.get('bookmarks',{})),('sync_folders','SYNC FOLDERS',prefs.get('sync_folders',{}))]:
        if key=='cloud' and not prefs.get('show_cloud',True) or key=='email' and not prefs.get('show_email',True) or key=='bookmarks' and not prefs.get('show_bookmarks',True):continue
        active=[(n,v) for n,v in items.items() if v not in hidden or key not in ('cloud','email')]
        if active:heading(host,title)
        for n,v in active:add_item(host,n,v,key)
def update_icon(host,origin,ic):
    for i in range(host.side.count()):
        item=host.side.item(i);url=item.data(Qt.UserRole)
        if isinstance(url,str) and url.startswith(('http://','https://')) and host.favicons.origin(url)==origin:item.setIcon(ic)
def add_bookmark(host):
    name,ok=QInputDialog.getText(host,'Clip website','Name:')
    if not ok or not name.strip():return
    url,ok=QInputDialog.getText(host,'Clip website','Website URL (https://):')
    if not ok:return
    try:u=urlsplit(url.strip())
    except ValueError:return
    if u.scheme!='https' or not u.hostname or u.username or u.password:QMessageBox.warning(host,'Bookmark','Enter a valid HTTPS website.');return
    host.prefs.setdefault('bookmarks',{})[name.strip()]=url.strip();host.save();host.refresh_sidebar()
def manage_services(host):
    names={**CLOUD,**EMAIL}
    name,ok=QInputDialog.getItem(host,'Cloud and email shortcuts','Choose a shortcut to show or hide:',list(names),0,False)
    if ok:
        hidden=host.prefs.setdefault('hidden_links',[]);url=names[name]
        if url in hidden:hidden.remove(url)
        else:hidden.append(url)
        host.save();host.refresh_sidebar()
def clip_folder(host,path):
    path=os.path.normpath(os.path.abspath(path))
    if not os.path.isdir(path):return
    items=host.prefs.setdefault('clipped',{})
    if any(os.path.normcase(os.path.normpath(v))==os.path.normcase(path) for v in items.values()):
        for key in list(items):
            if os.path.normcase(os.path.normpath(items[key]))==os.path.normcase(path):del items[key]
    else:
        label=Path(path).name or path
        if label in items:label=path
        items[label]=path
    host.save();host.refresh_sidebar()
def clip_label(host,path):
    return 'Unclip folder' if os.path.normcase(os.path.normpath(path)) in [os.path.normcase(os.path.normpath(v)) for v in host.prefs.get('clipped',{}).values()] else 'Clip folder'
def context(host,point):
    item=host.side.itemAt(point);menu=QMenu(host)
    if item:
        value=item.data(Qt.UserRole);kind=item.data(ROLE)
        if isinstance(value,str):
            menu.addAction('Open',lambda:host.open_place(item))
            if kind in ('cloud','email','bookmarks','sync_folders','clipped'):
                def remove():
                    if kind in ('cloud','email'):
                        hidden=host.prefs.setdefault('hidden_links',[])
                        if value not in hidden:hidden.append(value)
                    else:
                        for k,v in list(host.prefs.get(kind,{}).items()):
                            if v==value:host.prefs[kind].pop(k)
                    host.save();host.refresh_sidebar()
                menu.addAction(icon('paperclip'),'Unclip' if kind in ('clipped','bookmarks') else 'Hide shortcut' if kind in ('cloud','email') else 'Remove shortcut',remove)
            if os.path.isdir(value):
                menu.addAction(icon('paperclip'),clip_label(host,value),lambda:clip_folder(host,value))
                if value in [d.absolutePath() for d in __import__('PySide6.QtCore',fromlist=['QDir']).QDir.drives()]:menu.addAction('Safely remove hardware…',lambda:safe_removal(host))
    menu.addSeparator();menu.addAction(icon('paperclip'),'Clip website…',lambda:add_bookmark(host));menu.addAction('Manage cloud / email shortcuts…',lambda:manage_services(host))
    def choose():
        p=QFileDialog.getExistingDirectory(host,'Clip folder')
        if p:clip_folder(host,p)
    menu.addAction(icon('paperclip'),'Clip another folder…',choose)
    menu.exec(host.side.viewport().mapToGlobal(point))
