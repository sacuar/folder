"""Windows update provider. GitHub HTTPS release metadata + SHA-256 verification."""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from PySide6.QtCore import QObject, Signal, QTimer, QUrl, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QLabel,
    QPlainTextEdit, QDialogButtonBox, QMessageBox, QProgressDialog)
from version import VERSION, REPOSITORY

API = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"
RELEASES = f"https://github.com/{REPOSITORY}/releases"
MAX_BYTES = 1024 * 1024 * 1024

def version_tuple(value):
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", value)
    if not match:
        raise ValueError("Unsupported release version")
    return tuple(map(int, match.groups()))

def request(url):
    return urlopen(Request(url, headers={"User-Agent": f"Folder/{VERSION}",
        "Accept": "application/vnd.github+json"}), timeout=15)

def release_info():
    try:
        with request(API) as response:
            release = json.loads(response.read(2_000_000))
    except HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    if release.get("draft") or release.get("prerelease"):
        return None
    tag = release["tag_name"]
    if version_tuple(tag) <= version_tuple(VERSION):
        return None
    version = tag.removeprefix("v")
    name = f"Folder-{version}-Setup-x64.exe"
    asset = next((a for a in release.get("assets", []) if a.get("name") == name), None)
    expected_url = f"{RELEASES}/download/{tag}/{name}"
    if not asset or asset.get("browser_download_url") != expected_url:
        raise ValueError("The release has no matching Windows installer.")
    digest = asset.get("digest") or ""
    if not re.fullmatch(r"sha256:[0-9a-fA-F]{64}", digest):
        raise ValueError("Installer has no verifiable GitHub SHA-256 digest.")
    size = int(asset["size"])
    if not 0 < size <= MAX_BYTES:
        raise ValueError("Invalid installer size.")
    return {"version": version, "notes": release.get("body") or "No release notes.",
            "url": expected_url, "digest": digest[7:].lower(), "size": size, "name": name}

def installed_directory():
    if sys.platform != "win32" or not getattr(sys, "frozen", False):
        return None
    try:
        import winreg
        for hive in (winreg.HKEY_CURRENT_USER,winreg.HKEY_LOCAL_MACHINE):
            try:
                with winreg.OpenKey(hive,r"Software\FolderExplorer") as key:
                    directory=Path(winreg.QueryValueEx(key,"InstallPath")[0]).resolve()
                if directory==Path(sys.executable).resolve().parent:return directory
            except OSError:continue
    except OSError:
        pass
    return None

def download_installer(info, progress, cancel):
    directory = Path(tempfile.mkdtemp(prefix="FolderUpdate-"))
    destination = directory / info["name"]
    hashed = hashlib.sha256()
    count = 0
    try:
        with request(info["url"]) as response, destination.open("xb") as output:
            while True:
                if cancel.is_set():
                    raise InterruptedError("Download cancelled")
                chunk = response.read(256 * 1024)
                if not chunk:
                    break
                count += len(chunk)
                if count > info["size"]:
                    raise ValueError("Installer exceeds expected size.")
                hashed.update(chunk)
                output.write(chunk)
                progress(int(count * 100 / info["size"]))
        if count != info["size"] or hashed.hexdigest() != info["digest"]:
            raise ValueError("Installer integrity check failed.")
        if cancel.is_set():
            raise InterruptedError("Download cancelled")
        return str(destination)
    except Exception:
        destination.unlink(missing_ok=True)
        directory.rmdir()
        raise

class Updater(QObject):
    checked = Signal(object, str)
    downloaded = Signal(str, str)
    progress = Signal(int)

    def __init__(self, host, enabled=True):
        super().__init__(host)
        self.host = host
        self.enabled = enabled
        self.busy = False
        self.manual = False
        self.dialog = None
        self.cancel = threading.Event()
        self.checked.connect(self.on_checked)
        self.downloaded.connect(self.on_downloaded)
        self.progress.connect(self.on_progress)
        help_menu = host.menuBar().addMenu("Help")
        help_menu.addAction("About Folder", self.about)
        check = help_menu.addAction("Check for updates…", lambda: self.check(True))
        check.setEnabled(enabled)
        automatic = help_menu.addAction("Check for updates on startup")
        automatic.setCheckable(True)
        automatic.setChecked(host.prefs.get("auto_update_check", True))
        automatic.setEnabled(enabled)
        automatic.toggled.connect(self.set_auto)
        help_menu.addAction("GitHub releases", lambda: QDesktopServices.openUrl(QUrl(RELEASES)))
        if enabled and automatic.isChecked():
            QTimer.singleShot(2500, lambda: self.check(False))

    def set_auto(self, value):
        self.host.prefs["auto_update_check"] = value
        self.host.save()

    def about(self):
        QMessageBox.about(self.host, "About Folder", f"Folder {VERSION} (Alpha)\nOpen-source Windows file manager\nMIT license\nUpdates: GitHub releases")

    def check(self, manual):
        if not self.enabled:
            return
        if self.busy:
            if manual:
                QMessageBox.information(self.host, "Folder updates", "An update check or download is already running.")
            return
        self.busy = True
        self.manual = manual
        def work():
            try:
                info = release_info()
                self.checked.emit(info, "")
            except Exception as exc:
                try:
                    self.checked.emit(None, str(exc))
                except RuntimeError:
                    pass
        threading.Thread(target=work, daemon=True).start()

    def on_checked(self, info, error):
        self.busy = False
        if error:
            if self.manual:
                QMessageBox.warning(self.host, "Update check", error)
            return
        if info is None:
            if self.manual:
                QMessageBox.information(self.host, "Folder updates", f"Folder {VERSION}: no newer published release.")
            return
        dialog = QDialog(self.host)
        dialog.setWindowTitle("Folder update available")
        dialog.resize(570, 460)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(f"Installed: {VERSION}    →    Available: {info['version']}"))
        layout.addWidget(QLabel("What's new"))
        notes = QPlainTextEdit(info["notes"])
        notes.setReadOnly(True)
        layout.addWidget(notes, 1)
        layout.addWidget(QLabel(f"Download: {info['size']/1024/1024:.1f} MB • SHA-256 verification"))
        buttons = QDialogButtonBox(QDialogButtonBox.Cancel)
        install_dir = installed_directory()
        action = buttons.addButton("Download and install" if install_dir else "Open release page", QDialogButtonBox.AcceptRole)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() != QDialog.Accepted:
            return
        if not install_dir:
            QDesktopServices.openUrl(QUrl(RELEASES))
            return
        self.busy = True
        self.cancel.clear()
        self.dialog = QProgressDialog("Downloading verified installer…", "Cancel", 0, 100, self.host)
        self.dialog.setWindowModality(Qt.WindowModal)
        self.dialog.setAutoClose(False)
        self.dialog.setAutoReset(False)
        self.dialog.canceled.connect(self.cancel.set)
        self.dialog.show()
        def work():
            try:
                path = download_installer(info, self.progress.emit, self.cancel)
                self.downloaded.emit(path, "")
            except Exception as exc:
                try:
                    self.downloaded.emit("", str(exc))
                except RuntimeError:
                    pass
        threading.Thread(target=work, daemon=True).start()

    def on_progress(self, value):
        if self.dialog:
            self.dialog.setValue(value)

    def on_downloaded(self, path, error):
        self.busy = False
        if self.dialog:
            self.dialog.hide()
            self.dialog.deleteLater()
            self.dialog = None
        if error:
            if not self.cancel.is_set():
                QMessageBox.warning(self.host, "Update download", error)
            return
        directory = installed_directory()
        if self.cancel.is_set() or not directory:
            Path(path).unlink(missing_ok=True)
            return
        if QMessageBox.question(self.host, "Install update", "Installer verified. Close Folder and start installation now?") != QMessageBox.Yes:
            Path(path).unlink(missing_ok=True)
            return
        try:
            subprocess.Popen([path, "/SP-", "/NORESTART", f"/DIR={directory}"],
                             cwd=str(Path(path).parent), close_fds=True)
        except OSError as exc:
            QMessageBox.warning(self.host, "Installer", str(exc))
            return
        QApplication.quit()
