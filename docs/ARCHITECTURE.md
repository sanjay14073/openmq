# Architecture

## Control plane

FastAPI owns:
- client lifecycle
- queue resources
- broker registry
- ACL intent
- connection profiles

## Data plane

Apache Artemis owns:
- TCP/STOMP/AMQP connections
- message persistence
- message delivery
- acknowledgement semantics
- broker-level authorization

The FastAPI service must never become the message path for normal application traffic.

## Identity

A client has:
- OpenMQ `client_id`
- OpenMQ client secret
- Artemis username equal to `client_id`
- Artemis role equal to `client_id`

FastAPI provisions the Artemis user through the management API and applies per-address security settings.

This is deliberately different from the initial code, where a hard-coded admin broker credential was used for every operation.

## Resource model

Client -> QueueResource -> Broker

An ACL is represented by booleans on QueueResource in the MVP. The next evolution should normalize this into:

client
resource
policy(client, resource, action)

with actions:
- PRODUCE
- CONSUME
- CREATE
- DELETE
- BROWSE

## Why not prefix every queue with client_id?

Because Artemis already has address-based authorization. Keeping the logical queue name clean lets multiple clients share a queue when a policy grants them access.

## Distributed model

The first version uses queue sharding:
queue A -> broker 1
queue B -> broker 2

This is not replicated HA.

A future HA model should distinguish:
- logical queue placement
- live broker
- backup broker
- client failover endpoints

and should use Artemis-native HA rather than implementing message replication in FastAPI.

## Current limitations

- single broker selected in the default local environment
- queue deletion currently removes the broker queue
- client secret is returned only once by create-client
- the demo message consumer uses a short polling window
- SQLite is for local development
- admin key is intentionally simple for development
