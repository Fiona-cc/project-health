---
name: project-health-design
description: Use when the user wants engineering architecture / module design guidance BEFORE building — triggers like "帮我设计这个项目/模块的工程结构", "这个功能该怎么分模块", "帮我理工程框架/依赖", "生成工程宪法", "how should I structure this project/module". Covers module boundaries, interfaces, global concerns, dependency direction, and constitution. Not UI/visual/UX design.
---

# Project Health Design

## Overview

A **design advisor** — helps you think through project or module structure **before you start coding**, not after the mess sets in. It is **all markdown + judgment** (no script needed — thinking and conversation are the point). Sibling of `project-health-audit` / `fix` / `setup` / `watch` in the project-health suite.

**It does two things:**
1. **Scope the design** — identify project or module scope, walk through a checklist of engineering concerns (boundaries, interfaces, global concerns, dependency direction).
2. **Write the constitution** — after you confirm the design, record **concrete, stable project rules** in `.project-health/constitution.yml`. These rules are the bridge: B-face designs by them, A-face (future) audits against them.

**It never writes business code, generates scaffold directories, or replaces superpowers brainstorming (which is general creative ideation; this skill is specifically about engineering structure).**

## When to use

- "帮我设计这个项目/模块的工程结构" / "这个功能该怎么分模块" / "帮我理工程框架/依赖" / "生成工程宪法"
- "how should I structure this project/module" / "design the engineering structure"
- **Before** building a new feature or starting a new project, to think through structure first.

**Not for:** finding bugs (audit), fixing issues (fix), configuring the project (setup), UI/visual design, or general brainstorming.

## Core principles

1. **Advice only, no files** — output is design recommendations + (after confirmation) the constitution YAML; never creates business code or directories.
2. **Default conversational** — design advice stays in the chat; only the constitution is a persistent file (and only after you confirm).
3. **Domain-agnostic core** — the 7 universal engineering principles work for any field. Domain packs (frontend, deep-learning) add field-specific guidance; load them by reading `config.yml`'s `domain` field. For multi-domain projects, load only the packs relevant to the current design scope. No matching pack → honestly fall back to the universal principles + say "I don't have a deep pack for this domain."
4. **Deep in principles, shallow in domains** — the value is in the cross-domain engineering thinking (which we can master); domain-specific details are thin + point to authoritative sources (framework official guides, cookiecutter templates), not an encyclopedia.
5. **Fractal** — same thinking checklist, at project scale AND module scale.

## Engineering checklist (7 universal principles — the internal lens)

Walk the user through these when designing. Details: [references/design-rules.md](references/design-rules.md).

1. **Single responsibility / boundary** — can you describe this module/project in one sentence? If not, it needs to be split.
2. **Public interface vs internal implementation** — can you change the internals without breaking consumers? If not, the interface leaks internals.
3. **Global / cross-cutting concerns unified first** — config, notifications, logging, error handling, auth — define a single entry point before scattering them everywhere.
4. **No running accounts** — don't dump unrelated logic into one file; one file doing too many things -> split into blocks.
5. **One-way dependencies, no cycles** — A → B → A is broken; layers don't skip across.
6. **Name things for what they are**.
7. **Blocks first, then fill in** — identify the modules and their interfaces FIRST, then implement each one. Don't open a file and start typing.

## Two scopes (one skill, different checklists, identify scope first)

### Project scope ("help me structure this project")
- Module map: what are the top-level modules and what each does
- Application-level capabilities: notifications / config / auth / logging — who owns them, through what interface
- Business boundaries: where one module ends and another begins
- Dependency direction: who depends on whom
- Public interfaces: what each module exposes
- Output: structure recommendation + a proposed **constitution** (concrete rules)

### Module scope ("help me design this notification feature")
- **Responsibility** (one sentence: "它负责…")
- **What it does NOT do** (negative boundary — separates truly)
- **Public interface** — what it exposes
- **Internal structure** — how it's organized inside
- **Dependencies** — what it depends on, what depends on it
- **State / config / errors / testing** — where each lives
- Does it fit in the existing structure? Does it violate the constitution?
- Output: design recommendation

### Flow (both scopes): 
Identify scope → walk the checklist → give concrete advice grounded in the real project → **show the proposed constitution rules** → user confirms → **write `constitution.yml`**.

## Constitution (the bridge between B-face design and A-face audit)

- File: `.project-health/constitution.yml` — YAML, machine-readable, written **only after you confirm**.
- Each rule: `{id, scope(project|module), rule, level(hard|advisory), reason}`.
- **hard** → future audit would flag as 🔴; **advisory** → ⚠️.
- Only contains **confirmed, stable, concrete, judgeable** rules — NO abstract slogans ("keep single responsibility" stays in the checklist; the constitution gets "page components must not contain business logic; extract to services/hooks").
- The 7 principles are the **internal lens**; the constitution records **what those principles mean for this specific project**.

## Domain packs

Location: `design/references/domains/`. Available: `frontend.md` (精装), `deep-learning.md` (薄包), `_template.md`. Load by reading `config.yml`'s `domain` field. For multi-domain projects, only load the packs relevant to the current design scope. No matching pack → honestly fall back to the universal principles.

For domains without a deep pack: honestly fall back to the universal 7 principles. Never fabricate depth.

## Core principle

**Make the user think before they code.** This skill doesn't build — it asks the right questions and writes down the rules.
