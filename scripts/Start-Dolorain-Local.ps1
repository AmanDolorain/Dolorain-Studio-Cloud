# Dolorain Studio LOCAL preview: reuses the user's already running ComfyUI Easy Install.
# No packages or model files are downloaded, no GPU inference is started, no system configuration changed.
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$easy = 'C:\Users\Aman\Downloads\ComfyUI-Easy-Install\ComfyUI-Easy-Install'
$backend = 'http://127.0.0.1:8188'
$studio = 'http://127.0.0.1:8765'
Write-Host 'Dolorain Studio - Local native ComfyUI preview' -ForegroundColor Green
Write-Host 'Uses existing ComfyUI Easy Install; no installation or model downloads.'
Write-Host ('Easy Install directory: ' + $easy)
if (-not (Test-Path -LiteralPath $easy -PathType Container)) {
    Write-Warning 'ComfyUI Easy Install folder is not present at the saved location. Edit the $easy path in this launcher if you moved it.'
}
try {
    $status = Invoke-RestMethod -Uri ($backend + '/system_stats') -TimeoutSec 5 -ErrorAction Stop
    if (-not $status.devices) { throw 'ComfyUI responded without devices info.' }
    Write-Host 'ComfyUI backend is responding on port 8188.' -ForegroundColor Green
} catch {
    Write-Host ''
    Write-Host 'ComfyUI is not responding at http://127.0.0.1:8188.' -ForegroundColor Yellow
    Write-Host 'FIRST open ComfyUI Easy Install normally, keep it running, then launch this file again.'
    Write-Host 'If Easy Install uses a different port, edit $backend above.'
    exit 2
}
$candidates = New-Object 'System.Collections.Generic.List[string]'
if ($env:DSC_PYTHON) { $candidates.Add($env:DSC_PYTHON) }
$relative = @(
    'python_embeded\python.exe', 'python_embedded\python.exe',
    'ComfyUI_windows_portable\python_embeded\python.exe',
    '.venv\Scripts\python.exe', 'venv\Scripts\python.exe',
    'ComfyUI\.venv\Scripts\python.exe', 'ComfyUI\venv\Scripts\python.exe',
    'python\python.exe', 'runtime\python.exe',
    'installer_files\env\python.exe'
)
foreach ($rel in $relative) {
    $candidate = Join-Path $easy $rel
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
    Write-Host 'ComfyUI Easy Install may use a different Python folder.'
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
