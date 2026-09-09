$ErrorActionPreference = 'Stop'
$packageRoot = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $packageRoot
try {
    python -c "import sys; assert sys.version_info >= (3,11), 'Python 3.11+ necessario'"
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.11+ não disponível.' }
    if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
        python -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Falha ao criar venv.' }
    }
    & '.\.venv\Scripts\python.exe' -m pip install .
    if ($LASTEXITCODE -ne 0) { throw 'Instalação falhou; veja docs/troubleshooting.md.' }
    & '.\.venv\Scripts\agentops.exe' --version
    Write-Output 'Instalado. Siga README.md: defina AGENTOPS_HOME e execute onboard --source .'
} finally {
    Pop-Location
}
