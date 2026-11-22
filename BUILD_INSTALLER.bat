@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe py -3.12 -m venv .venv || goto fail
.venv\Scripts\python.exe -m pip install -r requirements.txt || goto fail
.venv\Scripts\python.exe tools\build_icon.py || goto fail
.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm --windowed --onedir --name Folder --icon assets\folder.ico --collect-all imageio_ffmpeg explorer.py || goto fail
powershell -NoProfile -ExecutionPolicy Bypass -File packaging\windows\fetch_vlc.ps1 -Destination dist/Folder/vlc || goto fail
powershell -NoProfile -ExecutionPolicy Bypass -File packaging\windows\fetch_everything.ps1 -Destination dist/Folder/everything || goto fail
.venv\Scripts\python.exe packaging\windows\collect_notices.py || goto fail
set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
 echo Install Inno Setup 6 from https://jrsoftware.org/isdl.php
 goto fail
)
for /f "delims=" %%V in ('.venv\Scripts\python.exe -c "from version import VERSION; print(VERSION)"') do set "VER=%%V"
"%ISCC%" /DAppVersion=%VER% packaging\windows\Folder.iss || goto fail
echo Installer: installer\Folder-%VER%-Setup-x64.exe
pause
exit /b 0
:fail
echo Installer build failed.
pause
exit /b 1
