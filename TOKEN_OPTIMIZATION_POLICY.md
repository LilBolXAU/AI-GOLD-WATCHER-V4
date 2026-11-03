# TOKEN OPTIMIZATION POLICY — AI GOLD WATCHER V4

**Document ID**: `AGW-V4-DOC-TOKENOPT`  
**Version**: 1.0.0  
**Status**: Active  
**Author**: Senior Quantitative Trading Architect  

---

## 1. Purpose & Core Philosophy

Large Language Models operate within finite context windows. Even with large token limits, token bloat causes **attention dilution ("Lost in the Middle")**, slower response latency, increased costs, and degradation of reasoning quality on edge cases.

This policy defines strict operational rules to keep context windows lean, focused, and high-fidelity, while ensuring that **safety-critical trading rules are never compromised**.

> [!IMPORTANT]
> **Measurement Discipline**:
> In accordance with quantitative standards, we make no unsubstantiated claims of percentage token reductions. Efficiency is achieved through concrete procedural discipline: eliminating redundant scans, practicing selective file reading, and utilizing progressive disclosure.

---

## 2. The 10 Core Token Optimization Rules

### Rule 1: Fixed Reading Sequence
Always consult context in the canonical order:
1. `AGENTS.md` and `GEMINI.md` (Security guardrails & core directives).
2. `project_memory/PROJECT_MASTER.md` and `project_memory/CURRENT_STATE.md` (Foundational bounds & current status).
3. Targeted task-specific skills and source files only.

### Rule 2: Progressive Disclosure of Skills
Do not load the full markdown body of all 42 installed skills into every conversation turn. The system prompt exposes only skill names and descriptions (`YAML frontmatter`). The agent reads the complete `SKILL.md` **only when executing a procedure directly governed by that skill**.

### Rule 3: Selective File Reading
When inspecting existing code or logs, **never read entire multi-hundred-line files** if only a specific function, class, or section is needed.
- Use `read_file` with `StartLine` and `EndLine` parameters.
- Example: `read_file(Path="src/data/models.py", StartLine=25, EndLine=60)`.

### Rule 4: Ban on Repeated Unbounded Repository Scans
Do not repeatedly execute recursive directory commands (`Get-ChildItem -Recurse`, `tree`, `find .`) across turns.
- Consult `project_memory/ARCHITECTURE.md` or `CURRENT_STATE.md` to locate exact file paths.
- Query targeted directories only when verifying newly created files.

### Rule 5: Elimination of Redundant Architecture Monologues
Avoid re-explaining the entire 12-module architecture in conversational prose when referencing a specific task. Point to `project_memory/ARCHITECTURE.md` and focus exclusively on the module under development.

### Rule 6: Minimal Inter-Agent Delegation Payloads
When invoking subagents (`invoke_subagent`):
- Transmit typed interface contracts, parameter schemas, and explicit file paths.
- **Never paste full implementations or multi-file contents** into subagent prompts.
- Subagents read files directly from disk rather than having text piped into the prompt.

### Rule 7: Prevention of Multi-Agent Ping-Pong Loops
Subagents must operate autonomously within their bounded task, execute tests, and return a single structured completion message with exact file paths and test outputs.

### Rule 8: Concise Engineering Reports with File Links
When presenting work to the user:
- Use concise bulleted reports with clickable GitHub-style links (e.g. `[models.py](file:///c:/Users/LEGION/Downloads/BOTTRADE/src/data/models.py)`).
- Avoid printing full file dumps in chat; the files exist on disk for inspection.

### Rule 9: Targeted File Edits
Use `edit_file` with precise string matching for targeted code modifications rather than completely rewriting large files with `write_file(Overwrite=True)`.

### Rule 10: Non-Compressible Context Guardrails (Zero-Tolerance)
Under no circumstances may any prompt compression, summarization, or agent handoff omit, abbreviate, or weaken:
1. **Financial Risk Controls**: $50 reference balance, 0.01 lot volume, $1.00 risk budget, $2.00 daily loss breaker, 3-consecutive-loss pause.
2. **Trading Safety Prohibitions**: Zero live order execution, no martingale, no grid trading, no uncontrolled averaging down.
3. **Data Integrity & Lookahead Bias Rules**: Closed-bar discipline (bar $t \to t+1$ fill), UTC normalization, and realistic spread/slippage modeling.
4. **Active Defects & Blockers**: All unresolved bugs and active blockers recorded in `BUGS_AND_FIXES.md`.

---

## 3. Agent Context Budget Matrix

| Agent Role | Base Context Injected | On-Demand Skills Loaded | Permitted File Read Scope |
| :--- | :--- | :--- | :--- |
| **Quant Researcher** | `AGENTS.md`, `PROJECT_MASTER.md` | `ml4t-stationarity-tests`, `ml4t-feature-families`, `ml4t-triple-barrier` | `src/data/`, `src/indicators/` |
| **Market Regime Analyst** | `AGENTS.md`, `PROJECT_MASTER.md` | `regime-detection-for-strategy-switching`, `ml4t-regime-awareness` | `src/regime/`, `src/indicators/` |
| **Strategy Developer** | `AGENTS.md`, `PROJECT_MASTER.md` | `multi-strategy-portfolio-orchestration`, `python-trading-system-architecture` | `src/strategies/`, `src/selector/` |
| **Backtesting Engineer** | `AGENTS.md`, `PROJECT_MASTER.md` | `ml4t-run-backtest`, `ml4t-cost-model`, `ml4t-cpcv`, `walk-forward-validation-setup` | `src/backtest/`, `src/evaluation/` |
| **Risk Manager** | `AGENTS.md`, `PROJECT_MASTER.md` | `broker-constraint-validation-exness`, `kill-switch-and-drawdown-circuit-breakers` | `src/risk/`, `src/execution/` |
| **AI/ML Researcher** | `AGENTS.md`, `PROJECT_MASTER.md` | `ml4t-data-leakage`, `ml4t-meta-labels`, `ml4t-drift-detection` | `src/scoring/`, `src/research/` |
| **Software QA Engineer** | `AGENTS.md`, `PROJECT_MASTER.md` | `pytest-test-suite-for-trading-systems`, `mocking-mt5-and-broker-apis` | `tests/`, `src/` (read-only) |
