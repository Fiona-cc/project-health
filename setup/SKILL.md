---
name: project-health-setup
description: Use when the user wants to set up or configure project-health for a project — triggers like "接入项目健康监控", "给项目做工程配置", "配置 project-health", "set up project health", usually once per project. Detects the project's background (domain/stack/verify) and writes .project-health/config.yml; suggests structure but creates no business code or project scaffolding.
---

# Project Health Setup

## Overview

One-time onboarding for a project. **Detects the project's background (猜后再问), confirms with the user, and writes `.project-health/config.yml`** so `project-health-audit` / `project-health-fix` fit this project. Suggests structure for new projects but **creates no business code and scaffolds no project directories** — its only output file is `.project-health/config.yml`.

## When to use

- "接入项目健康监控" / "给项目做工程配置" / "配置 project-health" / "set up project health".
- Usually **once** per project (re-run to update the config).

**Not for:** running the checkup (that's `project-health-audit`), fixing issues (`project-health-fix`), or scaffolding a project skeleton.

## Core principles

1. **猜后再问 (detect, then confirm)** — auto-detect everything you can; show the user your findings and let them correct — never make them describe from scratch.
2. **Brainstorm-like** — surface points they may not have considered (e.g. "MVP fast-iteration or long-term product? it changes how strict the thresholds should be") and let them confirm.
3. **Config-only, no scaffolding** — the only file it writes is `.project-health/config.yml`; it suggests structure but creates no business code and no project directories.
4. **Ask once, not in a loop** — after detection, group the un-detectable questions into one small set.
5. **Don't clobber** — if a config already exists, show it and confirm before overwriting.

## Process

1. **Detect** — scan manifests → domain/stack, verify command, existing doc structure, threshold starting point. See [references/setup-rules.md](references/setup-rules.md).
2. **Present + ask (guiding)** — show the detected profile; then **guide the user to describe their background** — they usually won't volunteer it. Ask, with examples: **what the project is *for*** (prod / prototype-demo / internal tool / learning), **their *role*** (solo/team; dev/PM/…), **their *biggest worry*** (getting messy / logic unclear / too slow / unreadable / docs lagging). From those, **propose** `level` and `goal` (don't ask them cold), summarize a one-line **`context`**, then ask about suppressions. Details: [references/setup-rules.md](references/setup-rules.md).
3. **Confirm** — let the user adjust the proposed level/goal/context; goal nudges thresholds (MVP slightly looser, long-term slightly stricter).
4. **Write** — create `.project-health/` if needed and write `config.yml` (full schema in references). Don't overwrite an existing config without confirmation.
5. **New project** — if the project is near-empty, give a **generic** structure suggestion for the detected domain (advice only, no files).
6. **Hand off** — tell the user they can now run **"检查项目健康"** to see audit use the new config.

## Config schema (setup is the initial generator / main maintainer)

**Who writes/reads it:** setup **generates & maintains** it · audit **reads only** (`thresholds`/`level`/`context`/`suppressions`) · fix **may append** `suppressions` (also reads `verify`) · watch reads `doc_maintenance` · design reads `domain` + `context` to load matching domain packs. **`constitution.path`** is the single source of truth for project rules (no separate `project_rules`). The authoritative schema is `docs/schema-contract-v1.md`.**

```yaml
# 正式 schema 以 docs/schema-contract-v1.md 为准；本处为示例。
schema_version: 1

domain: [frontend]
stack: [react, vite]
level: standard            # beginner | standard | expert
goal: long-term            # mvp | long-term — threshold strictness
context: ""                # one-line background (purpose / your role / biggest worry)

thresholds:                # audit 读取；setup 按 goal 提议、用户可调
  file_warn: 400
  file_error: 800
  doc_warn: 500
  churn_days: 180
  churn_min: 3

verify: "npm run build"    # fix 改代码后的兜底命令；v1 单条

execution:                 # fix 安全闸门
  trust: prompt            # prompt | trusted | disabled
  approved_verify: []

doc_links: []              # 代码→文档 显式映射（watch 降噪，Phase 4）

constitution:              # 工程规矩→唯一真源
  path: ".project-health/constitution.yml"

suppressions: []           # id = finding 的 stable id，由 audit 生成
```

Field details, detection rules, and per-domain structure advice: [references/setup-rules.md](references/setup-rules.md).

## Core principle

**Make the user confirm, not compose.** A good setup feels like the tool already understands the project and just needs a nod.
