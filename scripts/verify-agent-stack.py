#!/usr/bin/env python3
"""Offline verification of four checked-out upstream Git repositories."""
from pathlib import Path
import subprocess
import sys

NAMES = ("langgraph", "browser-use", "crewai", "dify")
root = Path(__file__).resolve().parents[1]
base = root / ".agent-stack"
errors = []
for name in NAMES:
    path = base / name
    if not (path / ".git").exists():
        errors.append(f"{name}: source not checked out at {path}")
        continue
    try:
        sha = subprocess.check_output(
            ["git", "-C", str(path), "rev-parse", "HEAD"], text=True, timeout=10
        ).strip()
        remote = subprocess.check_output(
            ["git", "-C", str(path), "remote", "get-url", "origin"],
            text=True, timeout=10,
        ).strip()
    except (subprocess.SubprocessError, OSError) as exc:
        errors.append(f"{name}: cannot inspect repository: {exc}")
        continue
    print(f"{name}: {sha} ({remote})")
if errors:
    print("\n".join(errors), file=sys.stderr)
    sys.exit(1)
print("All four source checkouts are present. Runtime integration is NOT verified.")
