#!/bin/sh
# Runs a hook with the first real Python 3. On Windows `python3` is usually the Microsoft Store stub (WindowsApps),
# which prints an error instead of running, so the hooks would silently not run there.
for p in python3 python; do
  path=$(command -v "$p" 2>/dev/null) || continue
  case "$path" in *WindowsApps*) "$p" -c "" >/dev/null 2>&1 || continue ;; esac
  [ "$p" = python3 ] || "$p" -c "import sys; sys.exit(sys.version_info[0] != 3)" 2>/dev/null || continue  # no Python 2
  exec "$p" "$@"
done
echo "hook: Python 3 não encontrado (instale ou ponha no PATH)" >&2
exit 1
