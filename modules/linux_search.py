"""Bounded, asynchronous directory search for Ubuntu. No indexing service required."""
import os
from pathlib import Path
from PySide6.QtCore import QObject, QThread, Signal, Qt
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QLabel, QFileDialog)
from modules.open_with import launch_cached

LIMIT = 10000
class Scan(QThread):
    hit = Signal(str)
    completed = Signal(int, bool)
    def __init__(self, root, term, parent=None):
        super().__init__(parent)
        self.root, self.term = Path(root), term.casefold()
    def run(self):
        scanned = 0
        stopped = False
        for base, dirs, files in os.walk(self.root, followlinks=False):
            if self.isInterruptionRequested():
                stopped = True
                break
            dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(base,d))
                       and d not in {'.git','.venv','node_modules'}]
            for name in dirs+files:
                if self.isInterruptionRequested():
                    stopped = True
                    break
                scanned += 1
                if self.term in name.casefold():
                    self.hit.emit(os.path.join(base,name))
                if scanned >= LIMIT:
                    stopped = True
                    break
            if stopped:
                break
        self.completed.emit(scanned, stopped)

class SearchDialog(QDialog):
    def __init__(self, host):
        super().__init__(host)
        self.host = host
        self.worker = None
        self.setWindowTitle("Search files — Ubuntu")
        self.resize(700,500)
        layout = QVBoxLayout(self)
        bar = QHBoxLayout()
        self.root = QLineEdit(host.active().path)
        self.query = QLineEdit()
        self.query.setPlaceholderText("File or folder name")
        pick = QPushButton("Browse…")
        pick.clicked.connect(self.pick_root)
        search = QPushButton("Search")
        search.clicked.connect(self.search)
        stop = QPushButton("Stop")
        stop.clicked.connect(self.stop)
        for w in (self.root,pick,self.query,search,stop):
            bar.addWidget(w)
        layout.addLayout(bar)
        self.status = QLabel("Search scans up to 10,000 entries; symlinks are not followed.")
        layout.addWidget(self.status)
        self.results = QListWidget()
        layout.addWidget(self.results,1)
        self.results.itemDoubleClicked.connect(self.open_result)
    def pick_root(self):
        path = QFileDialog.getExistingDirectory(self,"Search folder",self.root.text())
        if path: self.root.setText(path)
    def search(self):
        if self.worker and self.worker.isRunning():
            self.status.setText("Stop the current scan first.")
            return
        root = Path(self.root.text()).expanduser()
        term = self.query.text().strip()
        if not root.is_dir() or not term:
            self.status.setText("Choose an accessible folder and enter a search term.")
            return
        self.results.clear()
        worker = Scan(root,term,self)
        self.worker = worker
        worker.hit.connect(self.add_result)
        worker.completed.connect(self.done)
        worker.finished.connect(worker.deleteLater)
        self.status.setText("Searching…")
        worker.start()
    def add_result(self,path):
        item = QListWidgetItem(path)
        item.setData(Qt.UserRole,path)
        self.results.addItem(item)
    def done(self,count,limited):
        self.status.setText(f"{self.results.count()} matches among {count} entries"
                            + (" (limit reached or scan stopped)." if limited else "."))
        self.worker = None
    def stop(self):
        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
    def open_result(self,item):
        path = item.data(Qt.UserRole)
        if os.path.isdir(path): self.host.active().go(path)
        else: launch_cached(path,self.host.prefs)
    def closeEvent(self,event):
        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
            self.worker.wait(5000)
            if self.worker.isRunning():
                event.ignore()
                self.status.setText("Finishing filesystem scan…")
                return
        super().closeEvent(event)

def open_search(host):
    dialog = SearchDialog(host)
    dialog.exec()
