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

> ⚠️ **运行形态**：project-health 目前是一套 **Claude Code Skill**，通过与支持 Skill 的 Agent 会话**自然语言触发**，暂无独立 CLI。**audit 额外依赖 Python ≥3.8 + PyYAML**（`pip install pyyaml`）运行确定性扫描脚本（`audit/scripts/scan.py`）；缺运行时 audit 会报错说清、不会偷偷降级。fix / setup / watch / design 是纯 markdown skill，无额外依赖。README 里出现的 `git`/`grep`/`find` 等命令，是 skill 内部让 Agent 执行的示例步骤，**不是**一个叫 `project-health` 的可执行程序。

## 结构

```
project-health/
  audit/                     ← Stage 1：只读体检 skill
    SKILL.md                 ← 薄入口（触发词 + 4 步流程）
    scripts/scan.py          ← 确定性扫描引擎（Python，Agent 调它、不自己即兴）
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
  design/                    ← Stage 5：设计顾问（B 面）
    SKILL.md                 ← 薄入口（两尺度 + 7 条原则 + 宪法）
    references/
      design-rules.md        ← 工程设计清单 / scope 提问 / 宪法格式
      domains/               ← 领域包（前端·精装 / DL·薄包 / 模板）
  docs/                      ← 设计文档（给协作者看）
    blueprint.md             ← 完整蓝图（俯视图）
    schema-contract-v1.md    ← finding / config / state 数据契约
    hardening-plan-v1.1.md   ← A 面加固计划
    stage-1-audit.md … stage-4-watch.md  ← 各 Stage 实现 spec
    b-face-design-advisor.md ← B 面 spec
    research/                ← 高赞 skill 检查维度研究快照
  tests/                     ← 金测（fixtures + golden.py + expected）
```

## audit 做什么（v1）

| ID | 检查 | 阈值（可配） |
|----|------|------|
| C1 | 超大源文件（按 生产/测试/样式/数据 分组打标签） | ⚠️400 / 🔴800 非空行 |
| C2 | 文档断链（路径 + npm 命令），保守提取、宁漏勿错 | — |
| C3 | 超大文档 | ⚠️500 行 |
| C4 | 危险热点（大文件 × 高频改动，读 git 历史） | — |

**只读**，绝不改代码/文档。断链等位置型问题提供 `file:line`；文件/文档级问题提供路径和测量证据（如 `src/App.tsx — 986 非空行`）。健康分仅供感知、不是 KPI。
可选 `.project-health/config.yml` 覆盖阈值、`level`（`beginner / standard / expert`）、`suppressions`（"看着吓人其实没事"的沉淀）。

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

## 当前限制

- **设计顾问（design）** 只提供通用原则 + 前端/深度学习领域包；其他领域回退通用原则。
- **宪法自动检查（C5）** 当前仅支持 `max_file_lines`；其余 deterministic kind（`forbidden_dependency` 等）已定义 schema，检查逻辑待实现。
- **Watch** 的文档守护 hook（操作后自动提醒）尚未实现，需 Claude Code hook 配合。
- **跨 agent 验收**：目前仅在 Claude Code 上验证；Codex/Cursor 等平台未正式测试。
- **Golden 测试** 已在本地通过（12 fixtures），跨平台 CI 待配置。
- 项目仍为个人工具定位，未做多用户/团队权限设计。

**若想保留套件结构**把整个仓库放到 `~/.claude/skills/project-health/`。

装好后，新开一个会话，用大白话触发：
- **"配置 project-health"** → setup（首次，生成 config）
- **"检查项目健康"** → audit（体检出报告）
- **"修第 X 项"** → fix（体检后逐项修）
- **"看最近新增了哪些问题"** → watch（对比基线只报增量）
- **"帮我设计这个模块的工程结构"** → design（动工前想清楚结构+生成宪法）

## 协作说明

设计思路全在 `docs/blueprint.md`。欢迎 GPT / Codex / 人类围绕这份蓝图一起完善——
尤其是 **Design 的领域包**、**Constitution 契约**和跨 Agent 验收。

## 设计原则

渐进式披露 · 确定性优先 · 通用内核 + 可插拔领域包 · 领域约定要"软" · 猜后再问 · 报告不注水 · 归档而非堆积。
