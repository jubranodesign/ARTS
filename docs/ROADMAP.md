# Roadmap (ideas — not implemented)

ARTS is **early open source**. Items below are **directions for discussion and contribution**, not commitments or current features.

## In scope today

See [README](../README.md), [ARCHITECTURE](ARCHITECTURE.md), and [TARGET_REPO](TARGET_REPO.md).

## Near-term engineering (fits the current repo)

| Idea | Notes |
|------|--------|
| **Retrieval eval alignment** | Match keywords against `metadata.source_code` or document eval as Chroma-only |
| **Isolated test executor** | Per-run venv/container: clone `REPO_PATH`, `pip install`, run pytest, tear down |
| **Checkpoint-aware repair** | Optional revert to last passing checkpoint (not in graph today) |
| **CI smoke** | ingest + agent smoke on a fixture repo |
| **Multi-language profiles** | Extend `REPO_LANGUAGE` beyond splitter: scanner extensions, prompts, test runner (`ARTS_FULLY_SUPPORTED_LANGUAGES`) |

## Longer-term product ideas (community input)

### Security: static analysis → dynamic attack

Pain point: teams want **SAST-style understanding of code** connected to **exercises against a running system** (DAST / guided pen-test), often as a **CI or IDE plugin** — “test ourselves before attackers do.”

ARTS **does not** implement this today. A plausible evolution (separate from pytest generation):

1. Analyze repo / deps / entrypoints (static).
2. Derive attack scenarios or API probes from that model.
3. Run against a **staging** environment with strict isolation and policy gates.

Any implementation would need clear **scope, consent, and sandbox** rules — not production targets by default.

### Other

- Plugin packaging for CI (ingest + policy + report only).
- Stronger cost/latency metrics for the ML risk gate (benchmarks on real monorepos).

## What we are not building (by default)

- A hosted SaaS replacement for Cursor / Claude Code / Codex for daily coding.
- Unauthenticated scanning of third-party systems.

Contributions and issues welcome on [GitHub](https://github.com/jubranodesign/ARTS).
