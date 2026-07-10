---
name: project-health-watch
description: Use when the user wants to see what CHANGED in a project's health since last time — triggers like "看最近新增了哪些问题", "最近项目健康有什么变化", "对比上次体检", "项目健康监控", "watch project health". Compares a fresh audit against a saved baseline and reports only the delta (new / resolved / remaining) plus doc drift. Read-only.
---

# Project Health Watch

## Overview

**Watch = audit with memory.** It sets a **baseline**, then on later runs reports **only what changed** since — 🆕 new / ✅ resolved / 🟰 remaining — so a long-lived project isn't re-scared with its whole issue list every time. Also flags docs that look **out of date** vs recently-changed code. **Read-only** (like audit; never edits).

## When to use

- "看最近新增了哪些问题" / "最近项目健康有什么变化" / "对比上次体检" / "项目健康监控" / "watch project health".
- Periodically on an existing project you've already audited at least once.

**Not for:** the first full checkup (that's `project-health-audit`), fixing (`project-health-fix`), or configuring (`project-health-setup`).

## Core principles

1. **Report the delta, don't re-scare** — emphasize **new**; celebrate **resolved**; give **remaining** only as a count, not a re-listing.
2. **Read-only** — watch only looks; fixing is `project-health-fix`.
3. **Respect suppressions** — a suppressed finding never counts as "new".
4. **Baseline is updatable** — after clearing a batch, the user can set the current state as the new baseline ("accept current state").

## Process

1. **Get baseline** — `.project-health/baseline.md` → else the latest `.project-health/reports/audit-*.md` → else this is the **first run**: run an audit and offer to save it as the baseline. See [references/watch-rules.md](references/watch-rules.md).
2. **Fresh audit** — run the audit checks now (same engine/ids as `project-health-audit`).
3. **Diff by finding id** (`<check>:<path>`): **new** = now∖baseline · **resolved** = baseline∖now · **remaining** = both.
4. **Doc-drift check** — via git, find code changed in the last N days (default 14) whose related docs weren't updated; flag them (detection only — do not edit).
5. **Report** — emphasize 🆕 new; write `.project-health/reports/watch-YYYY-MM-DD.md` + show inline. If nothing new, say "自基线以来无新增问题" (no padding).

## Report shape

```
🆕 新增（n）  ← 重点，每条 file:line + 建议
✅ 已解决（m）
🟰 遗留（k，未重复展开）
📄 文档可能滞后（j）— 代码近期改过、文档未更新
基线：<来源与日期>
```

Baseline priority, id-diff rules, doc-drift judgment, and the full report template: [references/watch-rules.md](references/watch-rules.md).

## Note on the "doc guardian"

Watch does the **detection** half (you ask → it checks whether recently-changed code has stale docs). The **proactive** half (auto-prompt after every edit) needs a Claude Code **hook** (PostToolUse/Stop), not a skill — deferred; the `doc_maintenance.prompt_after_ops` config field is the reserved slot.
