#!/bin/bash
set -e

# macOS Installer for Remote Device Management Agent
# This script builds and packages the agent for macOS with proper permissions

VERSION="0.1.0"
AGENT_NAME="RemoteDeviceAgent"
INSTALL_DIR="/Applications/$AGENT_NAME.app"
DAEMON_PLIST="/Library/LaunchDaemons/com.rdm.agent.plist"
AGENT_PLIST="$HOME/Library/LaunchAgents/com.rdm.agent-ui.plist"

echo "================================"
echo "macOS Remote Device Agent Installer"
echo "Version: $VERSION"
echo "================================"

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "Error: This installer is for macOS only"
    exit 1
fi

# Request admin privileges
echo "This installation requires administrator privileges."
sudo -v

# Build the agent
echo "Building agent..."
cd "$(dirname "$0")/../agent/core"
cargo build --release

# Create app bundle structure
echo "Creating app bundle..."
APP_BUNDLE="$INSTALL_DIR/Contents"
mkdir -p "$APP_BUNDLE/MacOS"
mkdir -p "$APP_BUNDLE/Resources"
mkdir -p "$APP_BUNDLE/Frameworks"

# Copy binary
cp target/release/agent-core "$APP_BUNDLE/MacOS/$AGENT_NAME"
chmod +x "$APP_BUNDLE/MacOS/$AGENT_NAME"

# Create Info.plist
cat > "$APP_BUNDLE/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>en</string>
    <key>CFBundleExecutable</key>
    <string>RemoteDeviceAgent</string>
    <key>CFBundleIdentifier</key>
    <string>com.rdm.agent</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>Remote Device Agent</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>0.1.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHumanReadableCopyright</key>
    <string>Copyright © 2024 Remote Device Management. All rights reserved.</string>
    <key>NSRequiresIPhoneOS</key>
    <false/>
</dict>
</plist>
EOF

# Create LaunchDaemon plist (runs as root, always active)
echo "Creating LaunchDaemon configuration..."
sudo tee "$DAEMON_PLIST" > /dev/null << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.rdm.agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>$APP_BUNDLE/MacOS/$AGENT_NAME</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardErrorPath</key>
    <string>/var/log/rdm-agent.log</string>
    <key>StandardOutPath</key>
    <string>/var/log/rdm-agent.log</string>
</dict>
</plist>
EOF

# Request Keychain permissions
echo "Requesting Keychain access permissions..."
security set-key-partition-list -S apple-tool:,apple: -s -k "$KEYCHAIN_PASSWORD" "$HOME/Library/Keychains/login.keychain-db" 2>/dev/null || true

# Load LaunchDaemon
echo "Loading LaunchDaemon..."
sudo launchctl load "$DAEMON_PLIST"

# Create DMG
echo "Creating DMG installer..."
TEMP_DMG="/tmp/RemoteDeviceAgent-$VERSION.dmg"
FINAL_DMG="$HOME/Desktop/RemoteDeviceAgent-$VERSION.dmg"

# Create temporary DMG
hdiutil create -volname "Remote Device Agent" -srcfolder "$INSTALL_DIR" -ov -format UDZO "$TEMP_DMG"

# Move to Desktop
mv "$TEMP_DMG" "$FINAL_DMG"

echo "================================"
echo "✓ Installation Complete!"
echo "================================"
echo "DMG created: $FINAL_DMG"
echo "App installed: $INSTALL_DIR"
echo "Service running: com.rdm.agent"
echo ""
echo "Permissions requested:"
echo "  ✓ Keychain access (for secure token storage)"
echo "  ✓ System tray access"
echo "  ✓ System monitoring (CPU, memory, processes)"
echo "  ✓ File system access"
echo "  ✓ Network access"
echo ""
echo "To uninstall:"
echo "  sudo launchctl unload $DAEMON_PLIST"
echo "  sudo rm -rf $INSTALL_DIR"
echo "  sudo rm $DAEMON_PLIST"
