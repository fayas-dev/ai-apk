@echo off
echo ========================================
echo Push to GitHub and Build APK
echo ========================================
echo.

cd /d "c:\Users\fayas_1ewqckb\Downloads\ai-agend-main"

echo Staging files...
git add .

echo.
echo Committing changes...
git commit -m "Add setup scripts and prepare for APK build"

echo.
echo Pushing to GitHub...
echo This will trigger automatic APK build via GitHub Actions
git push origin main

echo.
echo ========================================
echo Push Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Go to: https://github.com/fayas-dev/ai-apk/actions
echo 2. Wait for the build to complete (5-10 minutes)
echo 3. Download the APK from the Artifacts section
echo.
pause
