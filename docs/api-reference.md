# API Reference

This document describes the REST and WebSocket APIs for the Remote Device Management system.

## REST API Endpoints

### Authentication

#### `POST /api/auth/login`
Authenticate a user and receive a JWT.

**Request Body:**
```json
{
  "username": "admin",
  "password": "password123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "user_id": "uuid...",
  "role": "admin"
}
```

### Enrolment

#### `POST /api/enrolment/generate`
Generate a one-time enrolment token (Admin only).

**Headers:** `Authorization: Bearer <user_jwt>`

**Response (200 OK):**
```json
{
  "token": "base64_url_safe_string",
  "expiry_minutes": 30
}
```

### Devices

#### `POST /api/devices/register`
Register a new device using an enrolment token.

**Request Body:**
```json
{
  "device_id": "device-123",
  "os": "macos",
  "hostname": "macbook-pro",
  "enrolment_token": "base64_url_safe_string",
  "public_key": "optional_pem_string"
}
```

**Response (200 OK):**
```json
{
  "device_token": "eyJhbGci..."
}
```

#### `GET /api/devices`
List all registered devices.

**Headers:** `Authorization: Bearer <user_jwt>`

**Response (200 OK):**
```json
[
  {
    "device_id": "device-123",
    "os": "macos",
    "hostname": "macbook-pro",
    "status": "connected",
    "last_heartbeat": "2023-10-25T12:00:00Z"
  }
]
```

#### `GET /api/devices/{id}`
Get details for a specific device.

**Headers:** `Authorization: Bearer <user_jwt>`

**Response (200 OK):**
```json
{
  "device_id": "device-123",
  "os": "macos",
  "hostname": "macbook-pro",
  "status": "connected",
  "last_heartbeat": "2023-10-25T12:00:00Z"
}
```

#### `POST /api/devices/{id}/revoke`
Revoke a device's access (Admin only).

**Headers:** `Authorization: Bearer <user_jwt>`

**Response (200 OK):**
```json
{
  "message": "Device revoked"
}
```

### Commands

#### `POST /api/devices/{id}/command`
Execute a command on a connected device.

**Headers:** `Authorization: Bearer <user_jwt>`

**Request Body:**
```json
{
  "command": "get_system_info",
  "params": {}
}
```

**Response (200 OK):**
```json
{
  "command_id": "uuid...",
  "status": "sent",
  "message": "Command sent to device"
}
```

### Audit Logs

#### `GET /api/audit`
Retrieve audit logs.

**Headers:** `Authorization: Bearer <user_jwt>`
**Query Parameters:**
- `device_id` (optional): Filter by device
- `limit` (default: 100): Maximum records to return
- `offset` (default: 0): Pagination offset

**Response (200 OK):**
```json
[
  {
    "id": "uuid...",
    "device_id": "uuid...",
    "action": "get_system_info",
    "status": "success",
    "timestamp": "2023-10-25T12:05:00Z",
    "details": { ... }
  }
]
```

### Updates

#### `GET /api/updates/check`
Check for available updates.

**Query Parameters:**
- `version`: Current agent version
- `platform`: OS platform (macos/windows)

**Response (200 OK):**
```json
{
  "available": true,
  "version": "0.2.0",
  "url": "https://downloads.example.com/agent-0.2.0.bin",
  "checksum": "sha256_hash",
  "signature": "ed25519_signature"
}
```

---

## WebSocket APIs

### Agent WebSocket (`/ws/agent`)

**Connection:** `wss://server:8443/ws/agent?token=<device_jwt>`

#### Client (Agent) Messages

**Authentication:**
```json
{
  "type": "auth",
  "device_token": "eyJhbGci...",
  "device_id": "device-123"
}
```

**Heartbeat:**
```json
{
  "type": "heartbeat",
  "device_id": "device-123",
  "timestamp": "2023-10-25T12:00:00Z"
}
```

**Metrics:**
```json
{
  "type": "metrics",
  "device_id": "device-123",
  "cpu_usage": [10.5, 12.1, 5.0, 8.2],
  "memory_used_mb": 4096,
  "memory_total_mb": 16384,
  "uptime_seconds": 86400,
  "timestamp": "2023-10-25T12:01:00Z"
}
```

**Command Response:**
```json
{
  "type": "command_response",
  "id": "command_uuid",
  "command": "get_system_info",
  "status": "success",
  "result": { ... }
}
```

**Consent Events:**
```json
{
  "type": "consent_paused"
}
```
```json
{
  "type": "consent_revoked"
}
```

#### Server (Backend) Messages

**Command Request:**
```json
{
  "type": "command",
  "id": "command_uuid",
  "command": "get_system_info",
  "params": {}
}
```

**Token Refresh:**
```json
{
  "type": "token_refresh",
  "new_token": "eyJhbGci..."
}
```

### Dashboard WebSocket (`/ws/dashboard`)

**Connection:** `wss://server:8443/ws/dashboard?token=<user_jwt>`

#### Client (Dashboard) Messages

**Subscribe to Device:**
```json
{
  "type": "subscribe",
  "device_id": "device-123"
}
```

#### Server (Backend) Messages

**Device Status Change:**
```json
{
  "type": "device_status_change",
  "device_id": "device-123",
  "status": "connected"
}
```

**Command Response Broadcast:**
```json
{
  "type": "command_response",
  "device_id": "device-123",
  "command_id": "command_uuid",
  "response": { ... }
}
```
