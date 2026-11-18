"""The development structure itself: hooks behave, settings are valid, skills and agents are well-formed."""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAUDE = ROOT / ".claude"
WIN = os.name == "nt"
VENV_BIN = "Scripts" if WIN else "bin"


def run_hook(name, event, env=None):
    return subprocess.run([sys.executable, str(CLAUDE / "hooks" / name)], input=json.dumps(event),
                          capture_output=True, text=True, encoding="utf-8", cwd=ROOT, timeout=60, env=env)


def load_hook(name):
    spec = importlib.util.spec_from_file_location(name, CLAUDE / "hooks" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class GuardHookTests(unittest.TestCase):
    def test_blocks_secrets_env_and_media(self):
        token = "1234567890:" + "A" * 35
        for event in ({"tool_name": "Write", "tool_input": {"file_path": "x.py", "content": f"T='{token}'"}},
                      {"tool_name": "Write", "tool_input": {"file_path": ".env", "content": "A=1"}},
                      {"tool_name": "Bash", "tool_input": {"command": "git add exports/gta-br/v.mp4"}},
                      {"tool_name": "Bash", "tool_input": {"command": "git add -A"}},
                      {"tool_name": "PowerShell", "tool_input": {"command": "git add jobs\\abc\\source.mp4"}},
                      {"tool_name": "PowerShell", "tool_input": {"command": "git add .\\jobs\\abc\\job.json"}},
                      {"tool_name": "Bash", "tool_input": {"command": "git add ./Exports/x/upload.json"}},
                      {"tool_name": "PowerShell", "tool_input": {"command": "git add 'C:\\p\\logs\\a.log'"}},
                      {"tool_name": "PowerShell", "tool_input": {"command": "git add ."}},
                      {"tool_name": "Write", "tool_input": {"file_path": "C:\\proj\\.env", "content": "A=1"}},
                      {"tool_name": "Edit", "tool_input": {"file_path": "k", "new_string": "-----BEGIN OPENSSH " + "PRIVATE KEY-----"}}):
            self.assertEqual(run_hook("guard.py", event).returncode, 2, event)

    def test_allows_normal_work(self):
        for event in ({"tool_name": "Write", "tool_input": {"file_path": "x.py", "content": "print('oi')"}},
                      {"tool_name": "Bash", "tool_input": {"command": "git add clipper/vods.py state/vods.json"}},
                      {"tool_name": "Bash", "tool_input": {"command": "python3 -m unittest discover -s tests"}}):
            self.assertEqual(run_hook("guard.py", event).returncode, 0, event)

    def test_stop_hook_never_loops_and_session_hook_prints_context(self):
        self.assertEqual(run_hook("verify_on_stop.py", {"stop_hook_active": True}).returncode, 0)
        out = run_hook("session_context.py", {"source": "startup"})
        self.assertEqual(out.returncode, 0)
        self.assertIn("Branch:", out.stdout)
        self.assertLess(len(out.stdout.splitlines()), 30)


class VenvHookTests(unittest.TestCase):
    """On the PC the deps live in .venv (uv sync); system python3 has none of them."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        (self.tmp / ".venv" / VENV_BIN).mkdir(parents=True)
        self.env = dict(os.environ, CLAUDE_PROJECT_DIR=str(self.tmp))
        self.env.pop("CLIPPER_SKIP_VERIFY", None)

    def test_session_hook_puts_venv_on_path_for_bash(self):
        env_file = self.tmp / "claude-env"
        for _ in range(2):  # resume/compact run it again: no duplicate line
            out = run_hook("session_context.py", {"source": "startup"}, env=dict(self.env, CLAUDE_ENV_FILE=str(env_file)))
            self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(len(env_file.read_text().splitlines()), 1)
        bash = shutil.which("bash")  # on Windows: Git Bash (System32\bash.exe would be WSL)
        sourced = subprocess.run([bash, "-c", f'. "{env_file.as_posix()}"; echo $VIRTUAL_ENV; echo $PATH; type -t python3'],
                                 capture_output=True, text=True).stdout.splitlines()
        self.assertEqual(sourced[0], str(self.tmp / ".venv"))
        bin_dir = load_hook("session_context").bash_path(self.tmp / ".venv" / VENV_BIN)
        self.assertTrue(sourced[1].startswith(f"{bin_dir}:"), sourced[1])
        if WIN:
            self.assertEqual(sourced[2], "function")  # python3 -> the venv's python, not the Store stub

    def test_bash_path_converts_windows_drives_only(self):
        bash_path = load_hook("session_context").bash_path
        self.assertEqual(bash_path("C:\\Users\\x\\proj\\.venv\\Scripts"), "/c/Users/x/proj/.venv/Scripts")
        self.assertEqual(bash_path("/home/x/proj/.venv/bin"), "/home/x/proj/.venv/bin")

    def test_stop_hook_picks_the_venv_python_of_either_os(self):
        venv_python = load_hook("verify_on_stop").venv_python
        self.assertEqual(venv_python(self.tmp), sys.executable)  # empty venv dir: falls back
        for rel in ("bin/python", "Scripts/python.exe"):
            with self.subTest(rel=rel):
                root = Path(tempfile.mkdtemp())
                self.addCleanup(shutil.rmtree, root)
                (root / ".venv" / rel).parent.mkdir(parents=True)
                (root / ".venv" / rel).write_text("")
                self.assertEqual(venv_python(root), str(root / ".venv" / rel))

    @unittest.skipIf(WIN, "the fake interpreter is a shell script")
    def test_stop_hook_runs_tests_with_venv_python(self):
        fake = self.tmp / ".venv" / "bin" / "python"
        fake.write_text("#!/bin/sh\necho VENV_PYTHON_USED >&2\nexit 1\n")
        fake.chmod(0o755)
        subprocess.run(["git", "init", "-q", str(self.tmp)], check=True)
        (self.tmp / "a.py").write_text("x = 1\n")
        out = run_hook("verify_on_stop.py", {}, env=self.env)
        self.assertEqual(out.returncode, 2)
        self.assertIn("VENV_PYTHON_USED", out.stderr)


class StructureTests(unittest.TestCase):
    def test_settings_valid_and_hook_scripts_exist(self):
        cfg = json.loads((CLAUDE / "settings.json").read_text(encoding="utf-8"))
        for entries in cfg["hooks"].values():
            for e in entries:
                for h in e["hooks"]:
                    for script in re.findall(r"\.claude/hooks/([\w.]+)", h["command"]):
                        self.assertTrue((CLAUDE / "hooks" / script).exists(), script)

    def test_hook_launcher_skips_the_store_stub_and_runs_python(self):
        sh = shutil.which("sh")
        if not sh:
            self.skipTest("no sh")
        out = subprocess.run([sh, str(CLAUDE / "hooks" / "python.sh"), "-c", "import sys; print(sys.version_info[0])"],
                             capture_output=True, text=True, timeout=30)
        self.assertEqual(out.stdout.strip(), "3", out.stderr)
        self.assertNotIn("\r", (CLAUDE / "hooks" / "python.sh").read_bytes().decode())  # sh chokes on CRLF
        json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))

    def test_skills_and_agents_are_well_formed(self):
        skills = [d for d in (CLAUDE / "skills").iterdir() if d.is_dir()]
        self.assertGreaterEqual(len(skills), 19)
        for d in skills:
            text = (d / "SKILL.md").read_text(encoding="utf-8")
            self.assertRegex(text, r"(?m)^name: ", d.name)
            self.assertRegex(text, r"(?m)^description:", d.name)
            self.assertTrue(list(d.glob("LICENSE*")), f"{d.name} sem licença")
            self.assertNotIn("superpowers:", text, d.name)
        for f in (CLAUDE / "agents").glob("*.md"):
            head = f.read_text(encoding="utf-8").split("---")[1]
            self.assertIn(f"name: {f.stem}", head)
            self.assertIn("description:", head)

    def test_rules_with_paths_have_frontmatter(self):
        for f in (CLAUDE / "rules").glob("*.md"):
            text = f.read_text(encoding="utf-8")
            if text.startswith("---"):
                self.assertIn("paths:", text.split("---")[1], f.name)


if __name__ == "__main__":
    unittest.main()
