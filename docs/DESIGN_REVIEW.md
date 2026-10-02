# Design review of the supplied starter

## What you were trying to build

Your starter clearly had these intended layers:

1. authentication/client ID
2. queue manager
3. permission verification
4. queue connection pass-through
5. ActiveMQ management API

That direction is correct.

## Problems in the original starter

### 1. Hard-coded broker admin credentials

`BROKER_URL`, `USERNAME`, and `PASSWORD` were hard-coded.

That makes every application operation an administrator operation.

**Correction:** FastAPI uses broker admin credentials only for control-plane provisioning. Runtime clients receive their own broker identity.

### 2. QueueVerifierModel is being used as if it were a database

The original code instantiated:

`QueueVerifierModel(queue_name=..., client_id=...)`

without supplying the required `can_create` and `can_delete` fields.

More importantly, a Pydantic model is not an authorization store.

**Correction:** authorization is persisted in the database and then enforced by Artemis roles.

### 3. Controller methods have broken `self` handling

The original static methods declare `self` and then try to use `self.queue_service`.

**Correction:** the control-plane logic is moved into explicit route/service functions.

### 4. Client ID was only planned in a header

The original route literally used:

`client_id = "we will retrieve this from the request header"`

**Correction:** `X-Client-Id` + `X-Client-Secret` are now actual dependencies.

### 5. The FastAPI API must not proxy normal message traffic

The original `QueueConnectionPassThroughService` suggested returning a TCP connection through FastAPI.

That would make FastAPI the data plane and create a bottleneck.

**Correction:** FastAPI provisions resources and returns the broker connection information. Clients connect directly to Artemis.

### 6. Queue naming

The original idea prefixed queue names with `client_id`.

That is unnecessary if Artemis address-based security is used.

A clean queue can remain:

`payment.requests`

and access is granted to roles:

`cli_abc123`

This also allows multiple clients to share one queue later.

### 7. Kubernetes replicas

A Deployment with multiple ActiveMQ replicas would not by itself replicate messages.

The platform therefore distinguishes:

- broker pool / sharding
- Artemis cluster
- HA live/backup replication

The current project implements the first.

## Tradeoff

### Sharding now

Pros:
- much easier to run today
- horizontal broker capacity
- simple queue placement model
- easy to explain and debug

Cons:
- a queue lives on one broker
- broker loss can make that queue unavailable
- no replicated messages

### Native Artemis HA later

Pros:
- broker failover
- replicated persistent data
- client reconnect/failover

Cons:
- substantially more Kubernetes and broker configuration
- stable broker identity and connectors
- backup placement
- replication traffic
- more complex operational model

For an MVP, sharding is the right place to start; HA should be added after the control plane and client lifecycle work.

## Final target architecture

```text
                   React Dashboard
                          |
                          v
                    FastAPI API
                   /     |      \
                  /      |       \
            Clients    Queues    Brokers
                \        |        /
                 \       |       /
                    PostgreSQL
                         |
                         v
              Apache Artemis pool
              /        |        \
          broker-1  broker-2  broker-3
             |         |         |
          queue A   queue B   queue C
```

Later:

```text
queue A
   |
   +---- live broker
   |
   +---- backup broker
```

with Artemis-native HA/failover.
