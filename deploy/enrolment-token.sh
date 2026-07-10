#!/bin/bash
set -e

# Script to generate a one-time enrolment token for device registration
# Usage: ./enrolment-token.sh [backend_url]

BACKEND_URL="${1:-https://localhost:8443}"

echo "Generating enrolment token..."
echo "Backend URL: $BACKEND_URL"

# TODO: Call the backend API to generate the token
# curl -X POST "$BACKEND_URL/api/enrolment/generate" \
#   -H "Authorization: Bearer <admin-token>" \
#   -H "Content-Type: application/json" \
#   -d '{}' \
#   | jq '.token'

echo "TODO: Implement enrolment token generation via API"
