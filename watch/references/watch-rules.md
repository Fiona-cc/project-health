# watch-rules.md — 基线来源 / 增量比对 / 文档漂移 / 报告模板

> Stage 4。watch **只读**：跑一次 audit，和基线比，只报增量。复用 audit 的检查引擎与 id 约定。

---

## 一、基线（baseline）来源与优先级

按顺序取第一个：
1. **`.project-health/baseline.md`** —— 显式基线（用户"接受现状"时存的），最稳。
2. **`.project-health/reports/audit-*.md`** 里**最近一次**报告 —— 没有显式基线就用它当参照。
3. **都没有 → 第一次运行**：先跑一次 audit，把结果**摘成基线**并提示用户"要不要存成 `baseline.md`"。存了下次就有参照。

**更新基线**：用户说"接受现状 / 重置基线" → 把当前 audit 结果写成新的 `baseline.md`（旧的可覆盖）。

**基线里存什么**：每条发现的 **id + 类型 + 严重度**（足够比对即可，不必存全文）。

---

## 二、增量比对（按发现的稳定 id）

- 发现 id = `<check>:<repo相对路径>`（与 audit/suppressions 同一套）。
  - `<check>` ∈ `large-file` / `broken-ref` / `oversized-doc` / `hotspot` …
- 跑一次**新 audit** → 当前发现集合 `NOW`；基线集合 `BASE`。
- 分三类：
  - **🆕 新增** = `NOW ∖ BASE`（当前有、基线没有）→ 重点报，带 file:line + 建议。
  - **✅ 已解决** = `BASE ∖ NOW`（基线有、当前没有）→ 报喜。
  - **🟰 遗留** = `NOW ∩ BASE`（两边都有）→ **只给数量**，不重复展开细节。
- **尊重 suppressions**：命中 suppression 的项，不算"新增"（并入"看着吓人其实没事"，不打扰）。

---

## 三、文档漂移检测（"文档守护"的检测半边）

- 读 git：最近 **N 天（默认 14）** 改动过的**代码文件**（源码白名单，排除忽略项）。
  示例：`git log --since="14 days ago" --name-only --pretty=format: -- .`
- 对这些代码，找**相关文档**：
  - 同目录 / 同模块下的 `*.md`；或根 `CLAUDE.md` / `README.md` / `AGENTS.md`。
- 比时间：若相关文档的最后改动**明显早于**这些代码 → 判为"可能滞后"。
  （用 git 最后提交时间比对；拿不准就不报，宁漏勿扰。）
- **只提示、不改**：列出"这些代码近期改了、对应文档没跟上,建议看一眼"。改文档是 `project-health-fix` 的活。

> 主动"每次操作后自动弹提醒"那种 → 需 Claude Code **hook**，本版不做（见 SKILL.md 说明）。

---

## 四、报告模板

内联 + 落盘 `.project-health/reports/watch-YYYY-MM-DD.md`。

```markdown
# 项目健康监控 · <YYYY-MM-DD>（对比基线 <基线日期/来源>）

## 🆕 新增问题（<n>）  ← 重点
- `<path>:<line>` [<类型>] — <一句影响> — 建议：<动作>
（无则写：自基线以来无新增问题）

## ✅ 已解决（<m>）
- `<path>` [<类型>]
（无则省略）

## 🟰 遗留（<k>，未重复展开）
- 仍有 <k> 项在册，详见基线/上次 audit 报告。

## 📄 文档可能滞后（<j>）
- `<doc>` — 相关代码 `<code>` 近 <days> 天改过、文档未更新，建议看一眼
（无则省略）

## 说明
- 基线：<来源与日期>
- 忽略/跳过：<同 audit：默认忽略 + .project-healthignore；非 git 仓则文档漂移/热点跳过>
```

**不注水**：没有新增就明说"自基线以来无新增问题"，不凑数。

---

## 五、边界

- **只读**，绝不改代码/文档。
- 非 git 仓：文档漂移检测跳过（并注明）。
- watch **不替代** audit：首次全量体检仍走 `project-health-audit`；watch 专管"之后只看变化"。
