---
name: project-health-fix
description: Use when the user wants to repair issues surfaced by a project-health audit — triggers like "修第3项", "把文档断链修了", "拆一下这个大文件", "压缩归档旧文档", "fix the audit findings". Writes code/docs (not read-only); only touches items the user explicitly names.
---

# Project Health Fix

## Overview

Repairs the issues found by `project-health-audit`. **This skill writes code/docs** (unlike audit, which is read-only) — so it is **safety-first**: it only fixes what you name, one commit per item, and re-audits to confirm. Sibling of the audit skill in the project-health suite.

## When to use

- **After** an audit, when you point at specific findings: "修第 3 项" / "把文档断链都修了" / "拆一下 xxx" / "压缩归档 xxx".

**Not for:** finding issues (that's `project-health-audit`), auto-fixing everything, or touching anything outside the audit report.

## Safety principles (non-negotiable)

1. **人说才修** — only fix items the user **explicitly names**. Never auto-fix everything.
2. **One commit per item** — each fix is independently revertible.
3. **Clean base** — ensure the working tree is clean (or commit/stash existing changes) before fixing; never mix a fix with unrelated changes.
4. **Verify after** — re-run the audit check for that item (confirm it's gone); if the project has tests, run them **before** (baseline) and **after**.
5. **Stay in scope** — only touch files **directly related** to the item.
6. **When unsure, stop** — for anything risky or ambiguous, present a plan and get confirmation first.
7. **Protected surfaces** (HTTP APIs / DB schema / frontend routes) — do not touch unless explicitly asked **and** confirmed.

## Tiered gate (谁先点头才动手)

| Tier | Types | How |
|------|-------|-----|
| 🟢 mechanical | F1 broken doc refs · **F2a archive-move**（把旧记录搬进 archive，**不改正文语义**） | do it directly, then show the diff |
| 🟡 refactor | **F2b restructure**（重写/压缩/拆分长文档结构）· F3 split oversized file | **plan first → user confirms → edit → verify** |

Rule details: [references/fix-rules.md](references/fix-rules.md).

## Per-item flow

1. **Locate** — from the latest audit report, get the item's `file:line` + type.
2. **Grade** — 🟢 do directly; 🟡 present a plan and **wait for confirmation**.
3. **Baseline** — ensure a clean working tree; run tests once if they exist.
4. **Fix** — touch only related files.
5. **Verify** — re-run the audit check for that item (gone?) + tests again (unbroken?).
6. **Commit** — one commit per item; message says **what** + **which audit item**.

## Suppressions ("这项我认了，先别修")

If the user says an item should be left as-is: **don't edit code** — add an entry to `.project-health/config.yml` `suppressions` (`id` + `reason` + optional `expires`). Audit will then stop reporting it (moves to "看着吓人其实没事"). This is the **write side** of audit's read-only suppressions.

## Core principle

**Never let a fix create a bigger mess than the finding it repairs.** Small, scoped, verified, revertible — or don't do it.
