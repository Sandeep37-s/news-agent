$ErrorActionPreference = 'Stop'
$statePath = Join-Path $PSScriptRoot 'data\local-processes.json'
if (-not (Test-Path -LiteralPath $statePath)) { Write-Host 'No saved studio process IDs.'; return }
$studioState = Get-Content -LiteralPath $statePath | ConvertFrom-Json
foreach ($studioId in @($studioState.api, $studioState.web)) {
    $owned = Get-CimInstance Win32_Process -Filter "ProcessId = $studioId" -ErrorAction SilentlyContinue
    $isApi = $owned -and $owned.ExecutablePath -like "$PSScriptRoot\.venv\*" -and $owned.CommandLine -like '*uvicorn backend.api:app*'
    $isWeb = $owned -and $owned.CommandLine -like "*$PSScriptRoot\frontend\node_modules\next\dist\bin\next*"
    if ($isApi -or $isWeb) {
        # The Windows virtual-environment launcher may own a child Python process.
        # Stop only children whose recorded command also belongs to this checkout.
        $children = Get-CimInstance Win32_Process -Filter "ParentProcessId = $studioId" -ErrorAction SilentlyContinue
        foreach ($child in $children) {
            if ($child.CommandLine -like "*$PSScriptRoot*" -and $child.CommandLine -like '*backend.api:app*') {
                Stop-Process -Id $child.ProcessId -ErrorAction SilentlyContinue
            }
        }
        Stop-Process -Id $studioId -ErrorAction SilentlyContinue
    }
}
Write-Host 'Stopped matching saved studio processes. The hourly task, if installed, is separate.'
