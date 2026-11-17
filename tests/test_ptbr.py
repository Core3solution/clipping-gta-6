"""Tests for the Brazilian adaptation: gta-br profile, Portuguese hooks and censorship, encoder choice, Telegram
delivery/approval (against a local fake Bot API) and VOD chunk recovery (yt-dlp mocked)."""
import json
import os
import subprocess
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest import mock

from clipper import captions, config, hooks, live, playbook, render, state, telegram, vods


class PortugueseHooksTests(unittest.TestCase):
    def test_portuguese_structures_are_recognised(self):
        self.assertIn("question", hooks.structures("Por que ele fugiu da polícia?"))
        self.assertIn("withheld / negation", hooks.structures("Ninguém esperava esse assalto"))
        self.assertIn("number promise", hooks.structures("3 detalhes escondidos no GTA 6"))
        self.assertIn("relatable situation", hooks.structures("Eu quando o GTA 6 finalmente lança"))
        self.assertIn("premise + twist", hooks.structures("Ele NÃO esperava a polícia"))
        self.assertIn("superlative", hooks.structures("A fuga mais insana do GTA 6"))
        self.assertEqual(hooks.check_hook("Por que ele *NÃO* fugiu da polícia?")[0], [])

    def test_portuguese_labels_and_vague_hooks_fail_like_english_ones(self):
        self.assertTrue(hooks.check_hook("Reação ao trailer")[0])
        self.assertTrue(any("vague" in f for f in hooks.check_hook("Espera isso...")[0]))

    def test_english_behaviour_is_unchanged(self):
        self.assertEqual(hooks.structures("Why did Kai crash?"), ["question"])
        self.assertTrue(hooks.check_hook("Wait for the harmony...")[0])

    def test_portuguese_openings(self):
        self.assertEqual(hooks.opening_type("então galera hoje a gente"), "filler (trim the start)")
        self.assertEqual(hooks.opening_type("meu deus olha isso"), "action cold open")
        self.assertIn("filler", hooks.check_opening({}, [{"w": "tipo", "s": 0.1, "e": 0.3}]) or "")

    def test_titles_portuguese(self):
        self.assertEqual(hooks.check_title("GTA 6: o carro MAIS caro do jogo")[0], [])
        self.assertTrue(hooks.check_title("ATUALIZAÇÃO NOVA DO GTA 6 SAIU")[0])  # all caps
        self.assertTrue(hooks.check_title("GTA 6 atualização explicada")[1])  # announcement wording note

    def test_clip_type_guess_reads_portuguese_titles(self):
        self.assertEqual(playbook.guess_type("REAGINDO ao GTA 6", "x", 100, 0), "reaction")
        self.assertEqual(playbook.guess_type("Fuga insana no GTA 6", "x", 100, 0), "gameplay")
        self.assertEqual(playbook.guess_type("Tudo sobre o mapa do GTA 6", "x", 100, 0), "news")


class PortugueseCensorTests(unittest.TestCase):
    def test_portuguese_swears_masked_and_slurs_dropped(self):
        self.assertEqual(captions.censor("porra!"), "p*rra!")
        self.assertEqual(captions.censor("CARALHO"), "C*RALHO")
        self.assertEqual(captions.censor("pqp"), "p*p")
        self.assertEqual(captions.censor("foda-se!"), "f*da-se!")
        self.assertIsNone(captions.censor("viado"))
        for ok in ("computador", "cultura", "pista", "guarda-chuva", "putz", "Michael", "class"):
            self.assertEqual(captions.censor(ok), ok)

    def test_censor_setting_extra_allow_and_off(self):
        words = [{"w": "mlk", "s": 0, "e": 1}, {"w": "cu", "s": 1, "e": 2}, {"w": "merda", "s": 2, "e": 3}]
        out = [w["w"] for w in captions.censor_words(words, {"extra": ["mlk"], "allow": ["cu"]})]
        self.assertEqual(out, ["m*k", "cu", "m*rda"])
        self.assertEqual([w["w"] for w in captions.censor_words(words, False)], ["mlk", "cu", "merda"])
        self.assertEqual([w["w"] for w in captions.censor_words(words, {"enabled": False})], ["mlk", "cu", "merda"])


class ProfileAndRenderTests(unittest.TestCase):
    def test_gta_br_profile_loads(self):
        cfg = config.load(profile="gta-br")
        try:
            self.assertEqual(cfg["language"], "pt")
            self.assertIn("caraca", cfg["hype_words"])
            self.assertNotIn("mano", cfg["hype_words"])  # too common: would flatten the keyword signal
            self.assertEqual(cfg["video_encoder"], "auto")
            self.assertTrue(playbook.for_profile(cfg)["reaction"]["examples"][0].startswith("Eu vendo"))
        finally:
            config.load()  # back to the default profile for the other tests

    def test_encoder_choice(self):
        self.assertEqual(render.encoder_args({})[:4], ["-c:v", "libx264", "-preset", "medium"])
        self.assertIn("veryfast", render.encoder_args({"x264_preset": "veryfast"}))
        self.assertIn("h264_nvenc", render.encoder_args({"video_encoder": "h264_nvenc"}))
        with mock.patch.object(render, "nvenc_available", return_value=False):
            self.assertIn("libx264", render.encoder_args({"video_encoder": "auto", "x264_preset": "veryfast"}))
        with mock.patch.object(render, "nvenc_available", return_value=True):
            self.assertIn("h264_nvenc", render.encoder_args({"video_encoder": "auto"}))

    def test_perspective_zoom_is_smooth_and_runs_in_ffmpeg(self):
        f = render.fx_filter([{"t": 1.0, "type": "zoom"}], 3.0, "perspective")
        self.assertTrue(f.startswith("fps=30,perspective="))
        self.assertIn("interpolation=cubic", f)
        self.assertIn("scale=w=", render.fx_filter([{"t": 1.0, "type": "zoom"}], 3.0))  # default unchanged
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "z.mp4"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                            "testsrc2=s=216x384:r=60:d=2", "-vf", f, "-c:v", "libx264", "-preset", "ultrafast",
                            str(out)], check=True)
            self.assertGreater(out.stat().st_size, 0)

    def test_portuguese_credit_line_and_twitch_links(self):
        self.assertIn("Corte de Gaules: L", render.post_description("d", [("Gaules", "L")], [], "pt"))
        self.assertIn("Clip from Kai: L", render.post_description("d", [("Kai", "L")], []))
        self.assertEqual(config.timestamp_link("https://www.twitch.tv/videos/123", 3725),
                         "https://www.twitch.tv/videos/123?t=1h2m5s")


class StateTests(unittest.TestCase):
    def test_atomic_round_trip_and_default(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"CLIPPER_STATE_DIR": d}):
            self.assertEqual(state.load("x"), {})
            state.save("x", {"a": 1})
            self.assertEqual(state.load("x"), {"a": 1})
            (Path(d) / "y.json").write_text("{broken")
            self.assertEqual(state.load("y", []), [])
            self.assertEqual(sorted(p.name for p in Path(d).iterdir()), ["x.json", "y.json"])


class FakeBot(BaseHTTPRequestHandler):
    calls, updates = [], []

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        method = self.path.rsplit("/", 1)[-1]
        FakeBot.calls.append((self.path, method, self.headers.get("Content-Type", ""), body))
        result = {"sendVideo": {"message_id": len(FakeBot.calls)}, "sendMessage": {"message_id": 999},
                  "getUpdates": FakeBot.updates}.get(method, True)
        data = json.dumps({"ok": True, "result": result}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass


class TelegramTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), FakeBot)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def setUp(self):
        FakeBot.calls, FakeBot.updates = [], []
        self.tmp = tempfile.TemporaryDirectory()
        self.env = mock.patch.dict(os.environ, {
            "TELEGRAM_BOT_TOKEN": "123456789:SECRET", "TELEGRAM_CHAT_ID": "42", "CLIPPER_STATE_DIR": self.tmp.name,
            "TELEGRAM_API_BASE": f"http://127.0.0.1:{self.server.server_port}"})
        self.env.start()
        folder = Path(self.tmp.name) / "exports" / "gta-br" / "2026-11-19" / "video 1"
        folder.mkdir(parents=True)
        (folder / "Por que ele fugiu.mp4").write_bytes(b"\x00" * 1000)
        (folder / "upload.json").write_text(json.dumps([{
            "file": "Por que ele fugiu.mp4", "hook": "Por que ele *fugiu*?", "title": "Por que ele fugiu no GTA 6?",
            "description": "Fuga absurda.\n\nCorte de Gaules: https://www.twitch.tv/videos/1?t=0h1m0s\n\n#gta6",
            "hashtags": ["#gta6"], "clip_type": "gameplay", "source_kind": "gameplay", "duration": 22.4,
            "source": "https://www.twitch.tv/videos/1?t=0h1m0s"}]))
        self.root = folder.parent.parent

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def test_send_delivers_video_buttons_and_description_once(self):
        out = telegram.send({"language": "pt"}, exports_root=self.root)
        self.assertEqual(len(out["sent"]), 1, out)
        methods = [m for _, m, _, _ in FakeBot.calls]
        self.assertEqual(methods, ["sendVideo", "sendMessage"])
        _, _, ctype, body = FakeBot.calls[0]
        self.assertIn("multipart/form-data", ctype)
        text = body.decode("utf-8", "replace")
        for piece in ("Por que ele fugiu no GTA 6?", "Crédito: Gaules", "Aprovar", "Rejeitar", "fonte: gameplay"):
            self.assertIn(piece, text)
        self.assertIn("Descrição para colar", FakeBot.calls[1][3].decode("utf-8"))
        FakeBot.calls = []
        self.assertEqual(telegram.send({"language": "pt"}, exports_root=self.root)["sent"], [])
        self.assertEqual(FakeBot.calls, [])

    def test_errors_never_show_the_token(self):
        with mock.patch.dict(os.environ, {"TELEGRAM_API_BASE": "http://127.0.0.1:1"}):
            with self.assertRaises(telegram.TelegramError) as e:
                telegram.call("getMe")
        self.assertNotIn("SECRET", str(e.exception))

    def test_poll_records_decisions_and_requests_only_from_own_chat(self):
        telegram.send({"language": "pt"}, exports_root=self.root)
        cid = next(iter(state.load("telegram")["sent"]))
        FakeBot.updates = [
            {"update_id": 10, "callback_query": {"id": "q1", "data": f"ok:{cid}",
                                                 "message": {"message_id": 1, "chat": {"id": 42}}}},
            {"update_id": 11, "message": {"message_id": 5, "chat": {"id": 42},
                                          "text": "faz esse https://www.twitch.tv/videos/777 por favor"}},
            {"update_id": 12, "message": {"message_id": 6, "chat": {"id": 666}, "text": "https://evil.example"}},
        ]
        out = telegram.poll({})
        self.assertEqual(out["decisions"], [{"id": cid, "decision": "aprovado"}])
        self.assertEqual(out["requests"], ["https://www.twitch.tv/videos/777"])
        self.assertEqual(out["ignored"], 1)
        st = state.load("telegram")
        self.assertEqual(st["offset"], 13)
        self.assertEqual(telegram.status()["aprovados"], 1)
        self.assertEqual([r["url"] for r in telegram.requests()], ["https://www.twitch.tv/videos/777"])
        self.assertEqual(telegram.requests(done="https://www.twitch.tv/videos/777"), [])

    def test_missing_credentials_message(self):
        with mock.patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "", "TELEGRAM_CHAT_ID": ""}):
            with self.assertRaises(SystemExit):
                telegram.credentials()


class VodChunkTests(unittest.TestCase):
    S = {"chunk": 1800, "max": 4, "lookback_h": 48, "min": 600}

    def test_plan_chunks(self):
        self.assertEqual(vods.plan_chunks(4000, 0, False, self.S), [(0.0, 1800.0), (1800.0, 3600.0)])
        self.assertEqual(vods.plan_chunks(4300, 3600, False, self.S), [(3600.0, 4300.0)])
        self.assertEqual(vods.plan_chunks(1500, 0, True, self.S), [(0.0, 1380.0)])  # live: edge kept back
        self.assertEqual(vods.plan_chunks(700, 0, True, self.S), [])  # live: not enough new footage yet

    def test_order_is_round_robin_newest_vod_first(self):
        cs = [{"stream": "a", "started_at": 1, "start": 0}, {"stream": "a", "started_at": 1, "start": 1800},
              {"stream": "b", "started_at": 5, "start": 0}, {"stream": "a", "started_at": 9, "start": 0}]
        got = [(c["stream"], c["started_at"], c["start"]) for c in vods.order(cs)]
        self.assertEqual(got, [("a", 9, 0), ("b", 5, 0), ("a", 1, 0), ("a", 1, 1800)])

    def test_fetch_creates_live_jobs_saves_progress_and_retries_failures(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"CLIPPER_STATE_DIR": d + "/state"}):
            jobs = Path(d) / "jobs"
            cfg = {"vods": {"chunk_minutes": 30, "max_chunks_per_run": 4, "min_chunk_minutes": 10},
                   "topic_patterns": ["\\bgta ?(6|vi)\\b"], "require_topic": True}
            info = {"timestamp": 2_000_000_000, "description": "GTA 6 DIA 1 !sorteio", "duration": 4000,
                    "is_live": True, "uploader": "Gaules"}
            calls = []

            def fake_download(url, a, b, dest):
                calls.append((a, b))
                if len(calls) == 2:
                    raise subprocess.CalledProcessError(1, "yt-dlp")
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                                "anullsrc=r=16000:cl=mono", "-t", "1", str(dest)], check=True)
                return dest

            with mock.patch.object(vods, "JOBS", jobs), mock.patch.object(live, "JOBS", jobs), \
                    mock.patch.object(vods, "load_streams", return_value=[{"name": "gaules-twitch",
                                                                           "url": "https://www.twitch.tv/gaules"}]), \
                    mock.patch.object(vods, "recent_vods", return_value=[{"id": "9", "url": "https://www.twitch.tv/videos/9"}]), \
                    mock.patch.object(vods, "ytdlp_json", return_value=info), \
                    mock.patch.object(vods, "download", side_effect=fake_download):
                out = vods.fetch_chunks(cfg, analyze=False)
                self.assertEqual(out["fetched"], ["live-vod-gaules-twitch-9-000000"])
                self.assertEqual(len(out["failed"]), 1)
                rec = state.load("vods")["9"]
                self.assertEqual(rec["done"], 1800.0)
                self.assertEqual(rec["failures"], {"1800-3600": 1})
                meta = json.loads((jobs / "live-vod-gaules-twitch-9-000000" / "job.json").read_text())
                self.assertEqual((meta["offset"], meta["channel"], meta["vod"]), (0.0, "Gaules", "9"))
                self.assertTrue((jobs / "live-vod-gaules-twitch-9-000000" / "live_ready").exists())
                with mock.patch.object(config, "PROFILE", "gta6"):
                    self.assertIn("live-vod-gaules-twitch-9-000000", live.ready_jobs())
                calls.clear()
                out = vods.fetch_chunks(cfg, analyze=False)  # next run: continues at 1800, never refetches 0-1800
                self.assertEqual(calls[0], (1800.0, 3600.0))

    def test_off_topic_vod_is_skipped(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"CLIPPER_STATE_DIR": d}):
            cfg = {"topic_patterns": ["\\bgta ?(6|vi)\\b"]}
            with mock.patch.object(vods, "load_streams", return_value=[{"name": "x", "url": "https://www.twitch.tv/x"}]), \
                    mock.patch.object(vods, "recent_vods", return_value=[{"id": "1", "url": "u"}]), \
                    mock.patch.object(vods, "ytdlp_json", return_value={"description": "Valorant ranked",
                                                                        "duration": 9000, "timestamp": 0}):
                out = vods.scan(cfg)
            self.assertEqual(out["chunks"], [])
            self.assertEqual(len(out["skipped_off_topic"]), 1)


if __name__ == "__main__":
    unittest.main()
