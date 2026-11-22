@echo off
cd /d "%~dp0"
py -3.12 -m venv .venv || goto fail
.venv\Scripts\python.exe -m pip install -r requirements.txt || goto fail
.venv\Scripts\python.exe -m PyInstaller --noconfirm --windowed --onedir --name Folder explorer.py || goto fail
echo Built: dist\Folder\Folder.exe
pause
exit /b 0
:fail
echo Build failed. Check Python 3.12 and internet connection.
pause
exit /b 1
