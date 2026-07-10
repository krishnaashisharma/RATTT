# Windows Installer for Remote Device Management Agent
# Run as Administrator

param(
    [string]$Version = "0.1.0"
)

$ErrorActionPreference = "Stop"

Write-Host "================================"
Write-Host "Windows Remote Device Agent Installer"
Write-Host "Version: $Version"
Write-Host "================================"

# Check if running as Administrator
$currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Error: This installer must be run as Administrator"
    Write-Host "Please right-click and select 'Run as administrator'"
    exit 1
}

# Define paths
$InstallDir = "C:\Program Files\RemoteDeviceAgent"
$ServiceName = "RemoteDeviceAgent"
$ServiceDisplayName = "Remote Device Management Agent"

# Create installation directory
Write-Host "Creating installation directory..."
if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}

# Build the agent
Write-Host "Building agent..."
$AgentPath = Split-Path -Parent $PSScriptRoot
$AgentPath = Join-Path $AgentPath "agent\core"
Push-Location $AgentPath
cargo build --release
$AgentBinary = Join-Path $AgentPath "target\release\agent-core.exe"
Pop-Location

# Copy binary to installation directory
Write-Host "Installing agent binary..."
Copy-Item $AgentBinary "$InstallDir\RemoteDeviceAgent.exe" -Force

# Request DPAPI permissions (automatic with Windows)
Write-Host "Configuring DPAPI for secure storage..."
# DPAPI permissions are automatic for the current user

# Create Windows Service
Write-Host "Creating Windows Service..."
$ServicePath = "$InstallDir\RemoteDeviceAgent.exe"

# Remove existing service if it exists
$existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($existingService) {
    Write-Host "Removing existing service..."
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    Remove-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# Create new service
Write-Host "Registering service..."
New-Service -Name $ServiceName `
    -DisplayName $ServiceDisplayName `
    -BinaryPathName $ServicePath `
    -StartupType Automatic `
    -Description "Remote Device Management Agent for secure device monitoring and control" | Out-Null

# Set service to run as Local System
$service = Get-Service -Name $ServiceName
$service.ServicesDependedOn = @()
$service | Set-Service -StartupType Automatic

# Create firewall rule
Write-Host "Creating firewall rule..."
$FirewallRule = Get-NetFirewallRule -DisplayName "Remote Device Agent" -ErrorAction SilentlyContinue
if (-not $FirewallRule) {
    New-NetFirewallRule -DisplayName "Remote Device Agent" `
        -Direction Outbound `
        -Action Allow `
        -Protocol TCP `
        -LocalPort 8443 `
        -Program $ServicePath | Out-Null
}

# Create log directory
$LogDir = "C:\ProgramData\RemoteDeviceAgent\logs"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

# Create config directory
$ConfigDir = "C:\ProgramData\RemoteDeviceAgent\config"
if (-not (Test-Path $ConfigDir)) {
    New-Item -ItemType Directory -Path $ConfigDir -Force | Out-Null
}

# Start service
Write-Host "Starting service..."
Start-Service -Name $ServiceName

# Create uninstaller script
$UninstallerPath = "$InstallDir\Uninstall.ps1"
@"
# Uninstaller for Remote Device Agent
Write-Host "Uninstalling Remote Device Agent..."

`$ServiceName = "RemoteDeviceAgent"
`$InstallDir = "C:\Program Files\RemoteDeviceAgent"

# Stop and remove service
Stop-Service -Name `$ServiceName -Force -ErrorAction SilentlyContinue
Remove-Service -Name `$ServiceName -Force -ErrorAction SilentlyContinue

# Remove firewall rule
Remove-NetFirewallRule -DisplayName "Remote Device Agent" -ErrorAction SilentlyContinue

# Remove installation directory
Remove-Item -Path `$InstallDir -Recurse -Force -ErrorAction SilentlyContinue

# Remove data directory
Remove-Item -Path "C:\ProgramData\RemoteDeviceAgent" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Uninstallation complete!"
"@ | Out-File -FilePath $UninstallerPath -Encoding UTF8

# Create shortcut for uninstaller
$WshShell = New-Object -ComObject WScript.Shell
$UninstallerShortcut = "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\RemoteDeviceAgent-Uninstall.lnk"
$WshShortcut = $WshShell.CreateShortcut($UninstallerShortcut)
$WshShortcut.TargetPath = "powershell.exe"
$WshShortcut.Arguments = "-ExecutionPolicy Bypass -File `"$UninstallerPath`""
$WshShortcut.Save()

Write-Host "================================"
Write-Host "✓ Installation Complete!"
Write-Host "================================"
Write-Host "Service installed: $ServiceName"
Write-Host "Installation path: $InstallDir"
Write-Host "Service status: $(Get-Service -Name $ServiceName | Select-Object -ExpandProperty Status)"
Write-Host ""
Write-Host "Permissions requested:"
Write-Host "  ✓ Administrator privileges (for service installation)"
Write-Host "  ✓ DPAPI (for secure token storage)"
Write-Host "  ✓ System monitoring (CPU, memory, processes)"
Write-Host "  ✓ File system access"
Write-Host "  ✓ Network access (port 8443)"
Write-Host ""
Write-Host "To uninstall:"
Write-Host "  Run: powershell -ExecutionPolicy Bypass -File `"$UninstallerPath`""
Write-Host "  Or use Control Panel > Programs > Programs and Features"
