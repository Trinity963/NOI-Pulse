# MiniTrini

## 🧠 Overview

**MiniTrini is a local-first AI orchestration kernel with a brain.**

It is not a chatbot.
It is not a single-purpose automation tool.
It is not a wrapper around an LLM.

MiniTrini is an **execution and governance kernel** designed to coordinate
intelligent agents, tools, and system actions under explicit safety,
ethics, and policy constraints.

Think:
- n8n / Node-RED (orchestration)
- + a reasoning core
- + ethics and safety gates
- + local hardware awareness
- + autonomous agents

All running **locally**, transparently, and under user control.

---

## 🧭 Core Philosophy

MiniTrini is built on five principles:

1. **Local-first**
   - No cloud dependency required
   - Designed for desktop and Raspberry Pi class hardware

2. **Orchestration over chat**
   - Intelligence is expressed through flows, decisions, and actions
   - Conversation is an interface, not the core

3. **Explicit governance**
   - Ethics, safety, and policy are first-class concepts
   - The system can refuse, halt, or escalate actions

4. **Composable intelligence**
   - LLMs, tools, and agents are modular
   - Nothing is hard-coded into the kernel

5. **Transparency**
   - Flows are declarative (YAML / JSON)
   - Actions are logged
   - State is inspectable

---

## 🧠 What MiniTrini Is

MiniTrini is an **orchestration kernel** that:

- receives events (triggers)
- creates context
- evaluates intent and constraints
- routes execution through flows
- delegates work to tools and agents
- observes outcomes
- persists state

It decides **when** and **how** intelligence acts.

---

## 🧩 Major Components

### Kernel (MiniTrini Core)
- Flow engine
- Context (working memory)
- Decision nodes
- Tool nodes
- Trigger system (manual, timer, HTTP, etc.)
- Backend safety & hardware awareness
- Ethics and policy enforcement

### Agents
Autonomous or semi-autonomous systems managed by the kernel.

Examples:
- **CodeWorm** — a long-running agent that explores, analyzes, and evolves codebases
- Future agents for monitoring, research, or maintenance

Agents are **not merged into the kernel**.
They are governed by it.

### Tools
Deterministic systems that perform bounded work.

Examples:
- **WormBot** — modular code analysis and repair engine
- **AI Dependency Checker** — system health, dependency, and CVE management

Tools do not decide *when* to act.
They execute when instructed.

### Interfaces
- GUI (NOI Pulse): system state, control surface, flow cockpit
- CLI
- Local HTTP API

Interfaces do not own logic.
They reflect kernel state and issue requests.

---

## 🐛 Relationship Between Components

Trigger
↓
MiniTrini Kernel
↓
Decision / Ethics / Policy
↓
Agent (e.g. CodeWorm) ──→ Tool (e.g. WormBot)
↓ ↓
Observation / Logs / State ←─┘


MiniTrini governs.
Agents explore and decide.
Tools execute.

---

## 🛡 Ethics & Safety

MiniTrini is designed to ask:

- *Should this action happen?*
- *Is it safe?*
- *Is it permitted?*
- *Does it need review?*

Before asking:
- *How fast can we do it?*

This makes it suitable for unattended automation, system modification,
and long-running agents.

---

## 🚀 What This Project Is Becoming

MiniTrini is evolving into a **personal AI operating kernel**:

- autonomous but governed
- intelligent but inspectable
- powerful but constrained

It is meant to **live with you**, not run on someone else’s server.

---

## 🧭 Status

This project is under active development.
The kernel architecture is in place.
Major subsystems already exist and are being unified under this model.

The path forward is explicit and intentional.
2️⃣ Project Manifest (machine-readable vision)
This is the memory anchor you were asking for.

Name it something like:

minitrini.project.json

or .minitrini.json

or project.manifest.json

This file answers:

“What is this project supposed to be?”

🧾 minitrini.project.json
{
  "name": "MiniTrini",
  "type": "ai-orchestration-kernel",
  "intent": "Local-first AI orchestration kernel with governance, ethics, and autonomous agents",
  "core_principles": [
    "local-first",
    "orchestration-over-chat",
    "explicit-governance",
    "composable-intelligence",
    "transparency"
  ],
  "kernel_responsibilities": [
    "flow_execution",
    "context_management",
    "decision_routing",
    "ethics_and_policy_enforcement",
    "trigger_handling",
    "agent_governance",
    "tool_delegation",
    "state_persistence"
  ],
  "components": {
    "kernel": {
      "language": "python",
      "role": "execution_brain_and_governor"
    },
    "agents": {
      "CodeWorm": {
        "language": "javascript",
        "role": "autonomous_code_exploration_and_evolution",
        "managed_by_kernel": true,
        "stateful": true
      }
    },
    "tools": {
      "WormBot": {
        "role": "deterministic_code_analysis_and_repair",
        "plugin_based": true
      },
      "DependencyChecker": {
        "role": "system_health_and_dependency_integrity"
      }
    },
    "interfaces": {
      "GUI": "system_status_and_control_surface",
      "CLI": "developer_control",
      "HTTP_API": "local_service_interface"
    }
  },
  "execution_model": {
    "event_driven": true,
    "flow_based": true,
    "branching": true,
    "async_capable": true
  },
  "safety": {
    "ethics_gate": true,
    "sandboxing": true,
    "hardware_awareness": true,
    "can_refuse_actions": true
  },
  "target_environments": [
    "desktop_linux",
    "raspberry_pi_5"
  ],
  "non_goals": [
    "cloud_first_saas",
    "opaque_black_box_ai",
    "chatbot_only_interface"
  ]
}
3️⃣ Why this solves the “new session” problem
With these two files:

You never have to reconstruct intent from memory

I (or any future system) can read them and immediately understand:

what MiniTrini is

what it is not

how pieces relate

New contributors don’t derail the architecture

You don’t accidentally drift into “just another AI app”

This is project memory, not documentation fluff.

