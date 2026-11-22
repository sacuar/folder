import os, unittest, tempfile
os.environ['QT_QPA_PLATFORM']='offscreen'
from PySide6.QtWidgets import QApplication
from explorer import Explorer
class Smoke(unittest.TestCase):
    def test_navigation(self):
        app=QApplication.instance() or QApplication([])
        w=Explorer()
        with tempfile.TemporaryDirectory() as p:
            w.active().go(p)
            self.assertEqual(w.active().path,os.path.abspath(p))
            self.assertEqual(w.active().stack.count(),2)
        w.close()
