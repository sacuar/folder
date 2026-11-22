"""In-app Wikipedia search, with explicit browser alternatives for other providers."""
import json,html
from urllib.parse import urlencode,quote_plus,quote
from PySide6.QtCore import QUrl,QTimer
from PySide6.QtNetwork import QNetworkAccessManager,QNetworkRequest
from PySide6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QLineEdit,QComboBox,QPushButton,QTextBrowser,QLabel
from modules.web_links import open_link
class WebSearch(QDialog):
    def __init__(self,host):
        super().__init__(host);self.setWindowTitle('Web search');self.resize(680,500);self.net=QNetworkAccessManager(self);self.reply=None
        l=QVBoxLayout(self);row=QHBoxLayout();l.addLayout(row)
        self.provider=QComboBox();self.provider.addItems(['Wikipedia (in Folder)','Google (browser)','ChatGPT (browser)','DeepSeek (browser)']);row.addWidget(self.provider)
        self.query=QLineEdit();self.query.setPlaceholderText('Search the web…');self.query.setMaxLength(300);row.addWidget(self.query,1)
        b=QPushButton('Search');b.clicked.connect(self.search);row.addWidget(b);self.query.returnPressed.connect(self.search)
        close=QPushButton('×');close.setToolTip('Close');close.clicked.connect(self.reject);row.addWidget(close)
        self.status=QLabel('Wikipedia searches return article excerpts here. Queries are sent to the selected service.');self.status.setWordWrap(True);l.addWidget(self.status)
        self.results=QTextBrowser();self.results.setOpenLinks(False);self.results.anchorClicked.connect(lambda u:open_link(u.toString()));l.addWidget(self.results,1)
        self.query.setFocus()
    def search(self):
        q=self.query.text().strip()
        if not q:return
        if self.reply:self.reply.abort();self.reply=None
        provider=self.provider.currentIndex()
        if provider:
            if provider==3:
                from PySide6.QtWidgets import QApplication
                QApplication.clipboard().setText(q);self.status.setText('Query copied; paste it into DeepSeek.')
                open_link('https://chat.deepseek.com/')
            else:open_link(('https://www.google.com/search?q=' if provider==1 else 'https://chatgpt.com/?q=')+quote_plus(q))
            return
        url='https://en.wikipedia.org/w/api.php?'+urlencode({'action':'query','list':'search','srsearch':q,'srlimit':7,'format':'json','utf8':1})
        req=QNetworkRequest(QUrl(url));req.setRawHeader(b'User-Agent',b'FolderExplorer/0.7.1 (https://github.com/sacuar/folder)');req.setTransferTimeout(10000)
        r=self.net.get(req);self.reply=r;self.results.clear();self.status.setText('Searching Wikipedia…')
        r.downloadProgress.connect(lambda received,total:r.abort() if received>500000 or total>500000 else None)
        def finished():
            try:
                if self.reply!=r:return
                self.reply=None
                if r.error():raise RuntimeError('Search unavailable. Try again.')
                data=json.loads(bytes(r.readAll()).decode('utf-8'));items=data.get('query',{}).get('search',[])
                from html.parser import HTMLParser
                class Plain(HTMLParser):
                    def __init__(self):super().__init__();self.parts=[]
                    def handle_data(self,s):self.parts.append(s)
                sections=[]
                for item in items:
                    p=Plain();p.feed(item.get('snippet',''));title=item['title'];url='https://en.wikipedia.org/wiki/'+quote(title.replace(' ','_'),safe='')
                    sections.append('<h3><a href="'+html.escape(url,quote=True)+'">'+html.escape(title)+'</a></h3><p>'+html.escape(''.join(p.parts))+'</p>')
                self.results.setHtml(''.join(sections) or '<p>No results.</p>');self.status.setText('Wikipedia • '+str(len(items))+' results • Article links open in browser')
            except Exception as exc:self.status.setText(str(exc))
            finally:r.deleteLater()
        r.finished.connect(finished)
def show_web(host):
    d=WebSearch(host);d.exec()
