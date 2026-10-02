# OpenMQ Platform

Open-source managed ActiveMQ Artemis control plane.

This project provides:
- FastAPI control plane
- React dashboard
- PostgreSQL metadata
- Apache Artemis broker integration through Jolokia
- Per-client broker credentials
- Per-queue authorization using Artemis security roles
- Queue-to-broker assignment
- Test message publish/consume endpoints
- Docker Compose for local development
- Kubernetes manifests for a broker-pool deployment

## Important architecture decision

The first runnable version is a **sharded broker pool**, not an HA replicated Artemis cluster.

Kubernetes can run multiple broker pods, but simply increasing replicas does not replicate queue data. This project therefore assigns each queue to one broker and returns that broker's connection endpoint to the client.

That gives us:
- horizontal broker capacity
- logical queue sharding
- independent broker failure domains

It does NOT yet give:
- automatic queue failover
- replicated queue data
- zero-loss broker failover

Those require an Artemis HA/replication topology and are deliberately kept as a separate phase.

## Run locally

Prerequisites:
- Docker Desktop
- Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

Open:
- Dashboard: http://localhost:3000
- API docs: http://localhost:8000/docs
- Artemis console: http://localhost:8161/console

Default admin key:
`dev-admin-key`

Default Artemis admin:
`artemis / artemis`

## Dashboard flow

1. Create a client.
2. Copy the generated client secret.
3. Create a queue for that client.
4. The platform creates the queue on Artemis and provisions the client's broker user.
5. Open the queue details to see its broker endpoint and credentials.
6. Use the message panel to publish and consume test messages.

## API

Admin endpoints require:
`X-Admin-Key: dev-admin-key`

Client endpoints use:
`X-Client-Id` and `X-Client-Secret`.

Example:

```bash
curl -X POST http://localhost:8000/v1/admin/clients \
  -H 'Content-Type: application/json' \
  -H 'X-Admin-Key: dev-admin-key' \
  -d '{"name":"payment-service"}'
```

Then create a queue:

```bash
curl -X POST http://localhost:8000/v1/queues \
  -H 'Content-Type: application/json' \
  -H 'X-Client-Id: <client_id>' \
  -H 'X-Client-Secret: <client_secret>' \
  -d '{"name":"payment.requests"}'
```

## Why Artemis

Apache Artemis is the current Apache multi-protocol broker line. It supports OpenWire, AMQP, MQTT and STOMP, and provides clustering and HA capabilities that can be added in a later phase.

The container image used here is `apache/artemis:2.57.0`.

## Production hardening still required

Before exposing this to the public internet:
- HTTPS/TLS everywhere
- secret manager instead of environment secrets
- real admin authentication/RBAC
- PostgreSQL HA/backups
- Artemis HA replication or shared-store topology
- Kubernetes StatefulSets and persistent volumes for brokers
- network policies
- rate limits
- audit logging
- client secret rotation
- tenant isolation
- metrics/tracing

## Verified MVP flow

1. `docker compose up --build`
2. Open `http://localhost:3000`
3. Create Client A, save its generated secret.
4. Create queue `orders`.
5. Create Client B, save its generated secret.
6. Create queue `orders` again. This is intentionally valid: the public queue name is scoped by client and Artemis receives unique internal names (`cli_x.orders`).
7. Send and receive messages from each client separately.
8. FastAPI docs: `http://localhost:8000/api/docs`.

The local MVP has one Artemis broker. Broker pooling/sharding and then live/backup HA are separate phases. Kubernetes replicas alone are not treated as HA.
