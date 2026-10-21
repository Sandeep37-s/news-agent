$ErrorActionPreference = 'Stop'
$studioRoot = Split-Path -Parent $PSScriptRoot
$studioPython = Join-Path $studioRoot '.venv\Scripts\pythonw.exe'
if (-not (Test-Path -LiteralPath $studioPython)) { throw 'Run the project virtual-environment setup first.' }
$action = New-ScheduledTaskAction -Execute $studioPython -Argument '-m backend.monitor' -WorkingDirectory $studioRoot
$trigger = New-ScheduledTaskTrigger -Once -At ((Get-Date).AddMinutes(1)) -RepetitionInterval (New-TimeSpan -Hours 1)
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 30) -StartWhenAvailable
Register-ScheduledTask -TaskName 'DrishtiHourlyDiscovery' -Action $action -Trigger $trigger -Settings $settings -Description 'Hourly local news discovery. Azure Jobs are required for independence from this computer.'
