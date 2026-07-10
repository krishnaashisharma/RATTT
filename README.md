# Remote Device Management System

A production-ready, three-tier cross-platform remote device management platform with secure WebSocket communication, role-based access control, and comprehensive audit logging.

## Architecture

### Components

1. **Agent** (Rust) — Background service running on macOS/Windows devices
   - Persistent WebSocket connection with TLS 1.3 mutual authentication
   - Secure configuration storage (Keychain/DPAPI)
   - System-tray consent UI with pause/revoke functionality
   - Auto-update mechanism with signature verification
   - Encrypted local audit log

2. **Backend** (FastAPI) — Central management server
   - WebSocket endpoints for agents and dashboard
   - JWT-based authentication and device enrolment
   - Casbin-based command authorization (RBAC)
   - Redis pub/sub for horizontal scaling
   - PostgreSQL database for persistence
   - Comprehensive audit trail

3. **Dashboard** (React/Next.js) — Web-based management interface
   - Real-time device status via WebSocket
   - Secure command execution with policy enforcement
   - File transfer capability
   - Audit log viewer
   - Role-based access control

## Quick Start

### Prerequisites

- Docker & Docker Compose
- OpenSSL (for certificate generation)
- Rust 1.70+ (for building the agent)
- Node.js 18+ (for dashboard development)
- Python 3.11+ (for backend development)

### Setup

1. **Generate self-signed certificates:**
   ```bash
   cd deploy
   ./generate-certs.sh
   ```

2. **Start the backend, database, and dashboard:**
   ```bash
   cd deploy
   docker-compose up -d
   ```

3. **Verify services are running:**
   ```bash
   docker-compose ps
   ```

4. **Access the dashboard:**
   - URL: https://localhost:3000
   - (Note: Use `http://localhost:3000` for development without SSL)

### Build the Agent

```bash
cd agent/core
cargo build --release
```

The compiled binary will be at `target/release/agent-core`.

## Development

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --ssl-keyfile ../deploy/certs/server.key --ssl-certfile ../deploy/certs/server.crt
```

### Dashboard

```bash
cd dashboard
npm install
npm run dev
```

Open http://localhost:3000 in your browser.

### Agent

```bash
cd agent/core
cargo run
```

## API Reference

### REST Endpoints

- `POST /api/auth/login` — User login
- `POST /api/enrolment/generate` — Generate enrolment token (admin)
- `POST /api/devices/register` — Device registration
- `GET /api/devices` — List devices
- `GET /api/devices/{id}` — Get device details
- `POST /api/devices/{id}/command` — Execute command
- `GET /api/updates/check` — Check for updates
- `GET /api/audit` — View audit logs

### WebSocket Endpoints

- `/ws/agent` — Agent connection (requires device JWT)
- `/ws/dashboard` — Dashboard real-time updates (requires user JWT)

## Security

- **Transport:** TLS 1.3 with mutual authentication (mTLS)
- **Authentication:** JWT tokens with hourly rotation
- **Authorization:** Casbin RBAC with device-command policies
- **Encryption:** AES-256-GCM for data at rest
- **Audit:** Immutable, cryptographically-linked audit trail
- **Consent:** System-tray UI with pause/revoke capabilities

## Project Structure

```
remote-device-mgmt/
├── agent/                    # Rust agent
│   ├── core/                 # Main agent crate
│   ├── macos/                # macOS-specific code
│   └── windows/              # Windows-specific code
├── backend/                  # FastAPI backend
│   ├── app/                  # Application code
│   ├── casbin/               # Policy definitions
│   └── alembic/              # Database migrations
├── dashboard/                # React/Next.js dashboard
│   └── src/                  # Source code
├── deploy/                   # Deployment scripts
│   ├── docker-compose.yml
│   ├── generate-certs.sh
│   └── enrolment-token.sh
└── docs/                     # Documentation
```

## Implementation Status

- [x] Phase 0: Project scaffold & infrastructure
- [ ] Phase 1: Backend core (auth, device registration, WebSocket)
- [ ] Phase 2: Rust agent core (connection, commands)
- [ ] Phase 3: Agent enrolment & secure storage
- [ ] Phase 4: Consent UI (system tray)
- [ ] Phase 5: Auto-update mechanism
- [ ] Phase 6: React dashboard
- [ ] Phase 7: Dashboard real-time WebSocket
- [ ] Phase 8: Integration & testing

## License

MIT

## Contributing

See CONTRIBUTING.md for guidelines.
