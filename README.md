<div align="center">

<img src="assets/folder.svg" width="96" alt="Folder app icon" />

# Folder

**A better way to explore your files.**

![Windows](https://img.shields.io/badge/Windows-10%20%7C%2011-2563eb) ![License](https://img.shields.io/badge/license-MIT-blue) ![Release](https://img.shields.io/github/v/release/sacuar/folder)

[Download Windows installer](https://github.com/sacuar/folder/releases) · [Add-ons](docs/ADDONS.md) · [Changes](CHANGELOG.md)

</div>

## Screenshots
Actual running application captures (demo files; Windows CI). These images follow the latest successful release.

### Workspace

![Folder workspace — tabs, sidebar, thumbnails and preview](https://github.com/sacuar/folder/releases/latest/download/workspace.png)

### Add-on manager

![Folder built-in providers and add-ons](https://github.com/sacuar/folder/releases/latest/download/addons.png)

[View release assets](https://github.com/sacuar/folder/releases/latest).

## Available add-ons and built-in providers
| Provider | Availability |
|---|---|
| LibVLC video and audio | Bundled with Windows installer |
| PNG, JPG, SVG preview | Built in |
| PDF preview and thumbnails | Built in |
| DOCX text and tables | Built in |
| ZIP/TAR extraction | Built in |
| Thumbnail engine | Built in |
| STL preview and video thumbnails | Built in |
| Everything search | Built-in bridge; official Everything + ES required |
| Quick Photo Viewer | Separate installation, detected automatically |
| Trusted Python extensions | Local add-on directory |

The toolbar **Add-ons** button opens the plugin manager. Built-in providers are modular source components, not independently updatable binaries.

## Install
Download the x64 Setup EXE from Releases once the build succeeds. Python is not required. Unsigned alpha installers may trigger SmartScreen. Use Help → Check for updates to see release notes and install verified updates.

## Development
Python 3.12, PySide6, PyInstaller, Inno Setup 6. Use BUILD_INSTALLER.bat. Windows first; Linux remains experimental. See CONTRIBUTING.md, SECURITY.md and THIRD_PARTY_NOTICES.md. MIT license for Folder; dependencies have separate licenses.

## Roadmap
Native COM preview handlers, DOC rendering, video thumbnails, RAR/7z extraction, isolated and independently updated extensions, optional reversible default folder handler, and Microsoft Store packaging. No affiliation with Files Community.

## 0.6.0 Windows workspace
Folder Options includes thumbnail controls, hidden files, click mode, configurable New and context menus, sidebar shortcuts, cache reset and remembered applications. STL preview and video frame thumbnail generation are separate built-in providers. Cloud/email entries are browser bookmarks or user-selected local sync folders, not account connectors. Safe removal opens the Windows hardware dialog. Windows default apps remain user-controlled. Installer supports optional UAC elevation; Folder normally runs unprivileged. Native shell extensions are not registered by this release.

## 0.7.0 workspace
Responsive image/SVG previews, clipped folders and websites, cached website favicons, individually hideable cloud/email shortcuts, simplified appearance, compact Everything search, and Tools for file counts, drive usage, duplicate reports, cache clearing and Windows settings. Screenshot capture is removed from the active interface. Windows runtime verification is required.

## 0.7.1 compact search workspace
Icon-only toolbar and three-dot menu by default; restore labels and menus in Folder Options. View sizes and preview buttons use icons. Clip/Unclip is available in the folder tree and address toolbar. Bundled portable Everything and ES run on demand; full NTFS indexing may require administrator-approved Everything service. Wikipedia article excerpts appear inside a closable dialog; Google, ChatGPT and DeepSeek open externally. Yahoo Mail and website favicons use local cache. No private files are sent to web search.
