#!/bin/bash
set -e

# ============================================================
# RDM Pro — Mac Mini Server Setup (One-Click)
# ============================================================
# This script turns your Mac Mini into a public server for
# Remote Device Management. It installs everything needed,
# sets up a Cloudflare Tunnel for public access, and starts
# all services. After running this, your system is accessible
# from anywhere in the world.
# ============================================================

echo "╔══════════════════════════════════════════════════════╗"
echo "║   RDM Pro — Mac Mini Server Setup                   ║"
echo "║   Setting up your public remote management server   ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# --- Step 1: Install Homebrew (if not installed) ---
echo "▶ Step 1/8: Checking Homebrew..."
if ! command -v brew &>/dev/null; then
    echo "  Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    eval "$(/opt/homebrew/bin/brew shellenv)" 2>/dev/null || eval "$(/usr/local/bin/brew shellenv)" 2>/dev/null
else
    echo "  ✓ Homebrew already installed"
fi

# --- Step 2: Install Dependencies ---
echo "▶ Step 2/8: Installing dependencies..."
brew install docker docker-compose cloudflared rust node postgresql@15 redis 2>/dev/null || true
brew install --cask docker 2>/dev/null || true

# Ensure Docker is running
if ! docker info &>/dev/null 2>&1; then
    echo "  Starting Docker Desktop..."
    open -a Docker
    echo "  Waiting for Docker to start (this may take 30 seconds)..."
    sleep 30
    # Wait until Docker is ready
    while ! docker info &>/dev/null 2>&1; do
        sleep 5
    done
fi
echo "  ✓ Docker is running"

# --- Step 3: Clone the repository ---
echo "▶ Step 3/8: Cloning repository..."
RDM_DIR="$HOME/rdm-server"
if [ -d "$RDM_DIR" ]; then
    echo "  Updating existing installation..."
    cd "$RDM_DIR"
    git pull origin main
else
    git clone https://github.com/krishnaashisharma/RATTT.git "$RDM_DIR"
    cd "$RDM_DIR"
fi
echo "  ✓ Repository ready at $RDM_DIR"

# --- Step 4: Generate TLS Certificates ---
echo "▶ Step 4/8: Generating TLS certificates..."
cd "$RDM_DIR/deploy"
chmod +x generate-certs.sh
./generate-certs.sh
echo "  ✓ Certificates generated"

# --- Step 5: Start Services with Docker Compose ---
echo "▶ Step 5/8: Starting backend services..."
cd "$RDM_DIR/deploy"
docker compose down 2>/dev/null || true
docker compose up -d --build

# Wait for services to be healthy
echo "  Waiting for services to start..."
sleep 15

# Verify services
echo "  Checking service health..."
docker compose ps
echo "  ✓ Backend services running"

# --- Step 6: Set up Cloudflare Tunnel (Public Access) ---
echo "▶ Step 6/8: Setting up Cloudflare Tunnel for public access..."
echo ""
echo "  ┌─────────────────────────────────────────────────────┐"
echo "  │ Cloudflare Tunnel provides a FREE public URL        │"
echo "  │ No port forwarding, no static IP needed!            │"
echo "  └─────────────────────────────────────────────────────┘"
echo ""

# Check if already authenticated
if ! cloudflared tunnel list &>/dev/null 2>&1; then
    echo "  You need to authenticate with Cloudflare (one-time):"
    echo "  Running: cloudflared tunnel login"
    echo ""
    cloudflared tunnel login
fi

# Create tunnel
TUNNEL_NAME="rdm-server"
cloudflared tunnel delete "$TUNNEL_NAME" 2>/dev/null || true
cloudflared tunnel create "$TUNNEL_NAME"

# Get tunnel ID
TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}')
echo "  Tunnel ID: $TUNNEL_ID"

# Create tunnel config
TUNNEL_CONFIG="$HOME/.cloudflared/config.yml"
cat > "$TUNNEL_CONFIG" << EOF
tunnel: $TUNNEL_ID
credentials-file: $HOME/.cloudflared/${TUNNEL_ID}.json

ingress:
  - hostname: rdm-api.${TUNNEL_ID}.cfargotunnel.com
    service: https://localhost:8443
    originRequest:
      noTLSVerify: true
  - hostname: rdm-dashboard.${TUNNEL_ID}.cfargotunnel.com
    service: http://localhost:3000
  - service: http_status:404
EOF

echo "  ✓ Tunnel configured"

# --- Step 7: Start the tunnel ---
echo "▶ Step 7/8: Starting Cloudflare Tunnel..."

# Create LaunchDaemon for auto-start
PLIST_PATH="$HOME/Library/LaunchAgents/com.rdm.cloudflared.plist"
cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.rdm.cloudflared</string>
    <key>ProgramArguments</key>
    <array>
        <string>$(which cloudflared)</string>
        <string>tunnel</string>
        <string>run</string>
        <string>$TUNNEL_NAME</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardErrorPath</key>
    <string>/tmp/cloudflared.err.log</string>
    <key>StandardOutPath</key>
    <string>/tmp/cloudflared.out.log</string>
</dict>
</plist>
EOF

launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl load "$PLIST_PATH"

# Also start immediately
cloudflared tunnel run "$TUNNEL_NAME" &
TUNNEL_PID=$!
sleep 5

echo "  ✓ Tunnel running (PID: $TUNNEL_PID)"

# --- Step 8: Quick Start Tunnel (Alternative: No Cloudflare account needed) ---
echo "▶ Step 8/8: Creating quick-access tunnel..."
echo ""
echo "  If you don't have a Cloudflare account, use this instead:"
echo "  Run: cloudflared tunnel --url http://localhost:8443"
echo ""
echo "  This gives you a temporary public URL instantly."
echo ""

# Start a quick tunnel for immediate access
cloudflared tunnel --url http://localhost:8443 > /tmp/rdm-tunnel.log 2>&1 &
sleep 5
PUBLIC_URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /tmp/rdm-tunnel.log | head -1)

# --- Final Output ---
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║   ✅ SETUP COMPLETE!                                ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║                                                      ║"
echo "║   Your RDM Server is now PUBLIC:                     ║"
echo "║                                                      ║"
if [ -n "$PUBLIC_URL" ]; then
echo "║   🌐 Public URL: $PUBLIC_URL"
fi
echo "║                                                      ║"
echo "║   Local URLs:                                        ║"
echo "║   • Backend API:  https://localhost:8443             ║"
echo "║   • Dashboard:    http://localhost:3000              ║"
echo "║   • PostgreSQL:   localhost:5432                     ║"
echo "║   • Redis:        localhost:6379                     ║"
echo "║                                                      ║"
echo "║   Default Login:                                     ║"
echo "║   • Username: admin                                  ║"
echo "║   • Password: admin                                  ║"
echo "║                                                      ║"
echo "║   Services auto-start on reboot.                     ║"
echo "║                                                      ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║   NEXT STEPS:                                        ║"
echo "║                                                      ║"
echo "║   1. Open the mobile app (RDM Pro)                   ║"
echo "║   2. Go to Settings                                  ║"
echo "║   3. Enter the Public URL above                      ║"
echo "║   4. Login with admin/admin                          ║"
echo "║   5. Your devices will appear!                       ║"
echo "║                                                      ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# Save the public URL for reference
echo "$PUBLIC_URL" > "$RDM_DIR/.public-url"
echo "Public URL saved to: $RDM_DIR/.public-url"
