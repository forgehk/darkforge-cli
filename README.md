# darkforge-cli

> One command to run the entire **darkforge** security suite against a target — DNS / TLS audit, secret-scan a repo, phishing-email analysis, CTF and steganography helpers. Wraps every other tool in the suite behind a single CLI.

[![CI](https://github.com/forgehk/darkforge-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/forgehk/darkforge-cli/actions/workflows/ci.yml) [![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg)]() [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## What it does

`darkforge-cli` is the conductor. It calls into each tool in the suite and aggregates results into a single graded report.

```bash
$ darkforge scan example.com

  darkforge -- full security scan of example.com

  [1/4] DNS / TLS / email-auth audit ......... B+
  [2/4] HTTP security headers ................. C
  [3/4] Domain look-alike / typosquat sweep .. clean
  [4/4] Common-phishing landing heuristics ... 2 risk flags

  overall grade: B-
  full report: ./reports/example.com-2026-05-17.json
```

Audit a Git repo for leaked secrets / vulnerable patterns:

```bash
$ darkforge audit ./my-app

  [1/3] secrets ............ 0 findings
  [2/3] insecure patterns .. 3 findings (1 high, 2 low)
  [3/3] dependencies ........ pip-audit: 2 CVEs

  blocking: yes (high-severity findings exceed policy)
```

Analyze a suspicious email:

```bash
$ darkforge phish suspicious.eml

  verdict: PHISHING (score 88/100)
  ! display name impersonation: 'PayPaI Security'
  ! SPF=fail, DMARC=fail
  ! 3 URLs flagged
```

Plus quick CTF and steg helpers. Everything after `ctf` or `steg` is handed to
the underlying tool unchanged, so quoted arguments and paths with spaces survive:

```bash
$ darkforge ctf cipher caesar-brute "Uryyb, Jbeyq! Guvf vf n frperg zrffntr."
darkforge -- ctf

  [1/1] ctf        OK   . shift=13 → Hello, World! This is a secret message.

shift=13 → Hello, World! This is a secret message.
```

When a wrapped tool exits non-zero, the last line of its stderr is shown next
to `FAIL` so you can see why it failed.

---

## Suite layout

```
                          +------------------+
                          |  darkforge-cli   |
                          +--------+---------+
                                   |
   +------------+--------------+---+---+-----------+------------+
   v            v              v       v           v            v
dns-doctor   pipeline-      phish-   ctf-       steg-      secret-
              armor          forge   toolkit    toolkit    rotator
```

Each tool is a standalone repo with its own CLI. `darkforge-cli` calls them via subprocess (so each tool can be `pip install`-ed independently or all together).

---

## Subcommands

| Subcommand | Wraps | What it does |
|---|---|---|
| `darkforge scan <domain>` | `dns-doctor` | DNS, TLS, SPF, DKIM, DMARC, HTTP security headers |
| `darkforge audit <path>` | `pipeline-armor` | Secrets, AST-based code patterns, dependency CVEs |
| `darkforge phish <eml>` | `phish-forge` | Header forensics, URL scoring, body heuristics |
| `darkforge ctf <verb>` | `ctf-toolkit` | Ciphers, encoders, hashes, frequency |
| `darkforge steg <verb>` | `steg-toolkit` | LSB hide/extract, image-strings, entropy, heatmap |
| `darkforge full <target>` | scan + audit | Combined report card |

---

## Install

```bash
# Whole suite
pip install darkforge-cli[all]

# Or pick subsets
pip install darkforge-cli           # core only
pip install darkforge-cli[scan]     # scan + audit
pip install darkforge-cli[ir]       # phishing + steg + ctf
```

---

## Why this exists

The other tools in the suite are deliberately small and single-purpose. `darkforge-cli` is what you actually want at 2 AM during an incident: one command, one log, one report.

It is also the interview demo - "I built five security tools and a sixth one that orchestrates them." Walks through real composition (subprocess + result-aggregation + reporting), real CLI design (argparse subcommand pattern), and a real product story (suite > tool).

---

## License

[MIT](LICENSE)

---

*Built by [@forgehk](https://github.com/forgehk) - [DarkForge AI](https://darkforgeai.com)*
