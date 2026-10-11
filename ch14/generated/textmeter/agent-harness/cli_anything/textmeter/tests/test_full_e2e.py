"""Execute the installed command against real files, including a TTY."""
import errno
import json
import os
from pathlib import Path
import pty
import select
import shutil
import subprocess
import time


def _resolve_cli(name):
    """Require PATH installation; never silently fall back to source code."""
    path = shutil.which(name)
    force = os.environ.get("CLI_ANYTHING_FORCE_INSTALLED") == "1"
    if not path:
        raise RuntimeError(f"Install {name}; force-installed={force}")
    print(f"[_resolve_cli] Using installed command: {path}")
    return [path]


class TestCLISubprocess:
    CLI_BASE = _resolve_cli("cli-anything-textmeter")

    def _run(self, args, data=None):
        return subprocess.run(self.CLI_BASE + args, input=data,
                              capture_output=True, text=True, timeout=10)

    def test_help(self):
        result = self._run(["--help"])
        assert result.returncode == 0 and "analyze" in result.stdout

    def test_chinese_path(self, tmp_path):
        source = tmp_path / "中文 空白.txt"
        source.write_text("AI 幫你工作。\n先檢查，再執行。\n\n保留成果。\n")
        result = self._run(["--json", "analyze", str(source)])
        assert result.returncode == 0
        assert json.loads(result.stdout)["data"] == dict(
            bytes=61, lines=4, nonempty_lines=3, paragraphs=2,
            nonspace_characters=20)

    def test_missing_argument(self):
        result = self._run(["--json", "analyze"])
        assert result.returncode == 2
        assert json.loads(result.stdout)["ok"] is False

    def test_bad_encoding(self, tmp_path):
        source = tmp_path / "bad.txt"
        source.write_bytes(b"\xff")
        result = self._run(["--json", "analyze", str(source)])
        assert result.returncode == 2
        assert json.loads(result.stdout)["error"]["code"] == "UnicodeDecodeError"

    def test_export_repeat_workflow(self, tmp_path):
        source, target = tmp_path / "a.txt", tmp_path / "report.json"
        source.write_bytes(b"A\n")
        args = ["--json", "export", str(source), "--output", str(target)]
        assert self._run(args).returncode == 0
        first = target.read_bytes()
        assert json.loads(first)["bytes"] == 2
        assert self._run(args).returncode == 2
        assert target.read_bytes() == first
        assert source.read_bytes() == b"A\n"
        print(f"Report: {target} ({len(first)} bytes)")

    def test_repl_continues_after_error(self, tmp_path):
        source = tmp_path / "a.txt"
        source.write_bytes(b"A")
        result = self._run([], f'bad-command\n--json analyze "{source}"\nquit\n')
        records = [json.loads(line) for line in result.stdout.splitlines()]
        assert result.returncode == 0
        assert [r["ok"] for r in records] == [False, True]

    def test_json_requires_command(self):
        result = self._run(["--json"])
        assert result.returncode == 2
        assert json.loads(result.stdout)["ok"] is False

    def test_tty_repl(self):
        master, slave = pty.openpty()
        process = subprocess.Popen(self.CLI_BASE, stdin=slave, stdout=slave,
                                   stderr=slave, env={**os.environ, "TERM": "dumb"})
        os.close(slave)
        captured = bytearray()
        try:
            os.write(master, b"\nhelp\nquit\n")
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                if select.select([master], [], [], 0.1)[0]:
                    try:
                        block = os.read(master, 65536)
                    except OSError as error:
                        if error.errno == errno.EIO:
                            break
                        raise
                    if not block:
                        break
                    captured.extend(block)
                if process.poll() is not None:
                    break
            assert process.wait(timeout=1) == 0, captured.decode(errors="replace")
            assert b"analyze" in captured and b"export" in captured
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            os.close(master)
