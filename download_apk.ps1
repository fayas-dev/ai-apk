# APK Download Script from GitHub Actions
# This script downloads the built APK from GitHub Actions to a local folder

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "APK Download from GitHub Actions" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$repoOwner = "fayas-dev"
$repoName = "ai-apk"
$artifactName = "jarvis-release-apk"
$downloadFolder = "C:\Users\fayas_1ewqckb\Downloads\Jarvis_APK"

# Create download folder if it doesn't exist
if (-not (Test-Path $downloadFolder)) {
    New-Item -ItemType Directory -Path $downloadFolder -Force | Out-Null
    Write-Host "Created download folder: $downloadFolder" -ForegroundColor Green
}

Write-Host ""
Write-Host "Repository: $repoOwner/$repoName" -ForegroundColor Yellow
Write-Host "Download folder: $downloadFolder" -ForegroundColor Yellow
Write-Host ""

# Instructions for manual download
Write-Host "To download the APK automatically, you need GitHub CLI (gh)." -ForegroundColor Cyan
Write-Host ""
Write-Host "Option 1: Manual Download (Simple)" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
Write-Host "1. Go to: https://github.com/$repoOwner/$repoName/actions" -ForegroundColor White
Write-Host "2. Click on the latest successful workflow run" -ForegroundColor White
Write-Host "3. Scroll down to 'Artifacts' section" -ForegroundColor White
Write-Host "4. Click on '$artifactName' to download" -ForegroundColor White
Write-Host "5. Extract the ZIP file to get app-release.apk" -ForegroundColor White
Write-Host "6. Move the APK to: $downloadFolder" -ForegroundColor White
Write-Host ""

Write-Host "Option 2: Install GitHub CLI (Advanced)" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green
Write-Host "1. Install GitHub CLI from: https://cli.github.com/" -ForegroundColor White
Write-Host "2. Run: gh auth login" -ForegroundColor White
Write-Host "3. Run this script again" -ForegroundColor White
Write-Host ""

# Check if GitHub CLI is installed
$ghInstalled = $false
try {
    $ghVersion = & gh --version 2>&1
    $ghInstalled = $true
    Write-Host "GitHub CLI is installed!" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "GitHub CLI is not installed." -ForegroundColor Yellow
    Write-Host ""
}

if ($ghInstalled) {
    Write-Host "Attempting to download latest APK artifact..." -ForegroundColor Yellow
    Write-Host ""
    
    try {
        # Get the latest workflow run
        $latestRun = & gh run list --repo "$repoOwner/$repoName" --workflow "build-apk.yml" --limit 1 --json databaseId,status,conclusion | ConvertFrom-Json
        
        if ($latestRun.Count -eq 0) {
            Write-Host "No workflow runs found. Please push code to trigger a build first." -ForegroundColor Red
            exit 1
        }
        
        $runId = $latestRun[0].databaseId
        $status = $latestRun[0].status
        $conclusion = $latestRun[0].conclusion
        
        Write-Host "Latest workflow run ID: $runId" -ForegroundColor Cyan
        Write-Host "Status: $status" -ForegroundColor Cyan
        Write-Host "Conclusion: $conclusion" -ForegroundColor Cyan
        Write-Host ""
        
        if ($status -ne "completed") {
            Write-Host "Workflow is still running. Please wait for it to complete." -ForegroundColor Yellow
            Write-Host "Check status at: https://github.com/$repoOwner/$repoName/actions/runs/$runId" -ForegroundColor Yellow
            exit 0
        }
        
        if ($conclusion -ne "success") {
            Write-Host "Workflow failed. Please check the logs." -ForegroundColor Red
            Write-Host "View logs at: https://github.com/$repoOwner/$repoName/actions/runs/$runId" -ForegroundColor Yellow
            exit 1
        }
        
        # Download the artifact
        Write-Host "Downloading APK artifact..." -ForegroundColor Yellow
        & gh run download $runId --repo "$repoOwner/$repoName" --name "$artifactName" --dir "$downloadFolder"
        
        if (Test-Path "$downloadFolder\app-release.apk") {
            Write-Host ""
            Write-Host "========================================" -ForegroundColor Green
            Write-Host "APK Downloaded Successfully!" -ForegroundColor Green
            Write-Host "========================================" -ForegroundColor Green
            Write-Host ""
            Write-Host "Location: $downloadFolder\app-release.apk" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "You can now transfer this APK to your Android device!" -ForegroundColor Yellow
            
            # Open the folder
            Start-Process explorer.exe -ArgumentList $downloadFolder
        } else {
            Write-Host "APK file not found after download. Please check manually." -ForegroundColor Red
        }
        
    } catch {
        Write-Host "Error downloading APK: $_" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please download manually from:" -ForegroundColor Yellow
        Write-Host "https://github.com/$repoOwner/$repoName/actions" -ForegroundColor White
    }
} else {
    Write-Host "Please use Option 1 (Manual Download) above." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
