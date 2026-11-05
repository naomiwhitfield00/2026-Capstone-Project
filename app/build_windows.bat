@echo off
REM Builds Escapism.exe  ->  dist\Escapism\Escapism.exe   (run from the app\ folder)
REM Zip the whole dist\Escapism folder to share it; players just double-click Escapism.exe.

python -m pip install --upgrade pyinstaller pywebview
if errorlevel 1 goto :fail

python tools\fetch_three.py
if errorlevel 1 goto :fail

python -m PyInstaller --noconfirm --clean --windowed --name Escapism ^
  --add-data "escapism_app\ui;escapism_app\ui" ^
  --add-data "rooms;rooms" ^
  run_escapism.py
if errorlevel 1 goto :fail

echo.
echo Done!  Your game is in dist\Escapism\  (run Escapism.exe)
goto :eof

:fail
echo.
echo Build failed - read the messages above.
exit /b 1
