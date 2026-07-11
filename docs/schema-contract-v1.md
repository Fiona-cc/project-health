# 数据契约 v1（finding / config / state）—— Phase 1A

> 状态：待审（Phase 1A 产物之一）
> 日期：2026-07-11
> 用途：`scan.py` 产出、`compare.py` 消费、watch 据此对比、suppression 据此匹配的**统一数据格式**。
> 这是"跨 agent 结果一致"的**根**：任何 agent 调脚本,都产出这个格式。

---

## 一、单条 finding

```yaml
- id: "C2/broken-ref/README.md#L42→docs/setup.md"   # 人可读、本次运行内唯一
  check: C2                     # C1 | C2 | C3 | C4 （未来 CON=宪法）
  kind: broken-ref              # large-file | broken-ref | broken-command | oversized-doc | hotspot
  subject: "README.md"          # 这条"关于哪个文件"
  fingerprint: "C2|README.md|docs/setup.md"   # 稳定身份——watch 靠它对比（见 §四）
  severity: error               # error(🔴) | warning(⚠️) | info(ℹ️)
  category: production          # 仅 C1：production | test | style | data
  evidence:                     # 各检查自己的机器可用证据
    line: 42
    target: "docs/setup.md"
  message: "文档指向不存在的路径"   # 一句机器给的提示（报告可按 level 重新措辞）
  suppressed: false             # 命中 suppression 则 true
```

**字段解释（为什么要这些）**：
- `fingerprint`：**稳定身份**。同一 finding 跨多次运行的 fingerprint 不变 → watch 能判"新增/已解决/遗留"。**它是治"折叠"和"追踪升级"的关键。**
- `id`：人看的、本次唯一（带行号/target,方便定位）。
- `severity`：直接映射报告里的 🔴/⚠️/ℹ️。
- `evidence`：机器可用的细节（断链的 target、大文件的行数…）,fix/watch 都可能用。

---

## 二、fingerprint 怎么算（每种检查不同,治"折叠"）

| 检查 | kind | fingerprint | 效果 |
|---|---|---|---|
| 超大文件 | large-file | `C1\|<path>` | 每文件一条 |
| 断链·路径 | broken-ref | `C2\|<doc>\|<归一化target>` | **一文档多断链不折叠** |
| 断链·命令 | broken-command | `C2cmd\|<doc>\|<script>` | 每命令一条 |
| 超大文档 | oversized-doc | `C3\|<path>` | 每文档一条 |
| 危险热点 | hotspot | `C4\|<path>` | 每文件一条 |
| （未来）宪法 | constitution | `CON\|<rule_id>\|<subject>` | 每规则×对象一条 |

> **归一化 target**：把 `./setup.md` 按文档目录解析成 `docs/setup.md` 再进 fingerprint,保证同一目标稳定。

---

## 三、latest-run.yml（机器状态,与人看报告分开）

```yaml
schema_version: 1
run:
  id: "20260711T140230Z-8e5077f"   # 时间戳 + 短 commit（报告文件名同款,治同日覆盖）
  timestamp: "2026-07-11T14:02:30Z"
  commit: "8e5077f"
  tool_version: "0.2.0"
scan:
  files_scanned: 186
  docs_scanned: 8
  git: true
  skipped: []                       # 如 ["C4: 非 git 仓"]
findings:
  - <上面那种 finding>
score: 96                           # 简版总分（v1）
```
- `baseline.yml` = 某次 run 的 findings 快照（同格式,标为基线；用户确认后写）。
- 人看报告仍是 `reports/audit-<run.id>.md`,措辞可随 level 变,但**数字来自这份机器状态**。

---

## 四、watch 怎么用它对比（按 fingerprint）

- 本次 `findings` 的 fingerprint 集合 `NOW`；基线 `BASE`。
- **new** = NOW∖BASE；**resolved** = BASE∖NOW；**remaining** = 交集。
- **escalated / de-escalated** = fingerprint 相同但 `severity` 变了（⚠️→🔴 / 🔴→⚠️）。
- **suppression 匹配 fingerprint**（不是模糊匹配路径）：config 里 `suppressions[].id = fingerprint`。

---

## 五、config.yml 契约（scan.py 读什么）

```yaml
schema_version: 1
domain: [frontend]
stack: [react, vite]
level: standard          # beginner | standard | expert（新增 standard,别让"缺字段"当档）
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
  - id: "C1|src/Big.js"  # = fingerprint
    reason: "已评估暂不拆"
    expires: "2026-09-01"
doc_links: []            # 代码→文档 显式映射（Phase 4）
constitution:
  path: ".project-health/constitution.yml"   # project_rules 收敛到这
```
- **缺字段一律回落内置默认**（保证不依赖 setup 也能跑）。
- **Python 约束**（见加固计划 §定调）：脚本声明 ≥3.8、只用标准库、运行前检查、缺运行时**大声报错不静默降级**。

---

## 六、Phase 1A 下一步

契约（本文件）定了 → 造**最小 fixture**（`tests/fixtures/min/` 一个小项目 + `tests/expected/min.yml` 期望 findings）→ 作为 1B `scan.py` 的靶子。

---

## 附：待你拍板

1. finding 的字段（id/check/kind/subject/fingerprint/severity/category/evidence/message/suppressed）够用/冗余吗?
2. **fingerprint 分检查算**（治折叠 + 追升级）——这个核心思路对吗?
3. **suppression 改成匹配 fingerprint**(不再模糊匹配路径),同意吗?
4. severity 用 `error/warning/info`（对应 🔴/⚠️/ℹ️）,可以吗?
