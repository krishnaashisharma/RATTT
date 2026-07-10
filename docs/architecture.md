# System Architecture

## Overview

The Remote Device Management system is a three-tier architecture designed for secure, scalable remote management of macOS and Windows devices.

```
┌─────────────────┐          WebSocket (wss://)          ┌─────────────────┐
│   Agent (Rust)  │◄──────────────────────────────────►│  Backend (FastAPI)│
│  macOS / Windows │  TLS 1.3 + Mutual Auth + JWT token  │  + Redis pub/sub │
└──────┬──────────┘                                      └────────┬────────┘
       │                                                          │
       │ System Tray / Taskbar Icon                               │ REST API (HTTPS)
       │ (user consent: pause/revoke)                             │
       │                                                          │
       ▼                                                          ▼
┌─────────────────┐                                      ┌─────────────────┐
│  Local Secure   │                                      │  Dashboard (React)│
│  Storage        │                                      │  Role‑based Access│
│ (Keychain/TPM)  │                                      └─────────────────┘
└─────────────────┘
```

## Component Details

### Agent (Rust)

**Purpose:** Background service that runs on managed devices and communicates with the backend.

**Key Features:**
- **Async I/O:** Built on Tokio runtime for efficient resource usage
- **Persistent Connection:** Maintains a single multiplexed WebSocket connection
- **mTLS:** Uses TLS 1.3 with client certificates for mutual authentication
- **Secure Storage:** Encrypts configuration and tokens using platform-specific secure stores
- **Consent UI:** System-tray icon with pause/resume and revoke options
- **Auto-Update:** Self-updating with signature verification
- **Audit Logging:** Encrypted local log of all executed actions

**Architecture:**
```
┌─────────────────────────────────────────┐
│         Tokio Runtime                   │
├─────────────────────────────────────────┤
│  Main Command Dispatcher Loop           │
│  ├─ WebSocket Reader                    │
│  ├─ Command Handler                     │
│  └─ Response Sender                     │
├─────────────────────────────────────────┤
│  Background Tasks                       │
│  ├─ Heartbeat (30s interval)            │
│  ├─ Metrics Reporter (60s interval)     │
│  ├─ Token Rotator (hourly)              │
│  └─ Update Checker (6h interval)        │
├─────────────────────────────────────────┤
│  System Integration                     │
│  ├─ System Tray UI                      │
│  ├─ Secure Config Storage               │
│  ├─ Command Execution                   │
│  └─ Audit Log                           │
└─────────────────────────────────────────┘
```

**Supported Commands:**
- `ping` — Verify connectivity
- `get_system_info` — Retrieve OS, CPU, memory info
- `list_processes` — List running processes
- `file_transfer` — Upload/download files (chunked)

### Backend (FastAPI)

**Purpose:** Central management server that coordinates agents and serves the dashboard.

**Key Features:**
- **WebSocket Multiplexing:** Handles thousands of concurrent agent connections
- **JWT Authentication:** Stateless auth for both users and devices
- **Casbin RBAC:** Policy-based command authorization
- **Redis Pub/Sub:** Enables horizontal scaling across multiple instances
- **PostgreSQL:** Persistent storage for devices, audit logs, and policies
- **Real-Time Updates:** WebSocket endpoint for dashboard live status

**Architecture:**
```
┌─────────────────────────────────────────┐
│         FastAPI Application             │
├─────────────────────────────────────────┤
│  REST API Endpoints                     │
│  ├─ /api/auth/* — User authentication   │
│  ├─ /api/devices/* — Device management  │
│  ├─ /api/enrolment/* — Device enrolment │
│  ├─ /api/updates/* — Update management  │
│  └─ /api/audit/* — Audit logs           │
├─────────────────────────────────────────┤
│  WebSocket Endpoints                    │
│  ├─ /ws/agent — Agent connections      │
│  └─ /ws/dashboard — Dashboard updates   │
├─────────────────────────────────────────┤
│  Services Layer                         │
│  ├─ Device Service                      │
│  ├─ Command Service                     │
│  ├─ Audit Service                       │
│  └─ Auth Service                        │
├─────────────────────────────────────────┤
│  Data Layer                             │
│  ├─ PostgreSQL (persistence)            │
│  ├─ Redis (pub/sub, caching)            │
│  └─ Casbin (policy enforcement)         │
└─────────────────────────────────────────┘
```

**Database Schema:**

```sql
-- Devices
CREATE TABLE devices (
  id UUID PRIMARY KEY,
  os VARCHAR(50),
  hostname VARCHAR(255),
  last_heartbeat TIMESTAMP,
  status VARCHAR(20),
  token_hash VARCHAR(255),
  public_key TEXT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Enrolment Tokens
CREATE TABLE enrolment_tokens (
  id UUID PRIMARY KEY,
  token_hash VARCHAR(255) UNIQUE,
  used BOOLEAN DEFAULT FALSE,
  expiry TIMESTAMP,
  created_by UUID,
  created_at TIMESTAMP
);

-- Audit Logs
CREATE TABLE audit_logs (
  id UUID PRIMARY KEY,
  device_id UUID REFERENCES devices(id),
  user_id UUID,
  action VARCHAR(100),
  timestamp TIMESTAMP,
  details JSONB,
  created_at TIMESTAMP
);

-- Update Artifacts
CREATE TABLE update_artifacts (
  id UUID PRIMARY KEY,
  version VARCHAR(20),
  platform VARCHAR(50),
  binary_url VARCHAR(500),
  checksum VARCHAR(255),
  signature TEXT,
  rollout_percentage INT,
  created_at TIMESTAMP
);
```

### Dashboard (React/Next.js)

**Purpose:** Web-based management interface for administrators and operators.

**Key Features:**
- **Real-Time Status:** WebSocket-driven live device status
- **Command Execution:** Secure command dispatch with policy enforcement
- **File Transfer:** Upload/download files to/from devices
- **Audit Viewer:** Search and filter audit logs
- **RBAC:** Role-based UI with admin and user roles

**Pages:**
- `/login` — User authentication
- `/devices` — Device list with live status
- `/devices/[id]` — Device detail and command interface
- `/audit` — Audit log viewer

## Data Flows

### Device Registration

```
1. Admin generates enrolment token via dashboard
   → Backend stores hashed token in DB

2. Agent runs in enrolment mode with token
   → Agent → POST /api/devices/register
   → Backend validates token, generates device JWT
   → Backend stores device in DB
   → Agent stores JWT in secure storage

3. Agent connects via WebSocket
   → Agent → WebSocket /ws/agent?token=<device_jwt>
   → Backend verifies JWT, adds to ConnectionManager
   → Agent sends auth message
   → Connection established
```

### Command Execution

```
1. User clicks "Execute" in dashboard
   → Dashboard → POST /api/devices/{id}/command
   → Backend verifies user JWT
   → Backend checks Casbin policy
   → Backend looks up agent in ConnectionManager
   → Backend sends command via WebSocket

2. Agent receives command
   → Agent executes command
   → Agent sends response via WebSocket
   → Backend receives response
   → Backend sends to dashboard via WebSocket

3. Dashboard receives response
   → Dashboard updates UI with result
   → User sees command output
```

### Real-Time Status Update

```
1. Agent sends heartbeat every 30 seconds
   → Agent → WebSocket /ws/agent
   → Backend updates device.last_heartbeat in DB
   → Backend publishes to Redis: "device_heartbeat:{device_id}"

2. Dashboard WebSocket listener receives event
   → Dashboard → WebSocket /ws/dashboard
   → Backend forwards Redis event to dashboard
   → Dashboard updates device status badge

3. User sees live status
   → Device shows "Connected" (green)
   → Last heartbeat timestamp updates
```

## Security Model

### Authentication

**User Authentication:**
- Username/password → JWT (1-hour TTL)
- JWT claims include: `sub` (user_id), `role` (admin/user), `exp`

**Device Authentication:**
- Enrolment token (one-time) → Device JWT (1-hour TTL)
- Device JWT claims include: `sub` (device_id), `os`, `exp`
- Tokens rotated hourly via `token_refresh` message

### Authorization

**User Authorization (RBAC):**
- Dashboard checks user role from JWT claims
- Admin-only actions (enrolment, updates) hidden for non-admins

**Command Authorization (Casbin):**
- Policy engine enforces: `(user_id, device_id, command) → allow/deny`
- Example policies:
  - `admin, *, *` — Admin can do anything
  - `user, device_*, ping` — User can ping any device
  - `user, device_123, *` — User can do anything on device_123

### Encryption

**Transport Security:**
- TLS 1.3 with mutual authentication (mTLS)
- Agent presents client certificate
- Backend verifies client certificate against CA

**Data at Rest:**
- Agent config/logs: AES-256-GCM with key from platform secure store
- Backend: PostgreSQL with optional encryption-at-rest
- Audit logs: Cryptographically signed for non-repudiation

### Consent & Transparency

**System-Tray UI:**
- Shows connection status (green/grey/red)
- Pause/Resume option (pauses command execution)
- Revoke option (deletes token, unregisters device)
- Activity log (last 50 actions)

**Audit Trail:**
- Every action logged with timestamp, user, device, and details
- Backend stores immutable, signed audit log
- Agent stores encrypted local copy for transparency

## Scalability

### Horizontal Scaling

**Backend Scaling:**
- Multiple FastAPI instances behind a load balancer
- Redis pub/sub routes commands to correct instance
- PostgreSQL as single source of truth

**Agent Scaling:**
- Each agent maintains single WebSocket connection
- Backend can handle thousands of concurrent connections
- Heartbeat-based device discovery

### Performance Considerations

- **Heartbeat Interval:** 30 seconds (configurable)
- **Token Rotation:** Hourly (configurable)
- **Update Check:** Every 6 hours (configurable)
- **Metrics Reporting:** Every 60 seconds (configurable)
- **File Transfer Chunk Size:** 10 MB per chunk (configurable)

## Deployment

### Local Development

- Docker Compose with postgres, redis, backend, dashboard
- Self-signed certificates for TLS
- Single-instance backend

### Production

- Kubernetes deployment (see `deploy/k8s/`)
- Let's Encrypt certificates
- Multi-instance backend with load balancer
- Managed PostgreSQL (RDS, Cloud SQL, etc.)
- Managed Redis (ElastiCache, Cloud Memorystore, etc.)
- Agent distribution via S3/CDN

## Monitoring & Observability

**Logging:**
- Structured logging with `tracing` crate (agent)
- Structured logging with `logging` module (backend)
- All logs include: timestamp, level, component, message

**Metrics:**
- Prometheus-compatible metrics endpoint (future)
- Device connection count
- Command execution latency
- Error rates

**Audit Trail:**
- Immutable audit log in PostgreSQL
- Cryptographically signed for non-repudiation
- Queryable via `/api/audit` endpoint

## Future Enhancements

- [ ] Multi-factor authentication (MFA)
- [ ] Device groups and policies
- [ ] Scheduled commands
- [ ] Script execution engine
- [ ] Remote shell/terminal
- [ ] Desktop sharing
- [ ] Mobile app (iOS/Android)
- [ ] Kubernetes operator
- [ ] Terraform provider
