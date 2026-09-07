# Flutter Installation Script for Windows
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Flutter & Android Build Setup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Download Flutter SDK
Write-Host "[1/5] Downloading Flutter SDK..." -ForegroundColor Yellow
$flutterUrl = "https://storage.googleapis.com/flutter_infra_release/releases/stable/windows/flutter_windows_3.24.0-stable.zip"
$flutterZip = "$env:USERPROFILE\Downloads\flutter_sdk.zip"
$flutterDir = "C:\src\flutter"

if (Test-Path $flutterZip) {
    Write-Host "Flutter SDK already downloaded." -ForegroundColor Green
} else {
    $ProgressPreference = 'SilentlyContinue'
    try {
        Invoke-WebRequest -Uri $flutterUrl -OutFile $flutterZip -UseBasicParsing
        Write-Host "Flutter SDK downloaded successfully!" -ForegroundColor Green
    } catch {
        Write-Host "Error downloading Flutter SDK: $_" -ForegroundColor Red
        Write-Host "Please download manually from: https://docs.flutter.dev/get-started/install/windows" -ForegroundColor Yellow
        exit 1
    }
}

# Step 2: Extract Flutter
Write-Host "[2/5] Extracting Flutter SDK to C:\src\flutter..." -ForegroundColor Yellow
if (Test-Path $flutterDir) {
    Write-Host "Flutter directory already exists at $flutterDir" -ForegroundColor Green
} else {
    try {
        New-Item -ItemType Directory -Path "C:\src" -Force | Out-Null
        Expand-Archive -Path $flutterZip -DestinationPath "C:\src" -Force
        Write-Host "Flutter extracted successfully!" -ForegroundColor Green
    } catch {
        Write-Host "Error extracting Flutter: $_" -ForegroundColor Red
        exit 1
    }
}

# Step 3: Add Flutter to PATH
Write-Host "[3/5] Adding Flutter to PATH..." -ForegroundColor Yellow
$flutterBin = "C:\src\flutter\bin"
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")

if ($currentPath -like "*$flutterBin*") {
    Write-Host "Flutter is already in PATH" -ForegroundColor Green
} else {
    try {
        [Environment]::SetEnvironmentVariable(
            "Path",
            "$currentPath;$flutterBin",
            "User"
        )
        $env:Path = "$env:Path;$flutterBin"
        Write-Host "Flutter added to PATH successfully!" -ForegroundColor Green
    } catch {
        Write-Host "Error adding Flutter to PATH: $_" -ForegroundColor Red
        Write-Host "Please add C:\src\flutter\bin to your PATH manually" -ForegroundColor Yellow
    }
}

# Step 4: Download Java JDK 17
Write-Host "[4/5] Checking Java JDK..." -ForegroundColor Yellow
try {
    $javaVersion = & java -version 2>&1
    Write-Host "Java is already installed!" -ForegroundColor Green
} catch {
    Write-Host "Java not found. Downloading Java JDK 17..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please install Java JDK 17 manually from one of these sources:" -ForegroundColor Cyan
    Write-Host "1. Oracle JDK: https://www.oracle.com/java/technologies/downloads/#java17" -ForegroundColor White
    Write-Host "2. Zulu JDK: https://www.azul.com/downloads/?package=jdk#zulu" -ForegroundColor White
    Write-Host "3. Microsoft OpenJDK: https://learn.microsoft.com/en-us/java/openjdk/download" -ForegroundColor White
    Write-Host ""
    Write-Host "After installing Java, restart this script." -ForegroundColor Yellow
}

# Step 5: Run Flutter Doctor
Write-Host "[5/5] Running Flutter Doctor..." -ForegroundColor Yellow
Write-Host ""
try {
    & "C:\src\flutter\bin\flutter.bat" doctor
} catch {
    Write-Host "Could not run flutter doctor. Please restart PowerShell and run: flutter doctor" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "IMPORTANT: Please restart PowerShell for PATH changes to take effect!" -ForegroundColor Yellow
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Install Android Studio OR Android SDK Command Line Tools" -ForegroundColor White
Write-Host "2. Run: flutter doctor --android-licenses" -ForegroundColor White
Write-Host "3. Navigate to Mobile_App folder" -ForegroundColor White
Write-Host "4. Run: flutter pub get" -ForegroundColor White
Write-Host "5. Run: flutter build apk --release" -ForegroundColor White
Write-Host ""
