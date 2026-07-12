# setup-rules.md — 检测细则 / 提问清单 / config schema / 结构建议

> Stage 3。setup 只写 `.project-health/config.yml`，不碰别的文件。原则：猜后再问。

---

## 一、检测（能自动认的都认）

在**仓库根**跑，按 manifest 认：

| 检测 | 依据 |
|---|---|
| **领域 / 技术栈** | `package.json` 依赖含 react/vue/@angular/svelte → **前端**；含 express/nest/koa → **Node 后端**<br>`requirements.txt`/`pyproject.toml` 含 torch/tensorflow/jax → **深度学习**；含 fastapi/django/flask → **Python 后端**<br>`pom.xml`/`build.gradle`（spring-boot）→ **Java 后端**<br>`go.mod` → **Go**；`Cargo.toml` → **Rust** |
| **verify 命令** | `package.json` `scripts` 有 `build` → `npm run build`；有 `typecheck` → 取之<br>`pom.xml` → `./mvnw -q -DskipTests compile`；`build.gradle` → `./gradlew -q compileJava`<br>Python 包 → `python -m compileall <包>` |
| **现有文档结构** | 有无薄根 `CLAUDE.md`/`AGENTS.md`/`README.md`；`docs/` 是分层还是一坨；是否已有 `.project-health/config.yml` |
| **阈值起点** | 通用默认 400/800/500（再按"目标"微调，见三） |

- **多领域并存**（如前端 + Java 后端 + Python Agent）：全列出来，让用户确认主次或全保留。
- 检测不准 → 摆出来问，别硬猜。

---

## 二、提问（先引导用户描述背景，再据此提议 level/goal）

> **关键**：普通用户**想不到该交代背景**（只有 skill 作者才会主动说清）。所以**先用带例子的引导问题帮他说出来**，别一上来就冷问干巴巴的 level/goal。

**第 1 步 · 引导式背景**（给例子，用户照着选/补即可）：
- **这项目是干嘛的？** 例：生产系统 / 原型 demo / 内部工具 / 学习练手…
- **谁在用、你是什么角色？** 例：自己 / 团队；开发 / 产品经理 / 设计…
- **你最担心它哪方面？** 例：越改越乱 / 逻辑说不清 / 太慢 / 没人看得懂 / 文档跟不上…

**第 2 步 · 据背景"猜后再问"**（不要冷问 level/goal，用背景**提议**、让用户点头）：
- 从角色/担心推 `level`：如"产品经理 / 不写代码"→ 提议 **小白**；"资深开发"→ 提议 **专家**。
- 从"是干嘛的"推 `goal`：如"原型 demo / 快迭代"→ 提议 **MVP**；"生产系统 / 长期维护"→ 提议 **长线**。
- 把提议摆出来让用户**确认/改**。

**第 3 步 · 忽略偏好**（可选）：
- 有没有"某文件/文档故意很大、别报"？→ 进 `suppressions`（id + reason）。
- 有没有该忽略的目录？→ 提示可写 `.project-healthignore`。

**第 4 步 · 归纳 `context`**：把背景**压成一句话**写进 config 的 `context`（见 §四），供 audit/watch 的报告**围绕用户在意的点来讲**。
例：`context: "PM 的前端 demo，用于审计汇报和研发沟通；数据为 mock；最担心多轮改需求后逻辑变乱、结构不清晰。"`

> 别车轮战：背景 3 问 + 确认 level/goal + 忽略，这一轮问完就够，不要逐条无限追问。

---

## 三、goal → 阈值微调（brainstorm 式建议）

- `goal: mvp` → 建议略松：`file_warn 500 / file_error 1000 / doc_warn 600`（快迭代别老报警）。
- `goal: long-term` → 建议略严：`file_warn 400 / file_error 800 / doc_warn 500`（默认）。
- 只是**建议默认值**，用户可改。

---

## 四、config 完整 schema（本处定稿；setup 是初始生成者 / 主维护者）

```yaml
# .project-health/config.yml —— 正式 schema 以 docs/schema-contract-v1.md 为唯一契约；
# 本处为示例。由 project-health-setup 生成与维护。

schema_version: 1

domain: [frontend]
stack: [react, vite]
level: standard              # beginner | standard | expert
goal: long-term              # mvp | long-term
context: ""                  # 一句话背景（干嘛的 / 角色 / 最担心什么）

thresholds:                  # audit 读取；setup 按 goal 提议、用户可调
  file_warn: 400
  file_error: 800
  doc_warn: 500
  churn_days: 180
  churn_min: 3

verify: "npm run build"      # fix 改代码后的兜底命令；v1 单条

execution:                   # fix 安全闸门
  trust: prompt              # prompt | trusted | disabled
  approved_verify: []

doc_links: []                # 代码→文档 显式映射（watch 降噪，Phase 4）

constitution:                # 工程规矩 — 单一真源
  path: ".project-health/constitution.yml"

suppressions: []             # id = finding 的 stable id，由 audit 生成
```

- **谁写/谁读**：**setup 生成并维护**；**audit 只读**（`thresholds`/`level`/`context`/`suppressions`）；**fix 可追加 `suppressions`**（也读 `verify`）；**watch 读 `doc_maintenance`**；**design 读 `domain` + `context`** 加载对应领域包。
- **`constitution.path`** 是工程规矩的单一真源（config 里不再保留 `project_rules`）。
- **缺字段回落默认**：保证 audit/fix 不依赖 setup 也能跑。正式 schema 以 `docs/schema-contract-v1.md` 为准，本文件不维护独立 schema 复本。
- **缺字段回落默认**：保证 audit/fix 不依赖 setup 也能跑。
- 只写 setup 认得的字段；不确定的字段留默认，别乱填。

---

## 五、写入规则

- `.project-health/` 目录不存在则新建。
- **已有 config**：先展示现有内容，**确认后再覆盖**；能保留的用户自定义（如手写的 suppressions）尽量保留。
- 写完提示用户：现在说 **"检查项目健康"** 就能看到 audit 按这份 config 跑。

---

## 六、新项目结构建议（通用级，只说不做）

项目近乎空 + 已认出领域 → 给一句**通用**建议（**不建目录、不铺文件**）：

| 领域 | 建议 |
|---|---|
| 前端 | 一般分 `components/ pages(或 routes)/ services/ hooks/ store/`；别把逻辑全塞进页面组件 |
| 深度学习 | 一般分 `data/ models/ training/ eval/ configs/`；别全塞 `train.py` |
| Java 后端 | `controller → service → repository` 分层；别跨层直连 |
| Node 后端 | `routes/ controllers/ services/ models/`；路由别写业务逻辑 |

> 深度 / 权威版（各领域官方级理想骨架）留给后续**领域包**（`references/domains/`），v1 只给通用建议。
