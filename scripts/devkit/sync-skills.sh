#!/usr/bin/env bash
# Vendor third-party Claude Code skills into .claude/skills/ at pinned commits.
# Why vendored instead of plugins: cloud sessions and routines load the repo's .claude/skills/ but never install
# plugins, so a copy in the repo is the only way the same skills work on the PC and in the cloud.
# Usage: scripts/devkit/sync-skills.sh            (clone from GitHub at the pinned commits)
#        SRC_SUPERPOWERS=/path SRC_PONYTAIL=/path scripts/devkit/sync-skills.sh   (use local clones)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DEST="$ROOT/.claude/skills"
SUPERPOWERS_REPO=https://github.com/obra/superpowers   SUPERPOWERS_REF=22f0b46
PONYTAIL_REPO=https://github.com/DietrichGebert/ponytail PONYTAIL_REF=96608e0
# Skills taken from each (the rest stay out: diagnosing-superpowers is meta, ponytail-gain is the author's benchmark)
SUPERPOWERS_SKILLS="using-superpowers brainstorming writing-plans executing-plans subagent-driven-development
  dispatching-parallel-agents test-driven-development systematic-debugging verification-before-completion
  requesting-code-review receiving-code-review using-git-worktrees finishing-a-development-branch writing-skills"
PONYTAIL_SKILLS="ponytail ponytail-review ponytail-debt ponytail-audit ponytail-help"

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
fetch() {  # name repo ref local-override -> path
  if [ -n "${4:-}" ]; then echo "$4"; return; fi
  git clone -q "$2" "$TMP/$1" && git -C "$TMP/$1" checkout -q "$3" && echo "$TMP/$1"
}
SP="$(fetch superpowers "$SUPERPOWERS_REPO" "$SUPERPOWERS_REF" "${SRC_SUPERPOWERS:-}")"
PT="$(fetch ponytail "$PONYTAIL_REPO" "$PONYTAIL_REF" "${SRC_PONYTAIL:-}")"

mkdir -p "$DEST"
copy() {  # src-root vendor license-file skills...
  local src="$1" vendor="$2" lic="$3"; shift 3
  for s in "$@"; do
    rm -rf "$DEST/$s"; cp -R "$src/skills/$s" "$DEST/$s"
    cp "$src/$lic" "$DEST/$s/LICENSE.$vendor"
  done
}
copy "$SP" superpowers LICENSE $SUPERPOWERS_SKILLS
copy "$PT" ponytail LICENSE $PONYTAIL_SKILLS
# Plugin skills are namespaced ("superpowers:writing-plans"); as project skills they are plain names.
grep -rl "superpowers:" "$DEST" | xargs -r sed -i 's/superpowers:\([a-z-]*\)/\1/g'
echo "skills em $DEST:"; ls "$DEST"
