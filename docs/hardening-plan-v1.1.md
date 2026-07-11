# project-health 加固计划（v1.1 → 产品级）

> 状态：**reviewed**（GPT 终审 sign-off + Fiona 批准）
> 日期：2026-07-11
> 上位：`blueprint.md` + GPT 深度审查 + "skill + scripts" 定调
> 定位：把 A 面从"高质量原型"加固成**跨 agent 结果一致、可复现**的 skill 套件。**仍是 skill，不做独立产品**——只给"确定性计算"的部分加 `scripts/`；判断部分照旧 markdown。

---

## 定调（贯穿全程）

1. **Agent 要思考的 → markdown；机器能稳定算的 → 脚本。**（判断用 skill，测量用 script。）
2. **仍是 skill 套件**：`scripts/` 装在各 skill 文件夹里，不另立 CLI/产品。
3. **脚本用 Python**（读文件/git/glob 自然、可读、够用）。零运行时二进制是**可选的以后**，不是现在。约束：
   - 声明 **Python 版本**（≥3.8）与**依赖**（尽量零第三方依赖，只用标准库）。
   - **运行前检查**运行时/依赖是否就绪；**不自动安装**。
   - **缺运行时不静默降级**——大声报错说清"没 Python 跑不了确定性扫描"，**绝不偷偷回落成 AI 即兴**（那会破坏一致性）。
4. **做小**：一个 phase 一验一提交；每步能独立跑通。
5. **跨平台目标**：脚本写仔细（换行/路径/编码），让 Claude、Codex、Cursor 调同一脚本 → 底层 findings **一致**（措辞可不同）。

---

## Phase 1 · 确定性扫描脚本（地基，最高优先）

**契约先行**，拆成 1A / 1B：

### Phase 1A · 定 schema 契约 + 最小 fixture（先做）
- 定 **finding schema**（结果数据契约）：每条 `{id, check, subject, fingerprint, severity, evidence}`；`config.yml` 最小契约（含 `schema_version`）；`state/latest-run.yml` 格式。
- 建**最小 fixture**（一个小项目 + 期望输出 `expected/*.yml`），作 scanner 的靶子。
- 产物：契约文档 + `tests/fixtures/min/` + `tests/expected/`。

### Phase 1B · 写 `audit/scripts/scan.py`（对着契约实现）
C1–C4 扫描 → 结构化 findings（YAML），满足 1A 契约：
- **细粒度 finding**（治"折叠"）：断链带 `target`（一文档多断链**不折叠**）；大文件带**行数**；严重度可比、可追"升级"。
- **准确性（都在脚本里做对）**：
  - **C2 按 markdown 语义解析路径**：相对链接→文档目录；`/abs`→根；`../` 严格；反引号顶层→根；跳过 fenced + inline 代码。
  - **C4 绝对阈值+评分**：`行数≥file_warn AND 近N天改动≥churn_min` 才是候选，`size×churn` 排序；top-N 只限报告数量。
  - **大文件输出"986 行"**，不是 `path:986`。
  - **分类只认固定机械证据**：**扩展名 / 路径模式 / 文件名模式**（`*.test.*`、`__mocks__/`、`.css`…）。**不读"文件头自述"那种模糊证据**（脚本要确定性）。认不准 → 按生产代码。
- **suppression 在脚本里应用**（不在 markdown）：读 config `suppressions`，命中的确定性移出/标记。
- **config**：读 `schema_version` + 阈值/level；缺字段回落默认。
- **机器状态 vs 人看报告分开**：结构化 → `state/latest-run.yml`；报告 md 文件名带**时间戳+commit** `reports/audit-<ts>-<sha>.md`（治同日覆盖）。
- **skill 改造**：`audit/SKILL.md` 改成"**调 scan.py 拿结构化结果 → 解读 → 出报告**"；markdown 只留：何时调、读 context、说人话、语气/level。

**验收**：
- **canonical findings 一致**——同代码跑两次、不同 agent 跑，**结构化 findings 相同**（报告措辞可不同）。
- 脚本结果匹配最小 fixture 的 `expected/*.yml`。

---

## Phase 2 · 增量对比脚本

**`watch/scripts/compare.py`** —— 读 `state/baseline.yml` + `state/latest-run.yml` → 输出 `new / resolved / remaining / **escalated**(⚠️→🔴) / de-escalated`。

- `baseline.yml` 由 audit 首跑/用户确认写（YAML，非 md）。
- `watch/SKILL.md` 改成调它 + 解读。

**验收**：文件 450→900 行报 `escalated`；多断链改好一个报 `resolved` 不再整篇"遗留"。

---

## Phase 3 · fix 安全加固（拆：判断=markdown / 机械=helper 脚本）

**判断部分（markdown，留 SKILL.md）**：人说才修、分级闸门、先方案后确认、F2a 分级（用户点名归档=🟢；**agent 自己判断"已淘汰"=🟡** 先列候选确认）、是否信任该仓库的**决策**。

**机械安全部分（`fix/scripts/`，确定性）**：
- **verify 信任闸门**：config `execution.trust: prompt|trusted|disabled` + `approved_verify` 白名单；setup 探测的 verify 只是**候选**、非批准；陌生仓库/首次执行前确认（自动跑构建=跑任意代码）。
- **rollback 精确**：改前记录本次 **touched files（含未跟踪）**；失败只还原本次；**不盲目 `git restore .` / 不用 `git clean -fd`**。
- **基线本来失败**：脚本记录失败集，确认后允许，只要**本次不新增失败**。

---

## Phase 4 · setup 改进 + 自查文档漂移（dogfooding）

- **config**：加 `schema_version`；加 **`standard` 档**（`beginner|standard|expert`，别让"缺字段"当合法档）；按 lock 文件认包管理器（pnpm/yarn/bun/npm）；mvn/gradle 先查 wrapper 是否存在。
- **monorepo/workspaces 检测**：`frontend/package.json + backend/pom.xml + agent/pyproject.toml` → 各 workspace 独立 domain/verify。
- **doc-drift 降噪**：config 支持 `doc_links` 显式映射；无映射再用启发式且**降低置信度**。
- **修我们自己的漂移**（正好验"能查自己"）：
  - spec 状态词表：`draft / reviewed / implemented / fixture-validated / field-validated / released`——A 面四个 spec 改成 `implemented + field-validated`，别再写"待审"。
  - setup 里别再说 watch 是 "future"。
  - blueprint 健康分注明"v1 简版总分 / 未来四维"。
  - `project_rules` 与 `constitution` 对齐（单一真源）。

---

## Phase 5 · B 面（design skill）+ 可执行宪法

- **宪法 schema 升级**（这是 A/B 桥真通的前提）：拆 **severity（多重要）** 与 **enforcement（能不能自动查）**；每条含
  `id / scope / module / applies_to(globs) / statement / severity / enforcement.kind / status / rationale / schema_version`。
  - `enforcement.kind` ∈ `max_file_lines / required_path / forbidden_path / forbidden_dependency / allowed_dependency / required_file_pair / naming_pattern / manual_review`。
- **`architecture.yml`（可选，确认后写）**：`modules{id, paths, responsibility, excludes, public_interfaces, depends_on}`——让项目级设计**不蒸发**。（**注**：由它**自动审计"实现偏离设计"是较难的判断**，v1 先只**记录结构**；能确定性查的只有映射到 `enforcement.kind` 的那几条，别夸大"自动查架构漂移"。）
- **领域包 = 决策框架**（不是目录树）：关键决策 / 易失控边界 / 反模式 / 依赖方向 / 横切能力 / **可执行规则模板** / 权威引用。v1 前端，v1.1 DL。
- **建 `project-health-design` skill**（按 B 面 spec，但用升级后的宪法 schema）。

---

## Phase 6 · A/B 桥真通

- `audit/scripts/scan.py` **读 `constitution.yml`**：对 `enforcement` 可执行的规则（forbidden_dependency / max_file_lines…）**确定性检查**；`manual_review` 只在设计/人工审查时提示；未知 kind 不执行并说明。`severity` 决定 🔴/⚠️。
- 先只打通**少数几个** rule kind，就足以证明闭环：
  `design → architecture.yml(现状) + constitution.yml(规矩) → audit 查偏离 → fix 修 → watch 看漂移`。

---

## Phase 7 · 跨 agent 回归 + 平台验收（产品级）

> 各 phase **自带 fixture/测试**；Phase 7 只做**总回归 + 平台验收**。

- **总回归 golden test**（`tests/fixtures/` + `expected/*.yml`）：多断链不折叠 / 严重度升级 / 同日不覆盖 / dirty tree 不误伤 / 基线本失败能比较 / 陌生仓库 verify 不擅自跑 / monorepo 各自检测 / suppression 到期重现 / 宪法 manual 不自动报红 / 宪法 enforceable 能稳定查。（**rename/moved 检测本版砍掉**，太复杂、留后续。）
- **平台工具映射**：各 agent（Claude/Codex/…）怎么调脚本、路径/shell 差异的适配。
- **"Agent 确实调了脚本"验收**：确认 skill **真去调 `scan.py`**，而不是绕过它自己即兴（否则一致性白搭）。
- **eval**：Claude vs Codex 同 fixture → **canonical findings 一致**（"从 skill 升级成协议"的分界线）。
- **（可选）** scan 编译二进制，零运行时。

---

## 优先级 / 建议顺序

```
Phase 1（扫描脚本=地基）  ← 先做，最高杠杆
  → Phase 2（对比脚本）
  → Phase 3（fix 安全）
  → Phase 4（setup + 自查漂移）
  → Phase 5（B 面 + 可执行宪法）
  → Phase 6（桥真通）
  → Phase 7（跨 agent 回归 / 产品化）
```
**一个 phase 一验一提交。** Phase 1 做完,"跨 agent 结果一致"这个你最在意的地基就立住了。

---

## 附：已定（GPT 终审 sign-off + Fiona 批准 → reviewed）

- **语言 Python**（含版本≥3.8 / 依赖声明 / 运行前检查 / 不自动装 / 缺运行时不静默降级）。✅
- **顺序**：Phase **1A（schema 契约 + 最小 fixture）先做，再 1B（scanner）**。✅
- **GPT 6 项修订已并入**：测试分散各 phase、suppression 入脚本、config 前移 P1、"canonical findings 一致"、P3 拆判断/机械、P7 加平台映射 +"确实调脚本"验收；砍 rename、收紧 architecture 自动审计口径、分类只认固定机械证据。✅
