"""Exercise toolbar configuration against a running Qt workspace."""
import sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
import explorer
from modules.toolbar_layout import ToolbarEditor,order_for,IDS
app=QApplication([])
with tempfile.TemporaryDirectory() as tmp:
    explorer.CONFIG=Path(tmp)/'prefs.json'
    explorer.settings={'fetch_favicons':False,'auto_update_check':False}
    host=explorer.Explorer();host.show();app.processEvents()
    assert [a.text() for a in host.commands.actions()][:2]==['New folder','New file']
    assert host.tab_plus.isVisible()
    host.prefs.update(toolbar_order=['copy','new_file','space','new_tab'],toolbar_hidden=['cut'],new_tab_position='toolbar',toolbar_position='bottom')
    host.apply_options();app.processEvents()
    assert host.commands.actions()[0]==host.command_actions['copy']
    assert host.command_actions['cut'] not in host.commands.actions()
    assert host.command_actions['new_tab'] in host.commands.actions()
    assert host.command_actions['menus'] in host.commands.actions()
    assert host.toolBarArea(host.commands)==Qt.BottomToolBarArea
    assert host.tab_plus.isHidden()
    editor=ToolbarEditor(host.prefs)
    assert editor.values()['toolbar_order']==order_for(host.prefs)
    assert 'cut' in editor.values()['toolbar_hidden']
    editor.load({})
    host.prefs.update(editor.values());host.apply_options()
    assert host.commands.actions()[0]==host.command_actions['new_folder']
    assert host.toolBarArea(host.commands)==Qt.TopToolBarArea
    assert len(order_for({'toolbar_order':['copy','copy','unknown']}))==len(IDS)
    host.close()
print('Toolbar layout tests passed')
