#!/usr/bin/env python3
"""PreToolUse guard (Write/Edit/MultiEdit/Bash). Exit 2 blocks the call and tells Claude why.

1. Secrets: refuses to write or run anything that carries a token (Telegram bot token, GitHub, OpenAI/Anthropic,
   AWS, Google, Slack, private keys).
2. Media and private folders: refuses `git add` of .env, jobs/, exports/, logs/ or video/audio files.
3. main branch: asks before committing or pushing on main (work happens on feature branches).

Python only (no Node), so it runs the same on the PC (WSL2), the Windows notebook and Claude Code cloud sessions.
Inspired by agentville's secret-scan and guard-main-branch hooks (Apache-2.0, see THIRD_PARTY.md)."""
import json
import re
import subprocess
import sys

SECRETS = [
    (r"\b\d{8,10}:[A-Za-z0-9_-]{30,}", "token de bot do Telegram"),
    (r"\bghp_[A-Za-z0-9]{36}\b|\bgithub_pat_[A-Za-z0-9_]{50,}\b", "token do GitHub"),
    (r"\bsk-ant-[A-Za-z0-9_-]{20,}", "chave da Anthropic"),
    (r"\bsk-[A-Za-z0-9]{20,}", "chave estilo OpenAI"),
    (r"\bAKIA[0-9A-Z]{16}\b", "chave da AWS"),
    (r"\bAIza[0-9A-Za-z_-]{35}\b", "chave do Google"),
    (r"\bxox[baprs]-[A-Za-z0-9-]{10,}", "token do Slack"),
    (r"-----BEGIN (?:RSA |EC |OPENSSH |PGP |DSA )?PRIVATE KEY-----", "chave privada"),
]
PRIVATE_ADD = re.compile(r"\bgit\s+add\b[^;&|]*?(\s|^|[\"'.\\/])(\.env\b|jobs[\\/]|exports[\\/]|logs[\\/]"
                         r"|\S+\.(mp4|mov|mkv|webm|wav|m4a|mp3|ts)\b)", re.I)
BLANKET_ADD = re.compile(r"\bgit\s+add\s+(-A|--all|\.)(\s|$)")
MAIN_WRITE = re.compile(r"\bgit\s+(commit|push)\b")


def payload_text(ti):
    parts = [ti.get("content"), ti.get("new_string"), ti.get("command")]
    parts += [e.get("new_string") for e in ti.get("edits") or [] if isinstance(e, dict)]
    return "\n".join(p for p in parts if isinstance(p, str))


def branch():
    try:
        return subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True,
                              timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def block(msg):
    print(msg, file=sys.stderr)
    sys.exit(2)


def main():
    sys.stderr.reconfigure(encoding="utf-8")
    try:
        event = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return
    ti = event.get("tool_input") or {}
    text = payload_text(ti)
    path = str(ti.get("file_path") or "")
    if re.search(r"(^|[\\/])\.env$", path):
        block("guard: não escreva no .env pelo Claude. O usuário preenche os segredos (veja .env.example).")
    for pattern, name in SECRETS:
        if re.search(pattern, text):
            block(f"guard: bloqueado, o conteúdo parece conter um segredo ({name}). Use variável de ambiente ou .env, "
                  "nunca código, docs ou comandos.")
    cmd = ti.get("command") or ""
    if event.get("tool_name") in ("Bash", "PowerShell") and cmd:
        if PRIVATE_ADD.search(cmd):
            block("guard: não adicione .env, jobs/, exports/, logs/ nem arquivos de vídeo/áudio ao git.")
        if BLANKET_ADD.search(cmd):
            block("guard: evite `git add -A`/`git add .`; adicione os arquivos pelo nome (protege segredos e mídia).")
        if MAIN_WRITE.search(cmd) and branch() in ("main", "master"):
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse", "permissionDecision": "ask",
                "permissionDecisionReason": "commit/push direto na main: confirme (o padrão é trabalhar em branch)."}}))


if __name__ == "__main__":
    main()
