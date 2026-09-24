# Repository Guidelines

## Project Structure & Module Organization

This repository manages research into semiconductor design tools and models; implementation code and tests belong in separate track repositories.

- `tracks/`: A-run-tracker, B-sta-analyzer, C-flow-doctor, and D-irdrop research. Keep each track’s `plan.md`, `protocol.md`, `results.md`, and `tutorial.md` together.
- `tracks/INFRA-0/environment.md`: local EDA setup and smoke-test instructions.
- `research-tree.yaml` and `research-log.md`: authoritative hypothesis status and chronological decisions.
- `literature/survey.md` and `literature/raw/`: synthesis and supporting evidence.
- `issues/`: open decisions, named like `001-build-target-selection-brief.md`.
- `.claude/skills/`: research workflows and supporting templates.

Do not add new work to the retired `plans/` or `experiments/` directories. Consult `CLAUDE.md` and `tracks/README.md` for operating rules.

## Build, Test, and Development Commands

There is no repository-wide application build, test runner, or configured formatter.

- `git diff --check`: check changed files for whitespace errors before committing.
- `git diff --stat`: review change scope.
- `python3 .claude/skills/meta-research/templates/render-tree.py . --output /tmp/research-tree.html`: preview the research dashboard without adding generated output to the repository.

Run implementation tests in the relevant track repository. For EDA validation, follow the environment document; noninteractive LibreLane execution requires `--docker-no-tty` before `--dockerized`.

## Style & Naming Conventions

Preserve the existing Korean narrative and technical English identifiers. Use descriptive Markdown headings, relative links, fenced command examples, and dated research entries. Match surrounding YAML indentation; use four-space indentation in Python helpers. Retain established track names and lowercase, hyphenated document filenames.

## Validation & Research Integrity

Verify links, cited evidence, and consistency between results, hypothesis status, and logs. No central coverage threshold or test naming convention is configured here; use each implementation repository’s requirements.

Lock protocol criteria before implementation and result inspection. Never revise thresholds retrospectively; label deviations `EXPLORATORY`. Record negative results. Update the track tutorial’s experiment diary when recording judgments or major milestones.

## Commit & Pull Request Guidelines

The documented workflow uses direct commits to `main`. Follow history’s prefixes: `docs:`, `chore:`, `research(plan):`, and `research(results):`, with imperative subjects. Keep plans and results in separate commits; commit tutorial updates separately as `docs(tutorial):`.

If opening a PR, describe the affected track, link relevant decisions, and report validation evidence. Exclude secrets, virtual environments, and generated EDA artifacts according to `.gitignore`.
