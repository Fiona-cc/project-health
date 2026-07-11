#!/usr/bin/env python3
"""project-health · scan.py — 确定性扫描核心（C1–C4 → 结构化 findings）。

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
TOOL_VERSION = "0.2.0"


def die(code, msg):
    sys.stderr.write(f"[project-health scan] {msg}\n")
    sys.exit(code)


try:
    import yaml  # noqa
except ImportError:
    die(EXIT_DEPS, "缺少 PyYAML。请先安装：pip install pyyaml（本工具不会自动安装）。")

# ---- 常量：忽略 / 源码白名单 / 分类 --------------------------------------
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
DEFAULTS = {
    "level": "standard",
    "thresholds": {"file_warn": 400, "file_error": 800, "doc_warn": 500,
                   "churn_days": 180, "churn_min": 3},
    "suppressions": [],
}


# ---- 工具函数 ------------------------------------------------------------
def npath(root, abspath):
    """归一化：仓库相对 + 正斜杠 + 无开头 ./ + 无绝对路径。"""
    rel = os.path.relpath(abspath, root).replace(os.sep, "/")
    return rel[2:] if rel.startswith("./") else rel


def nonempty_lines(path):
    n = 0
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.strip():
                    n += 1
    except OSError:
        return 0
    return n


def total_lines(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


def classify(rel):
    parts = rel.lower().split("/")
    name = parts[-1]
    dirs = parts[:-1]
    ext = os.path.splitext(name)[1]
    if any(d in ("test", "tests", "__tests__") for d in dirs) or \
       name.startswith("test_") or "_test." in name or ".test." in name or \
       ".spec." in name or re.search(r"tests?\.[^.]+$", name):
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
    pats = []
    p = os.path.join(root, ".project-healthignore")
    if os.path.isfile(p):
        with open(p, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    pats.append(line.rstrip("/"))
    return pats


def walk_files(root, extra_ignore):
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in IGNORE_DIRS]
        for fn in fns:
            ab = os.path.join(dp, fn)
            rel = npath(root, ab)
            if any(seg in extra_ignore for seg in rel.split("/")):
                continue
            if ".min." in fn:
                continue
            yield rel, ab


# ---- 检查 ----------------------------------------------------------------
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
            if n >= th["file_error"]:
                sev = "error"
            elif n >= th["file_warn"]:
                sev = "warning"
        else:
            if n >= th["file_warn"]:
                sev = "info"
        if not sev:
            continue
        ev = {"lines": n}
        fid = f"C1|large-file|{rel}"
        out.append({"id": fid, "check": "C1", "kind": "large-file", "subject": rel,
                    "severity": sev, "category": cat,
                    "fingerprint": fingerprint(fid, ev), "evidence": ev,
                    "message_key": "oversized_source_file"})
    return out


DOC_ROOTS = ("README.md", "AGENTS.md", "CLAUDE.md")


def doc_set(root, files):
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


LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
CMD_RE = re.compile(r"\b(?:npm|pnpm)\s+run\s+([\w:-]+)|\byarn\s+([\w:-]+)|\bpnpm\s+([\w:-]+)")


def check_c2(root, docs, top_dirs, has_pkg, pkg_scripts):
    agg = {}  # (doc, target) -> {locations, kind, script}

    def add(doc, target, ln, kind):
        key = (doc, target, kind)
        agg.setdefault(key, []).append(ln)

    for rel, ab in docs:
        ddir = os.path.dirname(rel)
        try:
            lines = open(ab, encoding="utf-8", errors="replace").read().splitlines()
        except OSError:
            continue
        in_fence = False
        for i, raw in enumerate(lines, 1):
            fence = raw.lstrip().startswith("```")
            if fence:
                in_fence = not in_fence
                continue
            # 命令：扫代码块 + 反引号（仅有 package.json 时）
            if has_pkg:
                for m in CMD_RE.finditer(raw):
                    script = m.group(1) or m.group(2) or m.group(3)
                    if script and script not in pkg_scripts:
                        add(rel, script, i, "broken-command")
            # 路径：markdown 链接，跳过 fenced + inline 代码
            if in_fence:
                continue
            stripped = re.sub(r"`[^`]*`", "", raw)
            for m in LINK_RE.finditer(stripped):
                tgt = m.group(1).strip()
                path = tgt.split("#", 1)[0]
                if not path or path.startswith(("http://", "https://", "mailto:")):
                    continue
                first = path.split("/", 1)[0]
                is_pathref = path.startswith(("./", "../")) or first in top_dirs
                if not is_pathref:
                    continue
                # 归一化到仓库相对
                if ddir:
                    resolved = os.path.normpath(os.path.join(ddir, path)).replace(os.sep, "/")
                else:
                    resolved = os.path.normpath(path).replace(os.sep, "/")
                # 存在性：相对文档目录 或 相对根
                exists = os.path.exists(os.path.join(root, resolved)) or \
                    os.path.exists(os.path.join(root, path))
                if not exists:
                    add(rel, resolved, i, "broken-ref")

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


def check_c3(root, docs, th):
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


def git_state(root):
    try:
        r = subprocess.run(["git", "-C", root, "rev-parse", "--show-toplevel"],
                           capture_output=True, text=True)
    except (OSError, subprocess.SubprocessError):
        return False, "not_git_repository"
    if r.returncode != 0:
        return False, "not_git_repository"
    if os.path.realpath(r.stdout.strip()) != os.path.realpath(root):
        return False, "not_repo_root"
    return True, None


def check_c4(root, c1_files, th):
    r = subprocess.run(
        ["git", "-C", root, "log", f"--since={th['churn_days']} days ago",
         "--name-only", "--pretty=format:"], capture_output=True, text=True)
    churn = {}
    for line in r.stdout.splitlines():
        line = line.strip()
        if line:
            churn[line] = churn.get(line, 0) + 1
    out = []
    for rel, ab in c1_files:
        ext = os.path.splitext(rel)[1].lower()
        if ext not in SOURCE_EXT:
            continue
        n = nonempty_lines(ab)
        c = churn.get(rel, 0)
        if n >= th["file_warn"] and c >= th["churn_min"]:
            ev = {"lines": n, "churn": c}
            fid = f"C4|hotspot|{rel}"
            out.append({"id": fid, "check": "C4", "kind": "hotspot", "subject": rel,
                        "severity": "info", "category": None,
                        "fingerprint": fingerprint(fid, ev), "evidence": ev,
                        "message_key": "debt_hotspot"})
    return out


# ---- suppressions / 组装 -------------------------------------------------
def split_suppressions(findings, suppressions):
    now = datetime.now(timezone.utc).date()
    supp = {}
    for s in suppressions:
        supp[s.get("id")] = s
    live, suppressed, expired = [], [], []
    for f in findings:
        s = supp.get(f["id"])
        if not s:
            live.append(f)
            continue
        exp = s.get("expires")
        is_expired = False
        if exp:
            try:
                is_expired = datetime.strptime(str(exp), "%Y-%m-%d").date() < now
            except ValueError:
                is_expired = False
        if is_expired:
            live.append(f)
            expired.append({"id": f["id"], "reason": s.get("reason"), "expires": exp})
        else:
            suppressed.append({**f, "suppression_reason": s.get("reason")})
    return live, suppressed, expired


def sort_key(f):
    return (f["check"], f["kind"], f["subject"], f["id"])


def main():
    ap = argparse.ArgumentParser(prog="scan.py")
    ap.add_argument("--root", required=True)
    ap.add_argument("--config")
    ap.add_argument("--output")
    ap.add_argument("--format", choices=["yaml", "json"], default="yaml")
    ap.add_argument("--commit", default="")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        die(EXIT_ROOT, f"root 无效：{args.root}")

    cfg_path = args.config or os.path.join(root, ".project-health", "config.yml")
    cfg = dict(DEFAULTS)
    if os.path.isfile(cfg_path):
        try:
            loaded = yaml.safe_load(open(cfg_path, encoding="utf-8")) or {}
        except yaml.YAMLError as e:
            die(EXIT_CONFIG, f"config 解析失败：{e}")
        th = dict(DEFAULTS["thresholds"])
        th.update(loaded.get("thresholds") or {})
        cfg = {"level": loaded.get("level", "standard"), "thresholds": th,
               "suppressions": loaded.get("suppressions") or []}

    try:
        ignore = load_ignore(root)
        files = list(walk_files(root, ignore))
        th = cfg["thresholds"]
        docs = doc_set(root, files)
        top_dirs = top_level_dirs(root)
        pkg = os.path.join(root, "package.json")
        has_pkg = os.path.isfile(pkg)
        pkg_scripts = set()
        if has_pkg:
            try:
                pkg_scripts = set((json.load(open(pkg, encoding="utf-8")).get("scripts") or {}).keys())
            except (json.JSONDecodeError, OSError):
                pass

        findings = []
        findings += check_c1(root, files, th)
        findings += check_c2(root, docs, top_dirs, has_pkg, pkg_scripts)
        findings += check_c3(root, docs, th)

        is_git, git_reason = git_state(root)
        skipped = []
        if is_git:
            findings += check_c4(root, files, th)
        else:
            skipped.append({"check": "C4", "reason": git_reason})

        src_scanned = sum(1 for rel, _ in files
                          if os.path.splitext(rel)[1].lower() in SOURCE_EXT and not GENERATED_RE.search(rel))
        findings.sort(key=sort_key)
        live, suppressed, expired = split_suppressions(findings, cfg["suppressions"])
        summary = {"error": 0, "warning": 0, "info": 0}
        for f in live:
            summary[f["severity"]] = summary.get(f["severity"], 0) + 1

        now = datetime.now(timezone.utc)
        run_id = now.strftime("%Y%m%dT%H%M%SZ") + ("-" + args.commit if args.commit else "")
        state = {
            "schema_version": 1,
            "run": {"id": run_id, "timestamp": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "commit": args.commit, "tool_version": TOOL_VERSION},
            "scan": {"files_scanned": src_scanned, "docs_scanned": len(docs),
                     "git": is_git, "skipped_checks": skipped},
            "summary": summary,
            "findings": live,
            "suppressed_findings": suppressed,
            "expired_suppressions": expired,
        }
    except Exception as e:  # noqa
        die(EXIT_INTERNAL, f"内部扫描失败：{e}")

    if args.format == "json":
        text = json.dumps(state, ensure_ascii=False, indent=2, sort_keys=False)
    else:
        text = yaml.safe_dump(state, allow_unicode=True, sort_keys=False)

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
