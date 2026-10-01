$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

if (-not (Test-Path 'frontend/node_modules')) {
    Push-Location frontend
    try {
        npm ci
        if ($LASTEXITCODE -ne 0) { throw 'npm ci failed.' }
    } finally { Pop-Location }
}

Push-Location frontend
try {
    npm run build
    if ($LASTEXITCODE -ne 0) { throw 'Vue build failed.' }
} finally { Pop-Location }

$bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (Test-Path $bundledPython) {
    $python = $bundledPython
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $python = (Get-Command python).Source
} else {
    throw 'Python not found. Install Python 3, then run this script again.'
}

Write-Host 'Starting the Vue project. Open the URL printed by the server below.'
& $python .\server.py
