"""Generate one video frame with a bounded off-screen FFmpeg subprocess."""
import subprocess, sys
from PySide6.QtGui import QImage

VIDEO_EXTENSIONS={'.mp4','.mkv','.mov','.webm','.avi','.m4v','.wmv','.mpeg','.mpg','.ts'}
def video_frame(path):
    import imageio_ffmpeg
    exe=imageio_ffmpeg.get_ffmpeg_exe()
    for timestamp in ('1','0'):
        try:
            p=subprocess.run([exe,'-nostdin','-hide_banner','-loglevel','error','-ss',timestamp,'-i',path,'-map','0:v:0','-frames:v','1','-vf','scale=192:192:force_original_aspect_ratio=decrease','-f','image2pipe','-vcodec','png','pipe:1'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=9,creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=='win32' else 0,check=False)
            if p.returncode==0 and p.stdout:
                img=QImage.fromData(p.stdout,'PNG')
                if not img.isNull():return img
        except (OSError,subprocess.TimeoutExpired):pass
    return QImage()
