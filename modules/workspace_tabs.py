"""Compact workspace tabs: no redundant single-folder tab, adjacent New tab button."""
from PySide6.QtCore import Signal,QSignalBlocker,Qt
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QTabBar,QStackedWidget,QSizePolicy,QToolButton
from modules.icons import icon

class WorkspaceTabs(QWidget):
    currentChanged=Signal(int)
    tabCloseRequested=Signal(int)

    def __init__(self,parent=None):
        super().__init__(parent)
        self._pages={};self._serial=0;self._plus_enabled=True
        outer=QVBoxLayout(self);outer.setContentsMargins(0,0,0,0);outer.setSpacing(0)
        self.header=QWidget(self);row=QHBoxLayout(self.header)
        row.setContentsMargins(3,0,3,0);row.setSpacing(3)
        self.bar=QTabBar(self.header);self.bar.setExpanding(False);self.bar.setMovable(True)
        self.bar.setTabsClosable(True);self.bar.setUsesScrollButtons(True)
        self.bar.setElideMode(Qt.ElideRight)
        self.bar.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Fixed)
        row.addWidget(self.bar)
        self.plus=QToolButton(self.header);self.plus.setIcon(icon('plus'))
        self.plus.setToolTip('New tab (Ctrl+T)');self.plus.setAccessibleName('New tab')
        self.plus.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
        row.addWidget(self.plus);row.addStretch(1)
        outer.addWidget(self.header)
        self.stack=QStackedWidget(self);outer.addWidget(self.stack,1)
        self.bar.currentChanged.connect(self._sync)
        self.bar.tabMoved.connect(lambda *_:self._sync(self.bar.currentIndex()))
        self.bar.tabCloseRequested.connect(self.tabCloseRequested.emit)
        self._refresh_header()

    def tabBar(self):return self.bar
    def count(self):return self.bar.count()
    def currentIndex(self):return self.bar.currentIndex()
    def widget(self,index):
        return self._pages.get(self.bar.tabData(index)) if 0<=index<self.count() else None
    def currentWidget(self):return self.widget(self.currentIndex())
    def setTabText(self,index,text):
        if 0<=index<self.count():self.bar.setTabText(index,text)
    def setCurrentIndex(self,index):
        if 0<=index<self.count():self.bar.setCurrentIndex(index)
    def setCurrentWidget(self,page):
        for i in range(self.count()):
            if self.widget(i) is page:self.setCurrentIndex(i);return

    def addTab(self,page,title):
        self._serial+=1;key=self._serial;self._pages[key]=page
        with QSignalBlocker(self.bar):
            i=self.bar.addTab(title);self.bar.setTabData(i,key)
            self.stack.addWidget(page)
        self._refresh_header();self._sync(self.currentIndex())
        return i

    def removeTab(self,index):
        page=self.widget(index)
        if page is None:return
        key=self.bar.tabData(index)
        with QSignalBlocker(self.bar):
            self.bar.removeTab(index);self.stack.removeWidget(page);del self._pages[key]
        self._refresh_header();self._sync(self.currentIndex())

    def set_plus_visible(self,enabled):
        self._plus_enabled=bool(enabled);self._refresh_header()

    def _refresh_header(self):
        multiple=self.count()>1
        self.bar.setVisible(multiple)
        self.plus.setVisible(self._plus_enabled)
        self.header.setVisible(multiple or self._plus_enabled)

    def _sync(self,index):
        page=self.widget(index)
        if page is not None:self.stack.setCurrentWidget(page)
        self.currentChanged.emit(index)
