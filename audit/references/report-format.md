# report-format.md — 报告模板 / 健康分 / 语气

> audit v1 的输出规范。**报告不再靠 AI 现场扫，而是渲染 `scan.py` 写出的 `.project-health/state/latest-run.yml`。**

---

## 输入与渲染（从结构化状态出发）

渲染只做三件事：**severity→emoji、message_key→人话（按 level）、算分**。

**severity → emoji**：`error`→🔴 · `warning`→⚠️ · `info`→ℹ️。
**分组**：`kind==hotspot` 单列 **🔥 危险热点** 一节；其余 `info`（测试/样式/数据大文件）列 **ℹ️ 信息**。

**message_key → 人话**（按 `level` 展开；数据取自 `evidence`）：

| message_key | 简明（standard） | 建议 |
|---|---|---|
| oversized_source_file | 文件过大（`lines` 行），改动风险高 | 按职责拆分为多个文件/类 |
| broken_local_reference | 文档指向不存在的路径 `target` | 改成正确路径或删除该引用 |
| broken_npm_script | 文档引用了不存在的 npm 脚本 `target` | 改成 package.json 里真有的脚本 |
| oversized_doc | 文档过长（`lines` 行） | 拆分/压缩；旧记录归档为一句话 |
| debt_hotspot | 又大又常改（`lines` 行 / 近改 `churn` 次） | 优先关注/拆分 |

- 定位：纯文本 `subject:line`，行号取自 `evidence.locations`（多处就列多个）。
- `suppressed_findings` → "看着吓人其实没事"一节；`expired_suppressions` → 提示"抑制已到期，重新计入"。
- `scan.skipped_checks` → 在"扫描范围"说明（如 非 git 仓 C4 跳过 / 坏 package.json 命令检查跳过）。

---

## 落盘 + 内联

- 写入 `.project-health/reports/audit-YYYY-MM-DD.md`（若 config 指定别的路径则用之）。
- 同时在对话里内联展示。
- 日期用当前日期。

## 定位方式（重要）

- **每条发现必须保留纯文本 `file:line`**（如 `audit/references/doc-rules.md:42`），这是**唯一保证可靠的定位方式**——任何环境、任何工具都能读。
- 可点击链接（如 markdown `[file:line](file#Lline)`）**只是增强，不能替代纯文本**。要用就在纯文本旁边加，别只给链接。

## 结合项目背景（context）

- 若 `.project-health/config.yml` 有非空 `context`，报告**开头用一句话呼应它**，并在解读发现时**围绕用户在意的点**来讲——不要千篇一律的通用报告。
  - 例：context 说"PM 的 demo、最担心多轮改需求后逻辑变乱" → 把 🔥 热点解读成"这几个又大又常改的文件，最可能是逻辑缠在一起的地方，建议优先看"；把"业务代码都不超阈值"解读成"结构目前还拎得清"。
- 没有 `context` 就正常通用报告。

---

## 简版健康分（仅供感知，不是 KPI）

从 100 分起扣（数据取自 `summary` counts）：
- 每个 `error`（🔴）：**-6**
- 每个 `warning`（⚠️）：**-2**
- 下限 0。
- `info`（ℹ️，含 🔥 热点 + 测试/样式/数据大文件）**不计分**——热点是优先级提示、非生产代码是正常偏长，都不该拖累"生产健康"感知。

报告顶部一行展示，并**明确标注**"仅供快速感知，不是考核指标；行动项才是主角"。

---

## 报告模板

```markdown
# 项目健康体检 · <YYYY-MM-DD>

**Project Health: <score>/100**  （仅供感知，非 KPI）
🔴 严重 <n>   ⚠️ 提醒 <m>   ℹ️ 信息 <i>   🔥 热点 <k>

---

## 🔴 严重（<n>）
- `<path>:<line>` — <一句影响> — 建议：<动作>
...
（无则写：✅ 无——已检查，全部通过）

## ⚠️ 提醒（<m>）
- `<path>:<line>` — <一句影响> — 建议：<动作>
...
（无则写：✅ 无——已检查，全部通过）

## ℹ️ 信息 · 非生产代码（<i>，仅提示，不计分）
- `<path>:<line>` `[测试|样式|数据]` — <一句>
...
（无则省略本节）

## 🔥 危险热点（<k>）
- `<path>`（近半年改 N 次 / M 行）— 技术债高发区，建议优先关注
...
（非 git 仓则整节写：跳过（非 git 仓库））

## 看着吓人其实没事（已抑制）
- `<path>` — <reason>（抑制到期 <date>）
...
（无则省略本节）

## 扫描范围（让"查过没问题"看得见）
- ✅ 已扫 <X> 个源文件（C1 大文件 / C4 热点）、<Y> 篇文档（C2 断链 / C3 超长）—— **明确列出来，是为了让你知道每一项都查了**：某类没发现 ≠ 没查。
- 忽略：默认规则 + .project-healthignore（有/无）
- 跳过：<如 非 git 仓，C4 跳过 / 无 package.json，命令检查跳过>
```

**不注水**：全部检查无 🔴/⚠️ 时，标题下写一句"未发现实质问题"，各节写 **"✅ 无——已检查，全部通过"**（**别只写"无"**——小白会以为"没查"而不是"查了没事"）。绝不为凑数造发现，绝不建议大重写。

---

## 语气（读 config `level`）

| level | 怎么说 |
|-------|--------|
| 缺省（中间档） | 简明；每条带一句影响 + 建议 |
| `expert` | 更短；只 `file:line` + 建议，不解释为什么 |
| `beginner` | 每条多一句"为什么这是问题"，并在建议里点明标准做法 |
