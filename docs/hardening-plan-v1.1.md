# project-health 加固计划（v1.1 → 产品级）

> 状态：待审
> 日期：2026-07-11
> 上位：`blueprint.md` + GPT 深度审查 + "skill + scripts" 定调
> 定位：把 A 面从"高质量原型"加固成**跨 agent 结果一致、可复现**的 skill 套件。**仍是 skill，不做独立产品**——只给"确定性计算"的部分加 `scripts/`；判断部分照旧 markdown。

---

## 定调（贯穿全程）

1. **Agent 要思考的 → markdown；机器能稳定算的 → 脚本。**（判断用 skill，测量用 script。）
2. **仍是 skill 套件**：`scripts/` 装在各 skill 文件夹里，不另立 CLI/产品。
3. **脚本用 Python**（读文件/git/glob 自然、可读、够用）。零运行时二进制是**可选的以后**，不是现在。
4. **做小**：一个 phase 一验一提交；每步能独立跑通。
5. **跨平台目标**：脚本写仔细（换行/路径/编码），让 Claude、Codex、Cursor 调同一脚本 → 底层 findings **一致**（措辞可不同）。

---

## Phase 1 · 确定性扫描脚本（地基，最高优先）

**`audit/scripts/scan.py`** —— C1–C4 扫描 → 输出**结构化 findings（YAML）**。一步到位把这些做进去：

- **细粒度 finding**（治"折叠"）：每条 `{id, check, subject, fingerprint, severity, evidence}`。
  - 断链带 `target`（一篇文档多个断链**不折叠**）；大文件带**行数**；严重度可比较。
  - id 稳定到能区分同一文件的不同问题、能追踪"严重度升级"。
- **顺手做对准确性**（这些本就在脚本里）：
  - **C2 按 markdown 语义解析路径**：相对链接→文档目录；`/abs`→仓库根；`../` 严格；反引号顶层路径→根；跳过 fenced + inline 代码。
  - **C4 绝对阈值 + 评分**：`行数≥file_warn AND 近N天改动≥churn_min` 才是候选，再 `size×churn` 评分排序；top-N 只限报告数量，不决定是不是问题。
  - **大文件输出"986 行"**，不是 `path:986`（避免误解成第 986 行）。
  - **分类用证据**（文件头自述/扩展名/明确路径），不凭目录名。
- **机器状态与人看报告分开**：
  - 结构化结果 → `.project-health/state/latest-run.yml`。
  - 人看报告仍 markdown，**文件名带时间戳+commit**：`reports/audit-<ts>-<sha>.md`（治同日覆盖）。
- **config**：读 `schema_version`；缺字段回落默认。
- **skill 改造**：`audit/SKILL.md` 从"教 AI 自己拼命令扫"改成"**调 scan.py 拿结构化结果 → 解读 → 出报告**"。markdown 只留：何时调、读 `context`、说人话、语气/level、suppressions 处理。

**验收**：同一份代码跑两次，findings 逐字节相同；脚本结果与人工核对一致。

---

## Phase 2 · 增量对比脚本

**`watch/scripts/compare.py`** —— 读 `state/baseline.yml` + `state/latest-run.yml` → 输出 `new / resolved / remaining / **escalated**(⚠️→🔴) / de-escalated`。

- `baseline.yml` 由 audit 首跑/用户确认写（YAML，非 md）。
- `watch/SKILL.md` 改成调它 + 解读。

**验收**：文件 450→900 行报 `escalated`；多断链改好一个报 `resolved` 不再整篇"遗留"。

---

## Phase 3 · fix 安全加固（markdown）

- **verify 信任闸门**：config `execution.trust: prompt|trusted|disabled` + `approved_verify` 白名单；setup 探测到的 verify 只是**候选**、非批准；**陌生仓库/首次执行前先确认**（自动跑构建=跑任意代码，有风险）。
- **rollback 精确**：改前记录本次 **touched files（含未跟踪）**；失败只还原本次；**不盲目 `git restore .` / 不用 `git clean -fd`**；（临时 worktree 可选）。
- **基线本来就失败**：不一刀切禁止（否则治不了最该治的存量项目）→ 记录失败集，确认后允许，只要**本次不新增失败**。
- **F2a 分级**：用户点名归档=🟢；**agent 自己判断"已淘汰"=🟡**（先列候选确认）。

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
- **`architecture.yml`（可选，确认后写）**：`modules{id, paths, responsibility, excludes, public_interfaces, depends_on}`——让项目级设计**不蒸发**，也让 audit 能查"实现偏没偏离设计"。
- **领域包 = 决策框架**（不是目录树）：关键决策 / 易失控边界 / 反模式 / 依赖方向 / 横切能力 / **可执行规则模板** / 权威引用。v1 前端，v1.1 DL。
- **建 `project-health-design` skill**（按 B 面 spec，但用升级后的宪法 schema）。

---

## Phase 6 · A/B 桥真通

- `audit/scripts/scan.py` **读 `constitution.yml`**：对 `enforcement` 可执行的规则（forbidden_dependency / max_file_lines…）**确定性检查**；`manual_review` 只在设计/人工审查时提示；未知 kind 不执行并说明。`severity` 决定 🔴/⚠️。
- 先只打通**少数几个** rule kind，就足以证明闭环：
  `design → architecture.yml(现状) + constitution.yml(规矩) → audit 查偏离 → fix 修 → watch 看漂移`。

---

## Phase 7 · 产品级回归（跨 agent 一致）

- **`tests/fixtures/` + `tests/expected/*.yml` golden test**，关键回归：多断链不折叠 / 严重度升级 / 同日不覆盖 / dirty tree 不误伤 / 基线本失败能比较 / 陌生仓库 verify 不擅自跑 / 文件重命名识别为移动 / monorepo 各自检测 / suppression 到期重现 / 宪法 manual 不自动报红 / 宪法 enforceable 能稳定查。
- **eval**：Claude vs Codex 同 fixture → **findings 一致**（这是"从 skill 升级成协议"的分界线）。
- **（可选）** 把 scan 编译成二进制，零运行时依赖、极致可移植。

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

## 附：待你拍板

1. **脚本语言 Python**（装进 skill 的 `scripts/`），可以吗?
2. **顺序**：Phase 1 先做(扫描脚本),对吗?
3. 这份清单**有没有漏 / 有没有想砍**的?(它已经把 GPT 那份审查的可用建议全收进来了。)
