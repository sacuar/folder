"""Aspect-ratio-preserving image and SVG display without minimum size feedback."""
from PySide6.QtCore import Qt,QSize,QRectF
from PySide6.QtGui import QPainter,QImageReader
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QWidget,QSizePolicy
class FitPreview(QWidget):
    def __init__(self,path,svg=False):
        super().__init__();self.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Ignored);self.setMinimumSize(0,0)
        self.renderer=QSvgRenderer(path,self) if svg else None
        self.image=None
        if self.renderer:
            if not self.renderer.isValid():raise ValueError("Invalid SVG")
            self.original=self.renderer.defaultSize()
            if not self.original.isValid():self.original=QSize(256,256)
        else:
            reader=QImageReader(path);reader.setAutoTransform(True);size=reader.size()
            if not size.isValid():raise ValueError("Preview unavailable")
            if max(size.width(),size.height())>2048:reader.setScaledSize(size.scaled(QSize(2048,2048),Qt.KeepAspectRatio))
            self.image=reader.read()
            if self.image.isNull():raise ValueError(reader.errorString())
            self.original=self.image.size()
    def sizeHint(self):return QSize(220,180)
    def minimumSizeHint(self):return QSize(0,0)
    def paintEvent(self,event):
        size=self.original.scaled(self.size()-QSize(12,12),Qt.KeepAspectRatio)
        if size.width()<=0 or size.height()<=0:return
        target=QRectF((self.width()-size.width())/2,(self.height()-size.height())/2,size.width(),size.height())
        p=QPainter(self);p.setRenderHint(QPainter.SmoothPixmapTransform);p.setRenderHint(QPainter.Antialiasing)
        if self.renderer:self.renderer.render(p,target)
        else:p.drawImage(target,self.image)
        p.end()
