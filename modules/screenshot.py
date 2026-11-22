"""Opt-in screenshot provider. Capture a Folder window or selected display."""
from datetime import datetime
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, QStandardPaths
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QComboBox,
    QDialogButtonBox, QFileDialog, QMessageBox, QApplication)

def screenshot_dialog(host):
    dialog=QDialog(host)
    dialog.setWindowTitle("Screenshot")
    layout=QVBoxLayout(dialog)
    layout.addWidget(QLabel("Select what to capture. Nothing is saved until you choose a file."))
    mode=QComboBox(dialog)
    mode.addItem("Folder window",None)
    for index,screen in enumerate(QGuiApplication.screens()):
        mode.addItem(f"Display {index+1} — {screen.name()}",screen)
    layout.addWidget(mode)
    layout.addWidget(QLabel("Display capture may include other windows and private information."))
    delay=QComboBox(dialog)
    for seconds in (0,3,5):
        delay.addItem(f"{seconds} second delay",seconds)
    layout.addWidget(delay)
    buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
    buttons.button(QDialogButtonBox.Ok).setText("Capture")
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)
    if dialog.exec()!=QDialog.Accepted:return
    screen=mode.currentData()
    seconds=delay.currentData()
    def capture():
        try:
            pixmap=screen.grabWindow(0) if screen is not None else host.grab()
            if pixmap.isNull():
                QMessageBox.warning(host,"Screenshot","Capture unavailable. Check display permissions.")
                return
            pictures=QStandardPaths.writableLocation(QStandardPaths.PicturesLocation) or str(Path.home())
            path=str(Path(pictures)/("Folder-"+datetime.now().strftime("%Y%m%d-%H%M%S")+".png"))
            filename,_=QFileDialog.getSaveFileName(host,"Save screenshot",path,"PNG image (*.png);;JPEG image (*.jpg *.jpeg)")
            if filename:
                if not Path(filename).suffix:filename+=".png"
                if not pixmap.save(filename):
                    QMessageBox.warning(host,"Screenshot","Could not write screenshot.")
                else:host.statusBar().showMessage("Screenshot saved: "+filename,5000)
        except RuntimeError:
            QMessageBox.warning(host,"Screenshot","The selected display is no longer available.")
    QTimer.singleShot(max(350,seconds*1000),host,capture)
