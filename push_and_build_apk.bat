@echo off
title Jarvis - Push to GitHub and Build APK
color 0b
echo ======================================================================
echo                  JARVIS - PUSH TO GITHUB ^& BUILD APK
echo ======================================================================
echo.
echo Target Repository: https://github.com/fayas-dev/ai-apk.git
echo.
cd /d "%~dp0"

echo [1/2] Connecting to GitHub...
echo If a browser window pops up asking to Sign In / Authorize GitHub, 
echo please click 'Authorize' to log in as fayas-dev.
echo.

git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ======================================================================
    echo [2/2] SUCCESS! Code has been pushed to GitHub successfully!
    echo.
    echo GitHub Actions has started building your Android APK automatically.
    echo Opening the build page in your browser...
    echo ======================================================================
    start https://github.com/fayas-dev/ai-apk/actions
) else (
    echo.
    echo ======================================================================
    echo [ERROR] Push encountered an issue. 
    echo If it asked for login, please retry or sign in with your browser.
    echo ======================================================================
)
echo.
pause
