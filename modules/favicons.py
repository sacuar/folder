"""Cache actual site icons; fetch only icon URLs, never send bookmarks to a lookup service."""
from pathlib import Path
from urllib.parse import urlsplit
import hashlib,time
from PySide6.QtCore import QObject,QUrl,QTimer,Signal
from PySide6.QtGui import QIcon,QPixmap,QImageReader
from PySide6.QtNetwork import QNetworkAccessManager,QNetworkRequest
CACHE=Path.home()/'.folder_explorer'/'favicons'
SITES={'mail.google.com':'https://ssl.gstatic.com/ui/v1/icons/mail/rfr/gmail.ico','drive.google.com':'https://drive.google.com/favicon.ico','outlook.live.com':'https://outlook.live.com/favicon.ico','outlook.office.com':'https://outlook.office.com/favicon.ico'}
class Favicons(QObject):
    ready=Signal(str,object)
    def __init__(self,parent):
        super().__init__(parent);self.net=QNetworkAccessManager(self);self.pending=set();self.failed={};self.queue=[];self.epoch=0
    def origin(self,url):
        u=urlsplit(url)
        if u.scheme not in ('http','https') or not u.hostname or u.username or u.password:return ''
        return u.scheme+'://'+u.netloc
    def path(self,origin):return CACHE/(hashlib.sha256(origin.encode()).hexdigest()+'.png')
    def get(self,url,download=True):
        try:origin=self.origin(url)
        except ValueError:return QIcon()
        if not origin:return QIcon()
        p=self.path(origin);result=QIcon(str(p)) if p.is_file() else QIcon()
        if download and origin not in self.pending and (not p.is_file() or time.time()-p.stat().st_mtime>30*86400) and time.time()-self.failed.get(origin,0)>3600:
            self.pending.add(origin);self.queue.append(origin);QTimer.singleShot(0,self.pump)
        return result
    def pump(self):
        if not self.queue:return
        origin=self.queue.pop(0);epoch=self.epoch
        url=SITES.get(urlsplit(origin).hostname,origin+'/favicon.ico')
        request=QNetworkRequest(QUrl(url));request.setTransferTimeout(7000)
        request.setAttribute(QNetworkRequest.RedirectPolicyAttribute,QNetworkRequest.NoLessSafeRedirectPolicy)
        reply=self.net.get(request)
        def limit(received,total):
            if received>262144 or total>262144:reply.abort()
        reply.downloadProgress.connect(limit)
        def finish():
            self.pending.discard(origin)
            try:
                if reply.error() or epoch!=self.epoch:return
                from PySide6.QtCore import QBuffer,QIODevice
                raw=reply.readAll()
                if len(raw)>262144:return
                buffer=QBuffer();buffer.setData(raw);buffer.open(QIODevice.ReadOnly)
                reader=QImageReader(buffer);size=reader.size()
                if not size.isValid() or max(size.width(),size.height())>1024:return
                image=reader.read()
                if image.isNull():return
                CACHE.mkdir(parents=True,exist_ok=True)
                image.save(str(self.path(origin)),'PNG');self.ready.emit(origin,QIcon(str(self.path(origin))))
            finally:
                self.failed[origin]=time.time();reply.deleteLater();QTimer.singleShot(0,self.pump)
        reply.finished.connect(finish)
    def clear(self):
        self.epoch+=1;self.failed.clear();self.queue.clear();self.pending.clear()
        if CACHE.is_dir():
            for p in CACHE.glob('*.png'):p.unlink(missing_ok=True)
