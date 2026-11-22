"""Capture actual running Qt UI with synthetic local demo files."""
import sys,tempfile
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage,QColor,QPainter
from PySide6.QtCore import QTimer
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import explorer
from addons import manage_addons
app=QApplication(sys.argv)
app.setStyle('Fusion')
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)/'Demo Library'; root.mkdir()
    for name in ('Documents','Pictures','Projects','Videos','Downloads'):
        (root/name).mkdir()
    for name,color in [('Coast.png','#447c9b'),('Forest.png','#527c61'),('Studio.png','#c49672')]:
        im=QImage(640,400,QImage.Format_RGB32); im.fill(QColor(color)); p=QPainter(im); p.setPen(QColor('white')); p.drawText(im.rect(),0x84,name); p.end(); im.save(str(root/name))
    (root/'Read me.txt').write_text('Folder — local files, clear previews, modular providers.',encoding='utf-8')
    explorer.settings={'theme':'Dark','view_mode':0,'auto_update_check':False,'preview_visible':True}
    w=explorer.Explorer(); w.resize(1280,800); w.active().go(str(root)); w.show()
    out=Path('screenshots'); out.mkdir(exist_ok=True)
    def capture():
        pane=w.active(); pane.gallery.setCurrentIndex(pane.model.index(str(root/'Coast.png')))
        pane.preview.show_file(str(root/'Coast.png'))
        w.statusBar().showMessage('Demo Library • example files')
        app.processEvents()
        if not w.grab().save(str(out/'workspace.png')):raise RuntimeError('Screenshot failed')
        def grab_dialog():
            d=app.activeModalWidget()
            if d:
                d.grab().save(str(out/'addons.png')); d.accept()
        QTimer.singleShot(400,grab_dialog)
        manage_addons(w)
        app.quit()
    QTimer.singleShot(1800,capture)
    QTimer.singleShot(15000,app.quit)
    app.exec()
