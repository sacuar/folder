"""Bounded STL reader and lightweight isometric preview; no external engine."""
import math, re, struct
from pathlib import Path
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QImage, QPainter, QPolygonF, QColor, QPen, QPixmap
from PySide6.QtWidgets import QLabel, QWidget, QVBoxLayout, QSlider

MAX_BYTES=32*1024*1024
MAX_FACES=12000
def read_mesh(path):
    p=Path(path)
    if p.stat().st_size>MAX_BYTES:raise ValueError('STL exceeds preview limit (32 MB)')
    data=p.read_bytes()
    faces=[]
    count=struct.unpack_from('<I',data,80)[0] if len(data)>=84 else 0
    if count and 84+count*50==len(data):
        stride=max(1,math.ceil(count/MAX_FACES))
        for i in range(0,count,stride):
            v=struct.unpack_from('<12f',data,84+i*50)[3:]
            faces.append([v[j:j+3] for j in range(0,9,3)])
    else:
        vertices=re.findall(rb'\bvertex\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)',data,re.I)
        n=len(vertices)//3; stride=max(1,math.ceil(n/MAX_FACES))
        for i in range(0,n,stride):
            faces.append([tuple(map(float,v)) for v in vertices[3*i:3*i+3]])
    faces=[f for f in faces if all(math.isfinite(x) and abs(x)<1e15 for v in f for x in v)]
    if not faces:raise ValueError('No valid STL triangles')
    return faces

def render_mesh(faces,size=256,angle=35):
    a=math.radians(angle); c,s=math.cos(a),math.sin(a)
    def project(v):
        x,y,z=v; u=c*x-s*y; d=s*x+c*y
        return (u,.48*d-.88*z,.88*d+.48*z)
    projected=[[project(v) for v in f] for f in faces]
    xs=[v[0] for f in projected for v in f]; ys=[v[1] for f in projected for v in f]
    cx=(min(xs)+max(xs))/2; cy=(min(ys)+max(ys))/2
    scale=size*.84/max(max(xs)-min(xs),max(ys)-min(ys),1e-9)
    img=QImage(size,size,QImage.Format_ARGB32_Premultiplied); img.fill(QColor('#202831'))
    painter=QPainter(img); painter.setRenderHint(QPainter.Antialiasing); painter.setPen(QPen(QColor('#43647a'),.6))
    for f in sorted(projected,key=lambda f:sum(v[2] for v in f)):
        x1,y1,_=f[0];x2,y2,_=f[1];x3,y3,_=f[2]
        shade=145+int(45*math.tanh(abs((x2-x1)*(y3-y1)-(x3-x1)*(y2-y1))*scale*scale/100))
        painter.setBrush(QColor(65,shade,205))
        painter.drawPolygon(QPolygonF([QPointF((v[0]-cx)*scale+size/2,(v[1]-cy)*scale+size/2) for v in f]))
    painter.end(); return img

class STLPreview(QWidget):
    def __init__(self,path):
        super().__init__(); self.faces=read_mesh(path)
        layout=QVBoxLayout(self); self.image=QLabel(); self.image.setAlignment(Qt.AlignCenter);layout.addWidget(self.image,1)
        layout.addWidget(QLabel('STL rotation • sampled mesh preview'))
        slider=QSlider(Qt.Horizontal);slider.setRange(0,360);slider.setValue(35);slider.setTracking(False);slider.valueChanged.connect(self.redraw);layout.addWidget(slider);self.redraw(35)
    def redraw(self,value):
        self.image.setPixmap(QPixmap.fromImage(render_mesh(self.faces,320,value)))
