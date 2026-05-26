"""Built-in runners that shell out to the suite tools."""

from __future__ import annotations

import re
import shutil

from .orchestrator import Severity, SubcommandResult, shell_runner


def _missing(tool: str, hint: str) -> SubcommandResult:
    return SubcommandResult(name=tool, ok=False,
                            error=f"{tool} not installed (pip install {hint})")


def run_scan(target: str, args: list) -> SubcommandResult:
    if shutil.which("dns-doctor") is None:
        return _missing("dns-doctor", "dns-doctor")
    def parse(out: str):
        m = re.search(r"Overall:\s*([ABCDF][+-]?)", out)
        if not m:
            return Severity.INFO, 0, "no overall grade parsed"
        grade = m.group(1)
        sev = {"A": Severity.INFO, "B": Severity.LOW, "C": Severity.MEDIUM,
               "D": Severity.HIGH, "F": Severity.CRITICAL}[grade[0]]
        findings = len(re.findall(r"^\s*(F|D)\b", out, re.M))
        return sev, findings, f"dns-doctor overall: {grade}"
    return shell_runner(["dns-doctor", "audit", target, *args], name="scan", parse=parse)


def run_audit(target: str, args: list) -> SubcommandResult:
    if shutil.which("pipeline-armor") is None:
        return _missing("pipeline-armor", "pipeline-armor")
    def parse(out: str):
        m = re.search(r"(\d+)\s+blocking,\s+(\d+)\s+allowlisted", out)
        if not m:
            return Severity.INFO, 0, "no findings line"
        blocking = int(m.group(1))
        if blocking == 0:
            return Severity.INFO, 0, "clean"
        sev = Severity.LOW
        for label, s in (("CRITICAL", Severity.CRITICAL), ("HIGH", Severity.HIGH),
                          ("MED", Severity.MEDIUM), ("LOW", Severity.LOW)):
            if f"[{label}" in out:
                sev = max(sev, s)
        return sev, blocking, f"{blocking} blocking findings"
    return shell_runner(["pipeline-armor", "scan", target, *args], name="audit", parse=parse)


def run_phish(target: str, args: list) -> SubcommandResult:
    if shutil.which("phish-forge") is None:
        return _missing("phish-forge", "phish-forge")
    def parse(out: str):
        m = re.search(r"verdict:\s*(\w+)\s*\(score (\d+)/100\)", out, re.I)
        if not m:
            return Severity.INFO, 0, "no verdict line"
        verdict = m.group(1).lower()
        score = int(m.group(2))
        sev = {"phishing": Severity.HIGH, "suspicious": Severity.MEDIUM,
               "benign": Severity.INFO}.get(verdict, Severity.INFO)
        findings = len(re.findall(r"^\s+!\s", out, re.M))
        return sev, findings, f"{verdict.upper()} (score {score}/100, {findings} signals)"
    return shell_runner(["phish-forge", "analyze", target, *args], name="phish", parse=parse)


def run_ctf(target: str, args: list) -> SubcommandResult:
    if shutil.which("ctf") is None:
        return _missing("ctf-toolkit", "ctf-toolkit")
    parts = target.split() + args
    return shell_runner(["ctf", *parts], name="ctf")


def run_steg(target: str, args: list) -> SubcommandResult:
    if shutil.which("steg") is None:
        return _missing("steg-toolkit", "steg-toolkit")
    parts = target.split() + args
    return shell_runner(["steg", *parts], name="steg")
