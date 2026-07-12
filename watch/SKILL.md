---
name: project-health-watch
description: Use when the user wants to see what CHANGED in a project's health since last time — triggers like "看最近新增了哪些问题", "最近项目健康有什么变化", "对比上次体检", "项目健康监控", "watch project health". Compares a fresh audit against a saved baseline and reports only the delta (new / resolved / remaining) plus doc drift. Never edits your code or project docs.
---

# Project Health Watch

## Overview

**Watch = audit with memory.** It sets a **baseline**, then on later runs reports **only what changed** since — 🆕 new / ✅ resolved / 🟰 remaining — so a long-lived project isn't re-scared with its whole issue list every time. Also flags docs that look **possibly out of date** vs recently-changed code. **It never touches your code or project docs**; the only things it writes are its own artifacts under `.project-health/` (a watch report; and — only when you explicitly say "接受现状 / 重置基线" — `baseline.md`).

## When to use

- "看最近新增了哪些问题" / "最近项目健康有什么变化" / "对比上次体检" / "项目健康监控" / "watch project health".
- Periodically on an existing project you've already audited at least once.

**Not for:** the first full checkup (that's `project-health-audit`), fixing (`project-health-fix`), or configuring (`project-health-setup`).

## Core principles

1. **Report the delta, don't re-scare** — emphasize **new**; celebrate **resolved**; give **remaining** only as a count, not a re-listing.
2. **Never touches your code/docs** — watch only reads your project; it writes only its own artifacts under `.project-health/` (the watch report always; `state/baseline.yml` **only on explicit user confirmation**). Fixing is `project-health-fix`.
3. **Respect suppressions** — a suppressed finding never counts as "new".
4. **Baseline is updatable** — after clearing a batch, the user can set the current state as the new baseline ("accept current state").

## Process

1. **Get or create a baseline** — `.project-health/state/baseline.yml` → else use the latest `.project-health/state/latest-run.yml` as reference → else this is the **first run**: run a `project-health-audit` first, show the result, and **ask whether to save the state as `baseline.yml`** — write it **only if the user confirms**; if they decline, just show this run and don't establish a baseline.
2. **Fresh audit** — run `project-health-audit` now (this produces `.project-health/state/latest-run.yml` with the current structured findings).
3. **Run the bundled comparator** — call `scripts/compare.py <baseline.yml> <latest-run.yml>`. The output is structured YAML (fire-and-forget — no hand-diffing). If Python/PyYAML are missing, explain which package is needed, then stop.
4. **Doc-drift check** — via git, find code changed in the last N days (default 14) whose related docs weren't updated; flag them as **possibly out of sync — worth a look** (detection only, hedged — never claim the docs are definitely stale, and never edit them).
5. **Report** — render the structured delta + doc-drift result: emphasize 🆕 new; write `.project-health/reports/watch-YYYY-MM-DD.md` + show inline. If nothing new, say "自基线以来无新增问题" (no padding).

## Report shape

```
🆕 新增（n）  ← 重点，每条 file:line + 建议
✅ 已解决（m）
🟰 遗留（k，未重复展开）
📄 文档可能未同步（j）— 相关代码近期改过、文档可能没跟上、建议看一眼
基线：<来源与日期>
```

Baseline priority, id-diff rules, doc-drift judgment, and the full report template: [references/watch-rules.md](references/watch-rules.md).

## Note on the "doc guardian"

Watch does the **detection** half (you ask → it checks whether recently-changed code has stale docs). The **proactive** half (auto-prompt after every edit) needs a Claude Code **hook** (PostToolUse/Stop), not a skill — deferred (a future Claude Code hook); config `doc_links` serves the current watch doc-drift checks.
