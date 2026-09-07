@echo off
echo ========================================
echo Opening GitHub Actions to Download APK
echo ========================================
echo.

:: Create download folder
set DOWNLOAD_FOLDER=C:\Users\fayas_1ewqckb\Downloads\Jarvis_APK
if not exist "%DOWNLOAD_FOLDER%" mkdir "%DOWNLOAD_FOLDER%"

echo Download folder ready: %DOWNLOAD_FOLDER%
echo.
echo Opening GitHub Actions page...
echo.
echo INSTRUCTIONS:
echo 1. Browser will open automatically
echo 2. Click on the LATEST successful workflow (green checkmark)
echo 3. Scroll down to "Artifacts" section
echo 4. Click "jarvis-release-apk" to download
echo 5. Extract the ZIP file
echo 6. Copy app-release.apk to: %DOWNLOAD_FOLDER%
echo.

:: Open GitHub Actions page
start https://github.com/fayas-dev/ai-apk/actions

:: Wait a moment then open the download folder
timeout /t 3 /nobreak > nul
explorer "%DOWNLOAD_FOLDER%"

echo.
echo Folder opened! Save the APK here after download.
echo.
pause
