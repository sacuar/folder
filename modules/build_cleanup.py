"""Local build inventory. Name matches alone never authorize deletion."""
import os,re,sys,time,stat
from pathlib import Path
from dataclasses import dataclass
from difflib import SequenceMatcher

APPS=('Quick Photo Viewer','Folder','Lumen','CaptureForge')
EXT={'.exe','.msi','.zip','.7z','.lnk'}
SKIP={'windows','$recycle.bin','system volume information','winsxs','windowsapps','.git','.venv','node_modules','__pycache__','package cache'}
def norm(s):return re.sub(r'[^a-z0-9]','',s.casefold())
def match_name(name,query):
    n=norm(name);q=norm(query)
    if len(q)<3:return False
    if q in ('qpv','quickpicviewer','quickphotoviewerpro'):q='quickphotoviewer'
    if q=='quickphotoviewer' and any(x in n for x in ('quickphotoviewer','quickpicviewer','qpv')):return True
    if q in n:return True
    stem=re.split(r'(?i)(?:[_ .-]+(?:v?\d|build|setup|portable|upgrade|source|installer|pro))',name)[0]
    n=norm(stem)
    return len(q)>=6 and len(n)>=6 and SequenceMatcher(None,n,q).ratio()>=.84
def linked(p):
    try:
        s=p.lstat()
        return p.is_symlink() or bool(getattr(s,'st_file_attributes',0)&0x400)
    except OSError:return True
def inside(p,root):
    try:return os.path.commonpath((os.path.normcase(str(p.resolve())),os.path.normcase(str(root.resolve()))))==os.path.normcase(str(root.resolve()))
    except (OSError,ValueError):return False
def programs():
    if sys.platform!='win32':return []
    import winreg
    results=[]
    for hive in (winreg.HKEY_CURRENT_USER,winreg.HKEY_LOCAL_MACHINE):
        for view in (winreg.KEY_WOW64_64KEY,winreg.KEY_WOW64_32KEY):
            try:
                with winreg.OpenKey(hive,r'Software\Microsoft\Windows\CurrentVersion\Uninstall',0,winreg.KEY_READ|view) as parent:
                    for i in range(winreg.QueryInfoKey(parent)[0]):
                        try:
                            with winreg.OpenKey(parent,winreg.EnumKey(parent,i)) as k:
                                def val(n):
                                    try:return str(winreg.QueryValueEx(k,n)[0])
                                    except OSError:return ''
                                name=val('DisplayName')
                                if not name:continue
                                loc=val('InstallLocation').strip('"')
                                results.append((name,loc,val('DisplayVersion')))
                        except OSError:continue
            except OSError:continue
    return list(dict.fromkeys(results))
def default_roots():
    home=Path.home()
    roots=[home/'Downloads',home/'Desktop',home/'Documents']
    for var in ('ProgramFiles','ProgramFiles(x86)','LOCALAPPDATA','APPDATA'):
        if os.environ.get(var):
            p=Path(os.environ[var]);roots.append(p/'Programs' if var=='LOCALAPPDATA' else p)
    return [p for p in roots if p.is_dir()]
def fixed_roots():
    if sys.platform!='win32':return [Path.home()]
    import ctypes
    mask=ctypes.windll.kernel32.GetLogicalDrives()
    return [Path(chr(65+i)+':\\') for i in range(26) if mask&(1<<i) and ctypes.windll.kernel32.GetDriveTypeW(chr(65+i)+':\\')==3]
def current_root():return Path(sys.executable).parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parents[1]
def protected_paths(installed):
    roots=[current_root()]
    for name,loc,version in installed:
        if loc:
            p=Path(os.path.expandvars(loc))
            if p.is_absolute() and p.is_dir() and p!=Path(p.anchor):roots.append(p)
    for var in ('WINDIR','ProgramData','ProgramFiles','ProgramFiles(x86)'):
        if os.environ.get(var):roots.append(Path(os.environ[var]))
    return roots
def protected(p,roots):
    return any(inside(p,r) or (p.is_dir() and inside(r,p)) for r in roots)
def build_dir(p,query):
    try:
        children=list(p.iterdir())
        if any(x.name.lower() in ('.git','pyproject.toml','setup.py','cmakelists.txt','package.json','requirements.txt','src','tests') or x.suffix.lower() in ('.py','.cpp','.cs','.js','.docx','.xlsx') for x in children):return False
        exe=any(x.is_file() and x.suffix.lower()=='.exe' and match_name(x.stem,query) for x in children)
        runtime=any(x.name.lower()=='_internal' or re.fullmatch(r'python3\d+\.dll',x.name.lower()) or x.name.lower()=='qt6core.dll' for x in children)
        return exe and runtime
    except OSError:return False
@dataclass
class Candidate:
    kind:str
    name:str
    path:str
    size:int=0
    modified:float=0
    removable:bool=False
    detail:str=''
def scan(roots,query,cancel,emit,limit=500000,seconds=120):
    installed=programs();guards=protected_paths(installed);seen=set();rows=set();count=0;batch=[]
    def add(c):
        key=(c.kind,os.path.normcase(c.path),c.name)
        if key in rows:return
        rows.add(key);batch.append(c)
        if len(batch)>=40:emit(batch[:]);batch.clear()
    for name,loc,version in installed:
        if match_name(name,query):add(Candidate('Installed app',name,loc,detail=version+' — use Windows uninstall'))
    if sys.platform=='win32':
        import winreg
        for name in ('QuickPhotoViewer','Quick_Photo_Viewer_Pro','Folder','Lumen','CaptureForge'):
            if not match_name(name,query):continue
            for hive,label in ((winreg.HKEY_CURRENT_USER,'HKCU'),(winreg.HKEY_LOCAL_MACHINE,'HKLM')):
                for sub in (r'Software\Microsoft\Windows\CurrentVersion\App Paths'+'\\'+name+'.exe',r'Software\Classes\Applications'+'\\'+name+r'.exe\shell\open\command'):
                    try:
                        with winreg.OpenKey(hive,sub) as k:command=str(winreg.QueryValueEx(k,'')[0])
                        add(Candidate('Registry reference',name,label+'\\'+sub,detail=command))
                    except OSError:pass
    stack=[Path(p) for p in roots];start=time.monotonic()
    while stack and not cancel.is_set() and count<limit and time.monotonic()-start<seconds and len(rows)<10000:
        folder=stack.pop()
        if linked(folder):continue
        key=os.path.normcase(str(folder.absolute()))
        if key in seen:continue
        seen.add(key);count+=1
        try:
            with os.scandir(folder) as entries:
                for e in entries:
                    if cancel.is_set() or time.monotonic()-start>=seconds or len(rows)>=10000:break
                    p=Path(e.path)
                    if linked(p):continue
                    if e.is_dir(follow_symlinks=False):
                        if e.name.casefold() in SKIP:continue
                        stack.append(p)
                        if match_name(e.name,query) and (norm(e.name)!='folder' or build_dir(p,query)):
                            s=e.stat(follow_symlinks=False);verified=build_dir(p,query);safe=verified and not protected(p,guards)
                            add(Candidate('Build folder' if verified else 'Similar folder',e.name,str(p),modified=s.st_mtime,removable=safe,detail='Recognised runtime layout; inspect contents' if verified else 'Name match only — inspect manually'))
                    elif e.is_file(follow_symlinks=False) and p.suffix.lower() in EXT and match_name(p.stem,query):
                        s=e.stat(follow_symlinks=False)
                        safe=not protected(p,guards) and not (p.suffix.lower()=='.exe' and norm(p.stem)=='folder')
                        add(Candidate('Build / installer',e.name,str(p),s.st_size,s.st_mtime,safe,'Protected location' if not safe else 'Review before recycling'))
        except OSError:continue
    if batch:emit(batch)
    return count,len(rows),bool(stack) or cancel.is_set()
def recheck(c,query):
    p=Path(c.path)
    if not p.is_absolute() or linked(p) or not p.exists() or protected(p,protected_paths(programs())):return False
    if any(linked(a) for a in p.parents if a.exists()):return False
    if not match_name(p.stem if p.is_file() else p.name,query):return False
    if c.kind=='Build folder':return p.is_dir() and build_dir(p,query)
    return c.kind=='Build / installer' and p.is_file() and p.suffix.lower() in EXT and not (p.suffix.lower()=='.exe' and norm(p.stem)=='folder')
