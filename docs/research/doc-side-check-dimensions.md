# 文档侧检查维度研究（研究快照）

> 来源：研读 5 个高赞文档/AI-上下文 lint 与标准（YawLabs/ctxlint、mattschaller/agent-context-lint、agent-sh/agnix、agentsmd/agents.md、netresearch/agent-rules-skill）
> 日期：2026-07-10
> 用途：喂给 audit 的 `references/doc-rules.md` 与 `config-rules.md`（通用内核 `[核]` 层）。蓝图 §六 文档侧/配置侧清单即从此提纯。
> 说明：原料快照，非最终规则。Stage 1 只挑跨工具、通用、高信号、可脚本化的少数几项。

---

## 一、逐仓分析

### 1. YawLabs/ctxlint（npm @yawlabs/ctxlint，零依赖）
**4 组检查**：
- **上下文文件**：stale-file-ref(断路径,error)、stale-command(命令与 package.json/Makefile/Cargo/go.mod/pyproject 不符,error)、staleness(代码改后上下文没更新,warn)、token-budget/信噪比(如"38% 信号 62% 噪声")、redundancy/redundant-readme(可推断内容+与 README trigram 重复)、no-inferable-stack、no-directory-tree(硬编码目录树,error)、max-lines(>200,warn)、no-style-guide、contradictions、frontmatter、ci-coverage、content-secrets(内联密钥,error)、hook-coverage(死 hook)
- **MCP 配置**（--mcp）：mcp-schema/security/commands/deprecated(SSE)/env/urls/consistency/redundancy
- **会话/跨项目**（--session）：missing-secret、diverged-file、missing-workflow、stale-memory、duplicate-memory、loop-detection、memory-index-overflow(MEMORY.md 超 200 行/25KB)
- **Skill**（--skills）：skill-frontmatter、skill-broken-ref、skill-trigger-collision、skill-orphaned、skill-dead-tool-restriction
**输出**：文本/JSON/SARIF；--watch 重扫；--fix 用 git 历史修断路径。

### 2. mattschaller/agent-context-lint（npm，含 GitHub Action）
**9 规则两层**：
- 仓库状态：check:paths(断路径,error)、check:scripts(npm 脚本不存在,error)、check:imports(相对导入不解析,error)、check:commands(shell 命令不存在,warn)
- 语义质量：check:token-budget(warn 2000/error 5000)、check:vague("遵循最佳实践/小心/用好判断力",warn)、check:required-sections(缺 Setup/Testing/Build,warn)、check:stale-dates(年份>2 年旧,warn)、check:contradictions("总是用 X"+"从不用 X",warn)
**输出**：逐文件行号+严重度+**0-100 质量分**。

### 3. agent-sh/agnix（Rust，~416/432 条规则，40+ 类）
**按前缀分类**：CC-SK-*(Skills)、CC-HK-*(Hooks)、CC-AG-*(Agents)、CC-MEM-*(CLAUDE.md：无效路径/循环导入/深导入>5/泛化指令/token 数/README 重复/关键内容排序/弱约束语言)、CC-PL-*(Plugins)、AGM-*(AGENTS.md：合法 md/缺节/字符上限/缺项目上下文/平台守卫/嵌套层级)、XP-*(跨平台：通用配置里的平台特性/跨文件命令冲突/跨文件约束冲突/多层无优先级说明/字节上限)、CUR/COP/MCP/PE-*(关键内容排序/CoT/冗余指令/只否定无肯定)/REF-*(导入文件不存在/断链/重复导入/非 md 导入)/XML/VER/…
**输出**：CLI(--strict)+LSP(内联诊断/code action/hover)；20+ 规则可自动修；`.agnix.toml` 配严重度。

### 4. agentsmd/agents.md（标准，非 linter）
定义 AGENTS.md = 给 AI coding agent 的 README。**无必填字段/无 schema**。monorepo"就近文件优先"。推荐内容：构建/测试命令、架构与关键目录、编码约定、测试指南、要避免的坑、术语表。
**结构立场（强"薄根"）**："保持短——每行都花 token，短而具体胜过详尽"；AGENTS.md 是真源，工具特定文件(CLAUDE.md/.cursorrules)应引用而非复制。
**v1.1 提案**：渐进式披露（薄根+分层/scoped 文件）、链接深度文档(TYPESCRIPT.md/TESTING.md)、**记录能力而非文件路径**（路径会过时）、反模式（臃肿根/类别过多/模糊指令/机器生成填充）。

### 5. netresearch/agent-rules-skill（生成器，编码结构规则）
自动检测项目类型(go.mod/composer.json/package.json/pyproject)→生成**薄根 AGENTS.md(~30 行)**+**scoped 文件**(backend/frontend/…)+从 Makefile/package.json 抽命令+**幂等更新**(保留结构刷新内容)+受管头部(时间戳)。验证脚本：validate-structure.sh / check-freshness.sh / verify-commands.sh。
**结构立场（强"薄根+scoped"）**：根 ~30 行只放全局默认；scoped 文件放在语义边界（责任转移/契约要紧处），不是每个目录。

---

## 二、提纯催化单：DOC-SIDE CHECK DIMENSIONS（去重）

标注：`确`=确定性可脚本，`判`=需 AI 读判断，`半`=半确定。**加粗**=蓝图 Stage 1 `[核]` 选中项。

### I. 断链引用
- **断文件/目录路径** — ctxlint/agent-context-lint/agnix — 确(test -e)
- **断脚本/命令引用**（命令不在 package.json/Makefile/go.mod） — 三者 — 确
- 断导入路径 — 确
- **断 skill 路径引用** — ctxlint — 确
- **skill 触发词撞车** — ctxlint — 确
- **孤儿 skill 目录**（无 SKILL.md） — ctxlint — 确
- **死工具限制**（列了不存在的工具） — ctxlint — 确
- 死 hook 引用 — 确
- 重复 @import / 非 md @import — 确

### II. 过时与漂移
- **上下文在代码变更后未更新** — ctxlint — 确(比 git 日期)
- 陈旧 memory 条目(引用已删路径) — 确
- 跨兄弟仓 canonical 配置漂移 — 确
- 缺 workflow / 缺 secret — 确
- **陈旧日期/年份引用(>N 年)** — agent-context-lint — 确
- 文档与代码漂移(命令不匹配构建系统) — netresearch — 确

### III. 模糊与矛盾
- **模糊指令("遵循最佳实践")** — agent-context-lint/agnix — 半(规则库)
- **矛盾指令("总是"+"从不")** — ctxlint/agent-context-lint — 半
- 只否定无肯定("别做 X"无"改做 Y") — agnix — 半
- 泛化/冗余指令(agent 已知) — agnix — 半
- 跨文件命令冲突 / 约束冲突 — agnix — 半
- 多层无优先级说明 — agnix — 半

### IV. token 臃肿与冗余
- **token 预算超标(warn 2K/error 5K)** — 三者 — 确(计 token)
- **文件行数超标** — ctxlint(200 行) — 确(wc -l)
- 字节上限(AGENTS.md >32KiB) — agnix — 确
- README 重复(trigram) — ctxlint/agnix — 半
- 可推断栈信息("我们用 React"而 package.json 已有) — ctxlint — 确
- 硬编码目录树 — ctxlint — 确
- 散文式风格指南(该在 eslint/prettier) — ctxlint — 半
- 信噪比 — ctxlint — 确
- 重复 memory(>60% 行重叠) — ctxlint — 确

### V. 结构与分层
- **缺必需节(Setup/Testing/Build)** — agent-context-lint/agnix — 确(标题正则)
- 缺项目上下文节 — agnix — 确
- 无效 md 结构(断标题/未闭合代码块) — agnix — 确
- 无效 YAML frontmatter — ctxlint/agnix — 确
- 嵌套 AGENTS.md 无层级说明 — agnix — 确
- 缺版本 pin — agnix — 确
- 平台特性无守卫 / 硬编码平台路径 — agnix — 确/半
- **关键内容埋在中间** — agnix — 半
- 弱约束语言("should"/"prefer") — agnix — 半
- 循环导入链 / 深导入>5 — agnix — 确(图)
- memory 索引溢出(MEMORY.md >200 行/25KB) — ctxlint — 确

### VI. 安全与误配置
- 内联密钥 — ctxlint/agnix — 半(有误报风险)
- MCP 硬编码密钥 / 弃用传输(SSE) / 断命令路径 / 无效 server 类型 — ctxlint/agnix — 确
- CI workflow 未记录 / secret 未提及 — ctxlint — 确
- skill 无限制 bash / agent 无效 model — agnix — 确

### VII. skill/plugin/agent 配置校验（→ 蓝图配置侧 `[核]`）
- **缺/无效 skill frontmatter** — 确
- 无效 hook 事件 / 缺 hook 命令 — 确
- 无效 agent name/description — 确
- plugin manifest 位置错 / 无效 semver — 确
- scoped 文件缺推荐节 — 确

### VIII. 生成/维护（netresearch 专属，→ 领域包/setup 参考）
薄根生成 / scoped 文件生成 / 命令自动抽取 / 幂等更新 / 受管头部 / 合规校验 — 均确定性(模板)。

---

## 三、要点
- **71 维中约 52 维确定性可脚本**，19 维需判断（模糊/矛盾/冗余语义等）。
- 头号价值：**断链（路径+命令）** 与 **过时** —— ctxlint 那篇爆款文标题即"你 74% 的 AGENTS.md 在浪费 AI 的时间"。
- 结构共识：**薄根 + 分层/scoped = 渐进式披露**；单个巨型文档 = 坏味道。这正是蓝图核心原则。
- 配置侧（VII）单独提出，对应蓝图 `references/config-rules.md`，有 `.claude/` 才查。

**来源链接**：ctxlint / agent-context-lint / agnix / agents.md / netresearch·agent-rules-skill（详见各仓 README）。
