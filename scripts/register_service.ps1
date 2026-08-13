# register_service.ps1 — Configura CodeBridge para arrancar automáticamente en Windows (cmd/PowerShell nativo).

$Dir = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
$VenvBin = Join-Path $Dir ".venv\Scripts\codebridge.exe"

if (-not (Test-Path $VenvBin)) {
    Write-Error "✗ Entorno virtual no detectado. Por favor, ejecuta primero: powershell -ExecutionPolicy Bypass -File scripts\setup.ps1"
    Exit 1
}

Write-Host "Configurando arranque automático para Windows (Startup Shortcut)..." -ForegroundColor Cyan

$StartupFolder = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup"
$ShortcutPath = Join-Path $StartupFolder "CodeBridge.lnk"

# Crear el acceso directo en la carpeta de Inicio
try {
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = "powershell.exe"
    # Argumentos para ejecutar codebridge de forma invisible en segundo plano
    $Shortcut.Arguments = "-WindowStyle Hidden -Command ""Start-Process -FilePath '$VenvBin' -ArgumentList 'serve' -WorkingDirectory '$Dir' -WindowStyle Hidden"""
    $Shortcut.WorkingDirectory = $Dir
    $Shortcut.Description = "Lanzador de CodeBridge Gateway en segundo plano"
    $Shortcut.Save()
    
    Write-Host "✓ Acceso directo creado en: $ShortcutPath" -ForegroundColor Green
    Write-Host "✓ CodeBridge se iniciará automáticamente cada vez que inicies sesión en Windows." -ForegroundColor Green
    
    # Iniciar el servicio ahora mismo si no está corriendo
    if (-not (Get-Process -Name "codebridge" -ErrorAction SilentlyContinue)) {
        Write-Host "Iniciando CodeBridge en segundo plano ahora..." -ForegroundColor Yellow
        Start-Process -FilePath $VenvBin -ArgumentList "serve" -WorkingDirectory $Dir -WindowStyle Hidden
        Write-Host "✓ CodeBridge iniciado correctamente en segundo plano." -ForegroundColor Green
    }
}
catch {
    Write-Error "✗ No se pudo configurar el inicio automático: $_"
}
