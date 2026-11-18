#!/usr/bin/env bash
# Copy the reusable development structure (not the clipper) into another project:
#   scripts/devkit/export.sh /caminho/do/outro-projeto
# Copies: vendored skills, generic agents, hooks, generic rules, VS Code and GitHub templates, context docs skeleton.
# Never overwrites an existing file (prints what it skipped). Review the rules afterwards: some mention this project.
set -euo pipefail
SRC="$(cd "$(dirname "$0")/../.." && pwd)"; DST="${1:?uso: export.sh <pasta-do-projeto>}"
[ -d "$DST" ] || { echo "pasta não existe: $DST"; exit 1; }
copy() { # relative path
  local s="$SRC/$1" d="$DST/$1"
  if [ -d "$s" ]; then find "$s" -type f | while read -r f; do copy "${f#$SRC/}"; done; return; fi
  if [ -e "$d" ]; then echo "mantido (já existe): $1"; return; fi
  mkdir -p "$(dirname "$d")"; cp "$s" "$d"; echo "copiado: $1"
}
for p in .claude/skills .claude/hooks .claude/agents/explorador.md .claude/agents/revisor.md .claude/agents/depurador.md \
         .claude/rules/01-principios.md .claude/rules/02-fluxo.md .claude/rules/03-contexto.md .claude/rules/04-seguranca.md \
         .vscode/extensions.json .github/pull_request_template.md .github/ISSUE_TEMPLATE scripts/devkit/sync-skills.sh \
         docs/contexto/HANDOFF.md .mcp.json; do copy "$p"; done
[ -e "$DST/.claude/settings.json" ] || { python3 - "$SRC/.claude/settings.json" "$DST/.claude/settings.json" <<'PY'
import json, re, sys
cfg = json.load(open(sys.argv[1]))
drop = re.compile(r"clipper|ffmpeg|ffprobe|jobs/|exports/")
cfg["permissions"]["allow"] = [r for r in cfg["permissions"]["allow"] if not drop.search(r)]
json.dump(cfg, open(sys.argv[2], "w"), indent=2)
PY
echo "copiado: .claude/settings.json (sem permissões do clipper)"; }
echo "Feito. Ajuste .claude/rules/ e docs/contexto/ ao novo projeto e crie um CLAUDE.md curto."
