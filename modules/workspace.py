"""Shared desktop presentation; no filesystem operations."""
from pathlib import Path
from PySide6.QtCore import Qt, QDir, QFileInfo, QStandardPaths
from PySide6.QtWidgets import QFileIconProvider, QListWidgetItem, QListView, QStyle

def configure_gallery(view):
    view.setMovement(QListView.Static)
    view.setUniformItemSizes(True)
    view.setSpacing(4)
    view.setWordWrap(True)

def populate_places(side):
    icons=QFileIconProvider()
    locations=[('Home',str(Path.home()))]
    for label,kind in [('Desktop',QStandardPaths.DesktopLocation),('Downloads',QStandardPaths.DownloadLocation),('Documents',QStandardPaths.DocumentsLocation),('Pictures',QStandardPaths.PicturesLocation),('Music',QStandardPaths.MusicLocation),('Videos',QStandardPaths.MoviesLocation)]:
        locations.append((label,QStandardPaths.writableLocation(kind)))
    locations.extend((d.absolutePath(),d.absolutePath()) for d in QDir.drives())
    for label,path in locations:
        if not path:continue
        item=QListWidgetItem(icons.icon(QFileInfo(path)),label)
        item.setData(Qt.UserRole,path)
        item.setToolTip(path)
        side.addItem(item)

def configure_commands(toolbar):
    toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
    icons={'New tab':QStyle.SP_FileDialogNewFolder,'New folder':QStyle.SP_FileDialogNewFolder,'Recycle':QStyle.SP_TrashIcon,'Appearance':QStyle.SP_FileDialogDetailedView,'Split':QStyle.SP_FileDialogListView}
    for action in toolbar.actions():
        if action.text() in icons:action.setIcon(toolbar.style().standardIcon(icons[action.text()]))

def apply_workspace_theme(host,prefs,windows):
    dark=prefs.get('theme','Dark')=='Dark'
    accent='#397aca' if windows else '#c64600'
    bg,panel,fg,edge,hover=('#202124','#292b30','#f0f0f2','#3b3d43','#353942') if dark else ('#f4f5f7','#ffffff','#20242a','#dce0e4','#e8edf4')
    host.setStyleSheet(f"""
    QWidget {{ background:{bg}; color:{fg}; font-size:13px; }}
    QToolBar {{ border:0; spacing:5px; padding:6px; }}
    QToolButton,QPushButton,QComboBox {{ padding:7px 10px; border:1px solid {edge}; border-radius:6px; }}
    QToolButton:hover,QPushButton:hover,QComboBox:hover {{ background:{hover}; }}
    QLineEdit {{ padding:8px; background:{panel}; border:1px solid {edge}; border-radius:7px; }}
    QLineEdit:focus {{ border:1px solid {accent}; }}
    QTreeView,QListView,QListWidget,QPlainTextEdit {{ background:{panel}; border:1px solid {edge}; border-radius:7px; outline:0; }}
    QTreeView::item,QListWidget::item {{ padding:5px; min-height:22px; border-radius:4px; }}
    QTreeView::item:hover,QListView::item:hover,QListWidget::item:hover {{ background:{hover}; }}
    QTreeView::item:selected,QListView::item:selected,QListWidget::item:selected,QToolButton:checked {{ background:{accent}; color:white; }}
    QTabWidget::pane {{ border:0; }}
    QTabBar::tab {{ padding:10px 16px; margin:2px; border-radius:7px; background:{bg}; }}
    QTabBar::tab:selected {{ background:{panel}; border:1px solid {edge}; }}
    QHeaderView::section {{ background:{panel}; color:{fg}; border:0; padding:8px; }}
    QSplitter::handle {{ background:{bg}; width:5px; height:5px; }}
    QMenu {{ background:{panel}; border:1px solid {edge}; padding:5px; }}
    QMenu::item {{ padding:7px 20px; }}
    QMenu::item:selected {{ background:{accent}; color:white; }}
    QStatusBar {{ border-top:1px solid {edge}; }}
    """)
