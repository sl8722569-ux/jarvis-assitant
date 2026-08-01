$ErrorActionPreference = 'Continue'
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if (-not (Test-Path "$PSScriptRoot\..\jarvis.py")) {
  $Root = Resolve-Path (Join-Path $PSScriptRoot '..')
} else {
  $Root = Resolve-Path (Join-Path $PSScriptRoot '..')
}
$py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
if (-not (Test-Path $py)) { $py = "python" }
Write-Host "Using $py"
Write-Host "Installing JARVIS dependencies..."
& $py -m pip install --upgrade pip
& $py -m pip install -r (Join-Path $Root 'requirements.txt')

# Try PyAudio wheels for microphone
Write-Host "Attempting PyAudio for microphone..."
& $py -m pip install pipwin 2>$null
& $py -m pip install pyaudio 2>$null
if ($LASTEXITCODE -ne 0) {
  Write-Host "PyAudio pip failed — trying unofficial wheel index..."
  & $py -m pip install pyaudio --only-binary=:all: 2>$null
}

Write-Host "Done. Run Start_JARVIS.bat"
