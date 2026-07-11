# code-rules.md — 代码侧检查规则（C1 超大文件 / C4 危险热点 / 扫描范围）

> audit v1。所有检查都是确定性的。命令示例基于 shell（bash/git）；Claude 按当前平台自适应。

---

## 扫描范围与默认忽略

**默认忽略目录/文件**（硬编码，任何项目都跳过）：
```
node_modules/  dist/  build/  out/  target/  bin/  obj/  coverage/
.git/  .idea/  .vscode/  .venv/  venv/  __pycache__/  .next/  .nuxt/
.gradle/  .mvn/  vendor/  .project-health/
*.min.js  *.min.css  *.map  *.lock
二进制/资源类扩展名：.png .jpg .jpeg .gif .svg .ico .pdf .zip .jar
  .war .class .pyc .so .dll .exe .bin .woff .woff2 .ttf .eot .mp4 .mp3
```

**用户扩展**：若仓库根有 `.project-healthignore`，叠加其规则。**v1 只支持"目录名/文件名"和"精确仓库相对路径"（及其子路径）**——**暂不支持完整 gitignore 语义**（`*` 通配、`!` 否定等）；将来要真支持,再引 `pathspec` 依赖(别自己手写)。

**读取顺序**：默认忽略 → 叠加 `.project-healthignore` → 再跑各检查。

---

## config 读取（阈值 / level / suppressions）

找 `.project-health/config.yml`。存在则用其值，缺失字段回落默认：
```yaml
thresholds: { file_warn: 400, file_error: 800, doc_warn: 500 }
level: expert            # beginner | expert；缺省=中间档
suppressions:
  - id: "large-file:<repo相对路径>"
    reason: "..."
    expires: "YYYY-MM-DD"
```
- 读不到文件 → 全用默认，`suppressions` 为空。
- `suppressions` 生效见 SKILL.md 第 3 步；`id` 约定 `<check>:<repo相对路径>`，C1 的前缀为 `large-file`。

---

## C1 · 超大源文件

**对象**：未被忽略、且扩展名在**源码白名单**内的文件：
```
.java .kt .scala .groovy
.py .rb .php .go .rs .swift .m .mm .c .cc .cpp .h .hpp .cs
.js .jsx .ts .tsx .vue .svelte
.css .scss .less .sql .sh .bash
.wxml .wxss            # 小程序
```
（白名单可按项目扩展；不在白名单的一律不算"源文件"。）

**生成文件排除**（即使在白名单内也跳过）：
```
*.generated.*  *_pb2.py  *.pb.go  *_pb.js  *.g.dart  *.designer.cs
```

**度量**：数**非空行**（去掉纯空白行），避免空行灌水虚高。
示例：`grep -cve '^[[:space:]]*$' <file>`（或读取后统计非空行）。

**文件分类（需明确证据，宁可当生产代码，不乱降级）**

> **原则**：**不要仅凭目录名**（如 `/data/`、`config/`、`scripts/`、`utils/`、`common/`、`core/`、`models/`、`services/`、`lib/`）判断性质或降级。降级必须有**路径、文件名或扩展名的明确证据**。**拿不准 → 按生产代码处理**，避免漏报真正的大文件。

- **测试**（需明确证据之一）：
  - 位于 `**/test/**`、`**/tests/**`、`**/__tests__/**` 目录；或
  - 文件名匹配 `test_*`、`*_test.*`、`*.test.*`、`*.spec.*`、`*Test.<扩展>`、`*Tests.<扩展>`
- **样式**：扩展名属于 `.css .scss .less .wxss`
- **数据 / mock / fixture / seed**（需明确证据之一）：
  - 文件名含 `mock`、`fixture`、`seed`、`stub`、`sample-data`（如 `*.mock.*`、`*fixtures*`、`seed*`）；或
  - 位于 `**/__mocks__/**`、`**/fixtures/**`、`**/__fixtures__/**` 目录；或
  - 扩展名是纯数据格式（`.json .csv .tsv .yaml .yml .xml`）
  - ⚠️ **仅在 `data/` 目录下不算证据**——如 `data/giftRecords.js` 无 mock/fixture/seed 证据 → 按**生产代码**处理（照常可 🔴）。
- **生产代码**：以上都不匹配的，一律按生产代码处理。

**判级（按性质区别对待，避免"狼来了")**：
- **生产代码**：行数 ≥ `file_error`(800) → 🔴；≥ `file_warn`(400) 且 < 800 → ⚠️
- **测试 / 样式 / 数据**：行数 ≥ `file_warn`(400) → ℹ️（仅提示，**永不 🔴**，**不计入健康分**）——它们体量大有合理性，标出来供参考，但不当"病"喊
- 均未超阈值 → 计入"通过"

**输出**：报告里**按性质分组**（见 report-format.md）——
- `🔴/⚠️ 生产代码`：`<repo相对路径>:<行数>` + 一句影响（"文件过大，改动风险高"）+ 建议（"按职责拆分为多个文件/类"）
- `ℹ️ 测试/样式/数据`：`<repo相对路径>:<行数> [测试|样式|数据]` + 一句（数据类："宜移入数据库/JSON，而非堆在源码里"）

---

## C4 · 危险热点（大文件 × 高频改动）

**前提**：当前目录是 git 仓库（`git rev-parse --is-inside-work-tree` 为真）。否则**整项跳过**，并在报告"扫描范围"里注明"非 git 仓，C4 跳过"。

**步骤**：
1. **改动频次**：近 6 个月每文件被改次数。
   示例：`git log --since="6 months ago" --name-only --pretty=format: -- . | sort | uniq -c | sort -rn`
   （过滤掉已忽略路径与已删除文件。）取 top-15 → 集合 A。
2. **大文件**：复用 C1 的行数，取行数最多的 top-15（只在源码白名单内）→ 集合 B。
3. **交集** A ∩ B = 又大又常改 → ⚠️ 热点。

**输出每条**：`<repo相对路径>`（近半年改 N 次 / M 行）+ "技术债高发区：改动频繁且体量大，建议优先关注/拆分"。

> 热点不额外扣分（避免和 C1 重复计分）；它是"优先级提示"，在报告里单列一节。
