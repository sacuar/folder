from PySide6.QtCore import Qt, QSize, QThreadPool, QRunnable, QObject, Signal, QTimer
from PySide6.QtGui import QImageReader, QPixmap, QIcon
from PySide6.QtWidgets import QFileSystemModel
from collections import OrderedDict
import os
from PySide6.QtPdf import QPdfDocument
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QImage,QPainter
class Signals(QObject):
    done=Signal(str,object)
class Job(QRunnable):
    def __init__(self,path,signals): super().__init__(); self.path=path; self.signals=signals
    def run(self):
        img=QImage()
        try:
            if self.path.lower().endswith('.pdf'):
                doc=QPdfDocument(None); doc.load(self.path)
                if doc.pageCount():
                    size=doc.pagePointSize(0).toSize().scaled(QSize(192,192),Qt.KeepAspectRatio)
                    if size.isValid():img=doc.render(0,size)
                doc.close()
            elif self.path.lower().endswith('.svg'):
                renderer=QSvgRenderer(self.path)
                if renderer.isValid():
                    size=renderer.defaultSize().scaled(QSize(192,192),Qt.KeepAspectRatio)
                    if size.isValid():
                        img=QImage(size,QImage.Format_ARGB32_Premultiplied); img.fill(Qt.transparent)
                        painter=QPainter(img); renderer.render(painter); painter.end()
            else:
                r=QImageReader(self.path); r.setAutoTransform(True); s=r.size()
                if s.isValid():
                    r.setScaledSize(s.scaled(QSize(192,192),Qt.KeepAspectRatio)); img=r.read()
        except Exception:
            pass
        self.signals.done.emit(self.path,img)
class ThumbnailModel(QFileSystemModel):
    def __init__(self,parent=None):
        super().__init__(parent); self.cache=OrderedDict(); self.pending=set(); self.signals=Signals(self); self.signals.done.connect(self.finished); self.pool=QThreadPool(self); self.pool.setMaxThreadCount(2); self.dataChanged.connect(self.invalidate_changed)
    def invalidate_changed(self,first,last,roles):
        if roles and all(r==Qt.DecorationRole for r in roles):return
        for row in range(first.row(),last.row()+1):
            p=self.filePath(self.index(row,0,first.parent())); self.cache.pop(p,None)

    def data(self,index,role=Qt.DisplayRole):
        if role==Qt.DecorationRole and index.column()==0 and index.isValid():
            p=self.filePath(index)
            if p.lower().endswith(('.jpg','.jpeg','.png','.webp','.bmp','.gif','.tif','.tiff','.svg','.pdf')):
                if p in self.cache:
                    icon=self.cache[p]
                    if icon is not None:return icon
                elif p not in self.pending and len(self.pending)<128:
                    self.pending.add(p); self.pool.start(Job(p,self.signals))
        return super().data(index,role)
    def finished(self,p,img):
        self.pending.discard(p); self.cache[p]=None if img.isNull() else QIcon(QPixmap.fromImage(img))
        while len(self.cache)>512:self.cache.popitem(last=False)
        i=self.index(p)
        if i.isValid():self.dataChanged.emit(i,i,[Qt.DecorationRole])
