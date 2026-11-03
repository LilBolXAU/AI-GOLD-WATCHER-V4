# AI GOLD WATCHER V4 — PROJECT MEMORY SYSTEM SPECIFICATION

**Document ID**: `AGW-V4-DOC-MEMSYS`  
**Version**: 1.0.0  
**Status**: Active  
**Author**: Senior Quantitative Trading Architect  

---

## 1. Executive Overview

In long-running autonomous trading system development, conversational context windows are ephemeral and subject to **attention degradation ("context rot")**. Relying on raw chat history leads to forgotten requirements, re-litigated architecture debates, lost test results, and token-expensive re-scans of the codebase.

The **AI GOLD WATCHER V4 Project Memory System** establishes a persistent, file-backed knowledge core inside the repository (`project_memory/`). It provides a deterministic single source of truth across all agent turns, pair-programming sessions, and subagent delegations.

---

## 2. Directory Layout & Document Taxonomy

```
project_memory/
├── PROJECT_MASTER.md       # [Immutable Charter] Core mission, market, broker, safety constraints
├── CURRENT_STATE.md        # [Mutable Ledger] Current stage, module progress, active blockers
├── ARCHITECTURE.md         # [Structural Blueprint] 12-module topology, dependencies, interfaces
├── DECISIONS.md            # [Append-Only ADRs] Architectural & trading research choices
├── BUGS_AND_FIXES.md       # [Defect Ledger] Discovered bugs, root cause analyses, regression tests
├── TEST_HISTORY.md         # [Empirical Test Log] Verifiable CLI test runs, pass/fail counts
├── NEXT_TASKS.md           # [Prioritized Backlog] Actionable task queue with acceptance criteria
└── SESSION_HANDOFF.md      # [Session Bridge] Compact context bridge for inter-session continuity
```

### Document Roles & Specifications

| Document | Primary Owner | Update Frequency | Purpose & Contents |
| :--- | :--- | :--- | :--- |
| **`PROJECT_MASTER.md`** | Architect / Lead | Rare (Charter change) | Immutable parameters: `XAUUSDm`, Exness MT5, $50 balance, 0.01 lot, $1 risk budget, zero live orders, development roadmap. |
| **`CURRENT_STATE.md`** | All Agents | End of every task | Real-time snapshot of the codebase: current stage, module status matrix (12 modules), current test status, active blockers. |
| **`ARCHITECTURE.md`** | Architect | When modules evolve | 12-module system topology, unidirectional data flow, module dependencies, Pydantic/dataclass interface contracts. |
| **`DECISIONS.md`** | All Agents | On design choice | Append-only Architecture Decision Records (ADRs). Records Date, Status, Context, Decision, Consequences. Never overwritten. |
| **`BUGS_AND_FIXES.md`** | Software QA | On defect / fix | Records Bug ID, severity, symptom, root cause, code fix location, and regression test link. |
| **`TEST_HISTORY.md`** | Software QA | On test execution | Verifiable record of test runs. Records exact CLI command, test counts, timings, exit code. **Zero fabrication permitted**. |
| **`NEXT_TASKS.md`** | Orchestrator | End of every task | Prioritized queue of upcoming work, assigned agent roles, dependencies, and explicit acceptance criteria. |
| **`SESSION_HANDOFF.md`** | Current Agent | End of turn / session | Compact continuity summary: Session intent, completed work, decisions, blockers, and exact next action prompt. |

---

## 3. Mandatory Reading Order for Agents

To prevent context bloat and ensure 100% compliance with safety rules, every agent must follow this strict **Tiered Reading Protocol**:

```
Tier 1: Mandatory Foundation (Always Read)
   ├── AGENTS.md / GEMINI.md       (Trading safety guardrails, zero live orders)
   ├── project_memory/PROJECT_MASTER.md (Financial boundaries, broker constraints)
   └── project_memory/CURRENT_STATE.md  (Current stage, module matrix, blockers)
              │
              ▼
Tier 2: Task Context (Read on Demand)
   ├── project_memory/SESSION_HANDOFF.md (Continuity bridge from previous session)
   ├── project_memory/NEXT_TASKS.md      (Acceptance criteria for assigned task)
   └── project_memory/ARCHITECTURE.md    (Interface contracts & data flow)
              │
              ▼
Tier 3: Execution Artifacts (Selective Reading)
   ├── Relevant SKILL.md                 (Only skills needed for current task)
   └── Target source files               (Specific lines/ranges via StartLine/EndLine)
```

---

## 4. Maintenance Lifecycle (Automatic Memory Maintenance)

At the conclusion of every development turn or milestone:

1. **Check Decisions**: If an architectural, mathematical, or risk decision was made, append an ADR to `DECISIONS.md`.
2. **Check Tests**: If unit or integration tests were executed, append the exact command, results, and timing to `TEST_HISTORY.md`. Never record assumed or fabricated results.
3. **Check Bugs**: If an unexpected error or defect was diagnosed and resolved, log it in `BUGS_AND_FIXES.md`.
4. **Update Progress**: Update the 12-module matrix in `CURRENT_STATE.md` and check off finished tasks in `NEXT_TASKS.md`.
5. **Generate Handoff**: Synthesize `SESSION_HANDOFF.md` with the single exact next prompt for the next session.

---

## 5. Non-Fabrication & Empirical Verification Rules

- **Strict Test Verifiability**: A test run may only be recorded in `TEST_HISTORY.md` if the tool execution succeeded and returned measurable test output from a real runner (`pytest` or `unittest`).
- **No Profitable-by-Assumption Claims**: An agent must never claim that a strategy or module is profitable based on visual checks or clean unit test runs. Profitability requires out-of-sample backtesting and CPCV validation under Stage 4.
- **Append-Only History**: Historical decisions and test runs must never be silently edited or deleted to present an idealized past. Development history is transparent and auditable.
