# Getting Started

This guide walks you through setting up and running the Remote Device Management system for local development.

## Prerequisites

- **Docker & Docker Compose** — For running backend, database, and dashboard
- **Rust 1.70+** — For building the agent
- **Node.js 18+** — For dashboard development
- **Python 3.11+** — For backend development
- **OpenSSL** — For certificate generation
- **Git** — For version control

## Step 1: Clone and Navigate

```bash
git clone <repository-url>
cd remote-device-mgmt
```

## Step 2: Generate Self-Signed Certificates

The system uses TLS 1.3 with mutual authentication. For development, we'll generate self-signed certificates:

```bash
cd deploy
./generate-certs.sh
cd ..
```

This creates:
- `deploy/certs/ca.crt` — Certificate Authority
- `deploy/certs/server.crt` / `server.key` — Backend server certificate
- `deploy/certs/client.crt` / `client.key` — Agent client certificate

## Step 3: Start Backend Services

Start PostgreSQL, Redis, and the FastAPI backend using Docker Compose:

```bash
cd deploy
docker-compose up -d
cd ..
```

Verify services are running:
```bash
docker-compose ps
```

Expected output:
```
CONTAINER ID   IMAGE                    STATUS
...            rdm-postgres             healthy
...            rdm-redis                healthy
...            rdm-backend              healthy
...            rdm-dashboard            healthy
```

## Step 4: Access the Dashboard

Open your browser and navigate to:
- **Development:** http://localhost:3000
- **Production (with SSL):** https://localhost:3000

You should see the Remote Device Management dashboard.

## Step 5: Build the Agent

In a new terminal, build the Rust agent:

```bash
cd agent/core
cargo build --release
```

The compiled binary will be at `target/release/agent-core`.

## Step 6: Enrol a Device

To register a device with the backend:

1. **Generate an enrolment token** (via backend API or dashboard admin panel):
   ```bash
   # TODO: Implement via API
   ENROLMENT_TOKEN="<generated-token>"
   ```

2. **Run the agent in enrolment mode:**
   ```bash
   ./agent/core/target/release/agent-core --enrol \
     --token "$ENROLMENT_TOKEN" \
     --server wss://localhost:8443 \
     --ca-cert deploy/certs/ca.crt \
     --client-cert deploy/certs/client.crt \
     --client-key deploy/certs/client.key
   ```

3. **Verify device appears in dashboard:**
   - Refresh the dashboard at http://localhost:3000
   - You should see the device in the device list with "Connected" status

## Step 7: Test a Command

1. **In the dashboard:**
   - Click on the device in the list
   - Select "Ping" from the command dropdown
   - Click "Execute"

2. **Verify the response:**
   - The dashboard should show "Pong" as the result
   - The agent's audit log should record the action

## Development Workflow

### Backend Development

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload \
  --ssl-keyfile ../deploy/certs/server.key \
  --ssl-certfile ../deploy/certs/server.crt
```

The backend will reload on file changes.

### Dashboard Development

```bash
cd dashboard
npm install
npm run dev
```

Open http://localhost:3000. The dashboard will hot-reload on file changes.

### Agent Development

```bash
cd agent/core
cargo watch -x run
```

Requires `cargo-watch`: `cargo install cargo-watch`

## Troubleshooting

### Docker Compose fails to start

**Problem:** `Error response from daemon: driver failed programming external connectivity`

**Solution:** Ensure Docker daemon is running and no other services are using ports 5432, 6379, 8443, or 3000.

### Agent fails to connect

**Problem:** `TLS handshake error` or `certificate verification failed`

**Solution:** 
- Ensure certificates were generated: `ls deploy/certs/`
- Verify the CA certificate path is correct
- Check backend is running: `docker-compose ps`

### Dashboard shows "Connection refused"

**Problem:** Dashboard cannot reach the backend

**Solution:**
- Verify backend is running: `docker-compose logs backend`
- Check the API URL in the dashboard environment: `echo $NEXT_PUBLIC_API_URL`
- Ensure CORS is enabled in the backend

### Agent fails to build

**Problem:** `error: linker 'cc' not found`

**Solution:** Install build tools:
- **macOS:** `xcode-select --install`
- **Ubuntu:** `sudo apt-get install build-essential`
- **Windows:** Install Visual Studio Build Tools

## Next Steps

1. **Explore the codebase:**
   - Backend: `backend/app/`
   - Agent: `agent/core/src/`
   - Dashboard: `dashboard/src/`

2. **Read the architecture documentation:**
   - `docs/architecture.md` — System design overview
   - `docs/threat-model.md` — Security analysis
   - `docs/api-reference.md` — API documentation

3. **Run tests:**
   ```bash
   # Backend
   cd backend && pytest
   
   # Agent
   cd agent/core && cargo test
   ```

4. **Deploy to production:**
   - See `docs/deployment.md` for Kubernetes/cloud deployment

## Support

For issues or questions:
1. Check existing GitHub issues
2. Review the documentation in `docs/`
3. Open a new issue with reproduction steps
