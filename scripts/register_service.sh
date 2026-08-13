#!/usr/bin/env bash
# register_service.sh — Configura CodeBridge para que arranque automáticamente en macOS, Linux o WSL.

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_BIN="$DIR/.venv/bin/codebridge"

# Validar existencia de .venv
if [ ! -f "$VENV_BIN" ]; then
    echo "✗ Entorno virtual no detectado. Por favor, ejecuta primero: bash scripts/setup.sh"
    exit 1
fi

detect_os() {
    case "$(uname -s)" in
        Darwin)
            echo "mac"
            ;;
        Linux)
            if grep -qi microsoft /proc/version; then
                echo "wsl"
            else
                echo "linux"
            fi
            ;;
        *)
            echo "unknown"
            ;;
    esac
}

OS=$(detect_os)
echo "Sistema detectado: $OS"

case "$OS" in
    mac)
        PLIST_PATH="$HOME/Library/LaunchAgents/com.codebridge.gateway.plist"
        echo "Configurando launchd para macOS..."
        mkdir -p "$(dirname "$PLIST_PATH")"
        cat <<EOF > "$PLIST_PATH"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.codebridge.gateway</string>
    <key>ProgramArguments</key>
    <array>
        <string>$VENV_BIN</string>
        <string>serve</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$DIR/codebridge_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>$DIR/codebridge_stderr.log</string>
</dict>
</plist>
EOF
        launchctl unload "$PLIST_PATH" 2>/dev/null
        launchctl load "$PLIST_PATH"
        echo "✓ macOS launchd configurado e iniciado."
        ;;

    linux|wsl)
        # Intentar con systemd si está activo y disponible
        if systemctl --user show-environment >/dev/null 2>&1; then
            echo "Configurando systemd user service..."
            SERVICE_DIR="$HOME/.config/systemd/user"
            mkdir -p "$SERVICE_DIR"
            cat <<EOF > "$SERVICE_DIR/codebridge.service"
[Unit]
Description=CodeBridge Gateway
After=network.target

[Service]
Type=simple
WorkingDirectory=$DIR
ExecStart=$VENV_BIN serve
Restart=always
RestartSec=3
StandardOutput=append:$DIR/codebridge_stdout.log
StandardError=append:$DIR/codebridge_stderr.log

[Install]
WantedBy=default.target
EOF
            systemctl --user daemon-reload
            systemctl --user enable codebridge
            systemctl --user restart codebridge
            echo "✓ Servicio de systemd habilitado e iniciado."
        else
            echo "systemd no está disponible en este entorno (común en WSL sin systemd habilitado)."
            echo "Agregando arranque automático al archivo de perfil del shell..."
            
            HOOK_CODE="
# CodeBridge Gateway Auto-start Hook
if ! curl -s http://127.0.0.1:8787/health > /dev/null 2>&1; then
    bash \"$DIR/scripts/cb\" mcp > /dev/null 2>&1 &
fi
"
            
            # Buscar el shell activo del usuario
            SHELL_PROFILE=""
            if [ -n "$ZSH_VERSION" ] || [ -f "$HOME/.zshrc" ]; then
                SHELL_PROFILE="$HOME/.zshrc"
            elif [ -f "$HOME/.bashrc" ]; then
                SHELL_PROFILE="$HOME/.bashrc"
            elif [ -f "$HOME/.profile" ]; then
                SHELL_PROFILE="$HOME/.profile"
            fi
            
            if [ -n "$SHELL_PROFILE" ]; then
                if grep -q "CodeBridge Gateway Auto-start Hook" "$SHELL_PROFILE" 2>/dev/null; then
                    echo "✓ El gancho de autoarranque ya está en $SHELL_PROFILE"
                else
                    echo "$HOOK_CODE" >> "$SHELL_PROFILE"
                    echo "✓ Agregado gancho de inicio automático a $SHELL_PROFILE"
                fi
            else
                echo "⚠ No se detectó un archivo de perfil de shell (.bashrc, .zshrc). Por favor, agrégalo manualmente."
            fi
        fi
        ;;
    *)
        echo "✗ Sistema operativo no soportado por este script. Si usas Windows nativo, usa register_service.ps1."
        exit 1
        ;;
esac
