import sys, os, shlex, subprocess
from pathlib import Path
DESKTOP=Path(os.environ.get('XDG_DATA_HOME',Path.home()/'.local/share'))/'applications/folder-explorer.desktop'
def register():
    args=[sys.executable] if getattr(sys,'frozen',False) else [sys.executable,str(Path(__file__).resolve().parents[1]/'explorer.py')]
    # Desktop Entry Exec uses double quoting rather than shell quoting.
    def quote(s): return '"'+str(s).replace('\\','\\\\').replace('"','\\"').replace('`','\\`').replace('$','\\$').replace('%','%%')+'"'
    DESKTOP.parent.mkdir(parents=True,exist_ok=True)
    DESKTOP.write_text('[Desktop Entry]\nType=Application\nName=Folder\nExec='+' '.join(map(quote,args))+' %f\nIcon=system-file-manager\nTerminal=false\nCategories=System;FileManager;\nMimeType=inode/directory;\n')
def unregister(): DESKTOP.unlink(missing_ok=True)
