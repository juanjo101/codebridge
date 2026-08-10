# Start CodeBridge Gateway (Windows PowerShell)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir

Set-Location $ProjectDir

Write-Host "Starting CodeBridge Gateway..."
Write-Host "Press Ctrl+C to stop."
Write-Host ""

uv run codebridge serve
