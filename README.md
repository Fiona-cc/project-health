# project-health

> AI 辅助开发的**工程健康**技能套件 —— 让 AI 参与的项目长期不臃肿、不混乱、可维护。

## 这是什么

AI 写代码有三个天然坏习惯：不清死代码、堆臃肿结构、文档轰炸。人往往到"改不动了"才发现。
`project-health` 是给项目做**定期体检 + 长期养护**的一套 Claude Code Skill，盯三件事：

1. **代码不堆砌** —— 文件别太大、结构别乱、别留"又大又常改"的定时炸弹
2. **文档能分层读** —— 薄根入口 + 渐进式披露，别糊成一坨
3. **改代码文档要跟上** —— 别让文档和代码越走越远（断链、过时）

**双重野心**：先**通用**（任何项目直接可用），再通过 `setup` 问答长出**贴合具体项目**的定制规则。

## 当前状态

| 阶段 | 内容 | 状态 |
|---|---|---|
| **Stage 1 · audit** | 只读体检器：超大文件 / 断链 / 超大文档 / 危险热点，出报告 | ✅ 精简版可用 |
| **Stage 2 · fix** | 按报告逐项修 + 压缩归档（安全为先、人说才修、分级闸门） | ✅ Claude Skill 初版可用 |
| **Stage 3 · setup** | 检测项目背景 → 用户确认 → 生成 `.project-health/config.yml` | ✅ Claude Skill 初版可用 |
| **Stage 4 · watch** | 立基线 → 只报增量（新增/已解决/遗留）+ 文档漂移检测 | ✅ Claude Skill 初版可用 |
| **Stage 5 · design** | 设计顾问：项目/模块 结构设计 + 生成工程宪法 | ✅ Claude Skill 初版可用 |

> ⚠️ **运行形态**：project-health 目前是一套 **Claude Code Skill**。**audit 额外依赖 Python ≥3.8 + PyYAML**（`pip install pyyaml`）运行确定性扫描脚本（`audit/scripts/scan.py`）；缺运行时 audit 会报错说清、不会偷偷降级。fix / setup / watch / design 是纯 markdown skill，无额外依赖。：project-health 目前是一套 **Claude Code Skill**（在 Claude Code / 支持 Skill 的 agent 会话里用**自然语言触发**），**暂无独立命令行工具（CLI）**。README 与 references 里出现的 `git …`、`grep …`、`find …` 等命令，是 skill 内部**让 agent 执行的示例步骤**，**不是**一个叫 `project-health` 的可执行程序，别当 CLI 直接敲。

## 结构

```
project-health/
  audit/                     ← Stage 1：只读体检 skill
    SKILL.md                 ← 薄入口（触发词 + 4 步流程）
    references/
      code-rules.md          ← C1 超大文件 / C4 热点 / 扫描范围
      doc-rules.md           ← C2 断链 / C3 超大文档
      report-format.md       ← 报告模板 / 健康分 / 语气
  fix/                       ← Stage 2：按报告逐项修（安全为先）
    SKILL.md                 ← 薄入口（安全原则 + 分级闸门 + 逐项流程）
    references/
      fix-rules.md           ← F1 断链 / F2 压缩归档 / F3 拆分 细则
  setup/                     ← Stage 3：检测背景 → 确认 → 生成 config
    SKILL.md                 ← 薄入口（检测 → 摆结论问确认 → 写 config）
    references/
      setup-rules.md         ← 检测细则 / 提问清单 / config schema / 结构建议
  watch/                     ← Stage 4：立基线 → 只报增量
    SKILL.md                 ← 薄入口（取基线 → 跑 audit → 比对 → 报增量+文档漂移）
    references/
      watch-rules.md         ← 基线来源 / 增量比对 / 文档漂移 / 报告模板
  docs/                      ← 设计文档（给协作者看）
    blueprint.md             ← 完整蓝图（俯视图）
    stage-1-audit.md         ← Stage 1 实现 spec
    stage-2-fix.md           ← Stage 2 实现 spec
    stage-3-setup.md         ← Stage 3 实现 spec
    stage-4-watch.md         ← Stage 4 实现 spec
    research/                ← 高赞 skill 检查维度研究快照（代码侧 57 + 文档侧 71）
```

## audit 做什么（v1）

| ID | 检查 | 阈值（可配） |
|----|------|------|
| C1 | 超大源文件（按 生产/测试/样式/数据 分组打标签） | ⚠️400 / 🔴800 非空行 |
| C2 | 文档断链（路径 + npm 命令），保守提取、宁漏勿错 | — |
| C3 | 超大文档 | ⚠️500 行 |
| C4 | 危险热点（大文件 × 高频改动，读 git 历史） | — |

**只读**，绝不改代码/文档。每条发现 `file:line` 可定位。健康分仅供感知、不是 KPI。
可选 `.project-health/config.yml` 覆盖阈值、`level`（小白/专家）、`suppressions`（"看着吓人其实没事"的沉淀）。

## 安装 / 使用

这是 Claude Code Skill，靠会话里**自然语言触发**，**没有独立 CLI**。

**推荐方式（独立 skill 文件夹，自动发现最稳）**：把本仓库 `audit/`、`fix/`、`setup/`、`watch/`、`design/` 各装成一个独立 skill——
```
~/.claude/skills/project-health-audit/     ← 复制自本仓库 audit/（SKILL.md + references/ + scripts/！）
~/.claude/skills/project-health-fix/       ← 复制自本仓库 fix/（SKILL.md + references/）
~/.claude/skills/project-health-setup/     ← 复制自本仓库 setup/（SKILL.md + references/）
~/.claude/skills/project-health-watch/     ← 复制自本仓库 watch/（SKILL.md + references/）
~/.claude/skills/project-health-design/    ← 复制自本仓库 design/（SKILL.md + references/ + domains/）
```
**⚠️ audit 必须带 `scripts/`**（`scan.py`），只复制 `SKILL.md + references/` 无法工作（audit 会报错说"缺脚本"、不会偷偷降级）。

**依赖**：audit 需要 **Python ≥3.8 + PyYAML**。安装：`pip install pyyaml`。fix / setup / watch / design 是纯 markdown skill，无额外依赖。

**若想保留套件结构**把整个仓库放到 `~/.claude/skills/project-health/`。

装好后，新开一个会话，用大白话触发：
- **"配置 project-health"** → setup（首次，生成 config）
- **"检查项目健康"** → audit（体检出报告）
- **"修第 X 项"** → fix（体检后逐项修）
- **"看最近新增了哪些问题"** → watch（对比基线只报增量）
- **"帮我设计这个模块的工程结构"** → design（动工前想清楚结构+生成宪法）

## 协作说明

设计思路全在 `docs/blueprint.md`。欢迎 GPT / Codex / 人类围绕这份蓝图一起完善——
尤其是 Stage 3 的**领域包**（各领域理想工程骨架）和健康分的按比例校准。

## 设计原则

渐进式披露 · 确定性优先 · 通用内核 + 可插拔领域包 · 领域约定要"软" · 猜后再问 · 报告不注水 · 归档而非堆积。
