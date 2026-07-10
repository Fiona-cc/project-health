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

## 二、提问（只问检测不出来的，一次问清）

集中成一小组：
1. **水平**：小白 / 专家？→ 写 `level`。影响报告语气与详略。
2. **目标**：MVP 快迭代 / 长线产品？→ 写 `goal`。影响阈值松紧。
3. **特殊偏好**（可选）：
   - 要不要调阈值？
   - 有没有"某文件/文档故意很大、别报"？→ 直接进 `suppressions`（id + reason）。
   - 有没有该忽略的目录？→ 提示可写 `.project-healthignore`。

> 别车轮战：这一组问完就够，不要逐条无限追问。

---

## 三、goal → 阈值微调（brainstorm 式建议）

- `goal: mvp` → 建议略松：`file_warn 500 / file_error 1000 / doc_warn 600`（快迭代别老报警）。
- `goal: long-term` → 建议略严：`file_warn 400 / file_error 800 / doc_warn 500`（默认）。
- 只是**建议默认值**，用户可改。

---

## 四、config 完整 schema（本处定稿；setup 是唯一写入者）

```yaml
# .project-health/config.yml —— 由 project-health-setup 生成
domain: [frontend]          # 检测+确认，可多个
stack: [react, vite]        # 检测到的技术栈（信息用）
level: expert               # beginner | expert
goal: long-term             # mvp | long-term
thresholds:
  file_warn: 400
  file_error: 800
  doc_warn: 500
verify: "npm run build"     # fix 改代码后的兜底命令
doc_maintenance:
  prompt_after_ops: false   # Stage 4 用
project_rules: []           # 项目专属硬规则（预留）
suppressions: []            # id + reason + expires
```

- **谁读**：audit 读 `thresholds`/`level`/`suppressions`；fix 读 `verify`/`suppressions`；Stage 4 读 `doc_maintenance`。
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
