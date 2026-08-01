$Root = Resolve-Path (Join-Path $PSScriptRoot '..')
$Desktop = [Environment]::GetFolderPath('Desktop')
$Wsh = New-Object -ComObject WScript.Shell

# Desktop launcher
$sc = $Wsh.CreateShortcut((Join-Path $Desktop 'JARVIS.lnk'))
$sc.TargetPath = Join-Path $Root 'Start_JARVIS.bat'
$sc.WorkingDirectory = $Root
$sc.WindowStyle = 7
$sc.Description = 'JARVIS Personal Assistant'
$sc.Save()

# Startup optional - create but user can enable via config later; place in Startup folder lightly
$Startup = [Environment]::GetFolderPath('Startup')
$sc2 = $Wsh.CreateShortcut((Join-Path $Startup 'JARVIS.lnk'))
$sc2.TargetPath = Join-Path $Root 'Start_JARVIS.bat'
$sc2.WorkingDirectory = $Root
$sc2.WindowStyle = 7
$sc2.Description = 'JARVIS Startup'
$sc2.Save()

Write-Host "Shortcuts created on Desktop and Startup."
Write-Host "To disable auto-start: delete $Startup\JARVIS.lnk"
