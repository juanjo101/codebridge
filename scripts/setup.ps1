# CodeBridge Setup Script for Windows PowerShell
# ================================================
# Run as: powershell -ExecutionPolicy Bypass -File scripts\setup.ps1

param(
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$EnvFile = Join-Path $ProjectDir ".env"

Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host " CODEBRIDGE GATEWAY - SETUP" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $ProjectDir

# -- Check Python ------------------------------------------------------
Write-Host "[1/6] Checking Python..."
try {
    $pyVersion = python --version 2>&1
    Write-Host "  ok $pyVersion" -ForegroundColor Green
    $Python = "python"
} catch {
    try {
        $pyVersion = python3 --version 2>&1
        Write-Host "  ok $pyVersion" -ForegroundColor Green
        $Python = "python3"
    } catch {
        Write-Host "  FAIL: Python not found. Install from https://python.org" -ForegroundColor Red
        exit 1
    }
}

# -- Check/Install uv --------------------------------------------------
Write-Host "[2/6] Checking uv..."
$uvPath = Get-Command uv -ErrorAction SilentlyContinue
if ($uvPath) {
    $uvVersion = uv --version
    Write-Host "  ok $uvVersion" -ForegroundColor Green
} else {
    Write-Host "  Installing uv..."
    try {
        $uvInstallUrl = "https://astral.sh/uv/install.ps1"
        Invoke-RestMethod $uvInstallUrl | Invoke-Expression
        Write-Host "  ok uv installed" -ForegroundColor Green
    } catch {
        Write-Host "  FAIL: Could not install uv. Install from https://github.com/astral-sh/uv" -ForegroundColor Red
        exit 1
    }
}

# -- Install dependencies -----------------------------------------------
Write-Host "[3/6] Installing dependencies..."
uv sync --extra dev
Write-Host "  ok Dependencies installed" -ForegroundColor Green

# -- Create .env --------------------------------------------------------
Write-Host "[4/6] Creating .env..."
if (Test-Path $EnvFile) {
    Write-Host "  ok .env already exists (not overwriting)" -ForegroundColor Green
} else {
    $envExample = Join-Path $ProjectDir ".env.example"
    Copy-Item $envExample $EnvFile
    Write-Host "  ok Created .env from .env.example" -ForegroundColor Green
}

# -- Generate local token -----------------------------------------------
Write-Host "[5/6] Generating local auth token..."
$TokenFile = Join-Path $ProjectDir ".codebridge_token"
if (Test-Path $TokenFile) {
    $Token = Get-Content $TokenFile
    Write-Host "  ok Existing token loaded" -ForegroundColor Green
} else {
    $Token = uv run python -c "import secrets; print(secrets.token_urlsafe(32))"
    $Token | Out-File -FilePath $TokenFile -Encoding ascii -NoNewline
    Write-Host "  ok Token generated" -ForegroundColor Green
}

# -- Run tests ----------------------------------------------------------
if (-not $SkipTests) {
    Write-Host "[6/6] Running tests..."
    try {
        uv run pytest tests\unit\ tests\integration\ -q --tb=short
        Write-Host "  ok Tests passed" -ForegroundColor Green
    } catch {
        Write-Host "  WARNING: Some tests failed" -ForegroundColor Yellow
    }
} else {
    Write-Host "[6/6] Skipping tests"
}

Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host " CODEBRIDGE INSTALLED" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host " Gateway URL:  http://127.0.0.1:8787"
Write-Host ""
Write-Host " +------------------------------------------"
Write-Host " | ACTION REQUIRED"
Write-Host " |"
Write-Host " | Open:"
Write-Host " |   $EnvFile"
Write-Host " |"
Write-Host " | Set:"
Write-Host " |   NVIDIA_API_KEY=YOUR_KEY_HERE"
Write-Host " +------------------------------------------"
Write-Host ""
Write-Host " Then:"
Write-Host ""
Write-Host "   Test NVIDIA connection:"
Write-Host "     python scripts\test_nvidia.py"
Write-Host ""
Write-Host "   Start gateway:"
Write-Host "     .\scripts\start.ps1"
Write-Host "     # or: uv run codebridge serve"
Write-Host ""
Write-Host "   Configure Codex:"
Write-Host "     uv run python scripts\configure_codex.py"
Write-Host ""
Write-Host "   Set Codex token (PowerShell):"
Write-Host "     `$env:CODEBRIDGE_LOCAL_TOKEN=`"$Token`""
Write-Host ""
Write-Host " For persistent token, add to your PowerShell profile:"
Write-Host "   [System.Environment]::SetEnvironmentVariable('CODEBRIDGE_LOCAL_TOKEN', '$Token', 'User')"
Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
