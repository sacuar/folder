"""Browser shortcuts: no credentials, OAuth tokens or cloud API access."""
from urllib.parse import quote_plus
from PySide6.QtCore import Qt,QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication,QInputDialog,QMessageBox,QListWidgetItem
from modules.icons import icon

CLOUD={'Google Drive':'https://drive.google.com/','OneDrive':'https://onedrive.live.com/','MEGA':'https://mega.nz/','pCloud':'https://my.pcloud.com/','Dropbox':'https://www.dropbox.com/home','iCloud Drive':'https://www.icloud.com/iclouddrive/','Box':'https://app.box.com/'}
EMAIL={'Yahoo Mail':'https://mail.yahoo.com/','Gmail':'https://mail.google.com/','Outlook':'https://outlook.live.com/mail/','Microsoft 365 Outlook':'https://outlook.office.com/mail/'}
def open_link(url):
    if QUrl(url).scheme() in ('https','http'):QDesktopServices.openUrl(QUrl(url))

def populate_links(side,prefs):
    for group,links in [('show_cloud',CLOUD),('show_email',EMAIL)]:
        if not prefs.get(group,True):continue
        for name,url in links.items():
            item=QListWidgetItem(icon('drive' if group=='show_cloud' else 'document'),name);item.setData(Qt.UserRole,url);item.setToolTip(url);side.addItem(item)
    if prefs.get('show_bookmarks',True):
        for name,url in prefs.get('bookmarks',{}).items():
            item=QListWidgetItem(icon('document'),name);item.setData(Qt.UserRole,url);side.addItem(item)
    for name,path in prefs.get('sync_folders',{}).items():
        item=QListWidgetItem(icon('folder'),name);item.setData(Qt.UserRole,path);side.addItem(item)

def search_web(host,provider):
    term,ok=QInputDialog.getText(host,'Search '+provider,'Search query:')
    if not ok or not term.strip():return
    if provider=='Google':open_link('https://www.google.com/search?q='+quote_plus(term))
    elif provider=='ChatGPT':open_link('https://chatgpt.com/?q='+quote_plus(term))
    else:
        QApplication.clipboard().setText(term);open_link('https://chat.deepseek.com/')
        QMessageBox.information(host,'DeepSeek','Query copied. Paste it into DeepSeek in your browser.')
