@echo off
chcp 65001 >nul
echo === WooPlans : installation du rendu automatique (une seule fois) ===
set ROOT=%~dp0
powershell -NoProfile -ExecutionPolicy Bypass -Command "if(-not (Get-Command uv -ErrorAction SilentlyContinue)){irm https://astral.sh/uv/install.ps1 | iex}"
set PATH=%PATH%;%USERPROFILE%\.local\bin
where ffmpeg >nul 2>nul || winget install -e --id Gyan.FFmpeg --accept-source-agreements --accept-package-agreements
uv tool install manimgx
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Force '%ROOT%visite_plan.zip' '%ROOT%'"
schtasks /Create /F /TN "WooPlansRendu" /SC ONLOGON /TR "powershell -WindowStyle Hidden -ExecutionPolicy Bypass -File \"%ROOT%watch.ps1\""
start "" powershell -WindowStyle Hidden -ExecutionPolicy Bypass -File "%ROOT%watch.ps1"
echo.
echo Termine. Le rendu se lance maintenant tout seul. Vous pouvez fermer cette fenetre.
pause
