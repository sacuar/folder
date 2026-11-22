# 0.7.7
- Route QPV image launches to complete installed packages rather than obsolete remembered build paths.
- Internal image viewer fallback instead of broken Windows image associations; image viewer settings and targeted reset.

# 0.7.6
- Opt-in GitHub plugin catalogue, pinned integrity checks, 3MF preview, storage and conversion tools.

# Changelog

## 0.7.5
- Native Old Build Manager with similar-name discovery, selectable candidates, protected locations, registry reports and CSV export.
- Background scans with cancellation, explicit Recycle Bin confirmation and path revalidation.


## 0.7.4
- Repair malformed maintenance PowerShell script; preserve review-only cleanup protections.
- Add Windows PowerShell syntax check and synthetic scan test before packaging.
- Report maintenance exit errors instead of silently closing.


## 0.7.3 — Customisable toolbar
- New folder and New file commands first, with configured file-type menu.
- Browser-style + button at the right of the tab strip; optionally move into the command toolbar or hide.
- Drag-to-reorder toolbar editor, per-command visibility, flexible spacer, top/bottom placement, independent menu and button labels, persistent settings and reset.
- Preserve shortcuts and an accessible application menu when buttons are hidden.
- Add offscreen layout/preview smoke checks and capture the toolbar settings page.


## 0.7.2
- Installer maintenance page and Tools entry (review-first old build discovery).
- Debounce preview loading, stop pending previews when navigating, skip thumbnails in Details mode, improve thumbnail LRU cache.
- Larger, labelled application screenshots.
- Treat repeated release builds as no-op publication rather than failure.


## 0.7.1
- Compact icon toolbar, view-size controls and optional full menus / labels.
- Clip/Unclip from sidebar folder tree and active folder toolbar.
- Bundled portable Everything with index controls (Windows; service may require UAC).
- Wikipedia in-app text results; browser alternatives for other providers.
- Yahoo Mail favicon and organized Folder Options.


## 0.7.0 — Workspace polish
- Aspect-fit image and SVG previews.
- Clip/unclip folders and bookmarks, hide/restore cloud and mail shortcuts, cached favicons.
- Compact Everything integration; external engine and ES required.
- Tools menu: installed apps/uninstall, Windows Update, cache reset, file counts, drive use and read-only duplicate reports.
- Simplified appearance; decorative backgrounds suspended and screenshot command removed.


## 0.6.1 — Windows branding and screenshots
- Original gold folder icon with blue slash-circle and mint accent.
- Embed Windows EXE icons in both portable and installer builds, including CI.
- Branded installer welcome panel and shortcut icons.
- Screenshot add-on: window or selected display, delay, PNG/JPEG export.
- Hide screenshot toolbar button in Folder Options.
- README embeds real release screenshots; automatic capture includes Folder Options.


## 0.6.0 — Folder Options and extensibility
- Configurable new-file templates and context menu choices.
- STL preview, sampled mesh thumbnails and FFmpeg video frame thumbnails (on by default).
- Remembered Open with / Play with application choices.
- Cloud storage, mail and web search shortcuts; optional local sync folders.
- Drive type labels and Windows safe-removal dialog.
- Rounded splitters and scrollbars, multicolour application and installer icon.
- Optional elevated installation, settings reset and thumbnail cache clearing.
- Native Windows shell extensions and system-wide default folder replacement remain pending.


## 0.5.1 — Windows media and visual polish
- Embedded LibVLC provider, muted autoplay, looping, seek and volume.
- Bundle official VLC runtime and codecs in Windows setup.
- Original refined vector icons, smaller folder tiles and compact toolbar.
- Visible Add-ons button and provider availability information.
- Prefer separately installed Quick Photo Viewer for opening images.
- Capture real workspace and add-on manager screenshots during Windows release build.
- Windows runtime and playback require validation; independent plugin updates remain planned.


## 0.5.0 — Alpha (Windows first)
- Thumbnail-first workspace with small, medium and large thumbnails plus Details mode.
- Folder tree synchronisation, native Places icons, status bar and improved active pane.
- Toggleable preview panel; SVG and first-page PDF thumbnails.
- PDF zoom, larger image previews, DOCX table text, muted video autoplay, seek and volume.
- Per-user Windows installer and uninstall support; no Python installation required for end users.
- Optional automatic update checks, release notes, download progress and SHA-256 validation.
- Manual check for updates and About dialog.
- Windows Explorer remains the default system shell. Store edition and Linux packaging will be addressed separately.
- Alpha limitations: native COM/DOC previews, RAR/7z, video thumbnails and isolated add-ons not yet implemented.
