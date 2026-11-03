---
name: project-memory-and-session-handoff
description: >-
  Establishes and maintains persistent project memory across developer and agent sessions,
  including Architecture Decision Records (ADR), test logs, state checkpointing, and structured handoffs.
license: Apache-2.0
metadata:
  domain: agent-engineering
  subdomain: memory-management
  tags: project-memory, session-handoff, adr, context-persistence, state-management
  version: "1.0.0"
---

# Project Memory & Session Handoff Management

This skill defines the operational runbook for maintaining persistent project memory and executing zero-loss session handoffs across conversational agent sessions in **AI GOLD WATCHER V4**.

## The Project Memory Core (`project_memory/`)

To prevent conversational context degradation ("context rot") and ensure development continuity, all durable project knowledge is partitioned into 8 structured markdown documents:

```
project_memory/
├── PROJECT_MASTER.md       # Immutable project charter, market constraints, roadmap
├── CURRENT_STATE.md        # Real-time development stage, module status, blockers
├── ARCHITECTURE.md         # 12-module topology, dependencies, interfaces
├── DECISIONS.md            # Append-only Architecture Decision Records (ADRs)
├── BUGS_AND_FIXES.md       # Discovered defects, root causes, regression tests
├── TEST_HISTORY.md         # Verifiable test execution records (never fabricated)
├── NEXT_TASKS.md           # Prioritized task backlog with acceptance criteria
└── SESSION_HANDOFF.md      # Compact bridge contract between chat sessions
```

## Maintenance Lifecycle (When to Update)

| Event | Files to Update | Procedure |
| :--- | :--- | :--- |
| **Architectural / Design Choice** | `DECISIONS.md` | Append ADR with Date, Context, Decision, Consequences. Never overwrite past records. |
| **Test Suite Execution** | `TEST_HISTORY.md` | Record exact CLI command, pass/fail counts, duration, and timestamp. |
| **Bug Discovered or Resolved** | `BUGS_AND_FIXES.md` | Record Bug ID, symptom, root cause, code fix location, and regression test link. |
| **Task / Milestone Completion** | `CURRENT_STATE.md`, `NEXT_TASKS.md` | Move completed items to done; update current stage progress and unblock dependents. |
| **Session Conclusion / Pause** | `SESSION_HANDOFF.md` | Write compact handoff containing completed scope, current state, and exact next prompt. |

## Session Handoff Protocol

### 1. CREATE Mode (Ending a Session)
Before ending a long turn or pausing work:
1. Review git status and files modified.
2. Ensure test results are committed to `TEST_HISTORY.md`.
3. Synthesize the session into `SESSION_HANDOFF.md` using the canonical template:
   - **Session Intent**: The original goal of the conversation.
   - **Completed Work**: Bulleted list of files created/modified and verified.
   - **Decisions Made**: Key choices made during the turn.
   - **Current Blockers / Incomplete State**: Explicit callout of unfinished threads.
   - **Exact Next Action**: A single, unambiguous instruction for the incoming agent.

### 2. RESUME Mode (Starting a Fresh Session)
When starting in a fresh or compacted context:
1. Read `AGENTS.md` and `GEMINI.md` for binding workspace constraints.
2. Read `project_memory/SESSION_HANDOFF.md` and `project_memory/CURRENT_STATE.md`.
3. Do **NOT** scan the entire workspace. Immediately proceed with the declared *Exact Next Action*.
