import sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from modules.photo_viewer import complete_package,reset_image_choices,is_qpv
with tempfile.TemporaryDirectory() as temp:
    root=Path(temp);good=root/'Quick Photo Viewer';good.mkdir()
    exe=good/'QuickPhotoViewer.exe';exe.touch()
    assert not complete_package(exe)
    (good/'python313.dll').touch();(good/'Qt6Core.dll').touch()
    assert complete_package(exe)
    old=root/'Quick_Photo_Viewer_Pro_3.0_Upgrade'/'build';old.mkdir(parents=True)
    bad=old/'QuickPhotoViewer.exe';bad.touch();(old/'python314.dll').touch();(old/'Qt6Core.dll').touch()
    assert not complete_package(bad)
    assert is_qpv(bad)
    prefs={'photo_viewer_path':str(bad),'open_apps':{'.jpg':str(bad),'.txt':'Lumen.exe'}}
    reset_image_choices(prefs)
    assert prefs=={'open_apps':{'.txt':'Lumen.exe'}}
print('Image launcher tests passed')
