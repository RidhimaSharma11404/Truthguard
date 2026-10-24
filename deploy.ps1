# PowerShell Push & Deploy Helper
param (
    [string]$RemoteUrl = ""
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " TruthGuard Git Push & Deploy Helper" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

if ($RemoteUrl -ne "") {
    git remote set-url origin $RemoteUrl
    Write-Host "[+] Updated remote origin to: $RemoteUrl" -ForegroundColor Green
}

$currentRemote = git remote get-url origin 2>$null
Write-Host "[*] Current remote origin: $currentRemote" -ForegroundColor Yellow

Write-Host "[*] Staging and committing any pending changes..." -ForegroundColor Yellow
git add .
git commit -m "feat: Prepare TruthGuard for cloud deployment" 2>$null

Write-Host "[*] Pushing to main branch..." -ForegroundColor Yellow
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "[SUCCESS] Pushed successfully to $currentRemote!" -ForegroundColor Green
    Write-Host "`nTo Deploy to Streamlit Community Cloud:" -ForegroundColor Cyan
    Write-Host "1. Visit https://share.streamlit.io"
    Write-Host "2. Select repository: $currentRemote"
    Write-Host "3. Set Main file path: ui/app.py"
    Write-Host "4. Click Deploy!`n"
} else {
    Write-Host "`n[ERROR] Push failed. If the repository does not exist on GitHub yet:" -ForegroundColor Red
    Write-Host "1. Go to https://github.com/new"
    Write-Host "2. Create a repository named: truthguard"
    Write-Host "3. Re-run: .\deploy.ps1"
}
