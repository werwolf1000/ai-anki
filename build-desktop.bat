@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "BUILD_SKIP_INSTALL=0"
set "BUILD_NO_PAUSE=0"
set "BUILD_EXIT=1"

:arguments
if "%~1"=="" goto prepare
if /i "%~1"=="--skip-install" (
  set "BUILD_SKIP_INSTALL=1"
  shift
  goto arguments
)
if /i "%~1"=="--no-pause" (
  set "BUILD_NO_PAUSE=1"
  shift
  goto arguments
)
if /i "%~1"=="--help" goto help
echo Unknown argument: %~1
echo Run build-desktop.bat --help for usage.
exit /b 2

:prepare
pushd "%~dp0"
if errorlevel 1 (
  echo ERROR: Cannot open the project folder.
  exit /b 1
)
set "BUILD_ROOT=%CD%"
echo AI Anki - Windows desktop installer
echo Project: "%BUILD_ROOT%"
echo.

where node.exe >nul 2>nul
if errorlevel 1 goto missing_node
where npm.cmd >nul 2>nul
if errorlevel 1 goto missing_node
node -e "const [major,minor]=process.versions.node.split('.').map(Number); process.exit(major>22 || major===22 && minor>=12 ? 0 : 1)"
if errorlevel 1 goto missing_node

if not exist "web\package-lock.json" goto missing_project
if not exist "desktop\package-lock.json" goto missing_project
if not exist "desktop\assets\icon.ico" goto missing_project

if "%BUILD_SKIP_INSTALL%"=="1" goto dependencies_ready
echo [1/3] Installing web dependencies...
call npm.cmd --prefix "%BUILD_ROOT%\web" ci --include=dev --no-audit --no-fund
if errorlevel 1 goto failed
echo.
echo [2/3] Installing desktop dependencies...
call npm.cmd --prefix "%BUILD_ROOT%\desktop" ci --include=dev --no-audit --no-fund
if errorlevel 1 goto failed

:dependencies_ready
if not exist "web\node_modules\.bin\vite.cmd" goto missing_dependencies
if not exist "desktop\node_modules\.bin\electron-builder.cmd" goto missing_dependencies
if exist "desktop\node_modules\electron\dist\electron.exe" goto build
if "%BUILD_SKIP_INSTALL%"=="1" goto missing_dependencies
echo Downloading the Electron runtime...
node "desktop\node_modules\electron\install.js"
if errorlevel 1 goto failed
if not exist "desktop\node_modules\electron\dist\electron.exe" goto missing_dependencies

:build
echo.
echo [3/3] Building the interface and Windows installer...
call npm.cmd --prefix "%BUILD_ROOT%\desktop" run dist -- --publish never --config.electronDist=node_modules/electron/dist
if errorlevel 1 goto failed
node -e "const fs=require('fs'),p=require('path'),j=require('./desktop/package.json'),f=p.resolve('desktop/dist','AI-Anki-Setup-'+j.version+'.exe'); if(!fs.existsSync(f)){console.error('ERROR: Installer was not created.');process.exit(1)} console.log('\nInstaller: '+f)"
if errorlevel 1 goto failed
echo.
echo Build completed successfully.
set "BUILD_EXIT=0"
goto finish

:missing_node
echo ERROR: Node.js 22.12 or newer, including npm, is required.
echo Install Node.js from https://nodejs.org/ and reopen this script.
goto finish

:missing_project
echo ERROR: Project files are missing. Keep this script in the repository root.
goto finish

:missing_dependencies
echo ERROR: Dependencies are incomplete. Run this script without --skip-install.
goto finish

:failed
echo.
echo ERROR: Build failed. See the command output above for details.
goto finish

:finish
popd
if "%BUILD_NO_PAUSE%"=="0" pause
exit /b %BUILD_EXIT%

:help
echo Usage: build-desktop.bat [--skip-install] [--no-pause]
echo.
echo By default, install dependencies from lockfiles and build the Windows installer.
echo --skip-install  Reuse installed dependencies when lockfiles have not changed.
echo --no-pause      Exit without waiting for a key, for terminal or CI use.
echo Output: desktop\dist\AI-Anki-Setup-VERSION.exe
exit /b 0
