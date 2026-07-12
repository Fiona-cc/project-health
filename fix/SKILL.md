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
4. **Honor `execution.trust` （安全闸门）** — read `.project-health/config.yml`'s `execution.trust` and `approved_verify` before running ANY project command.
   - `disabled`：**禁止执行** 项目 build/test/verify 等命令；只读检查（re-audit、读文件）**仍然允许**。改后明确说"未执行自动验证"。
   - `prompt`（缺省）：首次想跑 verify/test 命令前，**先展示具体命令 + 说明会执行项目代码 → 等用户确认**；确认后可记入 `approved_verify`（下次免问）。自动探测≠用户批准。
   - `trusted`：可直接跑 `config.verify` 和已在 `approved_verify` 白名单的命令；自动探测出的新命令**仍需确认**。
   - 优先级（高→低）：`approved_verify` > `trust` > 自动探测。Agent **不自行往白名单加东西**。
5. **Verify after — 改完必须确认没坏** — for any **code-touching** fix and when trust allows: run the verify command (baseline → fix → verify again). **If it passed at baseline but fails after → the fix broke something → revert this fix immediately** (revert precisely per rule 6). Doc-only fixes skip build-verify. If trust forbids or no verify command exists, **say so honestly** — do not claim verification.
6. **Precise rollback（精确回滚）** — before fixing, record the **touched files** list (including new files the fix will create). If rollback is needed: **revert only those files** — do not `git restore .`, `git checkout -- .`, `git clean -fd`, or `git reset --hard`. New files created by the fix → delete only those. Do NOT affect pre-existing untracked files. If you cannot determine the exact rollback scope, **stop and report**; do not execute a wide clean.
7. **Stay in scope** — only touch files **directly related** to the item.
8. **When unsure, stop** — for anything risky or ambiguous, present a plan and get confirmation first.
9. **Protected surfaces** (HTTP APIs / DB schema / frontend routes) — do not touch unless explicitly asked **and** confirmed.

## Tiered gate (谁先点头才动手)

| Tier | Types | How |
|------|-------|-----|
| 🟢 mechanical | F1 broken doc refs · **F2a archive-move**（把旧记录搬进 archive，**不改正文语义**） | do it directly, then show the diff |
| 🟡 refactor | **F2b restructure**（重写/压缩/拆分长文档结构）· F3 split oversized file | **plan first → user confirms → edit → verify** |

Rule details: [references/fix-rules.md](references/fix-rules.md).

## Per-item flow

1. **Locate** — from the latest audit report, get the item's `file:line` + type.
2. **Grade** — 🟢 do directly; 🟡 present a plan and **wait for confirmation**.
3. **Baseline** — ensure a clean working tree. **If code-touching and trust allows**: run the verify command + tests as a baseline. If baseline already has failures (not all-green), record the failing set — don't block outright; only a **new** failure from the fix is a problem. If the failure set cannot be reliably compared, note "verification uncertain" and proceed with user consent.
4. **Fix** — touch only related files. Record the file paths (including new files this fix creates).
5. **Verify** — re-run the audit check for the item (gone?). **If code-touching and trust allows**: re-run verify command + tests. If they now fail but passed at baseline → **revert precisely** (only this fix's files). If baseline already had failures: compare the failure sets — **new failures = the fix broke something → revert**; same old failures = OK. If trust forbids or no verify/tests exist, **say so honestly**.
6. **Commit** — one commit per item; message says **what** + **which audit item**.

## Suppressions ("这项我认了，先别修")

If the user says an item should be left as-is: **don't edit code** — add an entry to `.project-health/config.yml` `suppressions` (`id` + `reason` + optional `expires`). Audit will then stop reporting it (moves to "看着吓人其实没事"). This is the **write side** of audit's read-only suppressions.

## Core principle

**Never let a fix create a bigger mess than the finding it repairs.** Small, scoped, verified, revertible — or don't do it.
