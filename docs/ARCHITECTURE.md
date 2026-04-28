System map — “what exists, how it connects, what’s coming”)

# MiniTrini Architecture

This document describes the **structural architecture** of MiniTrini:
existing modules, integration boundaries, and planned extensions.

It is intended as a long-lived reference.

---

## 1. Architectural Overview

MiniTrini follows a **kernel-centric architecture**.

- The kernel governs execution
- Agents perform autonomous exploration
- Tools execute bounded actions
- Interfaces observe and request

Nothing bypasses the kernel.

---

## 2. Kernel Layer (Core)

**Location:** `core/`  
**Language:** Python  

### Responsibilities
- Event intake (triggers)
- Context creation and propagation
- Flow execution
- Decision routing
- Ethics & policy enforcement
- Agent governance
- Tool delegation
- State persistence

### Key Modules
- `orchestrator.py` — execution engine
- `context.py` — shared working memory
- `nodes.py` — base node abstraction
- `nodes_llm.py` — reasoning nodes
- `nodes_decision.py` — branching logic
- `nodes_tool.py` — side-effect execution
- `flow_loader.py` — YAML → node graph
- `flow_validator.py` — structural validation
- `backend_safety.py` — hardware & backend gating
- `triggers/` — event sources (manual, timer, HTTP)

---

## 3. Flow System

**Format:** YAML (declarative)

Flows define:
- execution order
- branching logic
- delegation points

Flows are **data**, not code.

Planned extensions:
- parallel branches
- async nodes
- retry / backoff semantics
- flow versioning

---

## 4. Agent Layer

Agents are **managed intelligences**.

They may:
- run continuously
- maintain state
- iterate independently
- request or propose actions

They may not:
- bypass kernel governance
- self-expand scope without approval

### CodeWorm (JavaScript)
**Role:** Autonomous code exploration & evolution agent  

Key characteristics:
- Event-driven
- Stateful (storage, logs)
- Patch generation and execution
- Delegation to repair tools
- Continuous observation loop

Kernel relationship:
- Started / stopped by kernel
- Receives task envelopes
- Reports outcomes and anomalies
- Halted on policy or ethics violations

---

## 5. Tool Layer

Tools are **deterministic executors**.

They do not reason about intent.

### WormBot
- Modular language handlers
- Plugin architecture
- Code analysis and repair
- CLI + GUI capable

### AI Dependency Checker
- Dependency graph analysis
- CVE scanning
- Auto-fix with sandbox verification
- System integrity monitoring

Tools are invoked **only via kernel-approved flows**.

---

## 6. Trigger System

Triggers initiate execution.

### Existing
- Manual trigger
- Timer trigger

### Planned
- HTTP / webhook trigger
- File system trigger
- GPIO / hardware trigger
- Agent-originated trigger (request → approval)

---

## 7. Interfaces

Interfaces are **control surfaces**, not logic owners.

### GUI (NOI Pulse)
- System status
- Agent state
- Flow control
- Manual trigger execution

### CLI
- Developer control
- Diagnostics
- Emergency overrides

### HTTP API
- Local service integration
- External system requests
- Home automation / tooling hooks

---

## 8. Ethics & Governance Layer

Cross-cutting concern enforced by kernel.

Capabilities:
- Action refusal
- Scope limitation
- Escalation requirements
- Sandboxing
- Audit logging

Planned:
- Policy profiles
- Per-agent permissions
- Risk scoring
- Human-in-the-loop gates

---

## 9. Future Modules (Planned)

### Memory & Persistence
- Long-term state
- Decision history
- Outcome tracking

### Scheduler
- Priority-based execution
- Resource awareness

### Observability
- Metrics
- Health monitoring
- Flow tracing

### Multi-Agent Coordination
- Agent-to-agent messaging
- Cooperative task decomposition

---

## 10. Design Constraints (Intentional)

MiniTrini explicitly avoids:
- cloud-first dependency
- opaque black-box decision making
- hard-coded behavior
- UI-driven logic

These constraints are architectural, not accidental.

---

## 11. Summary

MiniTrini is a **governed intelligence kernel**.

It coordinates:
- events
- reasoning
- agents
- tools
- outcomes

Under:
- explicit constraints
- transparent flows
- local control

This architecture is designed to grow **without losing clarity**.