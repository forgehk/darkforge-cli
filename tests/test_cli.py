"""Tests for the CLI pass-through and subprocess error reporting."""

import subprocess

import pytest

from darkforge_cli import cli, runners
from darkforge_cli.orchestrator import shell_runner


class FakeRun:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr
        self.calls = []

    def __call__(self, cmd, **kwargs):
        self.calls.append(cmd)
        return subprocess.CompletedProcess(cmd, self.returncode,
                                           self.stdout, self.stderr)


@pytest.fixture
def fake_run(monkeypatch):
    fake = FakeRun(stdout="shift=13 -> Hello, World!\n")
    monkeypatch.setattr(runners.shutil, "which", lambda tool: "/usr/bin/" + tool)
    monkeypatch.setattr(subprocess, "run", fake)
    return fake


def test_ctf_keeps_quoted_argument_intact(fake_run, capsys):
    rc = cli.main(["ctf", "cipher", "caesar-brute", "Uryyb, Jbeyq!"])
    assert rc == 0
    assert fake_run.calls == [["ctf", "cipher", "caesar-brute", "Uryyb, Jbeyq!"]]
    assert "Hello, World!" in capsys.readouterr().out


def test_steg_keeps_paths_with_spaces(fake_run):
    cli.main(["steg", "extract", "my photo.png"])
    assert fake_run.calls == [["steg", "extract", "my photo.png"]]


def test_ctf_passes_flags_through(fake_run):
    cli.main(["ctf", "cipher", "caesar", "--shift", "3", "abc"])
    assert fake_run.calls == [["ctf", "cipher", "caesar", "--shift", "3", "abc"]]


def test_failure_reports_last_stderr_line(monkeypatch):
    fake = FakeRun(returncode=2, stderr="usage: ctf ...\nctf: error: unrecognized arguments: x\n")
    monkeypatch.setattr(subprocess, "run", fake)
    r = shell_runner(["ctf", "x"], name="ctf")
    assert not r.ok
    assert r.error == "ctf: error: unrecognized arguments: x"


def test_failure_without_stderr_reports_exit_status(monkeypatch):
    monkeypatch.setattr(subprocess, "run", FakeRun(returncode=3))
    r = shell_runner(["steg", "x"], name="steg")
    assert not r.ok and r.error == "exit status 3"


def test_success_has_no_error(monkeypatch):
    monkeypatch.setattr(subprocess, "run", FakeRun(stdout="ok\n", stderr="warning\n"))
    r = shell_runner(["ctf"], name="ctf")
    assert r.ok and r.error == "" and r.summary == "ok"
