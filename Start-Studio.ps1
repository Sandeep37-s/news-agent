$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if ((Get-NetTCPConnection -LocalPort 3000,8000 -State Listen -ErrorAction SilentlyContinue)) {
    Write-Host 'A service is already listening on port 3000 or 8000. Open http://localhost:3000 or stop the existing studio before restarting.'
    return
}
$studioPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $studioPython)) { throw 'Run the setup steps in README.md first.' }
& $studioPython scripts/setup.py
& $studioPython -m alembic upgrade head
if ($LASTEXITCODE -ne 0) { throw 'Database migration failed.' }
& $studioPython -m backend.bootstrap
if ($LASTEXITCODE -ne 0) { throw 'Database initialization failed.' }
New-Item -ItemType Directory -Force -Path (Join-Path $PSScriptRoot 'data') | Out-Null
$apiProcess = Start-Process -FilePath $studioPython -ArgumentList @('-m','uvicorn','backend.api:app','--host','127.0.0.1','--port','8000','--no-access-log') -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $PSScriptRoot 'data\api.log') -RedirectStandardError (Join-Path $PSScriptRoot 'data\api-error.log') -PassThru
$nodePath = (Get-Command node.exe).Source
$nextEntry = '"' + (Join-Path $PSScriptRoot 'frontend\node_modules\next\dist\bin\next') + '"'
$webProcess = Start-Process -FilePath $nodePath -ArgumentList @($nextEntry,'start','--hostname','127.0.0.1') -WorkingDirectory (Join-Path $PSScriptRoot 'frontend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $PSScriptRoot 'data\web.log') -RedirectStandardError (Join-Path $PSScriptRoot 'data\web-error.log') -PassThru
@{api=$apiProcess.Id;web=$webProcess.Id} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'data\local-processes.json')
Write-Host 'Studio starting at http://localhost:3000'
Write-Host "Owned process IDs: API $($apiProcess.Id), web $($webProcess.Id)."
Write-Host 'Your administrator password is the ADMIN_PASSWORD value in the private .env file.'
Write-Host 'Hourly monitoring is separate. See README.md to install the local schedule or deploy Azure Jobs.'
