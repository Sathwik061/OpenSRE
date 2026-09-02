# fix-temp.ps1
# Permanently fixes the PyInstaller/OpenSRE temp directory issue on Windows
# when the username has a space (e.g. "madire sathwik")
#
# Run once as Administrator, or add to your PowerShell profile.

$tempPath = "C:\Temp"
New-Item -ItemType Directory -Force -Path $tempPath | Out-Null

[System.Environment]::SetEnvironmentVariable("TEMP", $tempPath, [System.EnvironmentVariableTarget]::User)
[System.Environment]::SetEnvironmentVariable("TMP",  $tempPath, [System.EnvironmentVariableTarget]::User)

Write-Host "TEMP and TMP permanently set to $tempPath for your user." -ForegroundColor Green
Write-Host "Restart your terminal for changes to take effect." -ForegroundColor Yellow
