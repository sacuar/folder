"""Optional 3MF package thumbnail and simple model mesh preview."""
import zipfile,xml.etree.ElementTree as ET,math
from PySide6.QtCore import Qt,QSize
from PySide6.QtGui import QImage,QImageReader,QPixmap
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import QBuffer,QIODevice
def thumbnail(path):
    with zipfile.ZipFile(path) as z:
        entries=z.infolist()
        if len(entries)>20000:return QImage()
        candidates=[x for x in entries if x.filename.lower().endswith(('.png','.jpeg','.jpg')) and ('thumbnail' in x.filename.lower() or 'plate_1' in x.filename.lower()) and x.file_size<=4*1024*1024]
        for f in sorted(candidates,key=lambda x:('thumbnail' not in x.filename.lower(),len(x.filename))):
            b=QBuffer();b.setData(z.read(f));b.open(QIODevice.ReadOnly);r=QImageReader(b);s=r.size()
            if s.isValid() and s.width()*s.height()<=16000000:
                r.setScaledSize(s.scaled(QSize(512,512),Qt.KeepAspectRatio));im=r.read()
                if not im.isNull():return im
        # Only simple single-resource meshes; no component transform or multi-plate assembly.
        model=next((x for x in entries if x.filename.lower()=='3d/3dmodel.model' and x.file_size<=8*1024*1024),None)
        if not model:return QImage()
        raw=z.read(model)
        if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():return QImage()
        root=ET.fromstring(raw);faces=[]
        for mesh in root.findall('.//{*}mesh'):
            vs=[(float(v.attrib['x']),float(v.attrib['y']),float(v.attrib['z'])) for v in mesh.findall('./{*}vertices/{*}vertex')]
            tris=mesh.findall('./{*}triangles/{*}triangle')
            for t in tris[::max(1,math.ceil(len(tris)/12000))]:
                try:
                    face=[vs[int(t.attrib[k])] for k in ('v1','v2','v3')]
                    if all(math.isfinite(a) and abs(a)<1e12 for v in face for a in v):faces.append(face)
                except (ValueError,KeyError,IndexError):continue
                if len(faces)>=12000:break
            if len(faces)>=12000:break
        if not faces:return QImage()
        from modules.stl_preview import render_mesh
        return render_mesh(faces,384)
class Preview(QLabel):
    def __init__(self,path):
        super().__init__();self.setAlignment(Qt.AlignCenter);self.setMinimumSize(0,0)
        from PySide6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Ignored)
        try:self.im=thumbnail(path)
        except Exception:self.im=QImage()
        self.setToolTip('3MF embedded thumbnail or sampled mesh. Not a slicer.')
        if self.im.isNull():self.setText('No supported 3MF thumbnail or simple mesh.')
    def resizeEvent(self,event):
        if not self.im.isNull():self.setPixmap(QPixmap.fromImage(self.im.scaled(self.size(),Qt.KeepAspectRatio,Qt.SmoothTransformation)))
        super().resizeEvent(event)
def register(api):api.preview('.3mf',Preview,thumbnail)
