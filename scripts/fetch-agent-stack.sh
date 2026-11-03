#!/usr/bin/env bash
set -euo pipefail
# Fetch four upstream projects for local integration work.
# Usage: bash scripts/fetch-agent-stack.sh
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${AGENT_STACK_DIR:-$ROOT/.agent-stack}"
mkdir -p "$TARGET"
for spec in   "langgraph|https://github.com/langchain-ai/langgraph.git"   "browser-use|https://github.com/browser-use/browser-use.git"   "crewai|https://github.com/crewAIInc/crewAI.git"   "dify|https://github.com/langgenius/dify.git"
do
  name="${spec%%|*}"
  url="${spec#*|}"
  if [[ -e "$TARGET/$name" ]]; then
    echo "SKIP: $TARGET/$name already exists"
    continue
  fi
  git clone --depth 1 --filter=blob:none "$url" "$TARGET/$name"
  echo "$name $(git -C "$TARGET/$name" rev-parse HEAD)" >> "$TARGET/checked-out-revisions.txt"
done
echo "Sources fetched into $TARGET. Nothing installed or started."
