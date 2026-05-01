# Repository Guidelines

## Project Structure & Module Organization

This repository contains the semiconductor-design research runner and supporting
knowledge graph workflow. Python source lives in `src/semi_design_runner/`, with
modules for the L1 runner CLI, AWS wrappers, lockfile verification, metric
collection, L2 recall/confidence helpers, and validation. CDK infrastructure lives
in `cdk/`, Docker runner images in `docker/`, executable scripts in `scripts/`,
spec inputs in `specs/`, tests in `tests/`, and research/planning material in
`docs/`, `issues/`, and `wiki/raw/`.

## Build, Test, and Development Commands

- `make install`: install runtime and development dependencies with `uv sync --all-extras`.
- `make test`: run the full pytest suite, including Docker tests when Docker and real pins are available.
- `make lint`: run Ruff checks on `src`, `tests`, and `scripts`.
- `make fmt`: format Python files with Ruff.
- `make clean`: remove pytest, Ruff, build, egg-info, and `__pycache__` artifacts.
- `uv run semi-run --help`: inspect the L1 runner CLI.
- `uv run semi-run lockfile-verify --scope l1`: verify L1 lockfile pins and emit the L1 cache hash.
- `uv run semi-confidence --help`: inspect graph confidence tooling.
- `cd cdk && npm test -- --runInBand`: run the CDK/Jest test suite.
- `make graph-update`: refresh the graphify index from the local corpus.
- `make graph-lint`: validate graph integrity thresholds.

## Coding Style & Naming Conventions

Use Python 3.12 idioms, type hints where they clarify interfaces, and 4-space
indentation. Ruff is the formatter and linter; keep lines at or below 100
characters per `pyproject.toml`. Name Python modules and functions in
`snake_case`, classes in `PascalCase`, and CLI entry points with the existing
`semi-*` pattern. Prefer small, focused functions and reuse existing helpers
before adding new layers.

For CDK TypeScript, follow the existing stack-per-boundary layout under
`cdk/lib/stacks/`. Keep generated snapshots intentional and review changes to
`cdk/test/__snapshots__/` carefully.

## Testing Guidelines

Use pytest for Python. Add or update tests in `tests/` for behavior changes,
especially for CLI workflows, lockfile behavior, AWS wrapper calls, Docker
entrypoint contracts, L2 recall/confidence, graph integrity, and metric parsing.
Test files should be named `test_<feature>.py`, and test functions should start
with `test_`. Use `tmp_path` and fixtures instead of writing into real artifact
or wiki trees.

Docker tests under `tests/docker/` require a local Docker daemon and real
lockfile pins. They are marked `slow` and `requires_real_lockfile`; keep them
skippable when the lockfile is intentionally in dry-run state.

Run `make lint`, the relevant pytest subset, and `cd cdk && npm test -- --runInBand`
before submitting infrastructure or runner changes.

## Commit & Pull Request Guidelines

Follow the existing conventional style: `docs: ...`, `chore: ...`, or a concise
scope such as `fix(runner): ...` / `test(docker): ...`. Use an imperative
subject. Pull requests should describe the change, explain why it is needed,
link relevant files or issues under `issues/`, and include test or lint results.
Include screenshots only for future UI or dashboard work.

## Security & Configuration Tips

Do not commit virtual environments, caches, generated build artifacts, or local
settings such as `.claude/settings.local.json`. Keep generated or experimental
files out of version control unless they are intentionally part of `docs/`,
`issues/`, `wiki/raw/`, `graphify-out/`, or another reviewed artifact path.

AWS resource names should follow the CDK convention: S3 bucket
`semi-design-${account}-${region}` and DynamoDB tables
`semi-design-${env}-{Runs|Generations|Candidates|Events}`. Prefer explicit CLI
options or environment variables when operating outside the default `dev`
environment.
