# Validator Leasing Platform Architecture

This document outlines an architecture for a platform that lets individuals lease idle home computers to run blockchain validators or mining nodes. The focus is on accessibility for people with disabilities or fixed incomes while ensuring security, reliability, and compliance. The suggestions below tighten the original concept with more concrete controls, onboarding guidance, and operational playbooks.

## Goals and Success Criteria
- **Inclusive participation:** Simple onboarding, accessible UI/UX, and predictable payouts for lessors with limited technical background.
- **Operational safety:** Protect validator keys and tenant workloads from host interference; avoid slashing and double-signing.
- **Transparent incentives:** Usage-based payouts with clear uptime/reliability metrics and verifiable logs.
- **Regulatory awareness:** Baseline KYC/KYB, AML controls, and geo-fencing where required by law.

## Participants
- **Lessors:** Provide hardware (CPUs/GPUs, storage, bandwidth) via a secure client; receive payouts for meeting SLAs.
- **Lessees:** Projects or operators who need validator/miner capacity without managing hardware.
- **Orchestrator:** Matches supply and demand, verifies host capabilities, distributes workloads, and manages payments/escrow.

## System Components
- **Secure host client:** Signed binary/OCI image that sandboxes workloads (VMs/containers), applies auto-updates, and reports health. Supports remote attestation when available.
- **Key custody layer:** Uses HSMs/secure enclaves for validator keys. Keys are generated/imported per tenant and never exposed to hosts; double-signing protection is enforced server-side.
- **Scheduler and matcher:** Allocates workloads based on hardware profiles, geo/policy constraints, and reputation scores. Supports failover and active/standby pairs for validators.
- **Escrow and payouts:** On-chain contracts hold tenant funds and lessor collateral. Payment streams (e.g., Sablier/Superfluid) are gated by uptime proofs and performance checkpoints.
- **Monitoring and proofs:** Heartbeat channels, signed metrics, and append-only logs. Optional ZK or TEEs for attesting workload integrity. Public reputation scores derived from SLA history.
- **Compliance layer:** KYC/KYB for both sides, sanctions screening, and optional tax-withholding logic per jurisdiction.

## Workflows
1. **Onboarding lessors:**
   - Identity verification and acceptance of terms.
   - Capability check (CPU/RAM/disk/bandwidth) and optional remote attestation.
   - Deposit collateral or opt into insurance pool against slashing/penalties.
2. **Tenant job creation:**
   - Specify chain (e.g., Aura/Cosmos, Ethereum L2), validator/miner type, region, and redundancy level.
   - Fund escrow; select payout schedule and maximum slashing exposure.
3. **Deployment:**
   - Scheduler assigns hosts that meet policy; workloads deployed in isolated sandboxes with mTLS and least-privilege networking.
   - Validator keys provisioned to custody layer; hosts receive only blinded signing endpoints.
4. **Operation:**
   - Continuous health checks, log streaming, and slashing-protection state sync.
   - Automatic failover to standby hosts if health thresholds fail.
5. **Settlement:**
   - Payout streams released according to verified uptime/performance.
   - Collateral returned or penalized based on SLA adherence and slashing events.

### Additional onboarding guidance (accessibility-first)
- Provide a **non-technical wizard** with built-in diagnostics that surfaces only essential choices (bandwidth cap, max disk usage, energy schedule) and proposes defaults based on detected hardware.
- Offer **assisted setup sessions** (screen-reader friendly and remote-help capable) with auditable consent logs; avoid requiring CLI interaction for baseline participation.
- Publish a **clear earnings simulator** that factors electricity costs, chain-specific slashing risk, and expected job mix to help fixed-income participants decide whether to opt in.

## Security and Reliability Practices
- Enforce **zero-trust networking**: mTLS, per-tenant namespaces, and firewall egress controls.
- **Image integrity:** Signed artifacts, reproducible builds, and mandatory auto-updates.
- **Backup and recovery:** Encrypted backups of validator state; runbooks for key rotation, slashing incidents, and data-center outages.
- **Observability:** Standardized dashboards and alerts (latency, missed attestations/blocks, peer count, disk usage).
- **Abuse prevention:** Rate-limit control-plane APIs, detect malicious traffic, and require collateral or insurance to cover slashing.

### Hardening suggestions
- **Slashing protection everywhere:** Centralize double-signing protection and force hosts to forward signing requests to a service that tracks consensus locks and finality before allowing signatures. Include periodic integrity proofs for this service.
- **Remote attestation fallback:** Where TEEs are unavailable, require reproducible builds with hash-published artifacts and periodic spot-checks using ephemeral challenge workloads.
- **Network isolation defaults:** Block unsolicited inbound traffic; allow egress only to chain peers and orchestrator endpoints with explicit allowlists per job type.
- **Energy/quiet hours:** Support schedules that pause non-critical workloads during local active hours to accommodate shared households without jeopardizing SLAs.

## Incentive and Reputation Model
- **Reputation scores** derived from uptime, incident history, and audit results; decay old data to allow recovery.
- **Collateral/insurance** tiers that unlock higher-paying jobs and reduce tenant risk.
- **Community pool** to subsidize accessibility-focused hosts (e.g., disability grants) funded by protocol fees or donations.

### Payment and economics
- **Dual-track payouts:** Offer stablecoin-denominated baseline payments plus variable performance bonuses to reduce volatility for fixed-income participants.
- **Transparent fee splits:** Publish per-job fee breakdowns (protocol fee, insurance, host take-home) and show effective APRs after expected downtime and energy costs.
- **Delayed finalization buffer:** Hold a small rolling reserve from payouts to cover delayed slashing penalties; release after a safety window to prevent negative balances.

## Accessibility Considerations
- Accessible dashboards (WCAG-compliant), clear earnings projections, and mobile-friendly controls.
- Guided setup with automated diagnostics; optional remote support tools with strict consent and audit trails.
- Fixed-income friendly options like stable-coin payouts, low-volatility staking strategies, and predictable schedules.

## Compliance and Legal Notes
- Distinguish between providing **compute services** vs. operating a **financial intermediary**; obtain legal review per target jurisdiction.
- Apply AML/KYC and sanctions screening; record-keeping for payouts and tax reporting.
- Geo-fence restricted regions and provide configurable policy sets for tenants with stricter requirements.

## Rollout Plan
1. **Pilot scope:** Start with a single chain’s validator profile (e.g., Aura/Cosmos) and a small host cohort. Instrument uptime and slashing protection thoroughly.
2. **Risk controls:** Run slashing-simulation drills; enforce mandatory backups and signed updates before scaling.
3. **Marketplace launch:** Gradually open to more chains and job types (RPC nodes, light clients, MEV relays) as reputation and insurance pools mature.
4. **Community programs:** Offer incentives for accessibility-focused hosts and publish transparent metrics on earnings, uptime, and incident response.

## Operations workflow
- **Weekly status email:** Send a weekly report to hosts and tenants covering uptime, payouts, incidents, and upcoming maintenance windows. Include opt-in preferences and accessibility-friendly formats (plain text + screen-reader friendly HTML).
- **Runbook cadence:** Review and refresh incident runbooks and escalation contacts monthly; document changes and notify affected stakeholders.

## Open issues and next steps
- **Legal posture:** Determine whether the orchestrator is a communications provider or a regulated financial intermediary per target jurisdictions; prepare a data retention policy for KYC artifacts.
- **Insurance modeling:** Quantify slashing risk per chain to size collateral and pool premiums; publish assumptions and historical slashing rates.
- **Job policy engine:** Define a machine-readable policy schema (region, hardware class, compliance flags) and simulate matching outcomes against expected supply to ensure feasible utilization.
- **Incident drills:** Establish quarterly tabletop exercises for key compromise, data breach, and orchestrator downtime; document recovery time objectives.
