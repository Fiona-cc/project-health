#!/usr/bin/env python3
"""project-health · compare.py — 确定性基线对比（baseline.yml vs latest-run.yml -> delta）。

契约见 docs/schema-contract-v1.md。要求 Python>=3.8 + PyYAML。
"""
import sys
import os
from datetime import datetime, timezone

for s in (sys.stdout, sys.stderr):
    try:
        s.reconfigure(encoding="utf-8")
    except Exception:
        pass

TOOL_VERSION = "0.3.0"

if sys.version_info < (3, 8):
    sys.stderr.write(f"[compare] need Python>=3.8, got {sys.version.split()[0]}\n")
    sys.exit(3)
try:
    import yaml
except ImportError:
    sys.stderr.write("[compare] PyYAML missing. pip install pyyaml\n")
    sys.exit(3)


def load(path):
    if not os.path.isfile(path):
        return {}
    return yaml.safe_load(open(path, encoding="utf-8")) or {}


def main():
    if len(sys.argv) < 3:
        sys.stderr.write("Usage: compare.py <baseline.yml> <latest-run.yml>\n")
        sys.exit(2)

    base = load(sys.argv[1])
    latest = load(sys.argv[2])

    base_findings = base.get("findings") or []
    latest_findings = latest.get("findings") or []
    suppressed = latest.get("suppressed_findings") or []
    base_map = {f["id"]: f for f in base_findings}
    latest_map = {f["id"]: f for f in latest_findings}

    new = []
    resolved = []
    escalated = []
    de_escalated = []
    evidence_changed = []
    remaining = 0

    severities = {"info": 0, "warning": 1, "error": 2}

    for fid, lf in latest_map.items():
        bf = base_map.get(fid)
        if bf is None:
            new.append(lf)
        else:
            sev_old = severities.get(bf.get("severity"), 0)
            sev_new = severities.get(lf.get("severity"), 0)
            if sev_new > sev_old:
                escalated.append(fid)
            elif sev_new < sev_old:
                de_escalated.append(fid)
            if lf.get("fingerprint") != bf.get("fingerprint"):
                evidence_changed.append(fid)
            remaining += 1

    for fid in base_map:
        if fid not in latest_map:
            resolved.append(base_map[fid])

    now = datetime.now(timezone.utc)
    output = {
        "run": {
            "timestamp": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "tool_version": TOOL_VERSION,
        },
        "delta": {
            "new": new,
            "resolved": resolved,
            "remaining": remaining,
            "escalated": [fid for fid in escalated],
            "de_escalated": [fid for fid in de_escalated],
            "evidence_changed": [fid for fid in evidence_changed],
        },
        "suppressed_active": len(suppressed),
        "base_findings_count": len(base_findings),
        "latest_findings_count": len(latest_findings),
    }
    sys.stdout.write(yaml.safe_dump(output, allow_unicode=True, sort_keys=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
