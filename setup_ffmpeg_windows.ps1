# PowerShell script to set up FFmpeg for Windows
# This script downloads and installs FFmpeg for audio conversion

Write-Host "Setting up FFmpeg for Slack audio processing..." -ForegroundColor Green

# Create FFmpeg directory
$ffmpegDir = "C:\ffmpeg"
if (!(Test-Path $ffmpegDir)) {
    New-Item -ItemType Directory -Path $ffmpegDir
    Write-Host "Created FFmpeg directory: $ffmpegDir" -ForegroundColor Yellow
}

# Download FFmpeg (using a reliable mirror)
$ffmpegUrl = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
$ffmpegZip = "$ffmpegDir\ffmpeg.zip"
$ffmpegExtractDir = "$ffmpegDir\ffmpeg-master-latest-win64-gpl"

try {
    Write-Host "Downloading FFmpeg..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri $ffmpegUrl -OutFile $ffmpegZip
    
    Write-Host "Extracting FFmpeg..." -ForegroundColor Yellow
    Expand-Archive -Path $ffmpegZip -DestinationPath $ffmpegDir -Force
    
    # Move binaries to bin directory
    $binDir = "$ffmpegDir\bin"
    if (!(Test-Path $binDir)) {
        New-Item -ItemType Directory -Path $binDir
    }
    
    # Copy FFmpeg executables
    $sourceBin = Get-ChildItem -Path $ffmpegExtractDir -Recurse -Name "ffmpeg.exe" | Select-Object -First 1
    $sourceProbe = Get-ChildItem -Path $ffmpegExtractDir -Recurse -Name "ffprobe.exe" | Select-Object -First 1
    
    if ($sourceBin) {
        Copy-Item -Path "$ffmpegExtractDir\$sourceBin" -Destination "$binDir\ffmpeg.exe" -Force
        Write-Host "Copied ffmpeg.exe to $binDir" -ForegroundColor Green
    }
    
    if ($sourceProbe) {
        Copy-Item -Path "$ffmpegExtractDir\$sourceProbe" -Destination "$binDir\ffprobe.exe" -Force
        Write-Host "Copied ffprobe.exe to $binDir" -ForegroundColor Green
    }
    
    # Add to PATH (current session)
    $env:PATH += ";$binDir"
    
    # Test installation
    Write-Host "Testing FFmpeg installation..." -ForegroundColor Yellow
    & "$binDir\ffmpeg.exe" -version
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "FFmpeg installation successful!" -ForegroundColor Green
        Write-Host "FFmpeg is available at: $binDir" -ForegroundColor Cyan
        Write-Host "You may need to restart your terminal or add $binDir to your system PATH" -ForegroundColor Yellow
    } else {
        Write-Host "FFmpeg installation failed!" -ForegroundColor Red
    }
    
    # Cleanup
    Remove-Item -Path $ffmpegZip -Force
    Remove-Item -Path $ffmpegExtractDir -Recurse -Force
    
} catch {
    Write-Host "Error setting up FFmpeg: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Please install FFmpeg manually from https://ffmpeg.org/download.html" -ForegroundColor Yellow
}

Write-Host "Setup complete!" -ForegroundColor Green
