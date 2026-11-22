"""Native review-first Old Build Manager for Folder."""
import threading,os,sys
from datetime import datetime
from pathlib import Path
from PySide6.QtCore import Qt,QObject,Signal,QRunnable,QThreadPool,QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QLabel,QComboBox,QLineEdit,
    QPushButton,QTreeWidget,QTreeWidgetItem,QFileDialog,QMessageBox,QHeaderView)
from send2trash import send2trash
from modules import build_cleanup as core
class Signals(QObject):
    batch=Signal(object);done=Signal(object);error=Signal(str)
class Scan(QRunnable):
    def __init__(self,roots,query,cancel):
        super().__init__();self.roots=roots;self.query=query;self.cancel=cancel;self.signals=Signals()
    def run(self):
        try:self.signals.done.emit(core.scan(self.roots,self.query,self.cancel,self.signals.batch.emit))
        except Exception as exc:self.signals.error.emit(str(exc))
class Manager(QDialog):
    def __init__(self,host):
        super().__init__(host);self.host=host;self.setWindowTitle('Old Build Manager');self.resize(1150,720)
        self.job=None;self.cancel=None;self.query='';self.rows={}
        l=QVBoxLayout(self)
        hint=QLabel('Find similar app names, installers, portable builds and stale registrations. Select only items you recognise. Installed apps and project folders are protected.');hint.setWordWrap(True);l.addWidget(hint)
        row=QHBoxLayout();l.addLayout(row);self.name=QComboBox();self.name.setEditable(True);self.name.addItems(core.APPS);row.addWidget(self.name,2)
        self.scope=QComboBox();self.scope.addItems(['Common locations','All fixed drives','Choose folder…']);row.addWidget(self.scope,1)
        self.start_button=QPushButton('Scan');self.start_button.clicked.connect(self.start);row.addWidget(self.start_button)
        self.stop_button=QPushButton('Stop');self.stop_button.setEnabled(False);self.stop_button.clicked.connect(self.stop);row.addWidget(self.stop_button)
        self.filter=QLineEdit();self.filter.setPlaceholderText('Filter results by name, path or type');self.filter.textChanged.connect(self.apply_filter);l.addWidget(self.filter)
        self.table=QTreeWidget();self.table.setHeaderLabels(['Name / select','Type','Size (file)','Modified','Location / registration','Notes']);self.table.setAlternatingRowColors(True);self.table.setRootIsDecorated(False);self.table.setSortingEnabled(True)
        self.table.header().setSectionResizeMode(QHeaderView.Interactive)
        for i,w in enumerate((235,140,90,130,370,250)):self.table.setColumnWidth(i,w)
        l.addWidget(self.table,1);self.table.itemDoubleClicked.connect(lambda *_:self.open_location())
        self.status=QLabel('Choose an application, then scan. Nothing is selected automatically.');l.addWidget(self.status)
        buttons=QHBoxLayout();l.addLayout(buttons)
        self.clear=QPushButton('Clear selection');self.clear.clicked.connect(self.clear_checks);buttons.addWidget(self.clear)
        b=QPushButton('Open location');b.clicked.connect(self.open_location);buttons.addWidget(b)
        b=QPushButton('Windows uninstall');b.clicked.connect(lambda:QDesktopServices.openUrl(QUrl('ms-settings:appsfeatures')));buttons.addWidget(b)
        b=QPushButton('Export CSV');b.clicked.connect(self.export);buttons.addWidget(b)
        self.recycle=QPushButton('Recycle selected…');self.recycle.clicked.connect(self.remove);buttons.addWidget(self.recycle)
        b=QPushButton('Close');b.clicked.connect(self.close);buttons.addWidget(b)
    def start(self):
        if self.job:return
        q=self.name.currentText().strip()
        if len(core.norm(q))<3:QMessageBox.information(self,'Search','Enter at least three characters.');return
        if self.scope.currentIndex()==2:
            path=QFileDialog.getExistingDirectory(self,'Select scan folder')
            if not path:return
            roots=[Path(path)]
        else:roots=core.default_roots() if self.scope.currentIndex()==0 else core.fixed_roots()
        self.query=q;self.table.clear();self.rows.clear();self.cancel=threading.Event()
        self.job=Scan(roots,q,self.cancel);self.job.signals.batch.connect(self.add);self.job.signals.done.connect(self.complete);self.job.signals.error.connect(self.failed)
        self.start_button.setEnabled(False);self.stop_button.setEnabled(True);self.recycle.setEnabled(False);self.status.setText('Scanning accessible locations…');QThreadPool.globalInstance().start(self.job)
    def stop(self):
        if self.cancel:self.cancel.set();self.status.setText('Stopping…')
    def add(self,rows):
        self.table.setSortingEnabled(False)
        for c in rows:
            size=f'{c.size/1048576:,.2f} MB' if c.size else '—'
            modified=datetime.fromtimestamp(c.modified).strftime('%Y-%m-%d %H:%M') if c.modified else ''
            i=QTreeWidgetItem([c.name,c.kind,size,modified,c.path,c.detail]);key=len(self.rows);self.rows[key]=c;i.setData(0,Qt.UserRole,key)
            if c.removable:i.setFlags(i.flags()|Qt.ItemIsUserCheckable);i.setCheckState(0,Qt.Unchecked)
            i.setToolTip(4,c.path);i.setToolTip(5,c.detail);self.table.addTopLevelItem(i)
        self.table.setSortingEnabled(True);self.apply_filter(self.filter.text());self.status.setText(f'{len(self.rows):,} matches found…')
    def complete(self,result):
        count,rows,partial=result;self.job=None;self.start_button.setEnabled(True);self.stop_button.setEnabled(False);self.recycle.setEnabled(True)
        self.status.setText(f'{rows:,} matches; {count:,} folders checked.'+(' Partial scan (limit or cancellation).' if partial else ' Scan completed.'))
    def failed(self,msg):
        self.complete((0,len(self.rows),True));QMessageBox.warning(self,'Scan failed',msg)
    def apply_filter(self,text):
        q=text.casefold()
        for n in range(self.table.topLevelItemCount()):
            i=self.table.topLevelItem(n);i.setHidden(not any(q in i.text(c).casefold() for c in range(6)))
    def clear_checks(self):
        for n in range(self.table.topLevelItemCount()):
            i=self.table.topLevelItem(n)
            if i.flags()&Qt.ItemIsUserCheckable:i.setCheckState(0,Qt.Unchecked)
    def selected_candidate(self):
        i=self.table.currentItem()
        return self.rows.get(i.data(0,Qt.UserRole)) if i else None
    def open_location(self):
        c=self.selected_candidate()
        if not c or not c.path:return
        p=Path(c.path)
        if p.is_absolute() and p.exists():QDesktopServices.openUrl(QUrl.fromLocalFile(str(p if p.is_dir() else p.parent)))
        else:QMessageBox.information(self,'Reference',c.path+'\n'+c.detail)
    def export(self):
        import csv
        filename,_=QFileDialog.getSaveFileName(self,'Save inventory','Old-builds.csv','CSV (*.csv)')
        if not filename:return
        try:
            with open(filename,'w',encoding='utf-8-sig',newline='') as f:
                w=csv.writer(f);w.writerow(['Name','Type','Path','Bytes','Modified','Notes'])
                for c in self.rows.values():w.writerow([c.name,c.kind,c.path,c.size,c.modified,c.detail])
        except OSError as exc:QMessageBox.warning(self,'Export',str(exc))
    def remove(self):
        if self.job:return
        chosen=[]
        for n in range(self.table.topLevelItemCount()):
            i=self.table.topLevelItem(n)
            if not i.isHidden() and i.flags()&Qt.ItemIsUserCheckable and i.checkState(0)==Qt.Checked:chosen.append((i,self.rows[i.data(0,Qt.UserRole)]))
        if not chosen:return
        paths='\n'.join(c.path for _,c in chosen[:12])
        if len(chosen)>12:paths+=f'\n…and {len(chosen)-12} more'
        if QMessageBox.question(self,'Review removal',f'Move {len(chosen)} selected visible items to the Recycle Bin? Review each folder for files you want to keep. No registry keys or installed apps are deleted.\n\n{paths}')!=QMessageBox.Yes:return
        removed=0;errors=[]
        for i,c in chosen:
            try:
                if not core.recheck(c,self.query):raise ValueError('Protected, changed, missing or not a recognised build')
                send2trash(c.path);self.table.takeTopLevelItem(self.table.indexOfTopLevelItem(i));self.rows.pop(i.data(0,Qt.UserRole),None);removed+=1
            except Exception as exc:errors.append(c.path+': '+str(exc))
        self.status.setText(f'{removed} moved to Recycle Bin; {len(errors)} skipped.')
        if errors:QMessageBox.warning(self,'Skipped items','\n'.join(errors)[:5000])
    def closeEvent(self,event):
        self.stop();super().closeEvent(event)
def open_manager(host):
    if not hasattr(host,'old_build_manager'):host.old_build_manager=Manager(host)
    host.old_build_manager.show();host.old_build_manager.raise_();host.old_build_manager.activateWindow()
