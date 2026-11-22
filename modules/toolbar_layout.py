"""Customisable command toolbar; preferences contain stable command IDs only."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QSizePolicy, QToolButton, QVBoxLayout, QWidget)

COMMANDS = (
    ('new_folder','New folder'), ('new_file','New file'),
    ('cut','Cut'), ('copy','Copy'), ('paste','Paste'), ('rename','Rename'),
    ('recycle','Recycle'), ('split','Split view'), ('space','Flexible space'),
    ('everything','Everything search'), ('web','Web search'),
    ('appearance','Appearance'), ('addons','Add-ons'), ('options','Folder options'),
    ('new_tab','New tab'), ('menus','Application menus'),
)
IDS = [key for key, _ in COMMANDS]

def order_for(prefs):
    raw = prefs.get('toolbar_order', [])
    ordered = []
    if isinstance(raw, list):
        for key in raw:
            if key in IDS and key not in ordered:
                ordered.append(key)
    return ordered + [key for key in IDS if key not in ordered]

def hidden_for(prefs):
    raw = prefs.get('toolbar_hidden')
    if isinstance(raw, list):
        return {key for key in IDS if key in raw and key not in ('menus','new_tab')}
    return {key for key, pref in [('everything','show_everything'),('web','show_web_search')]
            if not prefs.get(pref,True)}

class ToolbarEditor(QWidget):
    def __init__(self,prefs,parent=None):
        super().__init__(parent)
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0)
        hint=QLabel('Drag commands into any order. Uncheck commands to hide them. Move Flexible space to push the following commands to the right.')
        hint.setWordWrap(True);layout.addWidget(hint)
        self.items=QListWidget();self.items.setDragDropMode(QAbstractItemView.InternalMove)
        self.items.setDefaultDropAction(Qt.MoveAction);self.items.setAlternatingRowColors(True)
        layout.addWidget(self.items,1)
        layout.addWidget(QLabel('New tab button'))
        self.tab_position=QComboBox()
        self.tab_position.addItem('Right of tabs (browser style)','tabs')
        self.tab_position.addItem('Custom position in command toolbar','toolbar')
        self.tab_position.addItem('Hidden (Ctrl+T still works)','hidden')
        layout.addWidget(self.tab_position)
        layout.addWidget(QLabel('Command toolbar position'))
        self.position=QComboBox()
        self.position.addItem('Top','top');self.position.addItem('Bottom','bottom')
        layout.addWidget(self.position)
        reset=QPushButton('Restore default toolbar layout')
        reset.clicked.connect(lambda:self.load({}));layout.addWidget(reset)
        self.load(prefs)
    def load(self,prefs):
        self.items.clear();hidden=hidden_for(prefs)
        for key in order_for(prefs):
            title=dict(COMMANDS)[key]
            if key=='new_tab':title+=' (position below)'
            if key=='menus':title+=' (always available if menu bar hidden)'
            item=QListWidgetItem(title);item.setData(Qt.UserRole,key)
            item.setFlags(Qt.ItemIsEnabled|Qt.ItemIsSelectable|Qt.ItemIsDragEnabled)
            if key not in ('new_tab','menus'):
                item.setFlags(item.flags()|Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Unchecked if key in hidden else Qt.Checked)
            self.items.addItem(item)
        self.tab_position.setCurrentIndex(max(0,self.tab_position.findData(prefs.get('new_tab_position','tabs'))))
        self.position.setCurrentIndex(max(0,self.position.findData(prefs.get('toolbar_position','top'))))
    def values(self):
        rows=[self.items.item(i) for i in range(self.items.count())]
        hidden=[i.data(Qt.UserRole) for i in rows if i.flags()&Qt.ItemIsUserCheckable and i.checkState()==Qt.Unchecked]
        return {'toolbar_order':[i.data(Qt.UserRole) for i in rows],
                'toolbar_hidden':hidden,'new_tab_position':self.tab_position.currentData(),
                'toolbar_position':self.position.currentData(),
                'show_everything':'everything' not in hidden,'show_web_search':'web' not in hidden}

def apply_layout(host):
    toolbar=host.commands
    prefs=host.prefs
    actions=host.command_actions
    # Reuse actions and their shortcut registrations, never recreate or duplicate them.
    for action in list(toolbar.actions()):
        toolbar.removeAction(action)
    hidden=hidden_for(prefs)
    tab_pos=prefs.get('new_tab_position','tabs')
    for key in order_for(prefs):
        if key not in actions:continue
        if key in hidden or (key=='new_tab' and tab_pos!='toolbar') or (key=='menus' and prefs.get('show_menu_bar',False)):
            continue
        action=actions[key]
        toolbar.addAction(action)
        if key in ('new_file','menus'):
            widget=toolbar.widgetForAction(action)
            if isinstance(widget,QToolButton):widget.setPopupMode(QToolButton.InstantPopup)
    host.tab_plus.setVisible(tab_pos not in ('toolbar','hidden'))
    desired=Qt.BottomToolBarArea if prefs.get('toolbar_position')=='bottom' else Qt.TopToolBarArea
    if host.toolBarArea(toolbar)!=desired:host.addToolBar(desired,toolbar)
