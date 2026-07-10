# Stage 1 · audit（精简版 v1）— 实现 Spec

> 状态：待审
> 日期：2026-07-10
> 上位：`blueprint.md`（§六 检查维度、§八 报告规范）
> 定位：project-health 套件的第一块、可独立发布的最小可用体检器。**精简版先落地**，能真跑、能出报告、能挂到新项目和 GiftBook 上用。

---

## 一、目标与范围

**一句话**：一个**只读**扫描器，零配置就能跑，跨语言，扫出 3-4 类最要命的工程健康问题，出一份可点击定位的报告。

**精简版 v1 只做这 4 项检查**（蓝图 §六 里 `[核]` 的高价值子集）：

| # | 检查 | 侧 | 成本 | 本版必做 |
|---|---|---|---|---|
| C1 | 超大源文件 | 代码 | 确定性 | ✅ 必做 |
| C2 | 断链（文档里的路径 + 命令引用失效） | 文档 | 确定性 | ✅ 必做 |
| C3 | 超大文档 | 文档 | 确定性 | ✅ 必做 |
| C4 | 危险热点（大文件 × 高频改动） | 代码 | 确定性 | ✅ 做 |

**设计约束**（继承蓝图原则）：
- 只读，绝不改用户代码/文档。
- 零配置可跑：读 `.project-health/config.yml`，**读不到就用内置默认**。
- 跨语言：不依赖任何语言专用工具链。
- 确定性优先：全部用数行数 / 查路径存在 / git 历史，不靠 AI 猜。
- 不注水：每条发现 file:line；宁可"未发现实质问题"也不凑数。

---

## 二、本版明确不做（推迟，但留插座）

| 推迟项 | 去哪 | 为什么 |
|---|---|---|
| 配置侧检查 C1（skill/agent 配置健康） | 完整 Stage 1 | 精简版先聚焦代码+文档 |
| 结构烟雾（单文件目录/目录过载）、注释死代码、硬编码密钥 | 完整 Stage 1 | 价值次一档，先不铺 |
| 领域包 `[领]`（分层/骨架判断） | Stage 3 | 需领域识别 |
| baseline 快照 | 完整 Stage 1 / watch | 精简版先只出报告 |
| 四维健康分（Code/Docs/Config/Drift 细分） | 完整 Stage 1 | 精简版给**简版总分 + 分组计数**即可 |
| suppressions 的**写入** | fix / setup | 精简版只**读取并尊重**已存在的 suppressions |

> 插座：config 读取、ignore 读取、报告里"看着吓人其实没事"节，本版都留好，接得上后续。

---

## 三、扫描范围与忽略

**默认忽略**（内置，硬编码）：
```
node_modules/ dist/ build/ target/ .venv/ venv/ __pycache__/
.git/ .idea/ .vscode/ out/ bin/ obj/ coverage/ .next/ .nuxt/
*.min.js *.lock 以及常见二进制/图片/字体扩展名
```
**用户扩展**：若根目录存在 `.project-healthignore`（仿 .gitignore 语法），叠加其规则。
**领域默认忽略**：本版不做（领域包在 Stage 3）。

---

## 四、检查项详规

### C1 · 超大源文件
- **对象**：所有未被忽略的**源码文件**（非 .md、非二进制）。判定"源码"用扩展名白名单（`.java .py .js .ts .jsx .tsx .vue .go .rs .c .cc .cpp .h .hpp .cs .php .rb .kt .swift .scala .m .mm .wxml .wxss .css .scss .sql .sh` …，白名单存 `references/code-rules.md`，可扩展）。
- **怎么扫**：对每个对象数**非空行**行数。
- **阈值**（config `thresholds.file_warn/file_error`，默认 **⚠️400 / 🔴800**）。
- **输出**：`file:行数`（如 `gift-book-backend/.../GiftRecordService.java:1103`），给严重度 + 一句影响 + 建议（如"考虑按职责拆分"）。
- **防误报**：走完整忽略；生成文件（`.pb.go`、`*_pb2.py`、`*.generated.*`）默认忽略。

### C2 · 断链（头号价值）
- **扫描哪些文档**：根目录 `CLAUDE.md`、`AGENTS.md`、`README.md`，以及 `docs/**/*.md`。
- **提取两类引用**：
  1. **路径引用**（保守提取，宁漏勿错——误报最伤信任）：
     - Markdown 链接 `[..](target)` 中 target 为**本地相对路径**（排除 `http(s)://`、`#anchor`、`mailto:`）。
     - 反引号包裹且**明确像仓库路径**的 token：以 `./`、`../` 开头，或以已知顶层目录开头（`src/ docs/ app/ gift-book-backend/ gift-book-agent/ GiftBook_v2/ …`，清单可配），且含扩展名或以 `/` 结尾。
     - **不提取**：纯文件名无路径（如正文里的 `service.py`，歧义太大）、代码示例里明显是伪路径的。
  2. **命令引用**（仅当项目有可识别 manifest 时才查，否则跳过该子项）：
     - `npm/pnpm/yarn run <script>` → 比对 `package.json` 的 `scripts`。
     - 本版命令检查**只做 npm 系**；mvn/gradle/make 等推迟到完整 Stage 1。
- **判定**：路径相对**仓库根**（和相对文档所在目录都试一次）解析，`test -e` 不存在 → 🔴。命令 script 不在 `scripts` → 🔴。
- **输出**：`文档:行号 → 引用的目标`，标"指向不存在的路径/命令"。

### C3 · 超大文档
- **对象**：`docs/**/*.md` + 根目录 `CLAUDE.md/AGENTS.md/README.md`。
- **怎么扫**：数行数。
- **阈值**（config `thresholds.doc_warn`，默认 **⚠️500**）。
- **输出**：`文档:行数`，建议"拆分/压缩，或把过时段落归档"（呼应蓝图 §十 压缩归档，动手归 fix）。

### C4 · 危险热点（含，可最后做）
- **前提**：是 git 仓库；否则整项跳过（不报错）。
- **怎么扫**：
  - 取近 **6 个月** `git log --stat`，统计每文件改动次数 → 最常改 top-N。
  - 取最大文件 top-N（复用 C1 的行数）。
  - **交集** = 又大又常改 → ⚠️ 热点。
- **输出**：`file`（改动 N 次 / M 行），标"技术债高发区，改动频繁又大，优先关注"。

---

## 五、config 读取与默认值

启动先找 `.project-health/config.yml`：
```yaml
thresholds: { file_warn: 400, file_error: 800, doc_warn: 500 }
level: expert            # 影响报告语气；缺省=中间档
suppressions:            # 只读取并尊重（本版不写）
  - id: "large-file:<path>"
    reason: "..."
    expires: "YYYY-MM-DD"
```
- 读不到文件 / 读不到某字段 → 用**内置默认**（阈值同上，level=中间档，suppressions=空）。
- **suppressions 生效**：命中 `id` 的发现，**默认不报**，改列进报告底部"看着吓人其实没事"节；`expires` 已过 → 照常报，并注"抑制已到期"。
  - `id` 约定：`<check>:<path>`，如 `large-file:gift-book-backend/.../GiftRecordService.java`。

---

## 六、报告规范

**落盘** `.project-health/reports/audit-YYYY-MM-DD.md`（路径可 config 改）+ 内联给用户。

**模板**：
```
# 项目健康体检 · YYYY-MM-DD

Project Health: <简版总分>/100
  🔴 严重 N   ⚠️ 提醒 M   ✅ 通过项若干

## 🔴 严重
- [path:line](path#Lline) — <一句影响> — 建议：<动作>

## ⚠️ 提醒
- ...

## 看着吓人其实没事（已抑制）
- [path] — <reason>（到期 YYYY-MM-DD）

## 扫描范围
- 已扫 X 个源文件 / Y 篇文档；忽略规则：默认 + .project-healthignore(有/无)
- 跳过项：<如 非 git 仓，C4 跳过>
```

**简版总分**（本版够用，不搞四维）：从 100 起扣——每个 🔴 扣较多、每个 ⚠️ 扣较少（具体权重写进 `references/report-format.md`，可调）。**明确标注"仅供快速感知，不是 KPI，行动项才是主角"**。

**语气**（读 config `level`）：
- 中间档（默认）：简明 + 每条带一句影响。
- 专家：更短，只 file:line + 动作。
- 小白：多一句"为什么这是问题"。

**不注水**：无问题就写"未发现实质问题"，不凑数、不推荐大重写。

---

## 七、skill 文件结构（渐进式披露）

```
audit/
  SKILL.md                 ← 薄入口：触发词 + 4 步流程 + 指向 references
  references/
    code-rules.md          ← C1 源码扩展名白名单/阈值/生成文件规则；C4 热点算法
    doc-rules.md           ← C2 引用提取规则+保守清单；C3 阈值
    report-format.md       ← 报告模板 + 简版总分权重 + 语气档
```

**SKILL.md 入口逻辑（4 步，只写骨架，细节在 references）**：
```
1. 载入范围：读默认忽略 + .project-healthignore；读 .project-health/config.yml（无则默认）
2. 跑检查：C1/C3（数行数）→ C2（提引用查存在）→ C4（git 热点，非 git 则跳过）
   —— 具体规则见 references/code-rules.md、doc-rules.md
3. 应用 suppressions：命中的移入"看着吓人其实没事"
4. 组装报告：按 references/report-format.md → 落盘 + 内联
```

**触发词**（SKILL.md frontmatter description）：`检查项目健康 / 项目状态怎么样 / 审计代码库 / project health / audit`。

---

## 八、执行方式

本版**Claude 驱动**：SKILL.md 指导 Claude 用 shell 单行命令 + Glob/Grep 完成扫描（数行数、`test -e`、`git log --stat`）。具体命令写进 references。
- **已知局限**：超大仓库上 Claude 驱动会偏慢/耗 token。
- **插座**：完整 Stage 1 可加一个 `scripts/scan.*` helper 把确定性扫描脚本化（像 cartographer 的 scan-codebase.py），SKILL.md 调脚本拿结构化结果——本版先不做，但报告/规则设计不阻碍将来接入。

---

## 九、验收标准

**GiftBook（存量）跑一次，应至少：**
- C1：把 `GiftRecordService.java`（~1100 行）报为 🔴；列出其它超 300 行文件。
- C2：扫 CLAUDE.md/AGENTS.md/docs，报出任何指向不存在路径的引用（若有）。
- C3：列出 docs 下 >500 行的 .md（若有）。
- C4：给出"大×高改"热点（若是 git 仓）。
- 报告结构完整、每条可点击、有总分、有"扫描范围"节。

**空/新项目跑一次，应：**
- **全绿不误报**（没有源文件就没有 C1；没有超标文档就没有 C3；断链为 0）。
- 报告明确写"未发现实质问题"。

**误报红线**：C2 路径提取**保守**，在 GiftBook 上不得把正文里的普通词误判成断链。宁可漏报，不可乱报。

---

## 十、留给后续的插座

- config 读取口子 → setup 将来写 config 即生效。
- suppressions 读取 → fix/setup 将来写入即生效。
- 报告"新增/已解决/遗留"字段 → 本版先不做，watch 接。
- `references/` 三件套 → 完整 Stage 1 往里加 C1 配置侧、结构烟雾等，不改入口。
- `scripts/` helper → 将来脚本化确定性扫描。

---

## 附：已定的取值（v1 锁定）

- 阈值默认 **⚠️400 / 🔴800（源文件）/ ⚠️500（文档）** —— 已定。理由：warn 取 400 而非 300，避免在 Java/Spring 这类啰嗦语言上狼来了；任何项目可在 config 覆盖。
- C4 危险热点：**做**。
- 简版健康分：有一个感知分即可；扣分权重在实现时写进 `references/report-format.md`，可调。
