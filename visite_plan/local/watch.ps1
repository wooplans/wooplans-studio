# Surveille jobs\*\RENDER_PC et lance le rendu automatiquement (aucun clic nécessaire)
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$log = Join-Path $root "watch.log"
$env:Path += ";$env:USERPROFILE\.local\bin;$env:LOCALAPPDATA\Microsoft\WinGet\Links"
while ($true) {
  Get-ChildItem (Join-Path $root "jobs") -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    $j = $_.FullName
    if ((Test-Path "$j\RENDER_PC") -and -not (Test-Path "$j\DONE") -and -not (Test-Path "$j\RUNNING")) {
      "[$(Get-Date)] début $($_.Name)" | Add-Content $log
      "" | Set-Content "$j\RUNNING"
      uv run --no-project python (Join-Path $root "run_local.py") $j *>> $log
      Remove-Item "$j\RUNNING" -ErrorAction SilentlyContinue
      if (Test-Path "$j\$($_.Name).mp4") { "" | Set-Content "$j\DONE"; "[$(Get-Date)] fini $($_.Name)" | Add-Content $log }
      else { "" | Set-Content "$j\ERREUR"; "[$(Get-Date)] ERREUR $($_.Name)" | Add-Content $log }
    }
  }
  Start-Sleep -Seconds 5
}
