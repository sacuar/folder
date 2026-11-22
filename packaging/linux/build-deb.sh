#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
VERSION="$(python3 -c 'from version import VERSION;print(VERSION)')"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$STAGE/opt/folder" "$STAGE/DEBIAN" "$STAGE/usr/share/applications" "$STAGE/usr/share/icons/hicolor/scalable/apps" installer/linux
cp -a dist/Folder/. "$STAGE/opt/folder/"
cp assets/folder.svg "$STAGE/usr/share/icons/hicolor/scalable/apps/folder-explorer.svg"
cat > "$STAGE/usr/share/applications/folder-explorer.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Folder
Comment=Tabbed file manager with previews
Exec=/opt/folder/Folder %f
Icon=folder-explorer
Terminal=false
Categories=System;FileManager;
MimeType=inode/directory;
StartupNotify=true
EOF
cat > "$STAGE/DEBIAN/control" <<EOF
Package: folder-explorer
Version: $VERSION
Section: utils
Priority: optional
Architecture: amd64
Maintainer: SACUAR Tools <noreply@github.com>
Depends: libgl1, libegl1, libxkbcommon0, libxcb-cursor0, libdbus-1-3, libvlc5, vlc-plugin-base
Description: Folder file manager for Ubuntu
 Tabbed directory browsing, file previews and optional local add-ons.
EOF
OUTPUT="installer/linux/Folder-${VERSION}-ubuntu24.04-amd64.deb"
dpkg-deb --build --root-owner-group "$STAGE" "$OUTPUT"
sha256sum "$OUTPUT" > "$OUTPUT.sha256"
dpkg-deb --info "$OUTPUT"
