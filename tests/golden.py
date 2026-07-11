#!/usr/bin/env python3
"""Golden test：对每个 fixture 跑 scan.py，与 expected 比对。要求 Python>=3.8 + PyYAML。

三种 fixture：
- 普通：跑 scan → 去掉 run 元数据 → 比 expected/<name>.yml。
- 退出码：expected/<name>.exit 存在 → 只校验退出码（如坏 config 应 2）。
- git 热点：fixture 内有 _gitsetup.txt（"relpath 次数"）→ 复制到临时目录建 git 仓+提交，再跑。
缺 expected 直接 FAIL（防新增 fixture 忘写期望却仍 PASS）。
"""
import os
import shutil
import subprocess
import sys
import tempfile

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import yaml
except ImportError:
    sys.stderr.write("缺少 PyYAML：pip install pyyaml\n")
    sys.exit(3)

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SCAN = os.path.join(REPO, "audit", "scripts", "scan.py")
FIXTURES = os.path.join(HERE, "fixtures")
EXPECTED = os.path.join(HERE, "expected")


def scan_run(root):
    return subprocess.run([sys.executable, SCAN, "--root", root, "--format", "yaml"],
                          capture_output=True, text=True, encoding="utf-8")


def scan_state(root):
    r = scan_run(root)
    if r.returncode != 0:
        return None, f"scan 退出码 {r.returncode}: {r.stderr.strip()}"
    d = yaml.safe_load(r.stdout)
    d.pop("run", None)  # run 元数据易变，不比
    return d, None


def make_git_fixture(src):
    """复制 fixture 到临时目录、建 git 仓、按 _gitsetup.txt 制造 churn。返回 (tmpdir, repo_root)。"""
    tmp = tempfile.mkdtemp(prefix="ph-git-")
    dst = os.path.join(tmp, "repo")
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("_gitsetup.txt"))
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")

    def git(*a):
        subprocess.run(["git", "-C", dst, *a], capture_output=True, text=True, env=env)

    git("init", "-q")
    git("add", "-A")
    git("commit", "-q", "-m", "init")
    for line in open(os.path.join(src, "_gitsetup.txt"), encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        rel, cnt = line.rsplit(None, 1)
        for _ in range(int(cnt)):
            with open(os.path.join(dst, rel), "a", encoding="utf-8") as f:
                f.write("// t\n")
            git("add", rel)
            git("commit", "-q", "-m", "t")
    return tmp, dst


def check_fixture(name):
    fx = os.path.join(FIXTURES, name)
    exit_path = os.path.join(EXPECTED, name + ".exit")
    if os.path.isfile(exit_path):                       # 退出码 fixture
        want = int(open(exit_path, encoding="utf-8").read().strip())
        got = scan_run(fx).returncode
        return (got == want, f"退出码 {got}，期望 {want}")
    exp_path = os.path.join(EXPECTED, name + ".yml")
    if not os.path.isfile(exp_path):
        return (False, "缺少 expected（新增 fixture 必须配期望）")
    if os.path.isfile(os.path.join(fx, "_gitsetup.txt")):   # git 热点 fixture
        tmp, root = make_git_fixture(fx)
        try:
            got, err = scan_state(root)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    else:
        got, err = scan_state(fx)
    if err:
        return (False, err)
    expected = yaml.safe_load(open(exp_path, encoding="utf-8"))
    return (got == expected, "输出与期望不符")


def main():
    names = sorted(n for n in os.listdir(FIXTURES)
                   if os.path.isdir(os.path.join(FIXTURES, n)))
    fails = 0
    for name in names:
        ok, detail = check_fixture(name)
        print(f"{'✅' if ok else '❌'} {name}" + ("" if ok else f": {detail}"))
        if not ok:
            fails += 1
    print(f"\n{'PASS' if not fails else 'FAIL'}（{fails} 失败 / {len(names)} fixture）")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
