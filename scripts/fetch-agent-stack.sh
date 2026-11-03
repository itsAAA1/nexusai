#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${AGENT_STACK_DIR:-$ROOT/.agent-stack}"
mkdir -p "$TARGET"
: > "$TARGET/checked-out-revisions.txt"
for spec in \
  "langgraph|https://github.com/langchain-ai/langgraph.git" \
  "browser-use|https://github.com/browser-use/browser-use.git" \
  "crewai|https://github.com/crewAIInc/crewAI.git" \
  "dify|https://github.com/langgenius/dify.git"
do
  name="${spec%%|*}"
  url="${spec#*|}"
  if [[ -d "$TARGET/$name/.git" ]]; then
    echo "EXISTS: $name"
  elif [[ -e "$TARGET/$name" ]]; then
    echo "ERROR: $TARGET/$name exists but is not a git checkout" >&2
    exit 1
  else
    git clone --depth 1 "$url" "$TARGET/$name"
  fi
  actual="$(git -C "$TARGET/$name" remote get-url origin)"
  if [[ "$actual" != "$url" ]]; then
    echo "ERROR: unexpected origin for $name: $actual" >&2
    exit 1
  fi
  echo "$name $(git -C "$TARGET/$name" rev-parse HEAD)" >> "$TARGET/checked-out-revisions.txt"
done
python3 "$ROOT/scripts/verify-agent-stack.py"
echo "All four upstream source checkouts verified. No services installed or started."
