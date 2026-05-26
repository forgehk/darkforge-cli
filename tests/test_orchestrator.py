"""Tests for the orchestrator (no subprocess; fake runners)."""

import json
from pathlib import Path

from darkforge_cli.orchestrator import Orchestrator, Severity, SubcommandResult


def fake_ok(sev, count=0, summary="ok"):
    def runner(target, args):
        return SubcommandResult(name="fake", ok=True, worst_severity=sev,
                                findings_count=count, summary=summary)
    return runner


def test_register_and_run():
    o = Orchestrator()
    o.register("scan", fake_ok(Severity.LOW))
    r = o.run("scan", "example.com")
    assert r.ok and r.worst_severity == Severity.LOW


def test_unregistered_returns_failure():
    r = Orchestrator().run("nope", "x")
    assert not r.ok and "no runner" in r.error


def test_exception_caught():
    o = Orchestrator()
    def boom(target, args):
        raise RuntimeError("kaboom")
    o.register("scan", boom)
    r = o.run("scan", "x")
    assert not r.ok and "kaboom" in r.error


def test_severity_grade():
    assert Severity.INFO.grade == "A"
    assert Severity.MEDIUM.grade == "B"
    assert Severity.HIGH.grade == "D"
    assert Severity.CRITICAL.grade == "F"


def test_aggregate_uses_worst_ok():
    rs = [SubcommandResult("a", ok=True, worst_severity=Severity.LOW),
          SubcommandResult("b", ok=True, worst_severity=Severity.HIGH),
          SubcommandResult("c", ok=True, worst_severity=Severity.MEDIUM)]
    assert Orchestrator.aggregate_grade(rs) == "D"


def test_aggregate_ignores_failures():
    rs = [SubcommandResult("a", ok=True, worst_severity=Severity.LOW),
          SubcommandResult("b", ok=False, error="missing")]
    assert Orchestrator.aggregate_grade(rs) == "A"


def test_write_report(tmp_path: Path):
    rs = [SubcommandResult("scan", ok=True, worst_severity=Severity.MEDIUM,
                            findings_count=2, summary="2 findings")]
    out = Orchestrator.write_report(rs, "example.com", tmp_path)
    data = json.loads(out.read_text())
    assert data["target"] == "example.com" and data["grade"] == "B"
    assert len(data["results"]) == 1


def test_run_many():
    o = Orchestrator()
    o.register("a", fake_ok(Severity.LOW, summary="ran-a"))
    o.register("b", fake_ok(Severity.MEDIUM, summary="ran-b"))
    assert [r.summary for r in o.run_many(["a", "b"], "x")] == ["ran-a", "ran-b"]


def test_severity_from_name():
    assert Severity.from_name("high") == Severity.HIGH
    assert Severity.from_name("CRITICAL") == Severity.CRITICAL
    assert Severity.from_name("?") == Severity.INFO
