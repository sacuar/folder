# Folder on Ubuntu 24.04 x64

This Linux port provides Folder's Qt-based tabs, browsing, file previews, local file operations and toolbar preferences, with an XDG desktop entry. It **does not replace Nautilus**, the GNOME shell or Ubuntu default file handlers.

## Install

Download the `Folder-Ubuntu-24.04-amd64` artifact from the successful [Ubuntu build workflow](https://github.com/sacuar/folder/actions/workflows/ubuntu-build.yml), unzip, and run:

```bash
sha256sum -c Folder-0.7.9-ubuntu24.04-amd64.deb.sha256
sudo apt install ./Folder-0.7.9-ubuntu24.04-amd64.deb
```

Find **Folder** in the application launcher. Existing source-build scripts remain available:

```bash
sudo apt install python3-venv libegl1 libgl1 libxcb-cursor0 libxkbcommon-x11-0 libvlc5 vlc-plugin-base
bash run-linux.sh
```

The Ubuntu port replaces Windows Everything/ES search with an asynchronous, bounded directory scan and uses a native file properties summary. Windows-only settings, installer maintenance, and Windows registry integration are not used. The Linux desktop launcher is optional and does not change the default file manager.

The Ubuntu bundle uses the system LibVLC runtime; video embedding may depend on X11/Wayland compatibility. Some system thumbnails and previews depend on installed media codecs. Automated smoke tests do not replace hands-on verification for drag and drop, file permissions, media, and filesystem integration.
