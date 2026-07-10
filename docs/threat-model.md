# Threat Model: Remote Device Management System

This document outlines the threat model for the Remote Device Management system using the STRIDE methodology (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege).

## System Boundaries

The system consists of three main boundaries:
1. **Agent Environment:** The physical device (macOS/Windows) running the Rust agent.
2. **Backend Environment:** The server infrastructure running FastAPI, PostgreSQL, and Redis.
3. **Dashboard Environment:** The web browser running the React application.

## Threat Analysis (STRIDE)

### 1. Spoofing

**Threat:** An attacker attempts to impersonate a legitimate agent to connect to the backend.
**Mitigation:**
- **mTLS (Mutual TLS):** The backend requires a valid client certificate signed by the internal CA.
- **Device JWT:** Agents must authenticate with a device-specific JWT issued during enrolment.
- **Enrolment Tokens:** One-time, short-lived tokens required for initial registration.

**Threat:** An attacker attempts to impersonate an administrator on the dashboard.
**Mitigation:**
- **User JWT:** Strong authentication required for all dashboard endpoints.
- **Role-Based Access Control (RBAC):** Admin-only actions require specific JWT claims.

### 2. Tampering

**Threat:** An attacker modifies the agent binary on the device.
**Mitigation:**
- **Code Signing:** Binaries are signed by the OS developer program (Apple Developer ID / Windows Authenticode).
- **Auto-Update Integrity:** Updates require SHA-256 checksum and Ed25519 signature verification before application.

**Threat:** An attacker modifies the agent configuration or tokens.
**Mitigation:**
- **Secure Storage:** Tokens and configuration are stored in platform-specific secure enclaves (macOS Keychain / Windows DPAPI).
- **Data at Rest Encryption:** Local audit logs are encrypted using AES-256-GCM.

### 3. Repudiation

**Threat:** A malicious admin executes a command and denies doing so.
**Mitigation:**
- **Audit Trail:** Every action is logged in the backend PostgreSQL database.
- **Immutable Logs:** Audit logs are cryptographically signed for non-repudiation.
- **Local Audit Log:** The agent maintains an independent, encrypted local log of all executed commands.

### 4. Information Disclosure

**Threat:** Network traffic is intercepted to read commands or data.
**Mitigation:**
- **TLS 1.3:** All communication (REST and WebSocket) is encrypted in transit using TLS 1.3.

**Threat:** Database compromise exposes sensitive device data.
**Mitigation:**
- **Hashed Tokens:** Enrolment tokens are stored as SHA-256 hashes.
- **Minimal Data:** The backend stores minimal PII (only necessary device metadata).

### 5. Denial of Service (DoS)

**Threat:** An attacker floods the backend with WebSocket connections.
**Mitigation:**
- **Rate Limiting:** (To be implemented at the API Gateway/Load Balancer level).
- **Connection Limits:** The backend enforces maximum concurrent connections per device.
- **Horizontal Scaling:** Redis pub/sub allows scaling the backend across multiple instances.

### 6. Elevation of Privilege

**Threat:** A standard user attempts to execute an admin-only command.
**Mitigation:**
- **Casbin Policy Engine:** The backend enforces granular `(user, device, command)` policies.
- **JWT Claims:** Role claims are verified on every request.

**Threat:** A compromised agent attempts to execute arbitrary code on the host device.
**Mitigation:**
- **Memory Safety:** The agent is written in Rust, eliminating entire classes of memory-safety vulnerabilities.
- **Command Whitelist:** The agent only executes explicitly defined commands (ping, system_info, etc.), not arbitrary shell scripts.
- **Consent UI:** The user can pause or revoke consent at any time via the system tray.

## Compliance Considerations

### GDPR / CCPA
- **User Consent:** The system tray UI provides explicit pause/revoke mechanisms.
- **Transparency:** Users can view the local activity log to see exactly what actions were performed.
- **Data Minimization:** Only essential system metrics are collected.

### SOC 2
- **Access Control:** RBAC and Casbin policies enforce least privilege.
- **Audit Logging:** Comprehensive audit trails support security monitoring and compliance reporting.

## Residual Risks

1. **Compromised CA:** If the internal Certificate Authority is compromised, attackers could generate valid client certificates. (Mitigation: Use a secure offline Root CA and short-lived intermediate CAs).
2. **Zero-Day Vulnerabilities:** Vulnerabilities in dependencies (e.g., Tokio, OpenSSL, FastAPI). (Mitigation: Regular dependency updates and vulnerability scanning).
3. **Physical Access:** If an attacker has physical access to an unlocked device, they could potentially extract the device token from the Keychain/DPAPI if the OS protections are bypassed. (Mitigation: Full Disk Encryption and strong OS login policies).
