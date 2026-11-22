param([string]$Destination = "vendor/vlc")
$ErrorActionPreference = 'Stop'
$version = '3.0.24'
$name = "vlc-$version-win64.zip"
$base = "https://download.videolan.org/pub/videolan/vlc/$version/win64"
$tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("folder-vlc-" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $tmp | Out-Null
try {
  $zip = Join-Path $tmp $name
  Invoke-WebRequest "$base/$name" -OutFile $zip
  $checksum = (Invoke-WebRequest "$base/$name.sha256").Content
  if ($checksum -is [byte[]]) { $checksum = [Text.Encoding]::UTF8.GetString($checksum) }
  $expected = [regex]::Match([string]$checksum,'[0-9a-fA-F]{64}').Value
  if (!$expected -or (Get-FileHash $zip -Algorithm SHA256).Hash -ine $expected) { throw 'VLC checksum mismatch' }
  Expand-Archive $zip -DestinationPath $tmp
  $source = Get-ChildItem $tmp -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'libvlc.dll') } | Select-Object -First 1
  if (!$source) { throw 'LibVLC runtime not found in official archive' }
  New-Item -ItemType Directory -Force $Destination | Out-Null
  Copy-Item (Join-Path $source.FullName '*') $Destination -Recurse -Force
  if (!(Test-Path "$Destination/libvlccore.dll") -or !(Test-Path "$Destination/plugins")) { throw 'VLC runtime incomplete' }
  Write-Host "VideoLAN VLC $version runtime verified and copied."
} finally {
  Remove-Item $tmp -Recurse -Force
}
