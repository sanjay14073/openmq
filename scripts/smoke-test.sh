#!/usr/bin/env bash
set -e
BASE="${BASE:-http://localhost:8000/v1}"
KEY="${ADMIN_API_KEY:-dev-admin-key}"

echo "Health:"
curl -fsS "$BASE/health"
echo

echo "Broker health:"
curl -fsS "$BASE/health/broker"
echo
