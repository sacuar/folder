from pathlib import Path
import importlib.util
from PySide6.QtWidgets import QMessageBox
ADDON_DIR=Path.home()/'.folder_explorer'/'addons'
def load_addons(host):
    if QMessageBox.question(host,'Trusted code only','Add-ons run Python code with your permissions. Load all installed add-ons?')!=QMessageBox.Yes:return
    ADDON_DIR.mkdir(parents=True,exist_ok=True)
    loaded=getattr(host,'loaded_addons',set()); host.loaded_addons=loaded
    for p in sorted(ADDON_DIR.glob('*.py')):
        if p in loaded:continue
        try:
            spec=importlib.util.spec_from_file_location('bang_addon_'+p.stem,p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); m.register(host); loaded.add(p)
        except Exception as e:QMessageBox.warning(host,p.name,str(e))


def manage_addons(host):
    from PySide6.QtWidgets import QDialog,QVBoxLayout,QLabel,QTreeWidget,QTreeWidgetItem,QPushButton
    from modules.media_vlc import backend
    from modules.photo_viewer import locate_viewer
    dialog=QDialog(host); dialog.setWindowTitle('Plugin manager'); dialog.resize(600,420)
    layout=QVBoxLayout(dialog); layout.addWidget(QLabel('Built-in providers and trusted external add-ons'))
    table=QTreeWidget(); table.setHeaderLabels(['Provider','Status']); layout.addWidget(table)
    try:backend(); media='Available'
    except Exception as exc:media='Unavailable: '+str(exc)
    for name,status in [('LibVLC video / audio',media),('Quick Photo Viewer','Detected' if locate_viewer(host.prefs) else 'Not installed / locate in Appearance'),('Raster / SVG preview','Built in'),('PDF preview','Built in'),('DOCX preview','Built in'),('ZIP / TAR extraction','Built in'),('STL mesh preview','Built in'),('Video frame thumbnails','Built in (FFmpeg runtime)'),('SVG thumbnail provider','Built in'),('Everything search','Built in bridge — requires Everything and ES'),('Thumbnail engine','Built in')]:
        table.addTopLevelItem(QTreeWidgetItem([name,status]))
    ADDON_DIR.mkdir(parents=True,exist_ok=True)
    for p in sorted(ADDON_DIR.glob('*.py')):
        table.addTopLevelItem(QTreeWidgetItem([p.name,'Loaded' if p in getattr(host,'loaded_addons',set()) else 'Not loaded']))
    table.resizeColumnToContents(0)
    for title,fn in [('Open add-on directory',host.addon_folder),('Load trusted add-ons',lambda:load_addons(host)),('Close',dialog.accept)]:
        button=QPushButton(title); button.clicked.connect(fn); layout.addWidget(button)
    dialog.exec()
