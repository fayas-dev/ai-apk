# Push to GitHub and Build APK Automatically

Your repository is already configured with GitHub Actions that will automatically build the APK when you push code.

## Repository Information
- **Remote URL**: https://github.com/fayas-dev/ai-apk.git
- **Branch**: main

## Steps to Push and Build APK

### Option 1: Using Git Commands (Recommended)

Open a new PowerShell or Command Prompt window and run these commands:

```bash
cd "c:\Users\fayas_1ewqckb\Downloads\ai-agend-main"

# Stage all changes
git add .

# Commit the changes
git commit -m "Add Flutter setup script and prepare for APK build"

# Push to GitHub (this will trigger the APK build)
git push origin main
```

### Option 2: Using GitHub Desktop

1. Open GitHub Desktop
2. Select this repository
3. Review changes
4. Commit to main
5. Push to origin

## What Happens After Push?

Once you push to GitHub:

1. GitHub Actions will automatically start building your APK
2. The workflow is defined in `.github/workflows/build-apk.yml`
3. The build process will:
   - Set up Flutter 3.24.0
   - Set up Java 17
   - Build the release APK
   - Upload it as an artifact

## Download the Built APK

After the build completes (usually 5-10 minutes):

1. Go to: https://github.com/fayas-dev/ai-apk/actions
2. Click on the latest workflow run
3. Scroll down to "Artifacts"
4. Download `jarvis-release-apk`
5. Extract the ZIP file to get `app-release.apk`

## Install APK on Your Android Device

1. Transfer `app-release.apk` to your Android device
2. Enable "Install from Unknown Sources" in Settings
3. Tap the APK file to install
4. Grant necessary permissions (microphone, contacts, etc.)

## Troubleshooting

If the GitHub Actions build fails:
- Check the Actions tab for error logs
- Common issues:
  - Flutter dependency conflicts
  - Android SDK licensing
  - Gradle build errors

## Manual Build (If Needed)

If you want to build locally instead:
1. Install Flutter SDK from https://flutter.dev
2. Install Java JDK 17
3. Install Android SDK
4. Run:
   ```bash
   cd Mobile_App
   flutter pub get
   flutter build apk --release
   ```
5. APK will be at: `Mobile_App\build\app\outputs\flutter-apk\app-release.apk`
