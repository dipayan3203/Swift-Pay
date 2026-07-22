# Swift Pay
Next-generation payment gateway platform for India and emerging markets.

## Overview
Swift Pay is a comprehensive payments platform designed for card payments, UPI, net banking, wallets, BNPL, subscription billing, payouts, and international card acceptance. The architecture is built for low-latency processing, strong financial consistency, and compliance-ready operations.

## Included Documents
- [ARCHITECTURE.md](ARCHITECTURE.md) — technical architecture, services, deployment model, and observability
- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) — core database entities, relationships, and schema design
- [API_SPEC.md](API_SPEC.md) — merchant onboarding, payments, subscriptions, payouts, and webhooks
- [ROADMAP.md](ROADMAP.md) — phased MVP and advanced capability rollout plan

## Recommended Technology Stack
- Frontend: Next.js + React
- Backend: Python for the full backend, including payments, ledger, finance, risk, and ML workloads
- APIs: gRPC for internal services and REST for public APIs
- Messaging: Kafka
- Cache: Redis
- Database: PostgreSQL with an append-only ledger journal
- Analytics: ClickHouse
- Search and observability: OpenSearch, Prometheus, Grafana, and OpenTelemetry
- Deployment: Docker, Kubernetes, Istio, GitHub Actions, ArgoCD, and HashiCorp Vault

## Quick Start
1. Provision the required infrastructure services.
2. Deploy the services with container orchestration.
3. Review the design documents above for implementation details.
