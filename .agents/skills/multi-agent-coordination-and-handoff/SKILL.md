---
name: multi-agent-coordination-and-handoff
description: >-
  Standardizes communication, delegation, task decomposition, and handoff protocols across specialized
  autonomous subagents to minimize token bloat and prevent redundant work.
license: Apache-2.0
metadata:
  domain: agent-engineering
  subdomain: multi-agent-systems
  tags: multi-agent, agent-coordination, delegation, task-decomposition, subagent-handoff
  version: "1.0.0"
---

# Multi-Agent Coordination & Handoff Protocol

This skill establishes structured communication patterns, payload minimization rules, and handoff standards across the 7 specialized agent roles in **AI GOLD WATCHER V4**.

## Delegation Architecture

To prevent token waste from circular conversations and uncoordinated tool calls, all multi-agent operations follow a strict **Hierarchical Delegation Pattern**:

```
[Primary Orchestrator / Architect]
         │
         ├─► [Quant Researcher]: Produces mathematical hypothesis & feature contract
         ├─► [Strategy Developer]: Builds decoupled signal engine satisfying contract
         ├─► [Market Regime Analyst]: Generates regime classification matrix
         ├─► [AI/ML Researcher]: Validates meta-labeling & tests data leakage
         ├─► [Risk Manager]: Evaluates pre-trade bounds (Veto authority)
         ├─► [Backtesting Engineer]: Executes event-driven simulation & WFO
         └─► [Software QA Engineer]: Runs pytest suites & verifies edge cases
```

## Core Protocol Rules

### 1. The Minimal Delegation Payload
When invoking a subagent (`invoke_subagent`), the prompt **MUST** follow this structured format:
- **Role & Objective**: One-sentence goal.
- **Context Pointers**: Specific file paths (e.g. `src/indicators/ema.py`), NOT raw source text.
- **Input Contract**: Typed parameters or data structures expected.
- **Output Contract**: Expected return format (e.g., Python class, test suite, or JSON report).
- **Constraints**: Safety and environment bounds (e.g., "Must pass all tests under `pytest` with zero warnings").

### 2. Elimination of Conversational Ping-Pong
- Subagents are instructed to complete their assigned scope autonomously, execute validation tests, and return a single comprehensive completion message.
- Subagents must not ask rhetorical questions or return partial code that requires the orchestrator to assemble.

### 3. Handoff Contract Template
When an agent finishes its task and reports back:
```markdown
### Subagent Task Completion Report
- **Agent Role**: [e.g. Software QA Engineer]
- **Task**: [Assigned task description]
- **Files Created / Modified**: [List of exact file paths]
- **Verification Performed**: [Exact command run and test results]
- **Status**: [SUCCESS | BLOCKED | REJECTED]
- **Next Required Step**: [Single action for orchestrator]
```
