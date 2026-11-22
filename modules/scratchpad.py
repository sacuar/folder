"""Temporary notes, arithmetic and calendar. Notes are never written to disk."""
import ast,operator,math
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget,QWidget,QVBoxLayout,QHBoxLayout,QPlainTextEdit,QLineEdit,QLabel,QPushButton,QCalendarWidget,QTabWidget
OPS={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,ast.Mod:operator.mod}
def calculate(text):
    if len(text)>160:raise ValueError('Expression too long')
    def val(n):
        if isinstance(n,ast.Constant) and type(n.value) in (int,float):r=n.value
        elif isinstance(n,ast.BinOp) and type(n.op) in OPS:r=OPS[type(n.op)](val(n.left),val(n.right))
        elif isinstance(n,ast.UnaryOp) and type(n.op) in (ast.UAdd,ast.USub):r=val(n.operand)*(1 if isinstance(n.op,ast.UAdd) else -1)
        else:raise ValueError('Numbers and arithmetic only')
        if abs(r)>1e15 or not math.isfinite(r):raise ValueError('Out of range')
        return r
    return val(ast.parse(text,mode='eval').body)
class Pad(QDockWidget):
    def __init__(self,host):
        super().__init__('Scribble',host);self.setObjectName('Scribble');self.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea|Qt.BottomDockWidgetArea)
        t=QTabWidget();self.setWidget(t)
        notes=QWidget();l=QVBoxLayout(notes);l.addWidget(QLabel('Temporary notes — discarded when Folder closes.'))
        self.note=QPlainTextEdit();l.addWidget(self.note,1);r=QHBoxLayout();l.addLayout(r)
        for name,fn in [('Copy',self.note.copy),('Paste',self.note.paste),('Clear',self.note.clear)]:
            b=QPushButton(name);b.clicked.connect(fn);r.addWidget(b)
        t.addTab(notes,'Notes')
        calc=QWidget();l=QVBoxLayout(calc);self.expr=QLineEdit();self.expr.setPlaceholderText('125 * 3 + 10');l.addWidget(self.expr);self.answer=QLabel();self.answer.setTextInteractionFlags(Qt.TextSelectableByMouse);l.addWidget(self.answer);l.addStretch()
        def update(text):
            try:self.answer.setText(str(calculate(text.replace('×','*').replace('÷','/').replace('−','-'))))
            except Exception:self.answer.setText('—')
        self.expr.textChanged.connect(update);t.addTab(calc,'Calc')
        t.addTab(QCalendarWidget(),'Calendar')
def toggle(host):
    if not hasattr(host,'scribble'):
        host.scribble=Pad(host);host.addDockWidget(Qt.RightDockWidgetArea,host.scribble);host.scribble.show()
        host.resizeDocks([host.scribble],[270],Qt.Horizontal)
    else:host.scribble.setVisible(not host.scribble.isVisible())
