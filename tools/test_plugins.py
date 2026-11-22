"""Test exact plugin downloads, integrity rejection and 3MF registration."""
import sys,tempfile,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from modules import plugin_catalog as pc
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage,QColor
import types
app=QApplication([])
for key in pc.CATALOG:
    data=pc.download_plugin(key)
    assert pc.verify(key,data),key
    assert not pc.verify(key,data+b'\n'),key
    compile(data,key+'.py','exec')
    if key=='three_mf':
        mod=types.ModuleType(key);exec(compile(data,key+'.py','exec'),mod.__dict__)
        api=pc.API(None,None);mod.register(api)
        assert '.3mf' in pc.THUMBS
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            image=QImage(64,32,QImage.Format_RGB32);image.fill(QColor('blue'));assert image.save(str(root/'thumbnail.png'))
            with zipfile.ZipFile(root/'test.3mf','w') as z:z.write(root/'thumbnail.png','Metadata/thumbnail.png')
            result=pc.THUMBS['.3mf'](str(root/'test.3mf'))
            assert not result.isNull() and result.width()==result.height()*2
print('Verified GitHub downloads and 3MF thumbnail test passed')
