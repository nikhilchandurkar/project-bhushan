# -------------------------------
# Download & Install Font Awesome (Offline Local Static Files)
# -------------------------------

$downloadUrl = "https://use.fontawesome.com/releases/v6.6.0/fontawesome-free-6.6.0-web.zip"
$zipPath = "D:\fontawesome.zip"
$extractPath = "D:\fontawesome_extracted"
$targetPath = "D:\electronics\bhushan_web_project\static\lib\fontawesome"

Write-Host "Downloading Font Awesome..."
Invoke-WebRequest -Uri $downloadUrl -OutFile $zipPath

Write-Host "Extracting ZIP..."
Expand-Archive -LiteralPath $zipPath -DestinationPath $extractPath -Force

Write-Host "Creating target folder..."
New-Item -ItemType Directory -Force -Path $targetPath | Out-Null

Write-Host "Copying CSS and Webfonts..."
Copy-Item "$extractPath\fontawesome-free-6.6.0-web\css" -Destination $targetPath -Recurse -Force
Copy-Item "$extractPath\fontawesome-free-6.6.0-web\webfonts" -Destination $targetPath -Recurse -Force

Write-Host "Cleaning up..."
Remove-Item $zipPath -Force
Remove-Item $extractPath -Recurse -Force

Write-Host "Font Awesome Installed Successfully at static/lib/fontawesome"
