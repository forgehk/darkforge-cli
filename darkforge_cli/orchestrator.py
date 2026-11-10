"""Orchestrator -- runs each tool, aggregates results, computes overall grade."""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
from pathlib import Path
from typing import Any, Callable, Optional


class Severity(IntEnum):
    INFO = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    @property
    def grade(self) -> str:
        return {0: "A", 1: "A", 2: "B", 3: "D", 4: "F"}[self.value]

    @classmethod
    def from_name(cls, name: str) -> "Severity":
        try:
            return cls[name.upper()]
        except KeyError:
            return cls.INFO


@dataclass
class SubcommandResult:
    name: str
    ok: bool
    worst_severity: Severity = Severity.INFO
    findings_count: int = 0
    summary: str = ""
    detail: dict = field(default_factory=dict)
    error: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["worst_severity"] = self.worst_severity.name
        return d


class Orchestrator:
    """Registry + dispatcher of subcommand runners."""

    def __init__(self) -> None:
        self.runners: dict[str, Callable] = {}

    def register(self, name: str, runner: Callable) -> None:
        self.runners[name] = runner

    def run(self, name: str, target: str, args: Optional[list] = None) -> SubcommandResult:
        if name not in self.runners:
            return SubcommandResult(name=name, ok=False,
                                    error=f"no runner registered for {name!r}")
        try:
            return self.runners[name](target, args or [])
        except Exception as exc:
            return SubcommandResult(name=name, ok=False, error=str(exc))

    def run_many(self, names: list[str], target: str) -> list[SubcommandResult]:
        return [self.run(n, target) for n in names]

    @staticmethod
    def aggregate_grade(results: list[SubcommandResult]) -> str:
        oks = [r for r in results if r.ok]
        if not oks:
            return "?"
        return max(r.worst_severity for r in oks).grade

    @staticmethod
    def write_report(results: list[SubcommandResult], target: str, out_dir: Path) -> Path:
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
        safe = "".join(c if c.isalnum() else "_" for c in target).strip("_") or "scan"
        path = out_dir / f"{safe}-{ts}.json"
        path.write_text(json.dumps({
            "target": target, "ts": ts,
            "grade": Orchestrator.aggregate_grade(results),
            "results": [r.to_dict() for r in results],
        }, indent=2))
        return path


def shell_runner(cmd: list, *, name: str, parse=None) -> SubcommandResult:
    """Run cmd as subprocess; let parse normalise stdout into (severity, count, summary)."""
    try:
        completed = subprocess.run(cmd, capture_output=True, text=True,
                                    timeout=120, check=False)
    except FileNotFoundError as exc:
        return SubcommandResult(name=name, ok=False, error=f"command not found: {exc}")
    except subprocess.TimeoutExpired:
        return SubcommandResult(name=name, ok=False, error="timeout")
    out = completed.stdout
    error = ""
    if completed.returncode != 0:
        lines = completed.stderr.strip().splitlines()
        error = lines[-1] if lines else f"exit status {completed.returncode}"
    if parse is not None:
        severity, count, summary = parse(out)
    else:
        severity, count, summary = Severity.INFO, 0, (out.strip().splitlines()[0] if out.strip() else "")
    return SubcommandResult(
        name=name, ok=(completed.returncode == 0),
        worst_severity=severity, findings_count=count, summary=summary,
        detail={"stdout": out[:4000], "stderr": completed.stderr[:1000],
                "exit": completed.returncode},
        error=error,
    )
