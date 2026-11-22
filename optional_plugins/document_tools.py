"""Optional office document conversion through separately installed LibreOffice."""
import os,shutil,tempfile
from pathlib import Path
from PySide6.QtCore import QProcess
from PySide6.QtWidgets import QFileDialog,QInputDialog,QMessageBox,QProgressDialog
def run(host):
    choices=[shutil.which('soffice.exe'),shutil.which('soffice')]
    for var in ('ProgramFiles','ProgramFiles(x86)'):
        if os.environ.get(var):choices.append(str(Path(os.environ[var])/'LibreOffice'/'program'/'soffice.exe'))
    exe=next((x for x in choices if x and Path(x).is_file()),None)
    if not exe:
        QMessageBox.information(host,'Document conversion','Install LibreOffice from libreoffice.org first.');return
    source,_=QFileDialog.getOpenFileName(host,'Choose document','','Documents (*.doc *.docx *.odt *.rtf *.txt *.xls *.xlsx *.ods *.ppt *.pptx *.odp)')
    if not source:return
    ext=Path(source).suffix.lower()
    formats=['pdf','xlsx','ods','csv'] if ext in ('.xls','.xlsx','.ods') else ['pdf','pptx','odp'] if ext in ('.ppt','.pptx','.odp') else ['pdf','docx','odt','txt','rtf']
    formats=[x for x in formats if '.'+x!=ext]
    fmt,ok=QInputDialog.getItem(host,'Document conversion','Output format:',formats,0,False)
    if not ok:return
    dest=QFileDialog.getExistingDirectory(host,'Choose output directory')
    if not dest:return
    final=Path(dest)/(Path(source).stem+'.'+fmt)
    if final.exists():QMessageBox.warning(host,'Document conversion','Output exists. Choose another directory.');return
    temp=tempfile.TemporaryDirectory();root=Path(temp.name);profile=(root/'profile').as_uri()
    proc=QProcess(host);dialog=QProgressDialog('Converting locally…','Cancel',0,0,host);dialog.setAutoClose(False);dialog.canceled.connect(proc.kill)
    def finish(code,status):
        dialog.close()
        try:
            output=root/final.name
            if code or status!=QProcess.NormalExit or not output.is_file():raise ValueError('LibreOffice conversion failed or was cancelled.')
            with final.open('xb') as target,output.open('rb') as inp:shutil.copyfileobj(inp,target)
            QMessageBox.information(host,'Document conversion','Saved '+str(final))
        except Exception as e:QMessageBox.warning(host,'Document conversion',str(e))
        finally:temp.cleanup();proc.deleteLater();dialog.deleteLater()
    proc.finished.connect(finish);proc.errorOccurred.connect(lambda _:dialog.setLabelText(proc.errorString()))
    proc.start(exe,['-env:UserInstallation='+profile,'--headless','--convert-to',fmt,'--outdir',str(root),source]);dialog.show()
def register(api):api.action('Convert office document…',run)
