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
| Stage 2 · fix | 按报告逐项修 + 压缩归档 | 规划中 |
| Stage 3 · setup | 猜+问背景 → 生成配置 + 领域包 | 规划中 |
| Stage 4 · watch | 对比基线 + 文档守护（主动提醒） | 规划中 |

> ⚠️ **运行形态**：project-health 目前是一套 **Claude Code Skill**（在 Claude Code / 支持 Skill 的 agent 会话里用**自然语言触发**），**暂无独立命令行工具（CLI）**。README 与 references 里出现的 `git …`、`grep …`、`find …` 等命令，是 skill 内部**让 agent 执行的示例步骤**，**不是**一个叫 `project-health` 的可执行程序，别当 CLI 直接敲。

## 结构

```
project-health/
  audit/                     ← Stage 1：只读体检 skill
    SKILL.md                 ← 薄入口（触发词 + 4 步流程）
    references/
      code-rules.md          ← C1 超大文件 / C4 热点 / 扫描范围
      doc-rules.md           ← C2 断链 / C3 超大文档
      report-format.md       ← 报告模板 / 健康分 / 语气
  docs/                      ← 设计文档（给协作者看）
    blueprint.md             ← 完整蓝图（俯视图）
    stage-1-audit.md         ← Stage 1 实现 spec
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

**推荐方式（独立 skill 文件夹，自动发现最稳）**：把本仓库 `audit/` 装成一个独立 skill——
```
~/.claude/skills/project-health-audit/
  SKILL.md            ← 复制自本仓库 audit/SKILL.md
  references/         ← 复制自本仓库 audit/references/
    code-rules.md
    doc-rules.md
    report-format.md
```
即把 `audit/SKILL.md` 与 `audit/references/` 整体放到 `~/.claude/skills/project-health-audit/` 下。

**若想保留套件结构**（`project-health/audit/…`）：把整个仓库放到 `~/.claude/skills/project-health/`，audit 子 skill 即 `~/.claude/skills/project-health/audit/SKILL.md`。能否被自动发现，取决于你的 Claude Code 版本对**嵌套 skill** 的支持——发现不到就改用上面的"独立 skill 文件夹"方式。

装好后，新开一个会话说 **"检查项目健康" / "audit the codebase"** 即可触发。

## 协作说明

设计思路全在 `docs/blueprint.md`。欢迎 GPT / Codex / 人类围绕这份蓝图一起完善——
尤其是 Stage 3 的**领域包**（各领域理想工程骨架）和健康分的按比例校准。

## 设计原则

渐进式披露 · 确定性优先 · 通用内核 + 可插拔领域包 · 领域约定要"软" · 猜后再问 · 报告不注水 · 归档而非堆积。
