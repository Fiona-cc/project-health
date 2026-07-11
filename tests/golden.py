#!/usr/bin/env python3
"""Golden test: 对每个 fixture 跑 scan.py，去掉易变的 run 元数据后与 expected 逐项比对。

用法：python tests/golden.py       # 跑全部 fixture
要求 Python>=3.8 + PyYAML。
"""
import os
import subprocess
import sys

for _s in (sys.stdout, sys.stderr):   # Windows 控制台常是 GBK，强制 UTF-8 免编码崩
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


def run_fixture(root):
    r = subprocess.run([sys.executable, SCAN, "--root", root, "--format", "yaml"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None, f"scan 退出码 {r.returncode}: {r.stderr.strip()}"
    d = yaml.safe_load(r.stdout)
    d.pop("run", None)  # run 元数据(时间戳/commit)易变，不比
    return d, None


def main():
    fails = 0
    names = sorted(n for n in os.listdir(FIXTURES)
                   if os.path.isdir(os.path.join(FIXTURES, n)))
    for name in names:
        exp_path = os.path.join(EXPECTED, name + ".yml")
        if not os.path.isfile(exp_path):
            print(f"⚠️  {name}: 无 expected，跳过")
            continue
        got, err = run_fixture(os.path.join(FIXTURES, name))
        if err:
            print(f"❌ {name}: {err}")
            fails += 1
            continue
        expected = yaml.safe_load(open(exp_path, encoding="utf-8"))
        if got == expected:
            print(f"✅ {name}")
        else:
            print(f"❌ {name}: 输出与期望不符")
            fails += 1
    print(f"\n{'PASS' if not fails else 'FAIL'}（{fails} 个失败 / {len(names)} 个 fixture）")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
