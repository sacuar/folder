from PySide6.QtWidgets import QApplication
def register(host):
    host.addon_menu.addAction('Copy current folder path',lambda:QApplication.clipboard().setText(host.active().path))
