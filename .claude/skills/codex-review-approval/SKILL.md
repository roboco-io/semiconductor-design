---
name: codex-review-approval
description: Use when a work product (spec, implementation plan, or code/diff) needs an objective review-and-approval gate before proceeding — e.g. after writing a spec in brainstorming, after writing-plans, or after a code change in subagent-driven development. Delegates the verdict to Codex via the Codex MCP server so the judge is a different engine than the author (separation of powers). Triggers on "Codex로 검토/승인해줘", "객관적으로 리뷰해줘", "이 spec/plan/코드 승인 게이트", or reaching any review gate where Claude would otherwise review its own output.
---

# Codex Review-Approval Gate

Objective review/approval of a work product, with the verdict produced by **Codex** (a different
engine than the author) so the reviewer is not the same model that wrote the artifact.

**Why Codex, not a Claude subagent:** this project's core principle is 생성자 ≠ 판정자 (separation
of powers). A Claude subagent reviewing Claude's output shares the author's blind spots. Routing the
verdict through Codex makes the gate adversarially independent — the same reason the autonomous loop
uses a Codex promotion reviewer (`src/pipeline/promotion_reviewer.py`).

## Prerequisite: Codex MCP connected

This skill calls the `mcp__codex__codex` tool. It is provided by the `codex mcp-server` registered in
`.mcp.json`. If the tool is unavailable:

1. Confirm registration: `claude mcp list` should show `codex` (it may say "Pending approval").
2. **The server activates only after a Claude Code session restart** (CLAUDE.md staleness invariant:
   `.mcp.json` changes do not take effect in the same session). Restart, approve the server, then retry.
3. Until then, do NOT silently fall back to a Claude self-review — that defeats the gate's purpose.
   Tell the Operator the gate needs a restart, or (only if the Operator explicitly accepts) use the
   CLI path `codex exec --skip-git-repo-check <prompt>` as a stopgap and label it as such.

## Checklist (create a TodoWrite item per step)

1. **Identify the artifact and its contract.** What is being reviewed (spec / plan / code-diff), and
   what is it accountable to? (a spec → the brainstorming intent + INTENT.md; a plan → its spec; a
   code change → its plan/spec + the frozen contract).
2. **Build the review prompt** (see Prompt Construction).
3. **Call `mcp__codex__codex`** with the prompt, `cwd` = repo root, `sandbox` = `read-only`,
   `approval-policy` = `never`. Let Codex read the files itself — pass paths, not pasted content,
   for anything already on disk.
4. **Parse the verdict** (last JSON line; failure/missing = conservative `block`).
5. **Act on the verdict** (see Acting on the Verdict). Report it to the Operator verbatim with reasons.

## Prompt Construction

The prompt has four parts. Keep it tight; Codex reads the repo itself.

1. **Role + independence:** "You are an independent review gate for the AutoResearch EDA-surrogate
   project. You did not write this artifact. Judge it on its own merits; default to blocking when
   uncertain. Statistical/numeric correctness of experiments is out of scope unless the artifact
   claims it."
2. **Artifact + sources (paths):** name the file(s) under review and the document(s) it must conform
   to. Tell Codex to read them from `cwd`.
3. **Criteria** — pick the block matching the artifact type (below), plus the project invariants.
4. **Output contract:** "After your analysis, emit on the LAST line a single-line JSON object and
   nothing after it: `{\"verdict\": \"approve\"|\"request_changes\"|\"block\", \"reasons\":
   \"<concise>\", \"must_fix\": [\"<item>\", ...]}`. `must_fix` is empty for approve."

### Artifact-type criteria

- **spec** (from brainstorming): Does it match the stated intent? Internally consistent (no section
  contradicts another)? Scoped to one implementation plan? Any placeholder/TBD/ambiguous requirement?
  Does it over-build (YAGNI)? Are success criteria / gate conditions pre-fixed (not post-hoc)?
- **plan** (from writing-plans): Does every spec requirement map to a task? Any placeholder steps
  ("add error handling" without code)? Type/signature consistency across tasks? Each step bite-sized
  and TDD-ordered? Frozen files left unmodified by the plan?
- **code / diff**: Does it implement exactly the plan/spec (nothing missing, nothing extra)? Silent
  failures or swallowed errors? Tests verify behavior, not mocks? Naming/clarity? Does it touch any
  frozen file it must not?

### Project invariants (always include)

- **Frozen contract:** `train.py`, `prepare.py`, `src/prepare_lib/`, and committed `dataset.jsonl`
  files are read-only. Changing the train.py contract (single file, no new deps, `--data/--out/--seed`
  CLI, 8 FEATURE_NAMES, stdout `{"val_mae"}`) is a block-level violation. (Experiment variant *copies*
  under `experiments/` are allowed.)
- **INTENT.md `Not`:** the artifact must not enable blind autonomy (merges without the objective
  gate), redefine spec-authority thresholds (INTENT/plans may *quote* spec numbers, not re-define
  them), or introduce metered LLM API calls (subscription CLI/MCP only).
- **Pre-fixed judgments:** gate/success conditions must be fixed before results are seen (gen-002
  false-positive lesson).

## Acting on the Verdict

- **approve** → report it, then proceed to the next workflow step (e.g. writing-plans after a spec,
  or marking a task complete in subagent-driven development).
- **request_changes** → surface each `must_fix` item; fix them (or dispatch the implementer to), then
  re-run this skill. Do not proceed past the gate with open `must_fix` items.
- **block** → stop. Report the reasons to the Operator and ask how to proceed; do not work around it.
- **Parse failure / no JSON / Codex error** → treat as `block` (conservative), exactly like
  `promotion_reviewer.review_promotion`. Never interpret an unparseable response as approval.

## Tool call shape (reference)

```
mcp__codex__codex(
  prompt: "<the constructed review prompt, paths not pasted content>",
  cwd: "/Users/dohyunjung/Workspace/roboco-io/research/semiconductor-design",
  sandbox: "read-only",
  approval-policy: "never"
)
```

Leave `model`/`profile` unset to use the Codex default (subscription). For a follow-up clarification
on the same review, use `mcp__codex__codex-reply` with the returned `conversationId`/`threadId`.

## Notes

- One artifact per invocation. Reviewing a spec and its plan are two separate gates.
- This is a *gate*, not a co-author: Codex judges, it does not rewrite. Fixes are made by the author
  (Claude / the implementer subagent) and then re-reviewed.
