import zipfile, tarfile, shutil
from pathlib import Path

def members(path):
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:return z.namelist()
    if tarfile.is_tarfile(path):
        with tarfile.open(path) as t:return t.getnames()
    raise ValueError('Unsupported archive')

def extract(path,destination):
    root=Path(destination).resolve(); root.mkdir(parents=True,exist_ok=False)
    def target(name):
        p=(root/name).resolve()
        if not p.is_relative_to(root):raise ValueError('Unsafe archive path')
        return p
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            for i in z.infolist():
                p=target(i.filename)
                if i.is_dir():p.mkdir(parents=True,exist_ok=True)
                else:
                    p.parent.mkdir(parents=True,exist_ok=True)
                    with z.open(i) as src,p.open('xb') as dst:shutil.copyfileobj(src,dst)
    elif tarfile.is_tarfile(path):
        with tarfile.open(path) as t:t.extractall(root,filter='data')
    else:raise ValueError('Unsupported archive')
