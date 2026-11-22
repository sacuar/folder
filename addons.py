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
