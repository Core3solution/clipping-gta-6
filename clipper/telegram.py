"""Telegram as the phone interface: deliver each rendered MP4 with its title, description, hashtags, credit and
source link, take Aprovar/Rejeitar taps, and accept links sent from the phone as new production requests.

Only the Bot API over HTTPS (no extra packages). Secrets come from the environment or .env:
TELEGRAM_BOT_TOKEN (from @BotFather) and TELEGRAM_CHAT_ID (your own chat with the bot). Nothing is ever published to
a social network from here: approval only records your decision.

State (state/telegram.json): which clips were sent (so a re-run never sends twice), decisions, the update offset and
the queue of requested links."""
import hashlib
import json
import mimetypes
import os
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, request

from . import state
from .config import ROOT

API = "https://api.telegram.org"
MAX_UPLOAD = 50 * 1024 * 1024  # Bot API upload limit for sendVideo
CAPTION_MAX = 1024
MESSAGE_MAX = 4096
URL_RE = re.compile(r"https?://\S+")
STATE = "telegram"


class TelegramError(RuntimeError):
    pass


def credentials():
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip(), os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat:
        raise SystemExit("Telegram não configurado: defina TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID no .env "
                         "(veja docs/pt-br/TELEGRAM.md). Rode `python3 -m clipper telegram chat-id` para descobrir o id.")
    return token, chat


def _redact(text, token):
    return str(text).replace(token, "<token>") if token else str(text)


def _multipart(fields, files):
    boundary = uuid.uuid4().hex
    out = bytearray()
    for k, v in fields.items():
        out += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n".encode()
        out += (v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)).encode("utf-8") + b"\r\n"
    for k, path in files.items():
        path = Path(path)
        ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        out += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"; filename=\"{path.name}\"\r\n"
                f"Content-Type: {ctype}\r\n\r\n").encode("utf-8")
        out += path.read_bytes() + b"\r\n"
    out += f"--{boundary}--\r\n".encode()
    return bytes(out), f"multipart/form-data; boundary={boundary}"


def call(method, fields=None, files=None, token=None, timeout=120):
    """One Bot API call; returns its `result`. Errors never include the token."""
    token = token or credentials()[0]
    url = f"{os.environ.get('TELEGRAM_API_BASE', API).rstrip('/')}/bot{token}/{method}"
    fields = {k: v for k, v in (fields or {}).items() if v is not None}
    if files:
        body, ctype = _multipart(fields, files)
    else:
        body, ctype = json.dumps(fields, ensure_ascii=False).encode("utf-8"), "application/json"
    req = request.Request(url, data=body, headers={"Content-Type": ctype}, method="POST")
    try:
        with request.urlopen(req, timeout=timeout) as res:
            data = json.loads(res.read().decode("utf-8"))
    except error.HTTPError as e:
        try:
            data = json.loads(e.read().decode("utf-8"))
        except ValueError:
            raise TelegramError(f"{method}: HTTP {e.code}") from None
    except (error.URLError, TimeoutError, OSError) as e:
        raise TelegramError(f"{method}: {_redact(e, token)}") from None
    if not data.get("ok"):
        raise TelegramError(f"{method}: {_redact(data.get('description', data), token)}")
    return data.get("result")


def clip_id(mp4):
    """Stable short id for one MP4 (its path under the repo), used in the buttons' callback data."""
    p = Path(mp4).resolve()
    try:
        rel = p.relative_to(ROOT)
    except ValueError:
        rel = p
    return hashlib.sha1(str(rel).encode("utf-8")).hexdigest()[:12]


def caption(entry, lang="pt"):
    """The text under the video: what to post with it, credit and link. Plain text (no parse mode to escape)."""
    pt = lang == "pt"
    channels = ", ".join(dict.fromkeys(entry.get("channels") or []))
    lines = [entry.get("title") or "(sem título)" if pt else entry.get("title") or "(no title)"]
    if entry.get("hook"):
        lines.append(("Gancho na tela: " if pt else "On-screen hook: ") + entry["hook"].replace("*", ""))
    kinds = []
    if entry.get("clip_type"):
        kinds.append(entry["clip_type"])
    if entry.get("source_kind"):
        kinds.append(("fonte: " if pt else "source: ") + entry["source_kind"])
    if entry.get("duration"):
        kinds.append(f"{float(entry['duration']):.0f}s")
    if kinds:
        lines.append(" · ".join(kinds))
    if channels:
        lines.append(("Crédito: " if pt else "Credit: ") + channels)
    for link in (entry.get("sources") or [entry.get("source")])[:3]:
        if link:
            lines.append(("Fonte: " if pt else "Source: ") + link)
    if entry.get("hashtags"):
        lines.append(" ".join(entry["hashtags"]))
    text = "\n".join(lines)
    return text if len(text) <= CAPTION_MAX else text[:CAPTION_MAX - 1] + "…"


def _channels(desc):
    """Creator names from the description's credit line(s) ('Corte de X: link' / 'Cortes de:\\nX: link')."""
    names = re.findall(r"^(?:Corte de|Clip from) (.+?): https?://", desc or "", re.M)
    names += re.findall(r"^([^\n:]+): https?://", desc.split("Cortes de:")[-1] if "Cortes de:" in (desc or "")
                        else desc.split("Clips from:")[-1] if "Clips from:" in (desc or "") else "", re.M)
    return names


def pending(exports_root, sent):
    """[(mp4 path, manifest entry)] for rendered MP4s under exports_root that weren't sent yet, oldest first."""
    out = []
    for manifest in sorted(Path(exports_root).glob("**/upload.json")):
        try:
            entries = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for e in entries if isinstance(entries, list) else []:
            mp4 = manifest.parent / Path(e.get("file", "")).name
            if mp4.suffix.lower() == ".mp4" and mp4.exists() and clip_id(mp4) not in sent:
                out.append((mp4, dict(e, channels=_channels(e.get("description", "")))))
    return out


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def buttons(cid):
    return {"inline_keyboard": [[{"text": "✅ Aprovar", "callback_data": f"ok:{cid}"},
                                  {"text": "❌ Rejeitar", "callback_data": f"no:{cid}"}]]}


def send(cfg, exports_root=None, limit=None, dry_run=False):
    """Send every rendered MP4 not sent yet (video + caption + buttons, then the full description as a reply to copy).
    State is saved after each clip, so a crash never re-sends what already went out."""
    lang = cfg.get("language", "en")
    exports_root = Path(exports_root or ROOT / "exports" / cfg.get("profile", "gta6"))
    st = state.load(STATE)
    sent = st.setdefault("sent", {})
    todo = pending(exports_root, sent)[:limit] if limit else pending(exports_root, sent)
    report = {"sent": [], "skipped": [], "errors": []}
    if dry_run:
        report["would_send"] = [str(p) for p, _ in todo]
        return report
    token, chat = credentials() if todo else (None, None)
    for mp4, entry in todo:
        cid = clip_id(mp4)
        if mp4.stat().st_size > MAX_UPLOAD:
            report["skipped"].append({"file": str(mp4), "reason": f"{mp4.stat().st_size / 2**20:.0f} MB > 50 MB"})
            continue
        try:
            msg = call("sendVideo", {"chat_id": chat, "caption": caption(entry, lang), "supports_streaming": "true",
                                     "reply_markup": buttons(cid)}, {"video": mp4}, token=token)
            desc = entry.get("description") or ""
            if desc:
                head = "Descrição para colar:\n\n" if lang == "pt" else "Description to paste:\n\n"
                call("sendMessage", {"chat_id": chat, "text": (head + desc)[:MESSAGE_MAX],
                                     "reply_to_message_id": msg["message_id"]}, token=token)
        except TelegramError as e:
            report["errors"].append({"file": str(mp4), "error": str(e)})
            continue
        sent[cid] = {"file": str(mp4.relative_to(ROOT) if mp4.is_relative_to(ROOT) else mp4),
                     "message_id": msg["message_id"], "title": entry.get("title"), "sent_at": _now()}
        state.save(STATE, st)
        report["sent"].append(sent[cid]["file"])
        time.sleep(1)  # stay well under the Bot API's per-chat rate
    return report


DECISIONS = {"ok": ("aprovado", "✅ Aprovado"), "no": ("rejeitado", "❌ Rejeitado")}


def poll(cfg=None):
    """Read new taps and messages once (no long-running process): record Aprovar/Rejeitar, queue links sent from the
    phone. Only your own chat (TELEGRAM_CHAT_ID) is obeyed; anything else is ignored."""
    token, chat = credentials()
    st = state.load(STATE)
    st.setdefault("decisions", {})
    st.setdefault("requests", [])
    updates = call("getUpdates", {"offset": st.get("offset"), "timeout": 0,
                                  "allowed_updates": ["message", "callback_query"]}, token=token) or []
    report = {"decisions": [], "requests": [], "ignored": 0}
    for u in updates:
        st["offset"] = u["update_id"] + 1
        cq = u.get("callback_query")
        if cq:
            msg = cq.get("message") or {}
            if str(msg.get("chat", {}).get("id")) != chat:
                report["ignored"] += 1
                continue
            kind, _, cid = (cq.get("data") or "").partition(":")
            if kind in DECISIONS and cid:
                word, label = DECISIONS[kind]
                st["decisions"][cid] = {"decision": word, "at": _now(),
                                        "file": st.get("sent", {}).get(cid, {}).get("file")}
                report["decisions"].append({"id": cid, "decision": word})
                try:
                    call("answerCallbackQuery", {"callback_query_id": cq["id"], "text": label}, token=token)
                    call("editMessageReplyMarkup", {"chat_id": chat, "message_id": msg.get("message_id"),
                                                    "reply_markup": {"inline_keyboard": [[{"text": label,
                                                                                           "callback_data": "noop"}]]}},
                         token=token)
                except TelegramError:
                    pass  # an old tap whose query expired: the decision is still recorded
            continue
        m = u.get("message") or {}
        if str(m.get("chat", {}).get("id")) != chat:
            report["ignored"] += 1
            continue
        links = URL_RE.findall(m.get("text") or m.get("caption") or "")
        known = {r["url"] for r in st["requests"]}
        new = [x for x in dict.fromkeys(links) if x not in known]
        for link in new:
            st["requests"].append({"url": link, "at": _now(), "status": "pendente"})
        report["requests"] += new
        if new:
            try:
                call("sendMessage", {"chat_id": chat, "reply_to_message_id": m.get("message_id"),
                                     "text": "Recebido. Entra na próxima rodada de produção."}, token=token)
            except TelegramError:
                pass
    state.save(STATE, st)
    return report


def requests(done=None):
    """The links sent from the phone that weren't produced yet; `done` marks one as produced."""
    st = state.load(STATE)
    reqs = st.setdefault("requests", [])
    if done:
        for r in reqs:
            if r["url"] == done:
                r["status"], r["done_at"] = "feito", _now()
        state.save(STATE, st)
    return [r for r in reqs if r.get("status") == "pendente"]


def notify(text):
    """A plain message to your chat (run reports, failures)."""
    token, chat = credentials()
    return call("sendMessage", {"chat_id": chat, "text": text[:MESSAGE_MAX]}, token=token)


def chat_ids():
    """Chats that messaged the bot recently: send it any message first, then read your id here."""
    token = credentials_token_only()
    seen = {}
    for u in call("getUpdates", {"timeout": 0}, token=token) or []:
        c = (u.get("message") or (u.get("callback_query") or {}).get("message") or {}).get("chat") or {}
        if c.get("id"):
            seen[str(c["id"])] = c.get("username") or c.get("first_name") or c.get("title") or ""
    return seen


def credentials_token_only():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("defina TELEGRAM_BOT_TOKEN no .env primeiro (veja docs/pt-br/TELEGRAM.md)")
    return token


def status():
    st = state.load(STATE)
    dec = st.get("decisions", {})
    return {"enviados": len(st.get("sent", {})),
            "aprovados": sum(d["decision"] == "aprovado" for d in dec.values()),
            "rejeitados": sum(d["decision"] == "rejeitado" for d in dec.values()),
            "aguardando": len(set(st.get("sent", {})) - set(dec)),
            "pedidos_pendentes": len([r for r in st.get("requests", []) if r.get("status") == "pendente"])}
