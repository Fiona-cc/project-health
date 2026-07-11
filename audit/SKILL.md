---
name: project-health-audit
description: Use when the user wants a read-only engineering health checkup of a project — triggers like "check project health", "audit the codebase", "项目健康/体检/审计代码库", "is this project getting messy/unmaintainable", or periodically as a project grows to catch rot early. Scans code and docs; never edits.
---

# Project Health Audit

## Overview

Read-only engineering health checkup. It runs a bundled **deterministic scanner** (`scripts/scan.py`) so the **same code yields the same findings on any agent/platform**; the skill then interprets the structured results and writes a **file-cited** report of the highest-signal maintainability problems. **Never edits code or docs.**

This is the `audit` sub-skill of the project-health suite. Full design: the project's `blueprint.md` / `stage-1-audit.md` spec.

## When to use

- "检查项目健康" / "项目状态怎么样" / "审计代码库" / "check project health" / "audit the codebase"
- Periodically as a project grows, to catch the first signs of bloat/drift.

**Not for:** fixing issues (a separate step), deep security/performance audits, or language-specific dead-code detection.

## What it checks (v1)

| ID | Check | Signal |
|----|-------|--------|
| C1 | Oversized source files (⚠️400 / 🔴800 non-empty lines) | file too big to safely change |
| C2 | Broken references in docs (dead file paths + npm commands) | docs drifting from code |
| C3 | Oversized docs (⚠️500 lines) | doc-dump, needs splitting/compaction |
| C4 | Debt hotspots (large × frequently-changed, via git) | technical-debt time bomb |

## Process

1. **Run the bundled deterministic scanner** (the single source of truth — do **not** hand-scan). Ensure Python **≥3.8 + PyYAML**; then run this skill's `scripts/scan.py`:
   ```
   python <this-skill-dir>/scripts/scan.py --root <project-root> --output <project-root>/.project-health/state/latest-run.yml
   ```
   - On **non-zero exit, explain by code and STOP** — never fall back to improvising the scan:
     `2` = config error · `3` = Python/PyYAML missing (tell the user to `pip install pyyaml`; do NOT auto-install) · `4` = bad root · `5` = internal.
   - **Never re-compute C1–C4 yourself via shell / grep / find / git** — that reintroduces per-agent inconsistency. The scanner is authoritative; the scanner commits `commit` itself (agents don't pass it).
2. **Read the structured state** `latest-run.yml`: `summary`, `findings`, `suppressed_findings`, `expired_suppressions`, `scan.skipped_checks`.
3. **Render the report** per [references/report-format.md](references/report-format.md): map each finding's `message_key` → 人话 (by `level`), `severity` → 🔴/⚠️/ℹ️, compute the score **at this layer**, and state scan scope + any skipped checks (so "查过没问题" is visible). If `context` is set, frame the report around it. Write `.project-health/reports/audit-<run.id>.md` **and** show inline.

> `references/code-rules.md` / `doc-rules.md` now **document what the scanner does** (the check spec), not runtime shell instructions.

## Defaults (override via `.project-health/config.yml`)

`file_warn: 400`, `file_error: 800`, `doc_warn: 500`.

## Core principles

- **Deterministic via the scanner.** All C1–C4 measurement lives in `scripts/scan.py` (single source of truth). The skill **never re-derives findings by hand** — it only interprets the scanner's structured output.
- **Conservative on C2.** Markdown links are resolved by markdown semantics (relative to the doc); a real broken link is flagged, but plain prose words are never mistaken for paths.
- **No padding.** If nothing is material, say "未发现实质问题". Never recommend rewrites.
- **Score is for perception, not a KPI.** The action items are the point.
