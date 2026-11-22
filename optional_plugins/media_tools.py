"""Optional video conversion, trim and audio extraction with FFmpeg."""
import os,shutil
from pathlib import Path
from PySide6.QtCore import QProcess
from PySide6.QtWidgets import QFileDialog,QInputDialog,QMessageBox,QProgressDialog
def run(host):
    exe=shutil.which('ffmpeg')
    if not exe:
        try:
            import imageio_ffmpeg
            exe=imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:pass
    if not exe:QMessageBox.information(host,'Media tools','Install FFmpeg and add it to PATH.');return
    source,_=QFileDialog.getOpenFileName(host,'Choose media','','Video (*.mp4 *.mov *.mkv *.avi *.webm *.m4v *.mpeg *.wmv *.ts)')
    if not source:return
    mode,ok=QInputDialog.getItem(host,'Media tools','Operation:',['Convert video','Trim video','Extract audio'],0,False)
    if not ok:return
    args=['-nostdin','-hide_banner','-n']
    if mode=='Trim video':
        start,ok=QInputDialog.getDouble(host,'Trim video','Start (seconds):',0,0,86400,3)
        if not ok:return
        duration,ok=QInputDialog.getDouble(host,'Trim video','Duration (seconds):',10,.001,86400,3)
        if not ok:return
        args+=['-ss',str(start)]
    args+=['-i',source]
    if mode=='Trim video':args+=['-t',str(duration)]
    formats=['MP3','WAV','M4A','FLAC'] if mode=='Extract audio' else ['MP4','MKV','WebM','MOV']
    fmt,ok=QInputDialog.getItem(host,'Media tools','Output format:',formats,0,False)
    if not ok:return
    p=Path(source);target,_=QFileDialog.getSaveFileName(host,'Save new media file',str(p.with_name(p.stem+'-output.'+fmt.lower())),fmt+' (*.'+fmt.lower()+')')
    if not target:return
    if Path(target).exists() or Path(target).resolve()==p.resolve():QMessageBox.warning(host,'Media tools','Choose a new output filename.');return
    if mode=='Extract audio':
        args+=['-map','0:a:0','-vn','-c:a',{'MP3':'libmp3lame','WAV':'pcm_s16le','M4A':'aac','FLAC':'flac'}[fmt]]
    elif fmt=='WebM':args+=['-map','0:v:0','-map','0:a:0?','-c:v','libvpx-vp9','-crf','32','-b:v','0','-c:a','libopus']
    else:args+=['-map','0:v:0','-map','0:a:0?','-c:v','libx264','-preset','fast','-crf','23','-pix_fmt','yuv420p','-c:a','aac']
    proc=QProcess(host);dialog=QProgressDialog('Processing media locally…','Cancel',0,0,host);dialog.setAutoClose(False);dialog.canceled.connect(proc.kill)
    errors=[]
    def read():
        errors.append(bytes(proc.readAllStandardError()).decode(errors='replace')[-4000:]);del errors[:-5]
    proc.readyReadStandardError.connect(read)
    def finish(code,status):
        read();dialog.close()
        if code==0 and status==QProcess.NormalExit:QMessageBox.information(host,'Media tools','Saved '+target)
        else:QMessageBox.warning(host,'Media tools','Conversion stopped or failed. A partial output may remain.\n'+''.join(errors)[-3000:])
        proc.deleteLater();dialog.deleteLater()
    proc.finished.connect(finish);proc.errorOccurred.connect(lambda _:dialog.setLabelText(proc.errorString()))
    proc.start(exe,args+[target]);dialog.show()
def register(api):api.action('Video convert / trim / extract audio…',run)
