# Phase 3 · Fix 安全加固 — 实现 Spec

> 状态：待审
> 日期：2026-07-12
> 上位：`hardening-plan-v1.1.md` Phase 3
> 定位：让 Fix **遵守 execution.trust**、**不用宽泛撤销**、**允许基线本来就有失败**。不改 Fix 的修复逻辑，只补安全闸门。

---

## 一、范围

**v1 做这三件**：
1. **遵守 `execution.trust`**（disabled / prompt / trusted）+ `approved_verify`
2. **精确回滚**（只还原本次 touched files，禁止 `git restore .` / `git clean -fd`）
3. **基线本来就有失败 → 不死锁**（只判断"新增失败"，不一刀切禁止）

**本版不做**：
- 写辅助脚本（`fix/scripts/safety.py`）→ markdown 规则足够管住 Agent 行为了，将来需要再做
- 和 git worktree 整合 → 独立增强

---

## 二、execution.trust（Fix 必须读、不是摆设）

Setup 现在已经生成：
```yaml
execution:
  trust: prompt          # prompt | trusted | disabled
  approved_verify: []    # 用户明确批准过的命令
```

**Fix 的安全行为由它决定**：

### `disabled`
- **不执行任何** verify 命令 + 测试命令。
- 修改后明确说："我没跑验证；安全闸门关着，建议你手动确认项目还能正常 build/跑通。"
- 不再自动探测 build/test 命令。

### `prompt`（默认）
- 首次想跑某个 verify 命令前：**先展示具体命令 + 说明会执行项目代码 → 等用户确认 → 确认后才跑**。
- 用户批准后，可把它记进 `approved_verify`（可选，让下次不用再问）。
- **把"检测到项目有 npm build"和"用户批准跑 npm build"分开**——这两个不是一回事。

### `trusted`
- 可直接执行 `config.verify`；**自动探测出的其余命令**仍需确认或与 `approved_verify` 对照。

### `approved_verify`
- 白名单。里面的命令可以直接跑。
- Agent **不自己往白名单里加东西**——只有用户说了才算。

---

## 三、精确回滚（改坏只撤本次）

当前 Fix 规则里还有 `git restore .` → 可能误伤用户同目录下正在改的其它文件。

改为：
- **改前**：记录本次将要改的文件列表（touched files），包括未跟踪的新建文件。
- **改后验证失败（基线过→改后不过）→ 只还原这些 touched files，不碰别的**。
- **明确禁止**：`git restore .`、`git checkout -- .`、`git clean -fd`、`git reset --hard`。
- 若**无法精确判断回滚范围**（如改了一个目录级文件、不确定影响了谁）→ **停手、报告、不执行宽泛清理**。

---

## 四、基线本来就有失败 → 不死锁

当前 Fix：改前验证失败 → 全停。但存量项目可能本来就有几个失败的测试/编译警告。

改为脚本/Agent 分两档：
1. **基线全绿** → 改后必须全绿，挂一个就撤。
2. **基线本来就有失败**（记录失败集合）：改后**不得新增失败**（原失败的仍然失败 → 可以；原来没有的新失败冒出来 → 说明修坏了，撤）。

**判不了时（测试输出无法稳定比较）→ 诚实说"我无法自动判断有没有新增失败"，不装。**

---

## 五、改什么文件

只改 `fix/SKILL.md` + `fix/references/fix-rules.md`——两层：
- SKILL.md：安全原则加一条"遵守 execution.trust"、流程加信任闸门、回滚精确化措辞。
- fix-rules.md：详细的三档 trust 行为、approved_verify 规则、精确回滚细则、基线失败处理。

---

## 六、验收（不碰真项目，用一次性 fixture）

- **disabled**：设 trust=disabled，fix 修断链 → 应**不跑任何命令**，改后说明"未验证"。
- **prompt**：设 trust=prompt，fix 看到 verify 命令 → 应**先展示命令、不等用户确认就不跑**。
- **failing-baseline**：设一个本来就挂的 verify + 一个文件 → fix 改后仍只有旧失败 → 应继续(不撤)。
- **回滚精确**：改一个文件引入语法错误 → verify 失败 → 只还原该文件，不碰别的。

---

## 附：已定 + 补充（Fiona 确认）

✅ 三件范围（trust / 回滚 / 基线）—— 够，本轮不扩展。
✅ 只改 markdown —— 作为 Skill 行为契约落地，暂不写辅助脚本。
✅ 验收用一次性 fixture —— 不碰真项目。

**补充 4 条（全部落实在下文）**：
1. **disabled 不禁止只读检查**（如 re-audit、read file）——只禁止项目 **build / test / verify 等执行命令**。
2. **优先级明确**（从高到低）：`approved_verify` 白名单 > `execution.trust`（disabled / prompt / trusted）> 自动探测命令。自动探测出的命令不算"已批准"。
3. **回滚必须覆盖**：已修改文件 + 本次新建文件；**不得影响原有未跟踪文件**。
4. **基线失败只有可比较时才继续**：不可靠比较 → 标记"验证不确定"、不假装通过。
