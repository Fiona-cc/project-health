---
name: project-health-audit
description: Use when the user wants a read-only engineering health checkup of a project — triggers like "check project health", "audit the codebase", "项目健康/体检/审计代码库", "is this project getting messy/unmaintainable", or periodically as a project grows to catch rot early. Scans code and docs; never edits.
---

# Project Health Audit

## Overview

Read-only engineering health checkup. Scans a project and produces a **file-cited** report of the highest-signal maintainability problems, so rot gets caught before the code becomes unchangeable. **Never edits code or docs.**

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

1. **Load scan scope + config.** Apply built-in default ignores + `.project-healthignore` (if present). Read `.project-health/config.yml` for thresholds / `level` / `context` / `suppressions`, else use defaults. → see [references/code-rules.md](references/code-rules.md).
2. **Run checks.** C1 & C3 (count lines) → C2 (extract refs, test existence) → C4 (git churn ∩ largest files; **skip silently if not a git repo**). Rules: C1/C4 in [references/code-rules.md](references/code-rules.md), C2/C3 in [references/doc-rules.md](references/doc-rules.md).
3. **Apply suppressions.** Findings whose `id` matches a non-expired suppression move to the "看着吓人其实没事" section instead of being reported.
4. **Assemble report** per [references/report-format.md](references/report-format.md) — if `context` is set, frame the report around it; make clear that clean checks WERE run (not skipped) → write `.project-health/reports/audit-YYYY-MM-DD.md` **and** show inline.

## Defaults (override via `.project-health/config.yml`)

`file_warn: 400`, `file_error: 800`, `doc_warn: 500`.

## Core principles

- **Deterministic only.** Line counts, path-existence, git history — no guessing. Every finding cites `file:line`.
- **Conservative on C2.** Never flag a plain word as a broken path. Prefer under-reporting over false alarms — one bogus "broken link" and the user stops trusting the tool.
- **No padding.** If nothing is material, say "未发现实质问题". Never recommend rewrites.
- **Score is for perception, not a KPI.** The action items are the point.
