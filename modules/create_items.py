"""Safe creation of valid starter files, never overwriting an existing item."""
from pathlib import Path
from PySide6.QtGui import QImage,QColor,QPixmap,QIcon
from PySide6.QtWidgets import QInputDialog,QMessageBox

TYPES={'folder':'Folder','file':'Empty file','txt':'Text document (.txt)','docx':'Word document (.docx)','html':'HTML document (.html)','py':'Python script (.py)','jpg':'JPEG image (.jpg)','png':'PNG image (.png)','ico':'Icon (.ico)','bmp':'Bitmap (.bmp)','svg':'SVG image (.svg)'}
DEFAULT_TYPES=list(TYPES)
def create_item(host,directory,kind):
    ext='' if kind in ('folder','file') else '.'+kind
    default='New folder' if kind=='folder' else 'New file'+ext
    name,ok=QInputDialog.getText(host,'New '+TYPES[kind],'Name:',text=default)
    if not ok:return
    name=name.strip()
    if not name or name in ('.','..') or any(c in name for c in '\\/:*?"<>|') or name.endswith(('.', ' ')):
        QMessageBox.warning(host,'New item','Invalid Windows file name.');return
    if ext and not name.lower().endswith(ext):name+=ext
    path=Path(directory)/name
    created=False
    try:
        if kind=='folder':path.mkdir();return
        with path.open('xb') as f:pass
        created=True
        if kind=='docx':
            from docx import Document
            Document().save(str(path))
        elif kind in ('jpg','png','bmp','ico'):
            image=QImage(64,64,QImage.Format_RGB32);image.fill(QColor('white'))
            if not image.save(str(path),kind.upper()):raise ValueError('Image encoder not available')
        elif kind=='svg':path.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><rect width="64" height="64" fill="white"/></svg>',encoding='utf-8')
        elif kind=='html':path.write_text('<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><title>New page</title></head><body></body></html>\n',encoding='utf-8')
        elif kind=='py':path.write_text('# New Python script\n',encoding='utf-8')
    except Exception as exc:
        if created:path.unlink(missing_ok=True)
        QMessageBox.warning(host,'New item',str(exc))

def add_new_menu(menu,pane):
    sub=menu.addMenu('New')
    for key,label in TYPES.items():
        if key in pane.host.prefs.get('new_types',DEFAULT_TYPES):
            sub.addAction(label,lambda k=key:create_item(pane,pane.path,k))
