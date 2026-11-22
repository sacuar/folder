"""Shared desktop presentation; no filesystem operations."""
from pathlib import Path
from modules.drives import drive_kind
from modules.icons import icon
from PySide6.QtCore import Qt, QDir, QFileInfo, QStandardPaths, QSize
from PySide6.QtWidgets import QFileIconProvider, QListWidgetItem, QListView, QStyle

def configure_gallery(view):
    view.setMovement(QListView.Static)
    view.setUniformItemSizes(True)
    view.setSpacing(2)
    view.setWordWrap(True)

def populate_places(side):
    side.setIconSize(QSize(16,16))
    icons=QFileIconProvider()
    locations=[('Home',str(Path.home()))]
    for label,kind in [('Desktop',QStandardPaths.DesktopLocation),('Downloads',QStandardPaths.DownloadLocation),('Documents',QStandardPaths.DocumentsLocation),('Pictures',QStandardPaths.PicturesLocation),('Music',QStandardPaths.MusicLocation),('Videos',QStandardPaths.MoviesLocation)]:
        locations.append((label,QStandardPaths.writableLocation(kind)))
    locations.extend((d.absolutePath()+'  '+drive_kind(d.absolutePath()),d.absolutePath()) for d in QDir.drives())
    for label,path in locations:
        if not path:continue
        kind={'Home':'home','Desktop':'desktop','Downloads':'download','Documents':'document','Pictures':'image','Music':'music','Videos':'video'}.get(label,'drive')
        item=QListWidgetItem(icon(kind),label)
        item.setData(Qt.UserRole,path)
        item.setToolTip(path)
        side.addItem(item)

def configure_commands(toolbar,labels=False):
    toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon if labels else Qt.ToolButtonIconOnly)
    toolbar.setIconSize(QSize(19,19))
    kinds={'New tab':'plus','Split':'split','New folder':'folder','Copy':'copy','Cut':'cut','Paste':'paste','Rename':'rename','Recycle':'trash','Appearance':'settings','Add-ons':'plugins','Folder options':'options','Everything search':'search','Web search':'web','Clip folder':'paperclip'}
    for action in toolbar.actions():
        if action.text() in kinds:action.setIcon(icon(kinds[action.text()])); action.setToolTip(action.text())

def apply_workspace_theme(host,prefs,windows):
    dark=prefs.get('theme','Dark')=='Dark'
    accent='#397aca' if windows else '#c64600'
    bg,panel,fg,edge,hover=('#202124','#292b30','#f0f0f2','#3b3d43','#353942') if dark else ('#f4f5f7','#ffffff','#20242a','#dce0e4','#e8edf4')
    host.setStyleSheet(f"""
    QWidget {{ background:{bg}; color:{fg}; font-family:'Segoe UI'; font-size:12px; }}
    QToolBar {{ border:0; spacing:5px; padding:6px; }}
    QToolButton,QPushButton,QComboBox {{ padding:5px 8px; border:1px solid transparent; border-radius:6px; }}
    QToolButton:hover,QPushButton:hover,QComboBox:hover {{ background:{hover}; }}
    QLineEdit {{ padding:8px; background:{panel}; border:1px solid {edge}; border-radius:7px; }}
    QLineEdit:focus {{ border:1px solid {accent}; }}
    QTreeView,QListView,QListWidget,QPlainTextEdit {{ background:{panel}; border:0; border-radius:5px; outline:0; }}
    QTreeView::item,QListWidget::item {{ padding:3px; min-height:19px; border-radius:4px; }}
    QTreeView::item:hover,QListView::item:hover,QListWidget::item:hover {{ background:{hover}; }}
    QTreeView::item:selected,QListView::item:selected,QListWidget::item:selected {{ background:{hover}; color:{fg}; border:1px solid {accent}; border-radius:5px; }} QToolButton:checked {{ background:{accent}; color:white; }}
    QTabWidget::pane {{ border:0; }}
    QTabBar::tab {{ padding:7px 12px; margin:2px; border-radius:7px; background:{bg}; }}
    QTabBar::tab:selected {{ background:{panel}; border:1px solid {edge}; }}
    QHeaderView::section {{ background:{panel}; color:{fg}; border:0; padding:8px; }}
    QSplitter::handle {{ background:{edge}; border:1px solid {bg}; border-radius:3px; width:7px; height:7px; }} QSplitter::handle:hover {{ background:{accent}; }} QScrollBar:vertical {{ background:transparent; width:9px; margin:2px; }} QScrollBar::handle:vertical {{ background:{edge}; border-radius:4px; min-height:28px; }} QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical {{ height:0; }}
    QMenu {{ background:{panel}; border:1px solid {edge}; padding:5px; }}
    QMenu::item {{ padding:7px 20px; }}
    QMenu::item:selected {{ background:{accent}; color:white; }}
    QStatusBar {{ border-top:1px solid {edge}; }}
    """)
