---
name: llm-token-optimization-and-context-management
description: >-
  Techniques and policies for maximizing LLM context window efficiency, including selective file reading,
  progressive disclosure, prompt compression, and context caching optimization.
license: Apache-2.0
metadata:
  domain: agent-engineering
  subdomain: token-optimization
  tags: token-optimization, context-management, progressive-disclosure, selective-reading, prompt-compression
  version: "1.0.0"
---

# LLM Token Optimization & Context Management

This skill governs the consumption of context window tokens across all development phases of **AI GOLD WATCHER V4**, preventing attention dilution ("Lost in the Middle") and maximizing reasoning fidelity.

## The Principles of Context Efficiency

### 1. Selective File Reading
- **Rule**: Never read an entire multi-hundred-line file when only a specific function, class, or range is needed.
- **Pattern**:
  - First read the outline or symbol index.
  - Use `read_file` with explicit `StartLine` and `EndLine` arguments (e.g. `StartLine=45, EndLine=85`).
  - Use `edit_file` with targeted replacement strings rather than overwriting full files for minor edits.

### 2. Elimination of Redundant Repository Scans
- **Rule**: Never run unbounded directory recursive scans (`Get-ChildItem -Recurse`, `tree`, `find .`) repeatedly across turns.
- **Pattern**:
  - Consult `project_memory/ARCHITECTURE.md` or `CURRENT_STATE.md` to identify exact file paths.
  - Query specific directories only when newly added files need verification.

### 3. Progressive Disclosure of Skills & Instructions
- **Rule**: Do not dump the full text of all installed skills into agent prompts.
- **Pattern**:
  - System prompts expose only skill names and descriptions.
  - The model inspects the full `SKILL.md` only when actively executing a procedure that requires that skill.

### 4. Compact Inter-Agent Interfaces
- When delegating tasks between agents:
  - Transmit typed dataclasses, function signatures, and interface contracts.
  - **Never** paste full implementations or multi-file contents into subagent prompts.

### 5. Incompressible Context Guardrails (Zero-Tolerance)
Under no circumstances may context compression omit or abbreviate:
1. **Financial Risk Controls**: $50 balance, 0.01 lot volume, $1.00 risk budget, $2.00 daily loss breaker.
2. **Trading Safety Prohibitions**: Zero live trading, no martingale, no grid trading, no averaging down.
3. **Quantitative Integrity**: Closed-bar discipline (bar $t \to t+1$ fill), zero lookahead bias, realistic spread modeling.
4. **Known Active Bugs**: Any unresolved blocker recorded in `BUGS_AND_FIXES.md`.
