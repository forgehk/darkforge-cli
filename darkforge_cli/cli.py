"""darkforge -- the one CLI to rule the suite."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .orchestrator import Orchestrator
from .runners import run_audit, run_ctf, run_phish, run_scan, run_steg


def _make_orchestrator() -> Orchestrator:
    o = Orchestrator()
    o.register("scan", run_scan)
    o.register("audit", run_audit)
    o.register("phish", run_phish)
    o.register("ctf", run_ctf)
    o.register("steg", run_steg)
    return o


GLYPH = {"INFO": ".", "LOW": ".", "MEDIUM": "!", "HIGH": "!!", "CRITICAL": "!!!"}


def _print(idx: int, total: int, r) -> None:
    status = " OK " if r.ok else "FAIL"
    if not r.ok:
        print(f"  [{idx}/{total}] {r.name:<8}  {status}  {r.error}")
    else:
        glyph = GLYPH.get(r.worst_severity.name, ".")
        print(f"  [{idx}/{total}] {r.name:<8}  {status}  {glyph} {r.summary}")


def main(argv=None) -> int:
    o = _make_orchestrator()
    p = argparse.ArgumentParser(prog="darkforge",
                                 description="Run the entire darkforge security suite.")
    sub = p.add_subparsers(dest="cmd", required=True)
    sc = sub.add_parser("scan"); sc.add_argument("target"); sc.add_argument("--out", type=Path, default=Path("./reports"))
    au = sub.add_parser("audit"); au.add_argument("path"); au.add_argument("--out", type=Path, default=Path("./reports"))
    ph = sub.add_parser("phish"); ph.add_argument("eml")
    ctf = sub.add_parser("ctf");  ctf.add_argument("rest", nargs=argparse.REMAINDER)
    st = sub.add_parser("steg"); st.add_argument("rest", nargs=argparse.REMAINDER)
    full = sub.add_parser("full"); full.add_argument("target"); full.add_argument("--out", type=Path, default=Path("./reports"))
    args = p.parse_args(argv)

    print(f"darkforge -- {args.cmd} {getattr(args, 'target', getattr(args, 'path', getattr(args, 'eml', '')))}\n")

    if args.cmd == "scan":
        r = o.run("scan", args.target); _print(1, 1, r)
        out = Orchestrator.write_report([r], args.target, args.out)
        print(f"\n  report: {out}"); return 0 if r.ok else 1
    if args.cmd == "audit":
        r = o.run("audit", args.path); _print(1, 1, r)
        out = Orchestrator.write_report([r], args.path, args.out)
        print(f"\n  report: {out}"); return 0 if r.ok else 1
    if args.cmd == "phish":
        r = o.run("phish", args.eml); _print(1, 1, r); return 0 if r.ok else 1
    if args.cmd == "ctf":
        rest = " ".join(args.rest) if args.rest else ""
        r = o.run("ctf", rest); _print(1, 1, r)
        if r.detail.get("stdout"): print("\n" + r.detail["stdout"])
        return 0 if r.ok else 1
    if args.cmd == "steg":
        rest = " ".join(args.rest) if args.rest else ""
        r = o.run("steg", rest); _print(1, 1, r)
        if r.detail.get("stdout"): print("\n" + r.detail["stdout"])
        return 0 if r.ok else 1
    if args.cmd == "full":
        if "/" in args.target or args.target.startswith("."):
            results = [o.run("audit", args.target)]
        else:
            results = [o.run("scan", args.target), o.run("audit", args.target)]
        for i, r in enumerate(results, 1): _print(i, len(results), r)
        grade = Orchestrator.aggregate_grade(results)
        print(f"\n  overall: {grade}")
        out = Orchestrator.write_report(results, args.target, args.out)
        print(f"  report:  {out}"); return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
