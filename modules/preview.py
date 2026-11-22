from pathlib import Path
from modules.stl_preview import STLPreview
from modules.fit_preview import FitPreview
from modules.media_vlc import VideoPreview, MEDIA_EXTENSIONS
from modules.photo_viewer import open_file
from PySide6.QtCore import Qt,QUrl,QSize,QFileInfo
from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel,QPlainTextEdit,QScrollArea,QPushButton,QHBoxLayout,QSlider,QFileIconProvider,QToolButton,QListWidget,QListWidgetItem
from PySide6.QtGui import QPixmap,QImageReader,QDesktopServices
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtMultimedia import QMediaPlayer,QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
class Preview(QWidget):
    def __init__(self):
        super().__init__(); self.setMinimumWidth(200); self.layout_=QVBoxLayout(self); self.player=None; self.document=None; self.current_path=''; self.media_preview=None; self.prefs={}; self.show_file('')
    def clear(self):
        if self.media_preview:
            self.media_preview.dispose(); self.media_preview=None
        if self.player:
            self.player.stop(); self.player.setSource(QUrl()); self.player.deleteLater(); self.player=None
        while self.layout_.count():
            w=self.layout_.takeAt(0).widget()
            if w: w.hide(); w.deleteLater()
        if self.document: self.document.deleteLater(); self.document=None
    def hideEvent(self,event):
        if self.player:self.player.pause()
        super().hideEvent(event)
    def show_file(self,path):
        self.clear(); self.current_path=path; p=Path(path); ext=p.suffix.lower()
        try:
            if not path: self.layout_.addWidget(QLabel('Select a file')); return
            title=QLabel(p.name); title.setWordWrap(True); title.setTextFormat(Qt.PlainText); title.setStyleSheet('font-size:16px;font-weight:600;'); self.layout_.addWidget(title)
            info=p.stat()
            details=QLabel(('Folder' if p.is_dir() else f'{info.st_size:,} bytes')+'  •  '+(ext[1:].upper() or 'File')); self.layout_.addWidget(details)
            open_button=QPushButton('Open externally'); open_button.clicked.connect(lambda:open_file(path,self.prefs)); self.layout_.addWidget(open_button)
            if p.is_dir():
                from itertools import islice
                from PySide6.QtWidgets import QListWidget,QListWidgetItem,QFileIconProvider
                w=QListWidget(); icons=QFileIconProvider()
                for f in islice(p.iterdir(),200):
                    item=QListWidgetItem(icons.icon(QFileInfo(str(f))),f.name); item.setData(Qt.UserRole,str(f)); w.addItem(item)
                w.itemDoubleClicked.connect(lambda item:self.show_file(item.data(Qt.UserRole)))
            elif ext=='.stl':w=STLPreview(path)
            elif ext=='.svg':w=FitPreview(path,True)
            elif ext=='.pdf':
                self.document=QPdfDocument(self); self.document.load(path); w=QPdfView(); w.setDocument(self.document); w.setPageMode(QPdfView.PageMode.MultiPage); w.setZoomMode(QPdfView.ZoomMode.FitToWidth); controls=QWidget(); row=QHBoxLayout(controls); row.setContentsMargins(0,0,0,0)
                for label,fn in [('−',lambda:w.setZoomFactor(max(0.2,w.zoomFactor()/1.2))),('+',lambda:w.setZoomFactor(min(5,w.zoomFactor()*1.2))),('Fit',lambda:w.setZoomMode(QPdfView.ZoomMode.FitToWidth))]:
                    b=QPushButton(label); b.clicked.connect(fn); row.addWidget(b)
                self.layout_.addWidget(controls)
            elif ext in MEDIA_EXTENSIONS:
                w=VideoPreview(path); self.media_preview=w
            elif ext=='.docx':
                from docx import Document
                d=Document(path); lines=[x.text for x in d.paragraphs]
                for table in d.tables:
                    lines.extend(' | '.join(c.text for c in row.cells) for row in table.rows)
                w=QPlainTextEdit('\n'.join(lines)); w.setReadOnly(True)
            elif ext in ('.txt','.md','.csv','.json','.py','.log'):
                with p.open('r',encoding='utf-8',errors='replace') as f:s=f.read(200000)
                w=QPlainTextEdit(s); w.setReadOnly(True)
            elif ext in ('.zip','.tar','.gz','.7z'):
                from modules.archives import members
                w=QPlainTextEdit('\n'.join(members(path)[:2000])); w.setReadOnly(True)
            else:
                w=FitPreview(path)
            self.layout_.addWidget(w,1)
        except Exception as e:self.layout_.addWidget(QLabel('Preview unavailable: '+str(e)))
