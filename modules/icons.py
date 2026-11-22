"""Original, resolution-independent Folder line icons; no downloaded fonts."""
from functools import lru_cache
from PySide6.QtCore import Qt, QByteArray
from PySide6.QtGui import QIcon,QPixmap,QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QFileIconProvider
from pathlib import Path

PATHS={
 'folder':'<path d="M3 7V5a2 2 0 0 1 2-2h5l3 3h6a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M3 9h18"/>',
 'home':'<path d="m3 10 9-7 9 7v10h-6v-7H9v7H3z"/>',
 'desktop':'<rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8m-4-4v4"/>',
 'download':'<path d="M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5"/>',
 'document':'<path d="M6 3h8l5 5v13H6zM14 3v5h5M9 13h7m-7 4h7"/>',
 'image':'<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8" cy="8" r="2"/><path d="m3 17 6-6 4 4 3-3 5 5"/>',
 'music':'<path d="M9 18V5l11-2v13M9 8l11-2"/><ellipse cx="6" cy="18" rx="3" ry="2"/><ellipse cx="17" cy="16" rx="3" ry="2"/>',
 'video':'<rect x="3" y="4" width="18" height="16" rx="2"/><path d="m10 8 6 4-6 4z"/>',
 'drive':'<rect x="3" y="5" width="18" height="14" rx="3"/><path d="M3 14h18m-4 3h1"/>',
 'back':'<path d="m13 5-7 7 7 7M6 12h15"/>',
 'forward':'<path d="m11 5 7 7-7 7M3 12h15"/>',
 'up':'<path d="m5 11 7-7 7 7M12 4v17"/>',
 'refresh':'<path d="M20 10a8 8 0 1 0-2 8m2-14v6h-6"/>',
 'plus':'<path d="M12 5v14M5 12h14"/>',
 'split':'<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M12 4v16"/>',
 'copy':'<rect x="8" y="8" width="12" height="13" rx="2"/><path d="M16 8V3H3v13h5"/>',
 'cut':'<circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="m8 8 13 13M8 16 21 3"/>',
 'paste':'<rect x="5" y="5" width="14" height="16" rx="2"/><rect x="9" y="3" width="6" height="4" rx="1"/>',
 'rename':'<path d="m4 16 12-12 4 4L8 20H4zM13 7l4 4"/>',
 'trash':'<path d="M3 6h18M9 6V3h6v3M6 6l1 15h10l1-15M10 10v7m4-7v7"/>',
 'settings':'<circle cx="12" cy="12" r="3"/><path d="m10 3-1 3-3 1-3 3 2 2-1 4 3 3 3-1 2 3 3-2 3 1 3-3-1-3 1-3-3-3-3 1-2-4z"/>',
 'plugins':'<path d="M3 3h7v3a2 2 0 1 0 4 0V3h7v7h-3a2 2 0 1 0 0 4h3v7H3v-7h3a2 2 0 1 0 0-4H3z"/>',
 'archive':'<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M12 3v3m-2 2h4m-4 3h4m-4 3h4m-2 2v3"/>',
 'camera':'<rect x="3" y="6" width="18" height="14" rx="2"/><path d="M8 6l2-3h4l2 3"/><circle cx="12" cy="13" r="4"/>',
 'app':'<rect x="1" y="1" width="22" height="22" rx="5" fill="#303943" stroke="none"/><path d="M4 8V5h6l3 3h7v11H4z" fill="#FFD16C" stroke="none"/><circle cx="12" cy="13.5" r="4" fill="#286FBD" stroke="none"/><path d="m10.4 15.1 3.2-3.2" stroke="#F8FAFC" stroke-width="1.1"/><circle cx="14.4" cy="16" r=".7" fill="#6EE0AD" stroke="none"/>'
}
@lru_cache(maxsize=128)
def icon(name,colour='#a9b9ca'):
    body=PATHS.get(name,PATHS['document'])
    if name=='folder':colour='#d8ae60'
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{colour}" stroke-width="1.55" stroke-linecap="round" stroke-linejoin="round">{body}</svg>'
    result=QIcon()
    renderer=QSvgRenderer(QByteArray(svg.encode()))
    for n in (16,20,24,32,48,64,96,128,256):
        p=QPixmap(n,n); p.fill(Qt.transparent); painter=QPainter(p); renderer.render(painter); painter.end(); result.addPixmap(p)
    return result

class FileIcons(QFileIconProvider):
    def icon(self,info):
        if hasattr(info,'isDir'):
            if info.isRoot():return icon('drive')
            if info.isDir():return icon('folder')
            ext=info.suffix().lower()
            if ext in {'mp4','mkv','webm','mov','avi','wmv','m4v'}:return icon('video')
            if ext in {'mp3','wav','flac','aac','m4a'}:return icon('music')
            if ext in {'zip','tar','gz','7z','rar'}:return icon('archive')
            if ext in {'png','jpg','jpeg','gif','svg','webp','bmp','tiff'}:return icon('image')
        return super().icon(info)
