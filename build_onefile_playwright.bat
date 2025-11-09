@echo off
setlocal EnableDelayedExpansion
REM Jimeng Scripts - One-file packaging (includes Playwright Chromium)
REM Fix encoding & line continuation issues
chcp 65001 >nul

cd /d "%~dp0"

echo [1/5] Installing/Updating tools and dependencies...
python -m pip install --upgrade pip || goto :pipfail
python -m pip install -r requirements.txt || goto :pipfail
python -m pip install pyinstaller playwright || goto :pipfail

echo [2/5] Installing Playwright Chromium...
python -m playwright install chromium || goto :playfail

REM Resolve browsers directory
if not defined LOCALAPPDATA set "LOCALAPPDATA=%USERPROFILE%\AppData\Local"
set "BROWSERS_DIR=%LOCALAPPDATA%\ms-playwright"
if not exist "%BROWSERS_DIR%" (
  echo Browser directory not found: "%BROWSERS_DIR%"
  echo Please verify Playwright installation succeeded.
  goto :playfail
)

echo [3/5] Cleaning previous build output...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [4/5] Building single-file exe with PyInstaller...
pyinstaller -F -w --name "JimengScripts" --add-data "%BROWSERS_DIR%;ms-playwright" --collect-all playwright --hidden-import "playwright.async_api" --hidden-import "playwright.sync_api" app\main_pyqt6_simple.py
if errorlevel 1 goto :buildfail

echo [5/5] Done. Output: dist\JimengScripts.exe
echo Note: First run may take time to extract temp files.
pause
goto :eof

:pipfail
echo pip failed to install dependencies. Check network or mirrors.
exit /b 1

:playfail
echo Playwright Chromium installation failed. Try manually: python -m playwright install chromium
exit /b 1

:buildfail
echo Packaging failed. Please review error messages above.
exit /b 1