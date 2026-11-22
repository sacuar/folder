from PySide6.QtCore import Qt, QSize, QThreadPool, QRunnable, QObject, Signal, QTimer
from PySide6.QtGui import QImageReader, QPixmap, QIcon
from PySide6.QtWidgets import QFileSystemModel
from collections import OrderedDict
import os
class Signals(QObject):
    done=Signal(str,object)
class Job(QRunnable):
    def __init__(self,path,signals): super().__init__(); self.path=path; self.signals=signals
    def run(self):
        r=QImageReader(self.path); r.setAutoTransform(True); s=r.size()
        if s.isValid(): r.setScaledSize(s.scaled(QSize(192,192),Qt.KeepAspectRatio))
        self.signals.done.emit(self.path,r.read())
class ThumbnailModel(QFileSystemModel):
    def __init__(self,parent=None):
        super().__init__(parent); self.cache=OrderedDict(); self.pending=set(); self.signals=Signals(self); self.signals.done.connect(self.finished); self.pool=QThreadPool(self); self.pool.setMaxThreadCount(2)
    def data(self,index,role=Qt.DisplayRole):
        if role==Qt.DecorationRole and index.column()==0 and index.isValid():
            p=self.filePath(index)
            if p.lower().endswith(('.jpg','.jpeg','.png','.webp','.bmp','.gif','.tif','.tiff','.svg')):
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
