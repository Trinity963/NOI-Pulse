Technical + Visionary — “what this is, and why it exists”)

# MiniTrini

## An AI Orchestration Kernel with a Brain

MiniTrini is a **local-first AI orchestration kernel** designed to coordinate
intelligent agents, tools, and system actions under explicit governance,
ethics, and policy constraints.

It is not a chatbot.
It is not an LLM wrapper.
It is not a cloud service.

MiniTrini is a **thinking execution system**.

---

## Why MiniTrini Exists

Most AI systems optimize for *output*.

MiniTrini optimizes for:
- **intent**
- **context**
- **governance**
- **correct action at the correct time**

Instead of asking *“What should I say?”*, MiniTrini asks:

> “Should this action happen at all?”  
> “If so, who should do it?”  
> “Under what constraints?”  
> “And how do we observe the outcome?”

---

## Core Capabilities

MiniTrini provides:

- Event-driven execution (triggers, not prompts)
- Declarative orchestration (flows, not scripts)
- Explicit decision routing and branching
- Ethics and safety gates before execution
- Delegation to tools and autonomous agents
- Hardware-aware, sandboxed operation
- Persistent, inspectable state

All **locally**, under user control.

---

## Architectural Role

MiniTrini acts as a **kernel**, not an application.

It governs:
- when intelligence runs
- how it runs
- what it is allowed to do
- when it must stop, escalate, or refuse

It does *not*:
- hardcode behavior
- hide decision-making
- outsource control to the cloud

---

## Mental Model

Think less “assistant”  
Think more **operating system for intelligence**



Event / Trigger
↓
MiniTrini Kernel
↓
Decision + Policy + Ethics
↓
Agent or Tool Delegation
↓
Observation / Logging / State


---

## Components at a Glance

### Kernel (Python)
- Flow engine
- Context (working memory)
- Decision nodes
- Tool nodes
- Trigger system
- Backend safety & hardware detection
- Ethics and policy enforcement

### Agents
Autonomous or semi-autonomous systems governed by the kernel.

- **CodeWorm**  
  A long-running agent that explores, analyzes, patches, and evolves codebases.
  Stateful, iterative, and self-observing.

Agents do not bypass the kernel.  
They operate **within constraints defined by it**.

### Tools
Deterministic, bounded executors.

- **WormBot** — modular code analysis and repair engine
- **AI Dependency Checker** — system integrity, dependency, and CVE management

Tools execute actions.  
They do not decide *when* to act.

### Interfaces
- GUI (NOI Pulse): system state + control surface
- CLI
- Local HTTP API

Interfaces never own logic.  
They issue requests and reflect kernel state.

---

## Ethics & Safety

MiniTrini treats ethics and safety as **system primitives**, not features.

Before execution, the kernel evaluates:
- permissibility
- scope
- risk
- escalation conditions

The system can:
- refuse actions
- halt agents
- require review
- sandbox execution

This enables unattended operation without recklessness.

---

## Target Environments

- Desktop Linux
- Raspberry Pi 5 (AI Hat / GPIO aware)

MiniTrini is designed to *live with you*, not run somewhere else.

---

## Project Status

The orchestration kernel is real and operational.
Agents and tools already exist and are being unified under this model.

This project is transitioning from **capability accumulation**
to **intentional system integration**.

MiniTrini is becoming a personal AI operating kernel.