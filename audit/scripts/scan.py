#!/usr/bin/env python3
"""project-health · scan.py — 确定性扫描核心（C1–C5 → 结构化 findings）。

契约见 docs/schema-contract-v1.md。要求 Python>=3.8 + PyYAML。
scanner 只产机器状态；人看的 markdown 报告由 skill 按状态生成。
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

for _s in (sys.stdout, sys.stderr):   # Windows 控制台常是 GBK；输出可能含中文，强制 UTF-8
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

EXIT_OK, EXIT_CONFIG, EXIT_DEPS, EXIT_ROOT, EXIT_INTERNAL = 0, 2, 3, 4, 5
TOOL_VERSION = "0.3.0"


def die(code, msg):
    sys.stderr.write(f"[project-health scan] {msg}\n")
    sys.exit(code)


if sys.version_info < (3, 8):
    die(EXIT_DEPS, f"需要 Python>=3.8，当前 {sys.version.split()[0]}。")
try:
    import yaml  # noqa
except ImportError:
    die(EXIT_DEPS, "缺少 PyYAML。请先安装：pip install pyyaml（本工具不会自动安装）。")

# ---- 常量 ----------------------------------------------------------------
IGNORE_DIRS = {
    "node_modules", "dist", "build", "out", "target", "bin", "obj", "coverage",
    ".git", ".idea", ".vscode", ".venv", "venv", "__pycache__", ".next", ".nuxt",
    ".gradle", ".mvn", "vendor", ".project-health",
}
SOURCE_EXT = {
    ".java", ".kt", ".scala", ".groovy", ".py", ".rb", ".php", ".go", ".rs",
    ".swift", ".m", ".mm", ".c", ".cc", ".cpp", ".h", ".hpp", ".cs", ".js",
    ".jsx", ".ts", ".tsx", ".vue", ".svelte", ".css", ".scss", ".less", ".sql",
    ".sh", ".bash", ".wxml", ".wxss",
}
STYLE_EXT = {".css", ".scss", ".less", ".wxss"}
GENERATED_RE = re.compile(r"(\.generated\.|_pb2\.py$|\.pb\.go$|_pb\.js$|\.g\.dart$|\.designer\.cs$)")
LEVELS = {"beginner", "standard", "expert"}
DEFAULTS = {
    "level": "standard",
    "thresholds": {"file_warn": 400, "file_error": 800, "doc_warn": 500,
                   "churn_days": 180, "churn_min": 3},
    "suppressions": [],
}


# ---- 工具 ----------------------------------------------------------------
def npath(root, abspath):
    rel = os.path.relpath(abspath, root).replace(os.sep, "/")
    return rel[2:] if rel.startswith("./") else rel


def nonempty_lines(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return sum(1 for line in f if line.strip())
    except OSError:
        return 0


def total_lines(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


def classify(rel):
    parts = rel.split("/")
    orig_name = parts[-1]
    low_parts = [p.lower() for p in parts]
    name = low_parts[-1]
    dirs = low_parts[:-1]
    ext = os.path.splitext(name)[1]
    # 测试：明确模式（避免 latest.py / contest.py 误伤，同时认 Java 驼峰 FooTest.java）
    is_test = (
        any(d in ("test", "tests", "__tests__") for d in dirs)
        or name.startswith("test_")
        or "_test." in name
        or ".test." in name
        or ".spec." in name
        or re.search(r"(?:Test|Tests)\.[^.]+$", orig_name)   # 驼峰，区分大小写：FooTest.java / UserTests.java
    )
    if is_test:
        return "test"
    if ext in STYLE_EXT:
        return "style"
    if any(d in ("__mocks__", "fixtures", "__fixtures__") for d in dirs) or \
       any(k in name for k in ("mock", "fixture", "seed", "stub")):
        return "data"
    return "production"


def fingerprint(fid, evidence):
    canon = fid + "|" + json.dumps(evidence, sort_keys=True, ensure_ascii=False)
    return "sha256:" + hashlib.sha256(canon.encode("utf-8")).hexdigest()[:16]


def load_ignore(root):
    """v1：仅支持"目录名"和"精确仓库相对路径"（非完整 gitignore 语义，见 doc-rules）。"""
    pats = []
    p = os.path.join(root, ".project-healthignore")
    if os.path.isfile(p):
        with open(p, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    pats.append(line.rstrip("/"))
    return pats


def is_ignored(rel, pats):
    segs = rel.split("/")
    for p in pats:
        if "/" in p:
            if rel == p or rel.startswith(p + "/"):   # 精确相对路径或其子路径
                return True
        elif p in segs:                               # 目录名/文件名
            return True
    return False


def walk_files(root, pats):
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in IGNORE_DIRS]
        # 剪掉被 ignore 的目录
        dns[:] = [d for d in dns if not is_ignored(npath(root, os.path.join(dp, d)), pats)]
        for fn in fns:
            ab = os.path.join(dp, fn)
            rel = npath(root, ab)
            if is_ignored(rel, pats) or ".min." in fn:
                continue
            yield rel, ab


# ---- config 校验 ---------------------------------------------------------
def load_config(root, config_path):
    cfg_path = config_path or os.path.join(root, ".project-health", "config.yml")
    if not os.path.isfile(cfg_path):
        th = dict(DEFAULTS["thresholds"])
        return {"level": "standard", "context": "", "thresholds": th,
                "suppressions": [], "constitution": {}}, th
    try:
        loaded = yaml.safe_load(open(cfg_path, encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        die(EXIT_CONFIG, f"config 解析失败：{e}")
    if not isinstance(loaded, dict):
        die(EXIT_CONFIG, "config 顶层必须是映射。")
    sv = loaded.get("schema_version", 1)
    if sv != 1:
        die(EXIT_CONFIG, f"不支持的 schema_version={sv}（本工具支持 1）。")
    level = loaded.get("level", "standard")
    if level not in LEVELS:
        die(EXIT_CONFIG, f"level 非法：{level}（应为 {sorted(LEVELS)}）。")
    raw_th = loaded.get("thresholds") or {}
    if not isinstance(raw_th, dict):
        die(EXIT_CONFIG, "thresholds 必须是映射（键值对）。")
    th = dict(DEFAULTS["thresholds"])
    for k, v in raw_th.items():
        if k in th:
            if not isinstance(v, int) or isinstance(v, bool) or v < 0:
                die(EXIT_CONFIG, f"threshold {k} 必须是非负整数，得到 {v!r}。")
            th[k] = v
    if th["file_error"] < th["file_warn"]:
        die(EXIT_CONFIG, f"file_error({th['file_error']}) 不能小于 file_warn({th['file_warn']})。")
    supps = loaded.get("suppressions") or []
    if not isinstance(supps, list):
        die(EXIT_CONFIG, "suppressions 必须是列表。")
    seen = set()
    for s in supps:
        if not isinstance(s, dict) or not isinstance(s.get("id"), str) or not s["id"]:
            die(EXIT_CONFIG, f"suppression 缺少合法 id：{s!r}")
        if s["id"] in seen:
            die(EXIT_CONFIG, f"重复的 suppression id：{s['id']}")
        seen.add(s["id"])
        exp = s.get("expires")
        if exp is not None:
            try:
                datetime.strptime(str(exp), "%Y-%m-%d")
            except ValueError:
                die(EXIT_CONFIG, f"suppression {s['id']} 的 expires 非法日期：{exp!r}（应 YYYY-MM-DD）。")
    return {"level": level, "context": loaded.get("context") or "", "thresholds": th,
            "suppressions": supps, "constitution": loaded.get("constitution") or {}}, th


# ---- C1 ------------------------------------------------------------------
def check_c1(root, files, th):
    out = []
    for rel, ab in files:
        ext = os.path.splitext(rel)[1].lower()
        if ext not in SOURCE_EXT or GENERATED_RE.search(rel):
            continue
        n = nonempty_lines(ab)
        cat = classify(rel)
        sev = None
        if cat == "production":
            sev = "error" if n >= th["file_error"] else ("warning" if n >= th["file_warn"] else None)
        else:
            sev = "info" if n >= th["file_warn"] else None
        if not sev:
            continue
        ev = {"lines": n}
        fid = f"C1|large-file|{rel}"
        out.append({"id": fid, "check": "C1", "kind": "large-file", "subject": rel,
                    "severity": sev, "category": cat,
                    "fingerprint": fingerprint(fid, ev), "evidence": ev,
                    "message_key": "oversized_source_file"})
    return out


# ---- C2 ------------------------------------------------------------------
DOC_ROOTS = ("README.md", "AGENTS.md", "CLAUDE.md")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
BACKTICK_RE = re.compile(r"`([^`]+)`")
LOC_SUFFIX_RE = re.compile(r":\d+(?::\d+)?$")   # 剥掉 file.py:42 / file.py:42:8 的定位后缀


def doc_set(files):
    has_skill = any(rel.endswith("SKILL.md") for rel, _ in files)
    docs = []
    for rel, ab in files:
        if not rel.endswith(".md"):
            continue
        keep = rel in DOC_ROOTS or rel.startswith("docs/")
        if has_skill and (rel.endswith("SKILL.md") or "/references/" in rel):
            keep = True
        if keep:
            docs.append((rel, ab))
    return docs


def top_level_dirs(root):
    return {d for d in os.listdir(root)
            if os.path.isdir(os.path.join(root, d)) and d not in IGNORE_DIRS and not d.startswith(".")}


def _norm_join(base, path):
    joined = os.path.normpath(os.path.join(base, path)) if base else os.path.normpath(path)
    return joined.replace(os.sep, "/")


def resolve_md_link(root, ddir, target):
    """markdown link 语义：`/x`→仓库根；其余→严格相对文档目录；不再 fallback 到根。
    返回 (repo相对目标, exists) 或 None（外链/锚点/非本地）。"""
    path = target.strip().split("#", 1)[0]
    if not path or path.startswith("//") or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", path):
        return None   # 排除任何 scheme:（http/mailto/tel/data/file/vscode…）与协议相对 //host
    if path.startswith("/"):
        rel = path.lstrip("/")
    else:
        rel = _norm_join(ddir, path)
    if rel.startswith(".."):          # 逃出项目根 → 判为断链
        return (rel, False)
    return (rel, os.path.exists(os.path.join(root, rel)))


def extract_commands(line):
    """v1 只稳定检查 `npm/pnpm/yarn run <script>`；简写(yarn build)歧义大、会撞内置命令(install/add/exec…)，不查。"""
    return re.findall(r"\b(?:npm|pnpm|yarn)\s+run\s+([\w:./-]+)", line)


def looks_like_repo_path(tok, top_dirs):
    p = tok.split("#", 1)[0]
    if not p or " " in p:
        return False
    first = p.split("/", 1)[0]
    return p.startswith(("./", "../")) or (first in top_dirs and "/" in p)


def check_c2(root, docs, top_dirs, has_pkg, pkg_scripts, pkg_valid):
    agg = {}

    def add(doc, target, ln, kind):
        agg.setdefault((doc, target, kind), []).append(ln)

    for rel, ab in docs:
        ddir = os.path.dirname(rel)
        try:
            lines = open(ab, encoding="utf-8", errors="replace").read().splitlines()
        except OSError:
            continue
        in_fence = False
        for i, raw in enumerate(lines, 1):
            if raw.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            # 命令：扫代码块 + 反引号（仅 package.json 有效时）
            if has_pkg and pkg_valid:
                for script in extract_commands(raw):
                    if script not in pkg_scripts:
                        add(rel, script, i, "broken-command")
            if in_fence:
                continue
            # 反引号路径（保守，相对仓库根；剥掉 :行:列 定位后缀）
            for m in BACKTICK_RE.finditer(raw):
                tok = LOC_SUFFIX_RE.sub("", m.group(1).strip().split("#", 1)[0])
                if looks_like_repo_path(tok, top_dirs):
                    r = _norm_join("", tok)
                    if r.startswith("..") or not os.path.exists(os.path.join(root, r)):
                        add(rel, r, i, "broken-ref")
            # markdown 链接（跳过反引号内），严格相对文档目录
            stripped = BACKTICK_RE.sub("", raw)
            for m in LINK_RE.finditer(stripped):
                res = resolve_md_link(root, ddir, m.group(1))
                if res and not res[1]:
                    add(rel, res[0], i, "broken-ref")

    out = []
    for (doc, target, kind), locs in agg.items():
        locs = sorted(set(locs))
        ev = {"target": target, "locations": [{"line": x} for x in locs]}
        fid = f"C2|{kind}|{doc}|{target}"
        mk = "broken_local_reference" if kind == "broken-ref" else "broken_npm_script"
        out.append({"id": fid, "check": "C2", "kind": kind, "subject": doc,
                    "severity": "error", "category": None,
                    "fingerprint": fingerprint(fid, ev), "evidence": ev,
                    "message_key": mk})
    return out


# ---- C3 ------------------------------------------------------------------
def check_c3(docs, th):
    out = []
    for rel, ab in docs:
        n = total_lines(ab)
        if n >= th["doc_warn"]:
            ev = {"lines": n}
            fid = f"C3|oversized-doc|{rel}"
            out.append({"id": fid, "check": "C3", "kind": "oversized-doc", "subject": rel,
                        "severity": "warning", "category": None,
                        "fingerprint": fingerprint(fid, ev), "evidence": ev,
                        "message_key": "oversized_doc"})
    return out


# ---- C4 ------------------------------------------------------------------
def git_state(root):
    try:
        r = subprocess.run(["git", "-C", root, "rev-parse", "--show-toplevel"],
                           capture_output=True, text=True)
    except (OSError, subprocess.SubprocessError):
        return False, "not_git_repository", None
    if r.returncode != 0:
        return False, "not_git_repository", None
    if os.path.realpath(r.stdout.strip()) != os.path.realpath(root):
        return False, "not_repo_root", None
    h = subprocess.run(["git", "-C", root, "rev-parse", "--short", "HEAD"],
                       capture_output=True, text=True)
    commit = h.stdout.strip() if h.returncode == 0 else None
    return True, None, commit


def check_c4(root, files, th):
    r = subprocess.run(
        ["git", "-c", "core.quotepath=false", "-C", root, "log",
         f"--since={th['churn_days']} days ago", "--name-only", "-z", "--pretty=format:"],
        capture_output=True, text=True)
    if r.returncode != 0:
        return None   # git log 失败 → 交调用方标 skipped，不静默给"没热点"
    churn = {}
    for name in r.stdout.split("\0"):
        name = name.strip()
        if name:
            churn[name] = churn.get(name, 0) + 1
    out = []
    for rel, ab in files:
        ext = os.path.splitext(rel)[1].lower()
        if ext not in SOURCE_EXT or GENERATED_RE.search(rel):
            continue
        n = nonempty_lines(ab)
        c = churn.get(rel, 0)
        if n >= th["file_warn"] and c >= th["churn_min"]:
            ev = {"lines": n, "churn": c, "score": n * c}
            fid = f"C4|hotspot|{rel}"
            out.append({"id": fid, "check": "C4", "kind": "hotspot", "subject": rel,
                        "severity": "info", "category": None,
                        "fingerprint": fingerprint(fid, ev), "evidence": ev,
                        "message_key": "debt_hotspot"})
    return out


# ---- C5 · 宪法 -----------------------------------------------------------
CON_DETERMINISTIC_KINDS = {
    "max_file_lines", "forbidden_path", "required_path",
    "required_file_pair", "forbidden_dependency", "naming_pattern",
}

_sev_map = {"error": "error", "warning": "warning", "info": "info"}


def _glob_match(pattern, rel):
    """Simple glob: **跨任意目录，*匹配单层非斜杠。"""
    import fnmatch
    return fnmatch.fnmatch(rel, pattern)


def check_c5(root, files, constitution_path):
    cpath = os.path.join(root, constitution_path[2:] if constitution_path.startswith("./") else constitution_path)
    if not os.path.isfile(cpath):
        return [], None   # 无宪法 → 不报错（不是每个项目都有）
    try:
        c = yaml.safe_load(open(cpath, encoding="utf-8")) or {}
    except (yaml.YAMLError, OSError):
        return [], {"check": "CON", "reason": "invalid_constitution"}
    rules = c.get("rules") or []
    out = []
    for r in rules:
        if r.get("status", "active") != "active":
            continue   # proposed / deprecated / 未确认 → 不执行
        ek = (r.get("enforcement") or {}).get("kind")
        if ek not in CON_DETERMINISTIC_KINDS:
            continue   # manual_review / 未知 → 不执行
        sev = _sev_map.get(r.get("severity"), "info")
        sid = f"CON|{r['id']}"
        ev = {}
        if ek == "max_file_lines":
            val = (r.get("enforcement") or {}).get("value")
            if not isinstance(val, int) or val < 1:
                continue
            globs = ([r["applies_to"]] if isinstance(r.get("applies_to"), str) else
                     r.get("applies_to") or None)
            for rel, ab in files:
                ext = os.path.splitext(rel)[1].lower()
                if ext not in SOURCE_EXT:
                    continue
                if globs and not any(_glob_match(g, rel) for g in globs):
                    continue
                n = nonempty_lines(ab)
                if n > val:
                    ev = {"lines": n, "limit": val}
                    fid = f"{sid}|{rel}"
                    out.append({
                        "id": fid, "check": "CON", "kind": "constitution",
                        "subject": rel, "severity": sev, "category": None,
                        "fingerprint": fingerprint(fid, ev), "evidence": ev,
                        "message_key": "constitution_violation",
                        "constitution": {"rule_id": r["id"], "statement": r.get("statement", ""),
                                         "enforcement_kind": ek},
                    })
    return out, None


# ---- suppressions / 组装 -------------------------------------------------
def split_suppressions(findings, suppressions):
    today = datetime.now(timezone.utc).date()
    supp = {s["id"]: s for s in suppressions}
    live, suppressed, expired = [], [], []
    for f in findings:
        s = supp.get(f["id"])
        if not s:
            live.append(f)
            continue
        exp = s.get("expires")
        # config 已校验 expires 合法；此处只判是否过期
        if exp and datetime.strptime(str(exp), "%Y-%m-%d").date() < today:
            live.append(f)
            expired.append({"id": f["id"], "reason": s.get("reason"), "expires": exp})
        else:
            suppressed.append({**f, "suppression_reason": s.get("reason")})
    return live, suppressed, expired


def main():
    ap = argparse.ArgumentParser(prog="scan.py")
    ap.add_argument("--root", required=True)
    ap.add_argument("--config")
    ap.add_argument("--output")
    ap.add_argument("--format", choices=["yaml", "json"], default="yaml")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        die(EXIT_ROOT, f"root 无效：{args.root}")

    cfg, th = load_config(root, args.config)

    try:
        pats = load_ignore(root)
        has_ignore = os.path.isfile(os.path.join(root, ".project-healthignore"))
        files = list(walk_files(root, pats))
        docs = doc_set(files)
        top_dirs = top_level_dirs(root)
        pkg = os.path.join(root, "package.json")
        has_pkg = os.path.isfile(pkg)
        pkg_valid, pkg_scripts = True, set()
        if has_pkg:
            try:
                data = json.load(open(pkg, encoding="utf-8"))
                if not isinstance(data, dict):
                    raise ValueError("package.json 顶层不是对象")
                scripts = data.get("scripts") or {}
                if not isinstance(scripts, dict):
                    raise ValueError("scripts 不是对象")
                pkg_scripts = set(scripts.keys())
            except (json.JSONDecodeError, OSError, ValueError):
                pkg_valid = False

        skipped = []
        findings = []
        findings += check_c1(root, files, th)
        findings += check_c2(root, docs, top_dirs, has_pkg, pkg_scripts, pkg_valid)
        findings += check_c3(docs, th)
        if has_pkg and not pkg_valid:
            skipped.append({"check": "C2-command", "reason": "invalid_package_json"})

        is_git, git_reason, commit = git_state(root)
        if is_git:
            c4 = check_c4(root, files, th)
            if c4 is None:
                skipped.append({"check": "C4", "reason": "git_log_failed"})
            else:
                findings += c4
        else:
            skipped.append({"check": "C4", "reason": git_reason})

        # C5 · 宪法检查（只查可执行的 deterministic rules）
        const_path = cfg.get("constitution", {}).get("path", ".project-health/constitution.yml")
        c5, c5_skip = check_c5(root, files, const_path)
        if c5:
            findings += c5
        elif c5_skip:
            skipped.append(c5_skip)

        src_scanned = sum(1 for rel, _ in files
                          if os.path.splitext(rel)[1].lower() in SOURCE_EXT and not GENERATED_RE.search(rel))
        findings.sort(key=lambda f: (f["check"], f["kind"], f["subject"], f["id"]))
        live, suppressed, expired = split_suppressions(findings, cfg["suppressions"])
        summary = {"error": 0, "warning": 0, "info": 0}
        for f in live:
            summary[f["severity"]] += 1

        now = datetime.now(timezone.utc)
        ms = f"{now.microsecond // 1000:03d}"
        run_id = now.strftime("%Y%m%dT%H%M%S") + ms + "Z" + ("-" + commit if commit else "")
        state = {
            "schema_version": 1,
            "run": {"id": run_id,
                    "timestamp": now.strftime("%Y-%m-%dT%H:%M:%S.") + ms + "Z",
                    "commit": commit, "tool_version": TOOL_VERSION},
            "effective_config": {"level": cfg["level"], "context": cfg.get("context", ""),
                                 "thresholds": th},
            "scan": {"files_scanned": src_scanned, "docs_scanned": len(docs),
                     "git": is_git, "custom_ignore": has_ignore,
                     "custom_ignore_rules": len(pats), "skipped_checks": skipped},
            "summary": summary,
            "findings": live,
            "suppressed_findings": suppressed,
            "expired_suppressions": expired,
        }
    except SystemExit:
        raise
    except Exception as e:  # noqa
        die(EXIT_INTERNAL, f"内部扫描失败：{e}")

    text = (json.dumps(state, ensure_ascii=False, indent=2)
            if args.format == "json" else yaml.safe_dump(state, allow_unicode=True, sort_keys=False))
    if args.output:
        d = os.path.dirname(os.path.abspath(args.output))
        os.makedirs(d, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=d)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, args.output)
    else:
        sys.stdout.write(text)
    sys.exit(EXIT_OK)


if __name__ == "__main__":
    main()
