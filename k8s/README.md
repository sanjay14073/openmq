# Kubernetes

This manifest intentionally deploys a 3-pod Artemis StatefulSet as a **broker pool**.

Do not call this an HA cluster yet.

Before production:
1. Configure Artemis cluster connections.
2. Configure live/backup replication or another HA strategy.
3. Give each broker stable connectors.
4. Change the control plane from "first active broker" to a broker registry with health/load scoring.
5. Persist the control-plane database outside the API pods.
6. Add TLS and network policies.

The current control plane code is intentionally structured so `Broker` rows can represent multiple broker nodes.
