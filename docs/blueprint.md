# Project-Health 套件 — 完整蓝图（Vision / Blueprint）

> 状态：蓝图定稿中（v2）
> 日期：2026-07-10
> 定位：这是**俯视图**。只画整体形态与各部分边界，具体实现细节留给每个 Stage 各自的 spec。
> 本文取代旧版 `2026-07-10-project-health-design.md`（已移入 `archive/`）。

---

## 一、解决什么问题、给谁用

**病**：AI 辅助开发有三个天然坏习惯——不清死代码、堆臃肿结构、文档轰炸。人往往到"改不动了"才发现项目已经烂掉。

**药**：project-health 是给项目做**定期体检 + 长期养护**的一套 skill。它盯三件事：
1. 代码不堆砌（文件别太大、结构别乱、别留定时炸弹）
2. 文档能分层读（薄根入口 + 渐进式披露，别糊成一坨）
3. 改代码文档要跟上（别让文档和代码越走越远）

**受众（两类，别混）**：
- **执行者 = Claude（AI）**：读 SKILL.md 决定怎么扫、怎么修。所以 SKILL.md 写入口逻辑，规则细节沉到 `references/`。
- **报告读者 = 人**：化验单要能点击定位（file:line）、分级、能行动。

**双重野心**：先**通用**（任何项目直接可用），再通过 setup 问答**长出贴合具体项目的定制规则**——支持直接用，也支持贴近自己业务优化。

**边界（本次升级）**：project-health 有**两大面**（见下节）。目前 **A 面（养护已有）** 和 **B 面（从零建好）** 均已建成初版（design + frontend/DL domain packs + constitution v2）。无论哪面都**只出建议/配置，不亲自铺业务文件**——真正"铺文件"的脚手架仍作为可选的独立能力另立（见 §十一）。

---

## 一·五、两大面：A 医生（养护已有） + B 建筑师（从零建好）

> 本节是本套件的**顶层框架**（后补，故编号 一·五）。它把原来"一个套件 + 四个 stage"重新看清：**那其实只画了 A 面。**

**同一个目标（工程可维护），两副面孔：**

| | **A 面 · 医生**（养护已有） | **B 面 · 建筑师**（从零建好） |
|---|---|---|
| 对象 | 已有代码/文档的项目 | 即将开始的项目 / 即将做的模块 |
| 干嘛 | 体检 → 找病 → 修 → 长期盯 | 动工前想清楚：模块边界、全局关切、内部治理 vs 对外接口 |
| 性质 | 确定性、扫描、可测量 | 判断、设计、前瞻 |
| 组成 | audit / fix / watch / setup | **设计顾问**（一个可缩放 skill）+ 领域包 + 宪法 |
| 状态 | ✅ 已完成 | ✅ Claude Skill 初版可用（frontend + DL 领域包） |

**四条核心认知：**

1. **A 与 B 是一个循环，不是两件独立任务**：
   `B 搭好 → 用着用着长大/走样 → A 体检修 → 又加新功能(B) → 再养护(A) …` —— 所以它们**必须同一套件**。
2. **B 面是"分形"的**：同一套"工程脑子"，缩放到**项目**或**模块**都适用（大工程有大框架，每个模块也该有小框架）。故 B 面 = **一个可缩放的"设计顾问"skill**，对准哪个尺度就在哪个尺度帮你——不拆成两个。
3. **宪法（Constitution）= 连接两面的桥**（借鉴 Spec-Kit）：一份**机器可读的短文件**，写项目**不可谈判的工程规矩**（文件别超 N 行 / 模块不跨层直连 / 配置归全局 / 业务模块边界清晰…）。
   - **B 面照它设计，A 面照它检查**（audit 查"违没违宪"——正是我们推迟的 `[专]/[领]` 结构检查）。
   - 它就是 **`.project-health/constitution.yml`**（独立文件；config 里 `project_rules` 已收敛到此，单一真源）。
4. **知识用 hybrid 策略**：领域包写"**薄原则 + 指向权威深读**"（cookiecutter / 框架官方），**不抄整本书、也不硬绑别人的 skill**（用户不一定装了，断了就废；可"推荐搭配"但须能独立跑）。B 面真正深的价值是**通用工程原则**（跨领域），领域相关的只是薄骨架——所以"覆盖不全 / 只学皮毛"的担心，被"深处通用、浅处引用"化解。

**命名（甲案，暂定）**：套件名 `project-health` 暂不动（已发布、A 面名副其实）。**将来 B 面落地时，再决定要不要把套件名从"健康"扩成"工程可维护性"**（健康只是其中 A 面）。现在纠结改名属过早优化。

---

## 二、核心设计原则

1. **渐进式披露**：入口 skill 薄，知识沉到 references，用到才加载。套件本身不许变成"文档轰炸"。
2. **确定性优先**：能用脚本（数行数 / grep / git / 查路径存在）确定性扫的，就别让 AI 猜——便宜、稳、不瞎报。判断性检查只留给真需要"读懂再说"的。
3. **通用内核 + 可插拔**：跨语言跨领域的通病做进内核；领域相关的做成可插拔的领域包。
4. **领域约定要"软"**：通用通病可以硬报警（🔴）；领域骨架/分层约定是主观的，只能软建议（⚠️）、且一键可关/可覆盖，绝不和专家对着干。
5. **猜后再问**：了解项目背景时，先自动检测再摆给用户确认/纠正，而不是让用户从零描述。
6. **报告不注水**：每条发现必须 file:line；禁止"总体来看代码写得不错"这种废话；必须有"看着吓人其实没事"一节；宁可说"没发现实质问题"也不凑数。
7. **归档而非堆积**：过时的详细记录压缩成一句话归档，而不是无限堆在活文档里。

---

## 三、三层架构

代码侧和文档侧的检查，按"多通用"分成三层，从内到外逐层叠加：

```
① 通用内核（不挑语言、不挑领域）
     文件太大 / 单文件目录 / 大文件×高频改动的热点 /
     文档断链 / 超大文档 / 入口未分层 / 文档过时 / skill 配置健康
     —— 任何项目、零配置就能跑。Stage 1 就做这一层。

② 领域包（可插拔的"理想骨架 + 分层规矩"）
     前端包 / 深度学习包 / Spring 后端包 ……
     每个是一份 references/domains/<domain>.md，
     只有 audit 认出（或 setup 确认）是该领域时才加载。
     只出软建议（⚠️），可覆盖。

③ 项目专属配置（setup 生成，存 .project-health/config.yml —— 工具中立，不绑 Claude）
     自定义阈值 + 本项目特有的硬规则（如"某某必须成对出现"）+
     小白/专家 + 领域 + 目标等背景设定 + suppressions（见 §八）。
```

**关键解耦**：audit 启动先找 config，读不到就用内置默认——所以 audit **不依赖 setup 就能独立跑**。setup 只负责生成 config 和领域识别。

---

## 四、套件结构与五个子 skill 职责

成品是一个**套件**（和 superpowers 同构：多个各管一摊的子 skill）。**当前实现 = 五个独立子 skill 文件夹，各自带 `references/`（audit/watch 另含 `scripts/`），没有根 SKILL.md**；未来可选再加一个根路由 SKILL.md。

```
project-health/                 ← 仓库（= 套件源）
  audit/  SKILL.md + references/ + scripts/scan.py
  fix/    SKILL.md + references/
  setup/  SKILL.md + references/
  watch/  SKILL.md + references/ + scripts/compare.py
  design/ SKILL.md + references/ + domains/
  docs/                         ← 蓝图 + 各 stage spec + research
  tests/                        ← 金测（fixtures + golden.py）
  README.md
```

**安装（推荐·也是实际做法）**：把各子目录装成**独立** skill 文件夹——
`~/.claude/skills/project-health-audit / -fix / -setup / -watch / -design`。

**领域包 `domains/`** 已有 **frontend（精装）+ deep-learning（薄包）+ _template**，属 **B 面**。

**生成物（落在被检项目里，工具中立、不绑 Claude）**：
```
<被检项目>/
  .project-health/
    config.yml                  ← setup 生成：背景/阈值/verify/context/suppressions（完整 schema 见 §七）
    state/baseline.yml          ← 基线快照（watch 首跑、用户确认后写）
    reports/audit-YYYY-MM-DD.md ← 每次体检报告
    reports/watch-YYYY-MM-DD.md ← 每次监控报告
  .project-healthignore         ← 显式忽略清单（§八），根目录，仿 .gitignore
```

| 子 skill | 触发例 | 干啥 | 读写 |
|---|---|---|---|
| audit | "检查项目健康""项目状态怎么样" | 只读扫描 → 出化验单（含健康分） | 只读 |
| fix | "修第 3 项""压缩一下旧版本记录" | 按报告编号逐项修，每项独立 commit，修完重跑 audit | 读写 |
| setup | "接入项目健康监控""给项目做工程配置" | 猜+问背景 → 写 config；给结构建议但不铺文件 | 读写 |
| watch | "看看最近一个月新增了哪些问题" | 对比基线 → 标记 新增/已解决/遗留 + 文档漂移检测 | 不碰你的代码/文档；写自己的 watch 报告；`baseline.yml` 仅用户确认才写 |
| design | "帮我设计这个模块的工程结构" / "生成工程宪法" | 设计顾问：项目/模块 尺度 + 7 条通用原则 + 领域包 + 宪法 | 只出建议 + 确认后才写 `constitution.yml`；不铺文件 |

**领域包**是横切在五个子 skill 之上的一条线：setup 认领域、design 用领域包引导设计、audit 用领域骨架判断、fix 按领域骨架修。

---

## 五、流程线：生命周期

四个子 skill 不是散的，它们组成一条养护生命周期（和 superpowers「brainstorm→写→测」同理）。分两种入口：

```
🟢 新项目（空的）：
   setup                →  （开发中）           →  audit     →  fix   →  watch
   摸清背景+生成config      文档守护在旁边            定期体检       修        持续盯
   +给"理想结构建议"        该记文档时主动提醒(§十)
   （不亲自铺文件）

🟡 存量项目（如 GiftBook）：
   setup                →  audit（首跑立基线）  →  fix   →  watch
   摸清背景+确认            体检"看病"+存 baseline    修        对比基线只报增量
```

> 脚手架（真去铺文件）是**独立能力**，不在这条线内——见 §十一。

| 阶段 | 对应 superpowers | 说明 |
|---|---|---|
| setup | ≈ brainstorming | 先充分了解背景、把框架/配置定下来 |
| audit | ≈ 诊断 | 只读体检，出化验单 |
| fix | ≈ 写代码/TDD | 按单施工，逐项修 |
| watch | ≈ 回归检查 | 长期盯着，防复发、发现新增 |
| design | ≈ 结构设计 | 动工前想清楚架构、模块边界、工程规矩（B 面） |
| 文档守护 | ≈ hook 行为 | 贯穿开发期的横切，见 §十 |

---

## 六、检查维度全景

> 说明：以下清单是从高赞审计/lint skill 的真实检查项里（代码侧 57 维、文档侧 71 维）**筛选提纯**得来，只保留跨语言、通用、高信号的。完整来源见 §十三。

按"多通用"标注：`[核]`=通用内核（Stage 1 做）、`[领]`=领域包、`[专]`=项目专属配置。
按成本标注：`确`=确定性可脚本、`判`=需 AI 读判断。

**扫描范围**：内置一份默认忽略（vendor/dist/target/.venv/node_modules…），用户再用根目录 `.project-healthignore` 显式扩展（仿 .gitignore）；领域包可贡献默认忽略项——尤其 DL 项目要排除 `runs/ weights/ checkpoints/ outputs/ data/raw/`，否则扫描会很吵。

### 代码侧
| 检查 | 层 | 成本 | 说明 |
|---|---|---|---|
| 超大源文件（默认 ⚠️400 / 🔴800，排除 vendor/dist/target/.venv） | [核] | 确 | 文件一大就没人敢改 |
| 结构烟雾：单文件目录 / 目录过载 | [核] | 确 | 分了个寂寞 or 该分没分 |
| 危险热点：大文件 × 高频改动 的交集 | [核] | 确 | 技术债的藏身处，定时炸弹 |
| 注释掉的死代码块 | [核·可选] | 确 | grep 关键字 |
| 硬编码密钥 | [核·可选] | 确 | grep 常见密钥形态 |
| 理想骨架 / 分层是否被打破 | [领] | 判 | 依赖领域包给的"该长什么样" |
| 死代码/未用导出、重复逻辑、复杂度、耦合、类型安全、性能深检 | 延后 | 判/需语言工具 | Stage 1 明确不做 |

### 文档侧
| 检查 | 层 | 成本 | 说明 |
|---|---|---|---|
| 断链：文档写的文件路径/命令是假的 | [核] | 确 | **头号痛点**，含"命令 package.json 里没有" |
| 超大文档（默认 >500 行） | [核] | 确 | 该拆该压 |
| 入口未分层：有没有薄根入口，还是全糊一坨 | [核] | 确+判 | 渐进式披露 |
| 文档过时：代码近期改了，对应文档没跟 | [核] | 确 | 比 git 时间 |
| 旧版本记录堆积（该压缩归档） | [核] | 确 | 见 §十，检测归 audit、压缩归 fix |
| 模糊指令（"遵循最佳实践"这种废话）/ 冗余（复述了配置已有信息） | [核·可选] | 判/半确 | ctxlint 系列 |

### skill/agent 配置侧（有 .claude/ 才查，没有整组跳过）
| 检查 | 层 | 成本 |
|---|---|---|
| SKILL.md frontmatter 缺字段 / 引用路径断链 / 触发词撞车 / 空 skill 目录 / 无效工具限制 | [核] | 确 |

---

## 七、setup：猜后再问 + config 格式

**开场问答**（先自动检测，再**引导用户描述背景**、据此提议 level/goal）：
- 领域 / 技术栈（看 package.json、requirements.txt、pom.xml 猜）
- **引导式背景**：项目是干嘛的 / 你什么角色 / 最担心哪方面 → 归纳成一句 `context`
- 据背景提议：水平（小白 / 专家）、目标（MVP / 长线）
- 特殊偏好 / 阈值调整 / 要 suppress 的项

**产物 `.project-health/config.yml`**（工具中立；完整 schema 以 setup 的 spec 为准）：
```yaml
domain: [frontend]         # 检测+确认，可多个
stack: [react, vite]       # 检测到的技术栈（信息用）
level: expert              # beginner | expert
goal: long-term            # mvp | long-term
context: ""                # 一句话背景（干嘛的/角色/最担心什么）——报告据此来讲
thresholds:
  file_warn: 400
  file_error: 800
  doc_warn: 500
verify: "npm run build"    # fix 改代码后的兜底命令（v1 单条）
doc_maintenance:
  prompt_after_ops: false  # 操作后主动提醒维护文档（留给 hook，未来）
constitution:
  path: ".project-health/constitution.yml"  # 工程规矩 — 单一真源（project_rules 已收敛到此）
suppressions: []           # "看着吓人其实没事"的沉淀（id + reason + expires）
```
**谁读/谁写**：**setup** 生成并维护；**audit** 读 `thresholds`/`level`/`context`/`suppressions`；**fix** 读 `verify`、可追加 `suppressions`；**watch** 读 `doc_links`（文档漂移降噪）；**design** 读 `domain`/`context`（加载领域包）。
> 忽略清单不放这里，单独用根目录 `.project-healthignore`（仿 .gitignore，见 §八）。

---

## 八、报告规范

**输出**：落一份 artifact `.project-health/reports/audit-YYYY-MM-DD.md`（路径可在 config 改），同时内联给用户看。

**健康分（仅供快速感知，不是 KPI）**：报告顶部给一个轻量分，**分维度**，让人一眼看出问题集中在哪；分数下面才是主角——行动项。
```
Project Health: 82 / 100
  代码健康 (Code)          78
  文档健康 (Docs)          65   ← 问题主要在这
  Agent 配置 (Config)      90
  维护漂移 (Maint. Drift)  72
```
> 原则：分数只作快速感知，**禁止把它当考核指标**；真正重要的是下面每条 file:line 的行动项。

**每条发现**：
- file:line 可点击定位。
- 分级 ✅ / ⚠️ / 🔴，给"影响 + 建议动作"。
- 不注水：宁可"未发现实质问题"，不凑数、不推荐大重写。

**三个长期养护机制**：
1. **suppressions（沉淀"看着吓人其实没事"）**：已评估、暂不动的项写进 config 的 `suppressions`（带 `reason` + `expires`）。audit 据此**默认不再重复报**、到期后自动再提醒——不用每次重新解释。
2. **baseline（首跑不吓人）**：存量项目第一次 audit 可生成基线快照 `.project-health/state/baseline.yml`。之后 watch **只重点报**：新增问题 / 已解决 / 遗留——让它像长期养护工具，而不是一次性吓人的审计器。
3. **`.project-healthignore`（显式扫描范围）**：根目录一个仿 .gitignore 的忽略文件，用户可扩展；领域包贡献默认忽略（DL 的 `runs/ weights/ data/…`）。

---

## 九、小白 / 专家模式

同样的检查结果，按 config 里的 `level` 决定怎么汇报：

| | 小白 | 专家 |
|---|---|---|
| 语气 | 解释为什么这是病、该长啥样、教你 | 只报事实：file:line，不啰嗦 |
| 数量 | 只报最要命的几条，别吓着 | 要全量就给全量 |
| 领域约定 | 主动建议标准骨架 | 默认闭嘴，要才说 |

audit 读不到 config 时，默认走"简明 + 只报关键项"的中间档。

---

## 十、文档演进：主动维护提醒 + 压缩归档

两个机制，专治"文档跟不上 / 文档越堆越长"：

**① 主动维护提醒（文档守护）**
- 目的：用户不一定每次都记得维护文档，让 AI 在合适时机主动问"这次改动要不要同步文档？"
- 关键：**由模型按"这次任务值不值得记"判断该不该问**，不是每次都弹。判断松紧在 setup 按项目复杂度定（`doc_maintenance.prompt_after_ops`）。
- 形态：偏 hook / 工作流的横切行为，不属于 audit（只读扫描）。放后续 Stage。

**② 压缩归档**
- 目的：项目一版又一版迭代后，旧版本的逐条 bug/修改记录已经没意义了。
- 做法：把**已被完全淘汰版本**的详细记录，压成一句话——"曾有 vX，大致功能是 Y"——移入 archive，活文档只留当前有效内容。
- 分工：**发现**"文档过长/旧记录堆积"归 audit（§六）；**动手压缩**归 fix。

---

## 十一、分阶段实现路线图

每个 Stage 只交付一小块，同时为后面留好"插座"，不逼前面返工。

| 面/阶段 | 交付 | 状态 |
|---|---|---|
| **A 面 · Stage 1** | `audit`：通用内核检查 + 健康分 + `.project-healthignore` + 读 config + 报告 + baseline | ✅ 完成·真机验证 |
| **A 面 · Stage 2** | `fix`：逐项修 + 压缩归档 + **verify 兜底（改坏自动撤）** + 写 suppressions | ✅ 完成·真机验证 |
| **A 面 · Stage 3** | `setup`：**引导式**猜+问背景 → 生成 config（含 `context`） | ✅ 完成·真机验证 |
| **A 面 · Stage 4** | `watch`：对比 baseline 报增量 + 文档漂移检测 | ✅ 完成·真机验证 |
| **A 面 · 发布** | 拆成独立 skill 文件夹 + 发布 GitHub（Fiona-cc/project-health） | ✅ 完成 |
| **B 面 · design** | `design`：可缩放"设计顾问" skill（项目/模块）+ 前端·DL **领域包** + **宪法**（= `constitution.yml`） | ✅ Claude Skill 初版可用 |
| 伴生（独立·可选） | `scaffold`：真去铺项目骨架——独立能力，不在核心 | ⬜ 可选 |

**A 面已完整交付并真机验证（含四轮 GPT 审查 + 真项目全链路）。B 面（design + 领域包 + constitution v2）初版已建。** 想大、做小：整张图画全，一块块建。

---

## 十二、验证计划

- **GiftBook（存量）**：跑 audit，预期看到 ⚠️ GiftRecordService 超大、🔴 文档若干断链/过时、"看着吓人其实没事"里列已评估项。再用 fix 修 2-3 项验证流程。
- **新项目（空的，另一个正在起步的项目）**：验证空项目跑 audit **应全绿不误报**；用 setup 摸清背景→生成 config + 给出理想结构建议；写一个月代码后跑 audit，应在第一个超限文件出现时提醒。

---

## 十三、参考来源（学到了什么）

| 类别 | 参考 | 学到的点 |
|---|---|---|
| Skill 写法 | superpowers / anthropics·skills / mattpocock·skills | 套件拆分、入口 skill、渐进式披露、brainstorm 流程 |
| 代码审计 | ksimback/tech-debt-skill | file:line 强制、"看着吓人其实没事"、git 热点交集、不注水 |
| | kingbootoshi/cartographer | 代码库地图、依赖/入口/数据流、增量更新 |
| | awesome-skills/code-review-skill | references 按需加载、20+ 领域的分层约定（领域包金矿）|
| 文档/上下文 lint | YawLabs/ctxlint | 断链/过时/token 冗余/信噪比、SARIF 输出 |
| | mattschaller/agent-context-lint | 断路径/断命令、模糊指令、过期日期、矛盾指令、0-100 打分 |
| | agent-sh/agnix | 432 条规则的分类维度（结构/安全/一致性/跨平台）|
| | agentsmd/agents.md | 薄根 + 分层、"每行都花 token"、别复述可推断信息 |
| | netresearch/agent-rules-skill | 薄根 + scoped 文件、命令自动抽取、幂等更新 |
| 领域骨架 | cookiecutter-data-science / 各框架脚手架 | 每个领域"官方盖章"的理想目录（领域包依据）|
| **B 面 / 工作流**（本轮新增） | GitHub Spec-Kit（SDD，10 万★）/ Amazon Kiro | **"宪法（Constitution）"= 机器可读的不可谈判工程规矩**（B 面照它设计、A 面照它查）；what/why 与 how 分离；审批门。SDD"新项目好用、老项目吃力"→ 正好 B 面用 SDD、A 面用审计 |
| | GSD（Get Shit Done） | 状态落盘、防上下文腐化——**我们已独立在做**（config/baseline/reports）；wave 并行/多智能体 → 对我们过度，跳过 |
| | codex-dev-loop（ralph-wiggum / OpenAI cookbook） | Review→Repair→Validate + 原子改动+失败回滚——**我们 fix 已独立做出（改坏自动撤）**，算强验证 |

> **本轮检索的最大收获有两条**：① **"宪法"概念**——它是 A↔B 的共享桥，也是 config 里 `project_rules` 空字段的真身；② 一半"值得借鉴"的做法（文件存状态、审→修→验闭环、原子改动+回滚、归档不删）**我们已独立做出**，说明设计没跑偏。**明确避开**：SDD 的"Markdown 疯魔"（堆文档没人读）、EARS、多智能体并行——守住"薄 references、不注水"。

**研究快照（已落盘，防止聊天上下文蒸发）**：
- `research/code-side-check-dimensions.md` — 桶① 代码审计（tech-debt/cartographer/code-review），57 维催化单。喂 `code-rules.md`。
- `research/doc-side-check-dimensions.md` — 桶② 文档/上下文 lint（ctxlint/agnix/…），71 维催化单。喂 `doc-rules.md` + `config-rules.md`。
- 桶③ **工程结构/脚手架研究** — 待 Stage 3 学，来源见 `桌面/工程结构skill检索.txt`。**这是"领域包 `[领]`"的原料，Stage 1 不学**。

---

## 附：待明确（留给各 Stage 的 spec）

- config 文件的完整字段与格式 → setup spec（已定稿）
- **领域包的标准模板结构 + 宪法格式 → done**（design/references/domains/；constitution v2）
- 文档守护用 hook 还是别的机制 → 未来（Stage 4 已把主动提醒留作 hook）
- 各阈值默认值的具体取值 → Stage 1 audit spec（已定 400/800/500）
