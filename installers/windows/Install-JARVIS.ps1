# J.A.R.V.I.S [EARLY ACCESS] — Windows installer
# Copies the app, installs Python deps into a venv, creates shortcuts. No admin required.

$ErrorActionPreference = "Stop"
$Product = "J.A.R.V.I.S [EARLY ACCESS]"
$Src = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$Dest = Join-Path $env:LOCALAPPDATA "JARVIS"
$PyCandidates = @(
  "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
  "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
  "C:\Python312\python.exe"
)
$Py = $PyCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $Py) {
  $cmd = Get-Command python -ErrorAction SilentlyContinue
  if ($cmd) { $Py = $cmd.Source }
}

Write-Host "=== $Product installer ==="
Write-Host "From: $Src"
Write-Host "To:   $Dest"

if (-not $Py) {
  Write-Host "Python 3.11+ was not found."
  Write-Host "Opening the official installer page. Install Python, tick 'Add to PATH', then run this setup again."
  Start-Process "https://www.python.org/downloads/windows/"
  exit 1
}

Write-Host "Python: $Py"
& $Py --version

New-Item -ItemType Directory -Path $Dest -Force | Out-Null
$copy = @(
  "jarvis.py", "Start_JARVIS.bat", "requirements.txt", "README.md", "LICENSE",
  "PHASE1.md", "PHASE2.md", "VERSION", "config.example.json", ".env.example"
)
foreach ($f in $copy) {
  $p = Join-Path $Src $f
  if (Test-Path $p) { Copy-Item $p $Dest -Force }
}
foreach ($d in @("modules", "platform", "scripts", "assets", "docs", "installers")) {
  $p = Join-Path $Src $d
  if (Test-Path $p) {
    Copy-Item $p (Join-Path $Dest $d) -Recurse -Force
  }
}
New-Item (Join-Path $Dest "data") -ItemType Directory -Force | Out-Null
New-Item (Join-Path $Dest "logs") -ItemType Directory -Force | Out-Null
if (-not (Test-Path (Join-Path $Dest "config.json"))) {
  Copy-Item (Join-Path $Dest "config.example.json") (Join-Path $Dest "config.json") -Force
}

Write-Host "Creating virtual environment..."
& $Py -m venv (Join-Path $Dest ".venv")
$pip = Join-Path $Dest ".venv\Scripts\python.exe"
& $pip -m pip install --upgrade pip
& $pip -m pip install -r (Join-Path $Dest "requirements.txt")
& $pip -m pip install pyaudio
if ($LASTEXITCODE -ne 0) { Write-Host "PyAudio optional: mic still may work later." }

$launcher = Join-Path $Dest "Start_JARVIS.bat"
@"
@echo off
cd /d "$Dest"
".venv\Scripts\python.exe" "jarvis.py"
if errorlevel 1 pause
"@ | Set-Content $launcher -Encoding ASCII

$uninstall = Join-Path $Dest "Uninstall-JARVIS.ps1"
@"
`$d = '$Dest'
Remove-Item "`$env:USERPROFILE\Desktop\J.A.R.V.I.S.lnk" -Force -ErrorAction SilentlyContinue
Remove-Item "`$env:APPDATA\Microsoft\Windows\Start Menu\Programs\J.A.R.V.I.S.lnk" -Force -ErrorAction SilentlyContinue
Remove-Item `$d -Recurse -Force
Write-Host 'J.A.R.V.I.S removed from this user account.'
"@ | Set-Content $uninstall -Encoding UTF8

$Wsh = New-Object -ComObject WScript.Shell
$desk = Join-Path ([Environment]::GetFolderPath("Desktop")) "J.A.R.V.I.S.lnk"
$sc = $Wsh.CreateShortcut($desk)
$sc.TargetPath = $launcher
$sc.WorkingDirectory = $Dest
$sc.Description = $Product
$sc.Save()

$startDir = [Environment]::GetFolderPath("Programs")
$sc2 = $Wsh.CreateShortcut((Join-Path $startDir "J.A.R.V.I.S.lnk"))
$sc2.TargetPath = $launcher
$sc2.WorkingDirectory = $Dest
$sc2.Save()

Write-Host "Install complete."
Write-Host "Shortcut: Desktop\J.A.R.V.I.S.lnk"
Write-Host "Uninstall: $uninstall"
Start-Process $launcher
