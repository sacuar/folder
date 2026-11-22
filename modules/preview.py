from pathlib import Path
from PySide6.QtCore import Qt,QUrl
from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel,QPlainTextEdit,QScrollArea,QPushButton,QHBoxLayout
from PySide6.QtGui import QPixmap,QImageReader
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtMultimedia import QMediaPlayer,QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
class Preview(QWidget):
    def __init__(self):
        super().__init__(); self.setMinimumWidth(200); self.layout_=QVBoxLayout(self); self.player=None; self.document=None; self.show_file('')
    def clear(self):
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
        self.clear(); p=Path(path); ext=p.suffix.lower()
        try:
            if not path: self.layout_.addWidget(QLabel('Select a file')); return
            if p.is_dir():
                from itertools import islice
                from PySide6.QtWidgets import QListWidget,QListWidgetItem,QFileIconProvider
                from PySide6.QtCore import QFileInfo
                w=QListWidget(); icons=QFileIconProvider()
                for f in islice(p.iterdir(),100):w.addItem(QListWidgetItem(icons.icon(QFileInfo(str(f))),f.name))
            elif ext=='.svg':w=QSvgWidget(path)
            elif ext=='.pdf':
                self.document=QPdfDocument(self); self.document.load(path); w=QPdfView(); w.setDocument(self.document); w.setPageMode(QPdfView.PageMode.MultiPage); w.setZoomMode(QPdfView.ZoomMode.FitToWidth)
            elif ext in ('.mp4','.mkv','.webm','.mov','.avi','.mp3','.wav','.flac','.m4a'):
                w=QWidget(); l=QVBoxLayout(w); video=QVideoWidget(); l.addWidget(video); self.player=QMediaPlayer(self); audio=QAudioOutput(self.player); audio.setMuted(True); self.player.setAudioOutput(audio); self.player.setVideoOutput(video); self.player.setLoops(QMediaPlayer.Loops.Infinite); self.player.setSource(QUrl.fromLocalFile(path)); b=QPushButton('Play / pause'); b.clicked.connect(lambda:self.player.pause() if self.player.playbackState()==QMediaPlayer.PlaybackState.PlayingState else self.player.play()); l.addWidget(b); b=QPushButton('Mute / unmute'); b.clicked.connect(lambda:audio.setMuted(not audio.isMuted())); l.addWidget(b); self.player.play()
            elif ext=='.docx':
                from docx import Document
                d=Document(path); w=QPlainTextEdit('\n'.join(x.text for x in d.paragraphs)); w.setReadOnly(True)
            elif ext in ('.txt','.md','.csv','.json','.py','.log'):
                with p.open('r',encoding='utf-8',errors='replace') as f:s=f.read(200000)
                w=QPlainTextEdit(s); w.setReadOnly(True)
            elif ext in ('.zip','.tar','.gz','.7z'):
                from modules.archives import members
                w=QPlainTextEdit('\n'.join(members(path)[:2000])); w.setReadOnly(True)
            else:
                r=QImageReader(path); r.setAutoTransform(True); size=r.size(); w=QLabel(p.name); w.setAlignment(Qt.AlignCenter); w.setWordWrap(True)
                if size.isValid():
                    from PySide6.QtCore import QSize
                    r.setScaledSize(size.scaled(QSize(500,700),Qt.KeepAspectRatio)); w.setPixmap(QPixmap.fromImage(r.read()))
                else:w.setText(p.name+'\nPreview unavailable')
            self.layout_.addWidget(w)
        except Exception as e:self.layout_.addWidget(QLabel('Preview unavailable: '+str(e)))
