# Folder
**A better way to explore your files.**

Open-source Windows and Linux file manager. Early alpha, built with Python and Qt.

## Getting started
Install Python 3.12 on Windows, run RUN.bat for development or BUILD.bat for a portable executable in dist/Folder. No administrator rights required.

## Features
Tabs, dual panes, directory tree, image thumbnails, themes and folder wallpapers. Built-in preview for raster images, SVG, PDF, DOCX text, media (muted autoplay), folders, text and ZIP/TAR archives. Extract ZIP/TAR into a new directory. Media format support depends on Qt codecs. Context-menu registration is optional and reversible; Windows Explorer remains the system shell.

## Architecture
`explorer.py` is the application host; `modules/preview.py`, `modules/thumbnails.py` and `modules/archives.py` are independently maintained built-in components. `addons.py` loads explicitly trusted Python extensions. `integration.py` owns registry changes. Modules are source-level replaceable, not isolated processes. Restart after updates. Third-party add-ons execute with your privileges.

## Development goals
- Native Windows IPreviewHandler and thumbnail-provider bridge, including installed legacy DOC handlers.
- PDF and video gallery thumbnails, richer Word rendering, 7z/RAR extraction.
- Versioned provider API and isolated preview workers, signed add-on releases.
- Reversible opt-in default folder handler, installer and uninstall recovery.
- Accessibility, performance and automated Windows integration testing.

Contributions welcome: see CONTRIBUTING.md and SECURITY.md. MIT license. No affiliation with Files Community.

## Cross-platform edition (0.4 alpha)
Windows and Ubuntu share the application and built-in modules. OS-specific integration is routed through `platform_adapters/`. Windows uses a blue accent and Ubuntu uses a Yaru-inspired orange accent, with the same layout and independent dark/light themes. Windows: RUN.bat / BUILD.bat. Ubuntu 24.04: bash run-linux.sh / bash build-linux.sh (see packaging/linux). CI builds both platforms separately. Microsoft Store onboarding is documented in packaging/windows/STORE.md; no signed MSIX or Store listing is included. Native COM preview handlers remain Windows-only planned functionality; portable Qt preview remains the baseline on both platforms. This is a source release, not a certified or runtime-tested binary.

## Windows-first release 0.5.0 Alpha

Download the installer from [Releases](https://github.com/sacuar/folder/releases) when published. No Python is needed for the installed application. Developers can run BUILD_INSTALLER.bat with Python 3.12 and Inno Setup 6. The GitHub Actions Windows installer workflow builds, smoke-tests and uploads an installer artifact; after merging to main, manually run that workflow with publish enabled to publish the release. Increment version.py and update CHANGELOG.md for subsequent releases. The Help menu checks GitHub for newer releases and shows release notes; installed copies verify SHA-256 before launching an approved update. Store builds disable the independent updater. Unsigned alpha installers may trigger SmartScreen; review licensing and signing before wider distribution. Ubuntu remains source-only for now.
