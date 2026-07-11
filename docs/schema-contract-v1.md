# 数据契约 v1（finding / config / state）—— Phase 1A

> 状态：**reviewed**（GPT + Fiona）
> 日期：2026-07-11
> 用途：`scan.py` 产出、`compare.py` 消费、watch 据此对比、suppression 据此匹配的**统一数据格式**。
> 这是"跨 agent 结果一致"的**根**：任何 agent 调脚本，都产出这个格式。

---

## 一、单条 finding

```yaml
- id: "C2|broken-ref|README.md|docs/setup.md"   # 稳定身份：跨运行不变；watch 对比 + suppression 匹配都用它；不含行号
  check: C2                     # C1 | C2 | C3 | C4 （未来 CON=宪法）
  kind: broken-ref              # large-file | broken-ref | broken-command | oversized-doc | hotspot
  subject: "README.md"          # 这条"关于哪个文件"
  severity: warning             # error(🔴) | warning(⚠️) | info(ℹ️)
  category: null                # 仅 C1 有值(production|test|style|data)；其余恒为 null（顶层形状统一）
  fingerprint: "sha256:…"       # 当前证据的指纹：证据变了它就变 → 用来识别 evidence_changed；不用于身份对比
  evidence:
    target: "docs/setup.md"
    locations:                  # 同一(doc,target)的所有出现位置聚合在一条里
      - line: 42
      - line: 88
  message_key: broken_local_reference   # 机器键；skill 按 level/语言渲染成人话（机器状态不放人类措辞）
```

**核心分工**：
- **`id` = 稳定身份**。watch 靠它判"新增/已解决/遗留"，suppression 靠它匹配。**不含行号**（文档插一行不该变身份）。
- **`fingerprint` = 证据指纹**。证据变了(行数、位置)才变，只用来识别 `evidence_changed`。

---

## 二、每种检查的 stable id 规则（治"折叠" + 稳定）

| 检查 | kind | id | 说明 |
|---|---|---|---|
| 超大文件 | large-file | `C1\|large-file\|<path>` | 每文件一条 |
| 断链·路径 | broken-ref | `C2\|broken-ref\|<doc>\|<归一化target>` | **每(doc,target)一条**；多处出现聚合进 `locations` |
| 断链·命令 | broken-command | `C2\|broken-command\|<doc>\|<script>` | |
| 超大文档 | oversized-doc | `C3\|oversized-doc\|<path>` | |
| 危险热点 | hotspot | `C4\|hotspot\|<path>` | |
| （未来）宪法 | constitution | `CON\|<rule_id>\|<subject>` | |

- **id 不含行号**；行号进 `evidence.locations`。**同(doc,同target)多处 = 一条**（不同 target 仍是不同 finding，仍解决"一文档多断链被折叠"）。
- **归一化 target**：`./setup.md` 按文档目录解析成 `docs/setup.md` 再进 id。

---

## 三、fingerprint（证据指纹，识别 evidence_changed）

- = 把该 finding 的**当前证据**（大文件行数 / 断链 locations / 热点 churn·size…）做 canonical 序列化后取 `sha256`。
- 证据变（450→900 行、位置增减）→ fingerprint 变 → watch 报 `evidence_changed`。
- **它不参与身份对比**（那是 `id` 的活）。

---

## 四、latest-run（机器状态；YAML）

```yaml
schema_version: 1
run:
  id: "20260711T140230Z-8e5077f"   # 时间戳 + 短 commit（报告文件名同款，治同日覆盖）
  timestamp: "2026-07-11T14:02:30Z"
  commit: "8e5077f"
  tool_version: "0.2.0"
scan:
  files_scanned: 186
  docs_scanned: 8
  git: true
  skipped_checks:
    - check: C4
      reason: not_git_repository
summary:                      # Phase 1 只出 counts；score 留报告层（§八）
  error: 2
  warning: 3
  info: 1
findings: [ … ]               # 真正参与报告 / 对比 /（将来）评分
suppressed_findings: [ … ]    # 本次扫到但被 config 抑制的（同 finding 结构）
expired_suppressions: [ … ]   # 过期/失效的 suppression（其对应 finding 照常进 findings）
```
- **`compare.py` 只读 `findings`**（消歧义：被抑制的不在 findings 里，不参与 new/remaining）。
- **`baseline.yml`** = 某次 run 的快照（findings + summary），**用户确认后写**。

---

## 五、watch 怎么对比（按 `id`）

- id 集合 `NOW` vs `BASE`：`new = NOW∖BASE`；`resolved = BASE∖NOW`；`remaining = 交集`。
- `remaining` 里再比 `severity` → `escalated`/`de-escalated`；比 `fingerprint` → `evidence_changed`。
- suppression 按 `id` 精确匹配。

---

## 六、config.yml 契约（scan.py 读什么）

```yaml
schema_version: 1
domain: [frontend]
stack: [react, vite]
level: standard          # beginner | standard | expert（别让"缺字段"当合法档）
goal: long-term
context: ""
thresholds:
  file_warn: 400
  file_error: 800
  doc_warn: 500
  churn_days: 180        # C4 看近几天
  churn_min: 3           # C4 改动次数下限
verify: "npm run build"
execution:
  trust: prompt          # prompt | trusted | disabled
  approved_verify: []
suppressions:
  - id: "C1|large-file|src/Big.js"   # = finding 的 stable id
    reason: "已评估暂不拆"
    expires: "2026-09-01"
doc_links: []            # 代码→文档 显式映射（Phase 4）
constitution:
  path: ".project-health/constitution.yml"   # project_rules 收敛到这
```
- **缺字段一律回落内置默认**。

---

## 七、CLI + 运行时 + 规范化（跨平台一致的心脏）

**调用**：
```bash
python audit/scripts/scan.py --root <项目根> [--config <path>] [--output <state-path>] [--format yaml|json]
```
- **`commit` 由脚本自取**（`git rev-parse --short HEAD`；非 git → `null`），**不由 agent 传入**（否则 Claude 传了/Codex 忘传，状态就不一致）。
- scanner **只产状态、不生成报告**，故无 `--no-report`。

**运行时**：Python **≥3.8** + **PyYAML**（读/写 YAML）。运行前 `import yaml` 检查；**缺则明确提示安装、不自动 pip install、不静默降级**（不自己手写 YAML parser——那是新 bug 源）。

**路径归一化**（机器状态里所有路径）：**仓库相对 · 正斜杠 `/` · 无开头 `./` · 无绝对路径**。Windows 也必须输出 `src/App.ts`，不能 `src\App.ts`。

**findings 排序**（固定，消除不同文件系统遍历差异）：`check → kind → subject → id`。

**退出码**：`0=扫描成功(含发现健康问题) | 2=配置错误 | 3=Python/依赖不足 | 4=root 无效 | 5=内部失败`。**发现 🔴 问题不返回非零**（否则 agent 会把"发现问题"误解成"脚本崩了"）。

**写入**：先写临时文件再**原子替换** `latest-run.yml`；写失败明确报错。**scanner 只产状态；markdown 报告由 skill 按状态生成**（机器计算 vs 人类表达，边界最干净）。

---

## 八、score 暂不进脚本

- Phase 1 scanner **只输出 `summary` counts**，不算 score。
- score（扣分公式、C4 是否计、suppression/info 是否参与）属**报告层**，等和现有报告规则对齐后再加。

---

## 九、Phase 1A 下一步

契约（本文件）定了 → 造**最小 fixture**（`tests/fixtures/min/` 一个小项目 + `tests/expected/min.yml` 期望 findings）→ 作为 1B `scan.py` 的靶子。

---

## 附：本版已按 GPT + Fiona 敲定（5 大 + 4 小）

1. **`id`=稳定身份 / `fingerprint`=证据指纹**；suppression 匹配 `id`。
2. **声明 PyYAML**，解决 YAML 与标准库冲突。
3. **`findings / suppressed_findings / expired_suppressions` 三分**；删掉每条 finding 的 `suppressed` 字段。
4. **同(doc,target)多处聚合**进一条的 `locations`。
5. **补 CLI / 路径归一化 / 排序 / 退出码 / 原子写**。
6. `message` → `message_key`；`category` 恒存（null）；`score` 移到报告层（先出 counts）；`skipped` 结构化。
