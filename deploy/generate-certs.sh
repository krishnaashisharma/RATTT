#!/bin/bash
set -e

CERTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/certs" && pwd)"
mkdir -p "$CERTS_DIR"

echo "Generating self-signed certificates for development..."

# Generate CA private key
openssl genrsa -out "$CERTS_DIR/ca.key" 4096

# Generate CA certificate
openssl req -new -x509 -days 3650 -key "$CERTS_DIR/ca.key" -out "$CERTS_DIR/ca.crt" \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=Remote-Device-Mgmt-CA"

# Generate server private key
openssl genrsa -out "$CERTS_DIR/server.key" 4096

# Generate server certificate signing request
openssl req -new -key "$CERTS_DIR/server.key" -out "$CERTS_DIR/server.csr" \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Create config file for server certificate with SAN
cat > "$CERTS_DIR/server.conf" << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = State
L = City
O = Organization
CN = localhost

[v3_req]
subjectAltName = DNS:localhost,DNS:*.localhost,IP:127.0.0.1,IP:0.0.0.0
EOF

# Sign server certificate with CA
openssl x509 -req -days 365 -in "$CERTS_DIR/server.csr" \
  -CA "$CERTS_DIR/ca.crt" -CAkey "$CERTS_DIR/ca.key" -CAcreateserial \
  -out "$CERTS_DIR/server.crt" -extensions v3_req -extfile "$CERTS_DIR/server.conf"

# Generate client private key
openssl genrsa -out "$CERTS_DIR/client.key" 4096

# Generate client certificate signing request
openssl req -new -key "$CERTS_DIR/client.key" -out "$CERTS_DIR/client.csr" \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=agent-client"

# Sign client certificate with CA
openssl x509 -req -days 365 -in "$CERTS_DIR/client.csr" \
  -CA "$CERTS_DIR/ca.crt" -CAkey "$CERTS_DIR/ca.key" \
  -out "$CERTS_DIR/client.crt"

# Clean up CSR files and config
rm -f "$CERTS_DIR/server.csr" "$CERTS_DIR/client.csr" "$CERTS_DIR/server.conf" "$CERTS_DIR/ca.srl"

# Set permissions
chmod 600 "$CERTS_DIR"/*.key
chmod 644 "$CERTS_DIR"/*.crt

echo "✓ Certificates generated in $CERTS_DIR"
echo "  - ca.crt: CA certificate"
echo "  - server.crt/server.key: Server certificate (backend)"
echo "  - client.crt/client.key: Client certificate (agent)"
