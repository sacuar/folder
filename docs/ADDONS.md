# Add-ons available in Folder 0.7.0

Open **Add-ons → Manage plugins** (also available from the toolbar).

| Provider | Availability |
|---|---|
| LibVLC media | Bundled in Windows installer; MP4, MKV, MOV, WebM and common audio |
| Raster and SVG preview | Built in |
| PDF preview | Built in; page thumbnails and zoom |
| DOCX preview | Built in; text and tables |
| ZIP/TAR extraction | Built in |
| Thumbnail engine | Built in |
| Everything search | Built-in integration; requires external Everything and ES |
| Quick Photo Viewer | External integration; install separately or locate executable |
| Trusted Python extensions | Local .py files in the add-on directory; explicit loading |

Providers are separate source modules. Independent binary plug-in updates, signed add-on catalog, legacy DOC COM support and RAR/7z extraction are future work. No untrusted code is downloaded automatically.

## 0.6.0 additions
STL mesh preview and FFmpeg video thumbnail generation are built-in providers. SVG preview and thumbnails remain built in. These are not Windows Explorer COM shell extensions.
