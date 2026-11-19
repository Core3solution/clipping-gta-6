"""Tests for the Brazilian adaptation: gta-br profile, Portuguese hooks and censorship, encoder choice, Telegram
delivery/approval (against a local fake Bot API) and VOD chunk recovery (yt-dlp mocked)."""
import functools
import http.server
import json
import os
import subprocess
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
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

    def test_hls_master_and_media_playlists(self):
        master = ("#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=8000000,RESOLUTION=1920x1080\n1080p60/playlist.m3u8\n"
                  "#EXT-X-STREAM-INF:BANDWIDTH=3000000,RESOLUTION=1280x720\n720p60/playlist.m3u8\n")
        base = "https://cdn.example/x/master.m3u8"
        self.assertEqual(vods.pick_variant(master, base, 1080), "https://cdn.example/x/1080p60/playlist.m3u8")
        self.assertEqual(vods.pick_variant(master, base, 720), "https://cdn.example/x/720p60/playlist.m3u8")
        media = "#EXTM3U\n#EXTINF:10.000,\n0.ts\n#EXTINF:10.000,\n1.ts\n#EXTINF:4.5,\n2.ts\n#EXT-X-ENDLIST\n"
        segs = vods.parse_segments(media, "https://cdn.example/x/1080p60/playlist.m3u8")
        self.assertEqual([(s[0], s[1]) for s in segs], [(0.0, 10.0), (10.0, 10.0), (20.0, 4.5)])
        self.assertEqual(segs[2][2], "https://cdn.example/x/1080p60/2.ts")

    def test_hls_download_takes_exactly_the_range_without_reencoding(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "src"
            src.mkdir()
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=d=6:s=160x120:r=30",
                            "-f", "lavfi", "-i", "sine=d=6", "-c:v", "libx264", "-g", "30", "-c:a", "aac", "-f", "hls",
                            "-hls_time", "2", "-hls_playlist_type", "vod", str(src / "p.m3u8")], check=True)
            handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(src))
            handler.log_message = lambda *a: None
            srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
            threading.Thread(target=srv.serve_forever, daemon=True).start()
            self.addCleanup(srv.server_close)
            self.addCleanup(srv.shutdown)
            dest = Path(d) / "job" / "source.mp4"
            dest.parent.mkdir()
            vods.download_hls(f"http://127.0.0.1:{srv.server_port}/p.m3u8", 2, 6, dest)
            probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_name",
                                    "-of", "csv=p=0", str(dest)], capture_output=True, text=True).stdout
            self.assertIn("h264", probe)
            self.assertIn("aac", probe)
            self.assertAlmostEqual(float(probe.strip().splitlines()[-1]), 4.0, delta=0.2)
            self.assertFalse((dest.parent / "segments").exists())  # temporary segments cleaned up

    def test_kick_vods_start_at_vod_from_and_skip_older_broadcasts(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"CLIPPER_STATE_DIR": d}):
            cfg = {"topic_patterns": ["\\bgta ?(6|vi)\\b"], "vods": {"chunk_minutes": 30}}
            started = datetime(2026, 11, 18, 9, 32, 24, tzinfo=timezone.utc).timestamp()
            entries = [{"id": "kick-2", "url": "https://cdn/2/1080p60/playlist.m3u8", "page": "https://kick.com/d/videos/b",
                        "info": {"timestamp": started, "title": "GTA 6 GAMEPLAY", "is_live": True, "duration": 9000,
                                 "uploader": "Davy Jones"}},
                       {"id": "kick-1", "url": "https://cdn/1/1080p60/playlist.m3u8", "page": "https://kick.com/d/videos/a",
                        "info": {"timestamp": started - 86400, "title": "GTA 6 TA CHEGANDO", "is_live": False,
                                 "duration": 10540, "uploader": "Davy Jones"}}]
            stream = {"name": "davyjones-kick", "url": "https://kick.com/davyjones",
                      "vod_from": datetime(2026, 11, 18, 8, 0, tzinfo=timezone(timedelta(hours=-3)))}
            with mock.patch.object(vods, "load_streams", return_value=[stream]), \
                    mock.patch.object(vods, "kick_vods", return_value=entries) as kv:
                out = vods.scan(cfg, now=started + 9000)
            kv.assert_called_once_with("davyjones", 1080)
            self.assertEqual({c["vod"] for c in out["chunks"]}, {"kick-2"})  # the 16/11 broadcast ended before 08:00
            first = out["chunks"][0]
            self.assertEqual(first["start"], 5220.0)  # 08:00 is 5256 s in; floored to the minute, never later
            self.assertEqual((first["end"], first["page"], first["channel"]), (7020.0, "https://kick.com/d/videos/b",
                                                                                 "Davy Jones"))

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


def make_video(path, seconds, audio=True):
    """A small H.264 (+AAC) test file with a keyframe every 2 s, like a stream recording."""
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=s=160x90:r=30"]
    if audio:
        cmd += ["-f", "lavfi", "-i", "sine=f=440:r=48000", "-c:a", "aac"]
    cmd += ["-t", str(seconds), "-c:v", "libx264", "-preset", "ultrafast", "-g", "60", "-keyint_min", "60",
            "-sc_threshold", "0", str(path)]
    subprocess.run(cmd, check=True)
    return path


class ImportTests(unittest.TestCase):
    """clipper import: a local MP4 becomes live-vod jobs without touching the original."""

    def setUp(self):
        from clipper import imports
        self.imports = imports
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        env = mock.patch.dict(os.environ, {"CLIPPER_STATE_DIR": str(self.dir / "state")})
        env.start()
        self.addCleanup(env.stop)
        self.addCleanup(self.tmp.cleanup)

    def test_fingerprint_is_full_sha256_and_cached(self):
        import hashlib
        src = make_video(self.dir / "a.mp4", 4)
        fp = self.imports.fingerprint(src)
        self.assertEqual(fp["sha256"], hashlib.sha256(src.read_bytes()).hexdigest())
        self.assertEqual(fp["size"], src.stat().st_size)
        self.assertAlmostEqual(fp["duration"], 4.0, delta=0.2)
        with mock.patch.object(self.imports.hashlib, "sha256", side_effect=AssertionError("re-hashed")):
            self.assertEqual(self.imports.fingerprint(src), fp)  # same path, size and mtime: cached
            st = src.stat()
            os.utime(src, ns=(st.st_atime_ns, st.st_mtime_ns + 10**9))
            with self.assertRaises(AssertionError):
                self.imports.fingerprint(src)  # touched: hashed again

    def test_authorization_is_separate_from_live_yaml(self):
        prof = self.dir / "profiles" / "gta-br"
        prof.mkdir(parents=True)
        (prof / "authorizations.yaml").write_text(
            'davy-jones: {status: autorizado, evidencia: "DM no Instagram", data: "2026-11-17"}\n', encoding="utf-8")
        with mock.patch.object(config, "PROFILES", self.dir / "profiles"), \
                mock.patch.object(live, "load_streams", side_effect=AssertionError("live.yaml read")):
            self.assertEqual(self.imports.authorization("Davy Jones", "gta-br"),
                             {"status": "autorizado", "evidence": "DM no Instagram", "date": "2026-11-17"})
            self.assertEqual(self.imports.authorization("Paulinho o Loko", "gta-br")["status"], "pendente")

    def test_split_uses_real_cut_times(self):
        src = make_video(self.dir / "live.mp4", 50)
        blocks = self.imports.split(src, self.dir / "staging", chunk_s=12, from_s=7, duration=50)
        starts = [b["start"] for b in blocks]
        for got, want in zip(starts, [7, 19, 31, 43]):
            self.assertTrue(want <= got < want + 2.1, (got, want))  # cut on the first keyframe after the mark
        self.assertEqual(len(blocks), 4)
        for a, b in zip(blocks, blocks[1:]):
            self.assertAlmostEqual(a["end"], b["start"], places=3)  # contiguous: no gap, no overlap
        self.assertAlmostEqual(blocks[-1]["end"], 50, delta=0.2)
        for b in blocks:
            self.assertTrue(b["file"].exists())
            self.assertTrue(self.imports.av_check(b["file"])["ok"], b)

    def test_split_reuses_finished_staging(self):
        src = make_video(self.dir / "live.mp4", 20)
        first = self.imports.split(src, self.dir / "staging", chunk_s=8, from_s=0, duration=20)
        with mock.patch.object(self.imports.subprocess, "run", side_effect=AssertionError("ffmpeg ran again")):
            self.assertEqual(self.imports.split(src, self.dir / "staging", chunk_s=8, from_s=0, duration=20), first)

    def test_av_check_flags_missing_audio(self):
        src = make_video(self.dir / "mute.mp4", 3, audio=False)
        got = self.imports.av_check(src)
        self.assertFalse(got["ok"])
        self.assertEqual(got["reason"], "no audio")


if __name__ == "__main__":
    unittest.main()
