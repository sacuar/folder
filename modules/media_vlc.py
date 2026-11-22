"""Native LibVLC preview provider. Does not modify system file associations."""
import os
import sys
from pathlib import Path
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QLabel

MEDIA_EXTENSIONS={'.mp4','.mkv','.webm','.mov','.avi','.m4v','.mpeg','.mpg','.wmv','.ts','.mp3','.wav','.flac','.m4a','.ogg','.aac'}
_dll_dir=None
def backend():
    global _dll_dir
    if sys.platform=='win32':
        root=Path(sys.executable).parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parents[1]/'vendor'
        candidates=[root/'vlc',Path(os.environ.get('ProgramFiles','C:/Program Files'))/'VideoLAN'/'VLC']
        for p in candidates:
            if (p/'libvlc.dll').is_file() and (p/'plugins').is_dir():
                if _dll_dir is None:
                    _dll_dir=os.add_dll_directory(str(p))
                os.environ['PYTHON_VLC_LIB_PATH']=str(p/'libvlc.dll')
                os.environ['PYTHON_VLC_MODULE_PATH']=str(p/'plugins')
                os.environ['VLC_PLUGIN_PATH']=str(p/'plugins')
                break
        else:
            raise RuntimeError('LibVLC runtime missing. Install Folder using the Windows installer.')
    import vlc
    return vlc

class VideoPreview(QWidget):
    def __init__(self,path,parent=None):
        super().__init__(parent)
        self.instance=self.player=self.media=None
        self.disposed=False
        layout=QVBoxLayout(self); layout.setContentsMargins(0,0,0,0)
        self.surface=QWidget(self); self.surface.setAttribute(Qt.WA_NativeWindow)
        self.surface.setMinimumHeight(120); self.surface.setStyleSheet('background:#101010;border-radius:0;')
        layout.addWidget(self.surface,1)
        controls=QHBoxLayout()
        self.play=QPushButton('Play / pause'); self.play.clicked.connect(self.toggle); controls.addWidget(self.play)
        self.mute=QPushButton('Unmute'); self.mute.setCheckable(True); self.mute.toggled.connect(self.set_audio); controls.addWidget(self.mute)
        self.volume=QSlider(Qt.Horizontal); self.volume.setRange(0,100); self.volume.setValue(50); self.volume.valueChanged.connect(self.set_volume); controls.addWidget(self.volume)
        layout.addLayout(controls)
        self.seek=QSlider(Qt.Horizontal); self.seek.setRange(0,1000); self.seek.sliderMoved.connect(self.seek_to); layout.addWidget(self.seek)
        self.label=QLabel('Starting VLC preview…'); self.label.setWordWrap(True); layout.addWidget(self.label)
        self.timer=QTimer(self); self.timer.setInterval(250); self.timer.timeout.connect(self.tick)
        try:
            self.vlc=backend(); self.instance=self.vlc.Instance('--no-video-title-show','--no-snapshot-preview','--quiet','--no-audio-time-stretch')
            if not self.instance:raise RuntimeError('VLC initialization failed')
            self.player=self.instance.media_player_new(); self.media=self.instance.media_new_path(str(Path(path).resolve())); self.player.set_media(self.media)
            if sys.platform=='win32':self.player.set_hwnd(int(self.surface.winId()))
            elif sys.platform.startswith('linux'):self.player.set_xwindow(int(self.surface.winId()))
            self.player.audio_set_volume(50)
            self.player.audio_set_mute(True)
            QTimer.singleShot(0,self.start)
        except Exception as exc:
            self.dispose(); self.label.setText('VLC preview unavailable: '+str(exc))

    def start(self):
        if self.disposed or not self.player or not self.isVisible():return
        self.player.audio_set_mute(not self.mute.isChecked())
        if self.player.play()==-1:
            self.label.setText('VLC could not start this media file.')
        else:self.timer.start()

    def toggle(self):
        if self.player:
            if self.player.is_playing():self.player.set_pause(1)
            else:self.start()

    def set_audio(self,on):
        self.mute.setText('Mute' if on else 'Unmute')
        if self.player:self.player.audio_set_mute(not on)

    def set_volume(self,value):
        if self.player:self.player.audio_set_volume(value)

    def seek_to(self,value):
        if self.player and self.player.is_seekable():self.player.set_position(value/1000)

    def tick(self):
        if not self.player:return
        state=self.player.get_state()
        if state==self.vlc.State.Error:
            self.label.setText('VLC could not decode this file.'); self.timer.stop(); return
        if state==self.vlc.State.Ended and self.isVisible():
            self.player.stop(); self.start(); return
        if state==self.vlc.State.Playing and not self.mute.isChecked():self.player.audio_set_mute(True)
        if not self.seek.isSliderDown():self.seek.setValue(max(0,int(self.player.get_position()*1000)))
        def fmt(ms):
            seconds=max(0,ms//1000); return f'{seconds//60}:{seconds%60:02}'
        self.label.setText(f'{fmt(self.player.get_time())} / {fmt(self.player.get_length())}  •  VLC  •  {state}')

    def hideEvent(self,event):
        if self.player and self.player.is_playing():self.player.set_pause(1)
        super().hideEvent(event)

    def dispose(self):
        if self.disposed:return
        self.disposed=True; self.timer.stop()
        if self.player:self.player.stop(); self.player.release(); self.player=None
        if self.media:self.media.release(); self.media=None
        if self.instance:self.instance.release(); self.instance=None

    def closeEvent(self,event):
        self.dispose(); super().closeEvent(event)
