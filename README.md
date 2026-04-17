# semiconductor-design

AI agent-driven deep learning accelerator design, targeting MLPerf Tiny
workloads on SkyWater sky130A via Chipyard/Gemmini + OpenLane2.

See [design spec](docs/superpowers/specs/2026-04-17-semiconductor-design-agent-design.md)
for the full design rationale.

## Phase 1a — Wiki Skill Engine (done)

```bash
make install      # uv sync
make test         # pytest
uv run wiki-init --root wiki
uv run wiki-sync --root wiki
uv run wiki-lint --root wiki
```

## Next phases

| # | Sub-plan | Status |
|---|---|---|
| 1a | Wiki Skill Engine | ✅ done |
| 1b | Wiki Content Bootstrap | pending |
| 1c | Local EDA Smoke Tests | pending |
| 2 | AWS Foundation (CDK) | pending |
| 3 | Single-Candidate Flow | pending |
| 4 | Agent Orchestration | pending |
| 5 | Evolution Loop + Dashboard | pending |
| 6 | Baselines & Public Release | pending |

## Open decisions

Tracked in [issues/](issues/README.md).
