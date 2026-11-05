# Dolorain Studio LOCAL preview: reuse an already running ComfyUI backend; never install dependencies.
# No packages or model files are downloaded, no GPU inference is started, no system configuration changed.
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$localComfy = Join-Path $HOME 'ComfyUI'
$backend = 'http://127.0.0.1:8188'
$studio = 'http://127.0.0.1:8765'
Write-Host 'Dolorain Studio - Local native ComfyUI preview' -ForegroundColor Green
Write-Host 'Uses the running ComfyUI backend; no installation or model downloads.'
try {
    $status = Invoke-RestMethod -Uri ($backend + '/system_stats') -TimeoutSec 5 -ErrorAction Stop
    if (-not $status.devices) { throw 'ComfyUI responded without devices info.' }
    Write-Host 'ComfyUI backend is responding on port 8188.' -ForegroundColor Green
} catch {
    Write-Host ''
    Write-Host 'ComfyUI is not responding at http://127.0.0.1:8188.' -ForegroundColor Yellow
    Write-Host 'FIRST start your local ComfyUI on port 8188, then launch this file again.'
    Write-Host 'If ComfyUI uses a different port, edit $backend above.'
    exit 2
}
$candidates = New-Object 'System.Collections.Generic.List[string]'
if ($env:DSC_PYTHON) { $candidates.Add($env:DSC_PYTHON) }
$localVenv = Join-Path $localComfy '.venv\Scripts\python.exe'
if (Test-Path -LiteralPath $localVenv -PathType Leaf) { $candidates.Add($localVenv) }
$relative = @(
    'python_embeded\python.exe', 'python_embedded\python.exe',
    'ComfyUI_windows_portable\python_embeded\python.exe',
    '.venv\Scripts\python.exe', 'venv\Scripts\python.exe',
    'ComfyUI\.venv\Scripts\python.exe', 'ComfyUI\venv\Scripts\python.exe',
    'python\python.exe', 'runtime\python.exe',
    'installer_files\env\python.exe'
)
foreach ($rel in $relative) {
    $candidate = Join-Path $localComfy $rel
    if (Test-Path -LiteralPath $candidate -PathType Leaf) { $candidates.Add($candidate) }
}
foreach ($name in @('python.exe','python','py.exe','py')) {
    $cmd = Get-Command $name -ErrorAction SilentlyContinue
    if ($cmd) { $candidates.Add($cmd.Source) }
}
$python = $null
foreach ($candidate in $candidates | Select-Object -Unique) {
    try {
        & $candidate -c 'import aiohttp; import sys; print(sys.executable)' 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { $python = $candidate; break }
    } catch { }
}
if (-not $python) {
    Write-Host 'No installed Python environment with aiohttp was found.' -ForegroundColor Red
    Write-Host 'ComfyUI may use a different Python environment.'
    Write-Host 'Set DSC_PYTHON to its python.exe path and run this launcher again.'
    Write-Host 'No package installation was attempted.'
    exit 3
}
$env:DSC_LOCAL_PREVIEW = '1'
$env:DSC_LOCAL_COMFY_URL = $backend
$env:DSC_PUBLIC_TEST = '1'
Remove-Item Env:DSC_STUDIO_PASSWORD -ErrorAction SilentlyContinue
Write-Host ('Using Python: ' + $python) -ForegroundColor Green
Write-Host ('Native Dolorain Studio: ' + $studio) -ForegroundColor Green
Write-Host 'Browser will open after the server starts. Keep this window open.' 
$job = Start-Job -ScriptBlock {
    param($url)
    for ($i=0; $i -lt 30; $i++) {
        Start-Sleep -Milliseconds 500
        try {
            $r = Invoke-WebRequest -Uri ($url + '/_studio/ready') -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            if ($r.StatusCode -eq 200) { Start-Process $url; break }
        } catch { }
    }
} -ArgumentList $studio
try {
    & $python (Join-Path $repo 'deploy\runpod\cloud\app.py')
    exit $LASTEXITCODE
} finally {
    Stop-Job $job -ErrorAction SilentlyContinue | Out-Null
    Remove-Job $job -Force -ErrorAction SilentlyContinue | Out-Null
}
