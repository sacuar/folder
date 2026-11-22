"""Generate a multi-resolution Windows ICO from Folder's original artwork."""
from pathlib import Path
from PIL import Image,ImageDraw
out=Path('assets');out.mkdir(exist_ok=True)
im=Image.new('RGBA',(256,256));d=ImageDraw.Draw(im)
d.rounded_rectangle((9,9,247,247),radius=54,fill='#343b44')
d.rounded_rectangle((35,61,221,196),radius=19,fill='#eab54b')
d.rounded_rectangle((35,50,115,105),radius=13,fill='#f5cc75')
d.rounded_rectangle((35,91,221,208),radius=18,fill='#f5cc75')
d.rounded_rectangle((53,109,203,195),radius=12,fill='#f6f8fa')
d.rounded_rectangle((69,125,132,141),radius=7,fill='#538fde')
d.rounded_rectangle((69,153,164,168),radius=7,fill='#54a987')
d.rounded_rectangle((69,179,119,185),radius=3,fill='#66717d')
im.save(out/'folder.ico',sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
im.save(out/'folder.png')
