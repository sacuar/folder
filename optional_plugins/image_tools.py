"""Optional image conversion and resizing. Never overwrites source images."""
from pathlib import Path
from PySide6.QtCore import Qt,QSize
from PySide6.QtGui import QImageReader,QImageWriter
from PySide6.QtWidgets import QFileDialog,QInputDialog,QMessageBox
def run(host):
    source,_=QFileDialog.getOpenFileName(host,'Choose image','','Images (*.jpg *.jpeg *.png *.bmp *.webp *.tif *.tiff *.ico)')
    if not source:return
    reader=QImageReader(source);reader.setAutoTransform(True);size=reader.size()
    if not size.isValid() or size.width()*size.height()>80000000:
        QMessageBox.warning(host,'Image conversion','Unsupported image or exceeds 80 megapixels.');return
    width,ok=QInputDialog.getInt(host,'Resize','Maximum width in pixels (aspect ratio preserved):',size.width(),1,12000)
    if not ok:return
    if width!=size.width():reader.setScaledSize(size.scaled(QSize(width,12000),Qt.KeepAspectRatio))
    image=reader.read()
    if image.isNull():QMessageBox.warning(host,'Image conversion',reader.errorString());return
    target,_=QFileDialog.getSaveFileName(host,'Save converted copy',str(Path(source).with_name(Path(source).stem+'-converted.png')),'PNG (*.png);;JPEG (*.jpg);;WebP (*.webp);;BMP (*.bmp);;TIFF (*.tiff);;ICO (*.ico)')
    if not target:return
    p=Path(target)
    try:
        if p.exists() or p.resolve()==Path(source).resolve():raise ValueError('Choose a new output path; no overwriting.')
        fmt=p.suffix.lower().lstrip('.').encode()
        if fmt not in [bytes(x).lower() for x in QImageWriter.supportedImageFormats()]:raise ValueError('Encoder unavailable for this format.')
        writer=QImageWriter(str(p),fmt);writer.setQuality(90)
        if not writer.write(image):raise ValueError(writer.errorString())
        QMessageBox.information(host,'Image conversion',f'Saved {image.width()} × {image.height()} pixels\n{p}')
    except Exception as e:QMessageBox.warning(host,'Image conversion',str(e))
def register(api):api.action('Convert / resize image…',run)
