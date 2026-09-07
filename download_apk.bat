@echo off
echo ========================================
echo JARVIS APK Download Helper
echo ========================================
echo.

set DOWNLOAD_FOLDER=C:\Users\fayas_1ewqckb\Downloads\Jarvis_APK

:: Create download folder
if not exist "%DOWNLOAD_FOLDER%" (
    mkdir "%DOWNLOAD_FOLDER%"
    echo Created folder: %DOWNLOAD_FOLDER%
) else (
    echo Download folder: %DOWNLOAD_FOLDER%
)

echo.
echo ========================================
echo DOWNLOAD OPTIONS
echo ========================================
echo.
echo Option 1: Automatic Download (if gh CLI installed)
echo Option 2: Manual Download Instructions
echo.
set /p choice="Enter your choice (1 or 2): "

if "%choice%"=="1" goto automatic
if "%choice%"=="2" goto manual

:automatic
echo.
echo Checking for GitHub CLI...
where gh >nul 2>nul
if errorlevel 1 (
    echo GitHub CLI not found!
    echo Install from: https://cli.github.com/
    echo.
    goto manual
)

echo GitHub CLI found!
echo.
echo Downloading latest APK from GitHub Actions...
gh run download --repo fayas-dev/ai-apk --name jarvis-release-apk --dir "%DOWNLOAD_FOLDER%"

if exist "%DOWNLOAD_FOLDER%\app-release.apk" (
    echo.
    echo ========================================
    echo SUCCESS! APK Downloaded
    echo ========================================
    echo.
    echo Location: %DOWNLOAD_FOLDER%\app-release.apk
    echo.
    echo Opening folder...
    explorer "%DOWNLOAD_FOLDER%"
) else (
    echo.
    echo Download may have failed. Please check manually.
    goto manual
)
goto end

:manual
echo.
echo ========================================
echo MANUAL DOWNLOAD STEPS
echo ========================================
echo.
echo 1. Open this link in your browser:
echo    https://github.com/fayas-dev/ai-apk/actions
echo.
echo 2. Click on the latest successful workflow run (green checkmark)
echo.
echo 3. Scroll down to "Artifacts" section
echo.
echo 4. Click "jarvis-release-apk" to download
echo.
echo 5. Extract the downloaded ZIP file
echo.
echo 6. Copy app-release.apk to: %DOWNLOAD_FOLDER%
echo.
echo.
set /p open="Open GitHub Actions page now? (y/n): "
if /i "%open%"=="y" (
    start https://github.com/fayas-dev/ai-apk/actions
)

echo.
set /p openfolder="Open download folder? (y/n): "
if /i "%openfolder%"=="y" (
    explorer "%DOWNLOAD_FOLDER%"
)

:end
echo.
pause
