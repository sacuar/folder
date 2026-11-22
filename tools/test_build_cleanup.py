import sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from modules import build_cleanup as c
assert c.match_name('Quick_Photo_Viewer_Pro_3.0_Upgrade','Quick Photo Viewer')
assert c.match_name('QPv-3.0','Quick Photo Viewer')
assert not c.match_name('holiday pictures','Quick Photo Viewer')
with tempfile.TemporaryDirectory() as temp:
    root=Path(temp)
    old=root/'Quick_Photo_Viewer_Pro_3.0_Upgrade';old.mkdir()
    (old/'QuickPhotoViewer.exe').touch();(old/'python314.dll').touch()
    source=root/'QuickPhotoViewer-source';source.mkdir()
    (source/'app.py').touch();(source/'QuickPhotoViewer.exe').touch()
    rows=[]
    c.scan([root],'Quick Photo Viewer',threading.Event(),rows.extend,seconds=5)
    assert any(x.path==str(old) and x.kind=='Build folder' for x in rows)
    assert any(x.path==str(source) and not x.removable for x in rows)
    assert c.build_dir(old,'Quick Photo Viewer')
    assert not c.build_dir(source,'Quick Photo Viewer')
    assert c.protected(old,[root])
print('Old build discovery tests passed')
