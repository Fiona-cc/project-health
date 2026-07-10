# Stage 3 · setup — 实现 Spec

> 状态：待审
> 日期：2026-07-10
> 上位：`blueprint.md`（§一 边界、§四 职责、§七 setup 问答与 config）
> 定位：**接入项目时**，先摸清背景（**猜后再问**），生成 `.project-health/config.yml`，让 audit/fix **贴合这个项目**。

---

## 一、目标与范围

**一句话**：像 superpowers 的 brainstorm 那样——**先自动检测、把结论摆给你确认/纠正**，再落成一份 `config.yml`；顺便给新项目一点"该怎么搭结构"的建议。

**setup v1 做这些**：
1. **检测**（从 manifest 自动认）：领域/技术栈、合理默认阈值、verify 命令、现有文档结构。
2. **提问**（检测不出来的才问）：水平（小白/专家）、目标（MVP/长线）、特殊偏好。
3. **猜后再问**：把"检测 + 建议"的完整画像摆出来 → 你确认/改。
4. **生成** `.project-health/config.yml`（audit/fix 都读它）。
5. **新项目**：额外给一句"理想结构建议"（**通用级**，不铺文件）。

---

## 二、本版明确不做（推迟，但留插座）

| 推迟项 | 去哪 | 为什么 |
|---|---|---|
| **深度领域包**（各领域"官方级"理想骨架，来自桶③工程结构研究） | 后续 | 需要专门研究每个领域；v1 先"检测领域 + 通用结构建议"，把 `references/domains/` 空插槽留好 |
| **脚手架**（真去铺文件/建目录） | 独立能力 | 蓝图 §一 已划出核心之外 |
| 团队协作规则、CI 接入等 | 后续 | 先把单人/config 这条主线跑通 |

> 插座：`domain` 字段已写进 config、`references/domains/` 目录预留 → 将来深度领域包直接接上，不返工。

---

## 三、核心原则

1. **猜后再问**：能自动检测的绝不让用户从零描述；只把"猜的结果"摆出来让 ta 点头/改。
2. **像 brainstorm**：主动提示用户**可能没想到的点**（如"你是 MVP 快迭代还是长线？这会影响阈值松紧"），让 ta 确认。
3. **不铺文件**：只**生成 config** + 给结构**建议**；不创建/改动项目源码结构（那是脚手架，另说）。
4. **一次问清、别车轮战**：检测完，把需要确认的集中成**一小组问题**，不要一个个无限追问。
5. **config 是唯一产物**：setup 只写 `.project-health/config.yml`（必要时新建目录），不碰别的。

---

## 四、开场检测（能认的都自动认）

| 检测什么 | 怎么认 |
|---|---|
| 领域 / 技术栈 | `package.json`(react/vue/angular…) → 前端；`requirements.txt`/`pyproject.toml`(torch/tensorflow → DL，fastapi/django → 后端)；`pom.xml`/`build.gradle` → Java；`go.mod` → Go |
| verify 命令 | `package.json` 有 `build`/`typecheck` → 取之；`pom.xml` → mvn compile；等等 |
| 现有文档结构 | 有没有薄根 `CLAUDE.md`/`AGENTS.md`/`README.md`；`docs/` 分层还是一坨 |
| 默认阈值起点 | 通用默认 400/800/500（再按"目标"微调，见下） |

检测不准/多领域并存（如前端+后端+Agent）→ 摆出来问一句让用户确认。

---

## 五、提问（只问检测不出来的）

集中成一小组：
- **水平**：小白 / 专家？（影响报告语气与详略）
- **目标**：MVP 快迭代 / 长线产品？（影响阈值松紧建议：MVP 可略松，长线略严）
- **特殊偏好**：要不要调阈值？有没有"某文件故意很大、别报"（→ 直接进 suppressions）？

---

## 六、config 完整 schema（setup 是它的唯一写入者，本处定稿）

```yaml
# .project-health/config.yml —— 由 project-health-setup 生成
domain: [frontend]          # 检测+确认，可多个
stack: [react, vite]        # 检测到的技术栈（信息用）
level: expert               # beginner | expert —— 影响报告语气/详略
goal: long-term             # mvp | long-term —— 影响阈值松紧
thresholds:
  file_warn: 400
  file_error: 800
  doc_warn: 500
verify: "npm run build"     # fix 改代码后的兜底命令（检测得到就填）
doc_maintenance:
  prompt_after_ops: false   # 操作后是否主动提醒维护文档（Stage 4 用）
project_rules: []           # 项目专属硬规则（预留）
suppressions: []            # "看着吓人其实没事" 的沉淀（id + reason + expires）
```
- audit 读 `thresholds`/`level`/`suppressions`；fix 读 `verify`/`suppressions`；Stage 4 读 `doc_maintenance`。
- 缺字段一律回落内置默认（保证 audit/fix 不依赖 setup 也能跑）。

---

## 七、新项目结构建议（通用级，不铺文件）

- 若项目近乎空 + 已认出领域 → 给一句**通用**结构建议：
  - 前端："一般分 `components/ pages(或routes)/ services/ hooks/ store/`，别把逻辑全塞进页面组件。"
  - DL："一般分 `data/ models/ training/ eval/ configs/`，别全塞 `train.py`。"
  - 后端(Java)："controller → service → repository 分层，别跨层直连。"
- **只给建议、不建目录**。深度/权威版留给后续领域包。

---

## 八、skill 结构

```
setup/
  SKILL.md            ← 薄入口：检测 → 摆结论问确认 → 写 config（+新项目给建议）
  references/
    setup-rules.md    ← 检测细则 + 提问清单 + config schema + 结构建议话术
  （references/domains/ 空插槽，留给后续深度领域包）
```

---

## 九、验收标准（在一次性测试项目上验，不碰真实项目）

- 造 fixture：一个含 `package.json`(react) + 一个 `build` 脚本 的临时目录。
- 跑 setup：应**检测出** domain=frontend、verify=`npm run build`；就 level/goal 提问；**生成 `.project-health/config.yml`**。
- **闭环验证**：把 config 的 `file_warn` 改成一个小值 → 跑 audit → 确认 audit **真读了这个 config**（按新阈值报）。
- 验完删 fixture。
- （可选）之后可在 SmartMarketing_demo 上真跑一次 setup，给它生成一份正式 config——那是有用产物，你要就做。

---

## 十、留给后续的插座

- `domain` 字段 + `references/domains/` → 深度领域包直接接。
- `doc_maintenance` → Stage 4 watch/文档守护读。
- `project_rules` → 项目专属硬规则将来接 audit 的 `[专]` 层。

---

## 附：待你拍板

1. **领域包范围**：v1 只"**检测领域 + 通用结构建议**"，**不做深度领域包**（留插座、后续用桶③研究填）。够吗？
2. **提问方式**：检测→摆完整画像→你一次确认/改 + 只问 level/goal/偏好这一小组。可以吗？
3. **验收**：一次性 fixture 验（不碰真项目）；之后可选在 SmartMarketing_demo 上真生成一份 config。同意吗？
