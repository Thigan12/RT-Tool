@echo off
echo ============================================================
echo  RT Tool -- Build Portable EXE
echo ============================================================
echo.

REM Clean previous build
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build
if exist "RT_Tool_Optimizer.spec" del RT_Tool_Optimizer.spec

echo [1/3] Running PyInstaller...
pyinstaller ^
  --onefile ^
  --windowed ^
  --name "RT_Tool_Optimizer" ^
  --add-data "ui/style.qss;ui" ^
  --hidden-import "PyQt6.QtCore" ^
  --hidden-import "PyQt6.QtGui" ^
  --hidden-import "PyQt6.QtWidgets" ^
  --hidden-import "PyQt6.QtNetwork" ^
  --hidden-import "pyqtgraph" ^
  --hidden-import "psutil" ^
  --hidden-import "wmi" ^
  --hidden-import "win32api" ^
  --hidden-import "win32con" ^
  --hidden-import "win32process" ^
  --hidden-import "pywintypes" ^
  --hidden-import "requests" ^
  --collect-all "pyqtgraph" ^
  --noconfirm ^
  main.py

echo.
if exist "dist\RT_Tool_Optimizer.exe" (
    echo [2/3] Build successful!
    echo [3/3] Portable EXE: dist\RT_Tool_Optimizer.exe
    echo.
    echo ============================================================
    echo  RT_Tool_Optimizer.exe is ready -- no installation needed!
    echo  Copy it anywhere and run directly.
    echo ============================================================
) else (
    echo [ERROR] Build failed. Check output above.
)
echo.
pause
