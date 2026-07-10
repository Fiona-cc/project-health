# 代码侧检查维度研究（研究快照）

> 来源：研读 3 个高赞代码审计/地图类 skill（kingbootoshi/cartographer、ksimback/tech-debt-skill、awesome-skills/code-review-skill）
> 日期：2026-07-10
> 用途：喂给 audit 的 `references/code-rules.md`（通用内核 `[核]` 层）。蓝图 §六 的代码侧清单即从此提纯。
> 说明：这是**原料快照**，不是最终规则。Stage 1 只挑其中跨语言、通用、高信号、可脚本化的少数几项。

---

## 一、逐仓分析

### 1. kingbootoshi/cartographer
**性质**：代码库**测绘/文档化**工具，不是健康审计——它映射"有什么"，不标"哪里错"。
**结构**：单 SKILL.md + 一个 `scan-codebase.py`（生成按文件 token 计数的树）。无 references 拆分。
**它映射的维度**：文件树+token 计数 / 每文件用途 / 关键导出（公共 API）/ 导入依赖 / 被依赖 / 模式与约定 / 陷阱与非显然行为 / 入口点 / 数据流（时序图）/ 模块关系（架构图）/ 导航指南（"要加个 API 改哪些文件"）/ 变更检测（git diff 增量更新）。
**输出**：`docs/CODEBASE_MAP.md`（带 frontmatter：时间戳、文件数、token 数）+ Mermaid 架构图 + 目录树 + 模块表 + 数据流时序图 + 约定 + 陷阱 + 导航。并给 CLAUDE.md 加 2-3 句摘要。
**防空泛**：token 感知给出每文件具体数字；子 agent 读真实文件；按模块结构化；git 增量更新保新鲜。
**备注**：它不是审计工具，但其测绘维度（依赖/被依赖/入口/数据流/约定）被审计工具复用。

### 2. ksimback/tech-debt-skill
**性质**：全库技术债审计，只读。此类的黄金标准。
**结构**：单 SKILL.md（约 700 行，明说可拆但保持单体）。
**9 大维度（每个含子检查）**：
1. **架构腐化**：循环依赖、分层违规、god 文件(>500 LOC)、god 函数、3+ 处重复逻辑、无用抽象、死代码（未用导出/不可达分支/注释掉的旧块）
2. **一致性腐烂**：同一件事多种做法（HTTP 客户端/错误处理/日志/配置加载/校验/日期处理）、命名漂移、目录结构与实际代码不符
3. **类型与契约债**：`any`/`unknown`/`as any`/`# type: ignore`/松散 dict；未类型化的 API 边界；信任边界缺 schema 校验
4. **测试债**：关键路径覆盖缺口；测实现而非行为；跳过/flaky 测试；高 churn 文件无测试
5. **依赖与配置债**：CVE（npm/pip/cargo audit）；未用依赖；重复依赖；环境变量散乱
6. **性能与资源卫生**：N+1 查询；异步路径里的同步阻塞；热路径阻塞 I/O；未清理的监听/句柄
7. **错误处理与可观测性**：吞异常；宽泛 catch；记了日志但没处理；错误形状不一致；关键路径缺结构化日志
8. **安全卫生**：硬编码密钥；字符串拼 SQL；信任边界缺输入校验；宽松 auth/CORS；弱加密
9. **文档漂移**：README 与现实矛盾；注释与相邻代码矛盾；公共 API 无 docstring

**按栈跑的工具**：TS/JS(`npm audit`/`knip`/`madge --circular`/`depcheck`/`tsc --noEmit`)；Python(`pip-audit`/`ruff`/`vulture`/`pydeps`/`mypy --strict`)；Rust(`cargo audit`/`udeps`/`machete`/`clippy`)；Go(`govulncheck`/`go vet`/`staticcheck`/`golangci-lint`)。
**输出**：`TECH_DEBT_AUDIT.md`——执行摘要(≤10 条,按影响排序)+架构心智模型+发现表(30-80 条:ID/类别/File:Line/严重度/工作量/描述/建议)+Top5 带 diff 草图+速赢清单+**"看着吓人其实没事"一节(必须有)**+给维护者的开放问题。
**防空泛（关键）**：① 每条 file:line —— "没引用的发现只是感觉"；② Phase 1 强制定向：先读 README/manifest/架构文档，再 `git log -200`、`git log --stat --since=6mo`、最大 20 文件 ∩ 最常改 20 文件；③ 禁止阿谀（不许"总体结构良好"）；④ **"看着吓人其实没事"一节必须有，空了说明审计浅**；⑤ 禁止推荐重写，只给具体范围内改动；⑥ 禁止凑数（"无实质问题"可接受）；⑦ 重复跑标 RESOLVED/NEW/stale；⑧ >50k LOC 分模块派子 agent。

### 3. awesome-skills/code-review-skill
**性质**：PR 级代码评审，20+ 语言，只读（指导评审，不执行）。
**结构**：渐进式披露——SKILL.md(~220 行,核心流程+严重度+索引)+`reference/`(20+ 语言指南,各 200-1100 行,按需加载)+`reference/cross-cutting/`(SQLi/XSS/N+1/错误处理/并发)+`assets/`(清单/模板)+`scripts/`(PR 复杂度分析器)。
**跨语言（语言无关）检查**：文件大小(单文件>300/函数>50/类>200)、嵌套深度>4、参数数>4、复用审计(先搜已有工具)、参数散乱、泄漏抽象、stringly-typed、嵌套条件、复制粘贴变体、no-op 更新、TOCTOU 竞态、过宽操作(全量载入只用子集)、冗余状态、SOLID 违规、架构反模式(god object/big ball of mud/spaghetti/…)、耦合内聚(CBO/Ce/Ca/LCOM4)、Clean Arch 分层违规、N+1、SQLi、XSS、错误处理、异步并发、安全(SQLi/XSS/CSRF/SSRF/IDOR/命令注入)、off-by-one、空检查、资源管理、测试质量。
**语言专属**：React/Vue/Angular/Rust/TS/Python/Java/Go/C#/C/C++/Swift/PHP/Django/FastAPI/Kotlin/Svelte… 每份 30-100+ 具体检查项，带 bad/good 例子。
**6 级严重度**：🔴blocking / 🟡important / 🟢nit / 💡suggestion / 📚learning / 🎉praise。
**4 阶段**：上下文收集 → 高层评审 → 逐行分析 → 总结决策。
**防空泛**：渐进式披露只加载所需语言指南；每项带 bad/good 例；严重度排序；PR 复杂度脚本给数据。

---

## 二、提纯催化单：CODE-SIDE CHECK DIMENSIONS（13 主题·去重）

标注：`确`=确定性可脚本，`判`=需 AI 读判断。**加粗**=蓝图 Stage 1 `[核]` 选中项。

### 主题1 文件大小与结构
- **god 文件（>300/500 LOC）** — tech-debt/code-review/cartographer — 确
- god 函数（>~50 行） — 确（需解析）
- god 类（>200/1000 行） — 确
- 类公共方法过多（>5-7） — 确
- 嵌套深度>4 — 确
- 函数参数>4 — 确

### 主题2 重复与死代码
- 重复逻辑(3+ 处) — 判（或精确匹配工具）
- 复制粘贴变体 — 判
- 未用导出/死代码 — 确(knip/vulture/madge)
- **注释掉的死代码块** — 确(grep)
- 无用抽象(单实现/零使用接口) — 确(grep+依赖图)
- 未用依赖 — 确(depcheck/udeps/machete)

### 主题3 复杂度
- 圈复杂度 — 确(linter)
- 嵌套条件≥3 — 确
- 大 switch/if-else 链 — 判
- 布尔参数标志 — 确

### 主题4 测试覆盖
- 关键路径覆盖缺口 — 确(覆盖率工具)
- 高 churn 文件无测试 — 确(git+覆盖率)
- 测实现而非行为 — 判
- 跳过/flaky 测试 — 确(grep+日志)
- 缺边界用例测试 — 判
- 测试依赖外部服务 — 判

### 主题5 Git churn 与热点
- 最常改文件(近6月 top20) — 确(git log)
- **大 ∩ 高 churn 交集（债的藏身处）** — tech-debt — 确
- 自上次以来变更模块 — 确(git --since)

### 主题6 依赖与耦合
- 循环依赖 — 确(madge/pydeps)
- 高耦合(CBO>10) — 确
- 分层违规 — 判
- 重复依赖 — 确
- CVE 依赖 — 确(audit 工具)
- 宽松 CORS/auth — 确(grep)

### 主题7 类型安全与契约
- `any`/松散类型 — 确(tsc/mypy)
- 缺输入校验 — 判
- stringly-typed — 半
- 未类型化 API 边界 — 判
- 缺类型注解 — 确

### 主题8 安全
- **硬编码密钥** — 确(grep/gitleaks)
- 字符串拼 SQL — 确
- 端点缺 auth — 判
- 弱加密 — 确
- XSS — 明显确/细微判
- CSRF/SSRF/IDOR — 判
- 不安全反序列化 — 确(grep)

### 主题9 错误处理与可观测性
- 吞异常(空 catch) — 确
- 宽泛 catch — 确
- 记日志但没处理 — 判
- 错误形状不一致 — 判
- 关键路径缺日志 — 判
- 错误路径缺清理 — 确

### 主题10 性能
- N+1 — 明显确/细微判
- 异步路径同步 I/O — 确
- no-op 更新 — 判
- 过宽读取 — 判
- 不必要序列化 — 判
- 列表无分页 — 确

### 主题11 一致性与组织
- 同事多做法 — 判
- 命名漂移 — 半
- 目录结构与代码不符 — 判
- 文件放错层 — 判（**依赖领域包 `[领]`**）
- 单实现接口 — 确

### 主题12 文档与注释
- README 与现实矛盾 — 判
- 注释与代码矛盾 — 判
- 公共 API 无 docstring — 确
- 模块缺概览文档 — 确

### 主题13 架构与设计
- 循环模块依赖 — 确
- god/big ball of mud — 判
- 泄漏抽象 — 判
- 缺扩展点(OCP) — 判
- 过度工程 — 判
- 死抽象/boat anchor — 判

---

## 三、给 audit 的关键设计模式（从三仓提炼）
1. **分阶段协议**（tech-debt）：先定向、再审计、后交付——定向防"凭感觉"。
2. **Git churn 整合**：最大文件 ∩ 最常改文件 = 债的藏身处。
3. **工具整合**：跑真实静态工具并纳入其输出（Stage 1 暂不做，等 setup 知道语言链）。
4. **渐进式披露**（code-review）：核心精简，语言/领域参考按需加载。
5. **反空泛约束**：强制 file:line、禁凑数、禁重写、"看着吓人其实没事"必填。
6. **子 agent 派发**：>50k LOC 按模块 fan-out。
7. **重复跑=活文档**：跟踪发现状态(RESOLVED/NEW/stale)。
8. **严重度+工作量**：影响与工作量双估，发现才可行动。

> 全表 57 维中约 33 维确定性可脚本、24 维需判断。Stage 1 只取"确定性 + 跨语言 + 高信号"的少数几项（见蓝图 §六）。
