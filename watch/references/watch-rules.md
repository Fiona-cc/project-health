# watch-rules.md — 基线来源 / 增量比对 / 文档漂移 / 报告模板

> Stage 4。watch **只读**：跑一次 audit，和基线比，只报增量。复用 audit 的检查引擎与 id 约定。

---

## 一、基线（baseline）来源与优先级

按顺序取第一个：
1. **`.project-health/state/baseline.yml`** —— 显式基线（用户"接受现状"时存的），最稳。
2. **`.project-health/state/latest-run.yml`** —— 没有显式基线就用最近一次扫描状态当参照。**关键**：在跑 fresh audit **之前**，先把旧的 `latest-run.yml` 复制到临时快照（否则 fresh audit 会覆盖它 → 你在拿新结果跟新结果比 → 永远是"无变化"）。
3. **都没有 → 第一次运行**：先跑 `project-health-audit`（产出 `latest-run.yml`），**展示结果**，并**询问用户是否存成 `baseline.yml`**；**用户确认才写**，不确认就**只展示本次结果、不自动立基线**。

**更新基线**：用户说"接受现状 / 重置基线" → 把当前 `latest-run.yml` 复制为新的 `baseline.yml`。

---

## 二、增量比对（脚本确定性执行，不再手算）

**调用 `scripts/compare.py <baseline.yml> <latest-run.yml>`**——按 `finding.id`（稳定身份）比对，输出结构化 delta。

- 分类：
  - **🆕 新增（new）**：latest 有、baseline 没有
  - **✅ 已解决（resolved）**：baseline 有、latest 没有
  - **🟰 遗留（remaining）**：两边都有（只给数量，不重复展开每条细节）
  - **⬆️ 严重度升级（escalated）**：同 id，severity 升高（⚠️→🔴）
  - **⬇️ 严重度降级（de-escalated）**：同 id，severity 下降（🔴→⚠️）
  - **📝 证据变化（evidence_changed）**：同 id，fingerprint 变了
- **尊重 suppressions**：命中 suppression 的项已由 scan.py 移入 `suppressed_findings`，不在 `latest-run.yml` 的 `findings` 中，不会算进新增。

---

## 三、文档漂移检测（"文档守护"的检测半边）

- 读 git：最近 **N 天（默认 14）** 改动过的**代码文件**（源码白名单，排除忽略项）。
  示例：`git log --since="14 days ago" --name-only --pretty=format: -- .`
- 对这些代码，找**相关文档**：
  - 同目录 / 同模块下的 `*.md`；或根 `CLAUDE.md` / `README.md` / `AGENTS.md`。
- 比时间：若相关文档的最后改动**明显早于**这些代码 → 判为"**可能未同步**"（只是推断，不是定论）。
  （用 git 最后提交时间比对；拿不准就不报，宁漏勿扰。）
- **只提示、不改，且措辞要软**：列出"这些代码近期改了、对应文档**可能**没跟上，**建议看一眼**"——**不要写成"文档未更新"这种确定结论**（也许文档压根不用改、或为别的原因动过）。改文档是 `project-health-fix` 的活。

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

## 📄 文档可能未同步（<j>）
- `<doc>` — 相关代码 `<code>` 近 <days> 天改过、**文档可能未同步，建议看一眼**
（无则省略）

## 说明
- 基线：<来源与日期>
- 忽略/跳过：<同 audit：默认忽略 + .project-healthignore；非 git 仓则文档漂移/热点跳过>
```

**不注水**：没有新增就明说"自基线以来无新增问题"，不凑数。

---

## 五、边界

- **不碰你的代码/项目文档**；只写自己在 `.project-health/` 下的产物：watch 报告（每次）+ `state/baseline.yml`（**仅用户确认"接受现状/重置基线"时**才写/覆盖）。
- 非 git 仓：文档漂移检测跳过（并注明）。
- watch **不替代** audit：首次全量体检仍走 `project-health-audit`；watch 专管"之后只看变化"。
