# 루프 환류 — 교차설계 LODO 게이트 편입 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** AutoResearch 자동 게이트에 교차설계 LODO 게이트를 T1 앞에 추가하고(부분 실패 fold까지 차단), 루프 dataset을 3설계 혼합본으로 교체하며, 세대 리포트·program.md에 일반화 관찰을 노출한다.

**Architecture:** `run_crossdesign_gate`(순수 probe)는 무변경. 실패 fold 차단 정책은 **orchestrator 게이트 층**에 둔다(`n_valid < n_designs` → `rejected_lodo`). 판정 체인은 median → **LODO** → T1 → Codex. `render_generation_report`는 `lodo_report=None` 추가로 하위 호환. Makefile·program.md는 운영/문서 변경.

**Tech Stack:** Python 3.12 (uv), pytest, 기존 `src/pipeline/{orchestrator,report,validation}.py`.

**Spec:** `docs/superpowers/specs/2026-06-12-loop-crossdesign-integration-design.md` (Codex 검토 approve).

**공통 규칙 (모든 task):**
- frozen 파일(`train.py`, `prepare.py`, `src/prepare_lib/`, 커밋된 `dataset.jsonl`) 수정 금지. `make fmt`가 frozen을 재포맷하면 `git restore`로 복원하고 in-scope만 커밋.
- 커밋 전 `uv run pytest -q` green 필수. ruff line-length 100.
- pytest `pythonpath = ["src", "."]` → `from pipeline.X import ...` 바로 가능.

---

## File 구조

| 파일 | 변경 | 책임 |
|---|---|---|
| `src/pipeline/report.py` | modify | `render_generation_report`에 `lodo_report=None` 섹션 추가(하위 호환) |
| `src/pipeline/orchestrator.py` | modify | T1 앞 LODO 게이트 + 실패-fold 차단 + `lodo_gate_fn` 주입점 + generation.json 필드 |
| `tests/pipeline/test_gen_report.py` | modify | LODO 섹션 유/무 렌더 테스트 |
| `tests/pipeline/test_orchestrator.py` | modify | LODO 분기 신규 테스트 + 기존 auto 테스트에 통과형 LODO stub 주입 |
| `Makefile` | modify | `loop`의 `DATASET` 기본값 → 3설계 혼합본 |
| `program.md` | modify | 다설계 입력 설명 + 관찰 힌트(지시 아님) |

---

### Task 1: report.py — LODO 섹션 (하위 호환 파라미터)

**Files:**
- Modify: `src/pipeline/report.py`
- Modify: `tests/pipeline/test_gen_report.py`

- [ ] **Step 1: 실패 테스트 추가** (test_gen_report.py 끝에)

```python
def test_report_includes_lodo_section_when_provided():
    md = render_generation_report(
        gen_no=4,
        ranking=[("cand-001", "codex", "moderate", 0.099)],
        winner_id="cand-001",
        t1_report="T1: distinguishable",
        codex_verdict={"approve": True, "reasons": "ok"},
        decision="promoted",
        lodo_report="LODO-SENTINEL-XYZ",
    )
    assert "LODO-SENTINEL-XYZ" in md  # LODO 섹션 본문
    assert "교차설계" in md  # LODO 섹션 제목
    # LODO 섹션은 T1 섹션보다 앞에 온다 (게이트 순서와 동일)
    assert md.index("LODO-SENTINEL-XYZ") < md.index("T1: distinguishable")


def test_report_omits_lodo_section_when_none():
    md = render_generation_report(
        gen_no=4,
        ranking=[("cand-001", "codex", "moderate", 0.099)],
        winner_id="cand-001",
        t1_report="T1: distinguishable",
        codex_verdict={"approve": True, "reasons": "ok"},
        decision="promoted",
    )
    assert "교차설계" not in md
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/pipeline/test_gen_report.py -q`
Expected: FAIL — `render_generation_report() got an unexpected keyword argument 'lodo_report'`.

- [ ] **Step 3: report.py 교체**

`render_generation_report` 함수 전체(현 9–33행)를 아래로 교체:

```python
def render_generation_report(
    gen_no, ranking, winner_id, t1_report, codex_verdict, decision, lodo_report=None
) -> str:
    """ranking: [(id, sdk, strategy, median_val_mae), ...] (낮을수록 좋음, 정렬됨).

    lodo_report 가 주어지면 교차설계 LODO 게이트 섹션을 T1 섹션 앞에 삽입한다(게이트 순서와 동일).
    None 이면 생략 — 단일 설계 dataset·하위 호환.
    """
    rank_lines = ["| 후보 | sdk | 전략 | median_val_mae |", "|---|---|---|---|"]
    for cid, sdk, strat, mae in ranking:
        mark = " ⭐" if cid == winner_id else ""
        rank_lines.append(f"| {cid}{mark} | {sdk} | {strat} | {mae:.4f} |")
    codex_body = (
        f"- approve: **{codex_verdict.get('approve')}**\n"
        f"- 사유: {codex_verdict.get('reasons', '')}"
    )
    rule_body = (
        "median 선택 → LODO 통과 → T1 `distinguishable` **AND** Codex `approve` → "
        "자동 승격(train.py·tag).\n"
        "사람은 `program.md` 방향만 — per-winner 승인 없음(2026-06-08 재피벗)."
    )
    sections = [("후보 순위 (median val_mae, 낮을수록 좋음)", "\n".join(rank_lines))]
    if lodo_report is not None:
        sections.append(("교차설계 LODO 게이트 (held-out 설계 일반화)", lodo_report))
    sections += [
        ("T1 통계 게이트 (winner vs 현 baseline)", t1_report),
        ("Codex 승격 심사관 (무결성·안전·품질)", codex_body),
        ("승격 규칙", rule_body),
    ]
    L = [
        f"# gen-{gen_no:03d} 리포트 (자율 승격 게이트)",
        "",
        f"**최종 결정: {decision}**  ·  winner: `{winner_id}`",
        "",
    ]
    for i, (title, body) in enumerate(sections, 1):
        L.append(f"## {i}) {title}")
        L.append(body)
        L.append("")
    return "\n".join(L).rstrip("\n")
```

- [ ] **Step 4: 통과 확인**

Run: `uv run pytest tests/pipeline/test_gen_report.py -q`
Expected: 3 passed (기존 1 + 신규 2).

- [ ] **Step 5: 커밋**

```bash
uv run ruff check src/pipeline/report.py tests/pipeline/test_gen_report.py
git add src/pipeline/report.py tests/pipeline/test_gen_report.py
git commit -m "feat(report): 세대 리포트에 LODO 게이트 섹션(lodo_report=None, 하위 호환) — 루프 환류 Task 1"
```

---

### Task 2: orchestrator.py — LODO 게이트 (T1 앞, 실패-fold 차단)

**Files:**
- Modify: `src/pipeline/orchestrator.py`
- Modify: `tests/pipeline/test_orchestrator.py`

- [ ] **Step 1: 신규 LODO 테스트 + stub 헬퍼 추가** (test_orchestrator.py 끝에)

```python
def _stub_lodo(verdict, n_valid=2, n_designs=2):
    """run_crossdesign_gate 모양의 결과를 돌려주는 주입형 게이트(실학습 없음)."""

    def gate(winner_train_py, baseline_train_py, rows, workdir, **kw):
        return {
            "single_design": False,
            "n_designs": n_designs,
            "n_valid": n_valid,
            "n_winner_better": 1,
            "n_baseline_better": 0,
            "mean_gap": -0.1,
            "per_design": [
                {"design": "gcd", "winner_mae": 0.2, "baseline_mae": 0.3,
                 "naive_mae": 1.4, "valid": True},
                {"design": "ibex", "winner_mae": 0.2, "baseline_mae": 0.3,
                 "naive_mae": 1.4, "valid": True},
            ],
            "verdict": verdict,
        }

    return gate


def _dataset_single(tmp_path):
    # 단일 설계 dataset — LODO 생략 경로 검증용.
    rows = [
        {
            "endpoint": f"e{i}", "startpoint": f"s{i}", "num_stages": 2 + i % 5,
            "synth_slack_ns": 0.4 - (i % 6) * 0.1, "synth_arrival_ns": 0.3 + (i % 4) * 0.2,
            "max_stage_delay_ns": 0.1 + (i % 3) * 0.15, "mean_stage_delay_ns": 0.05 + (i % 3) * 0.05,
            "startpoint_is_ff": i % 2, "endpoint_is_ff": 1,
            "path_group": "clk" if i % 2 else "clk2",
            "post_route_slack_ns": 0.5 - (i % 7) * 0.1, "group_key": "gcd",
        }
        for i in range(50)
    ]
    p = tmp_path / "ds_single.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return p


def _spy_t1_gate():
    calls = []

    def gate(winner_train_py, baseline_train_py, rows, workdir, **kw):
        calls.append(1)
        return _stub_gate("distinguishable")(winner_train_py, baseline_train_py, rows, workdir)

    return gate, calls


def test_auto_gate_rejected_lodo_worse(tmp_path):
    t1_gate, t1_calls = _spy_t1_gate()
    codex_calls = []
    run_generation(
        gen_no=4, dataset=_dataset(tmp_path), baseline_train_py=_tmp_baseline(tmp_path),
        program_md="opt", n=2, gen_fn=_mock_gen, out_root=tmp_path / "gl",
        auto=True, gate_fn=t1_gate, lodo_gate_fn=_stub_lodo("worse"),
        reviewer_fn=lambda p: codex_calls.append(1) or '{"approve": true, "reasons": "x"}',
        do_git=False,
    )
    gen = json.loads((tmp_path / "gl" / "gen-004" / "generation.json").read_text())
    assert gen["status"] == "rejected_lodo"
    assert gen["lodo_verdict"] == "worse"
    assert t1_calls == []  # LODO 차단 → T1 미호출(fail-fast)
    assert codex_calls == []  # Codex 미호출
    assert "교차설계" in (tmp_path / "gl" / "gen-004" / "report.md").read_text()


def test_auto_gate_rejected_lodo_partial_fail(tmp_path):
    # Codex 검토가 잡은 안전 구멍의 회귀 가드: verdict는 통과형(mixed)이나 일부 fold 실패.
    t1_gate, t1_calls = _spy_t1_gate()
    run_generation(
        gen_no=4, dataset=_dataset(tmp_path), baseline_train_py=_tmp_baseline(tmp_path),
        program_md="opt", n=2, gen_fn=_mock_gen, out_root=tmp_path / "gp",
        auto=True, gate_fn=t1_gate,
        lodo_gate_fn=_stub_lodo("mixed", n_valid=1, n_designs=2),
        reviewer_fn=lambda p: '{"approve": true, "reasons": "x"}', do_git=False,
    )
    gen = json.loads((tmp_path / "gp" / "gen-004" / "generation.json").read_text())
    assert gen["status"] == "rejected_lodo"  # 부분 실패 → 차단
    assert t1_calls == []  # T1 미호출


def test_auto_gate_rejected_lodo_unverifiable(tmp_path):
    # 전 fold 실패(n_valid==0) → 함수가 unverifiable 반환 → 차단(spec §7 enumerated).
    t1_gate, t1_calls = _spy_t1_gate()
    run_generation(
        gen_no=4, dataset=_dataset(tmp_path), baseline_train_py=_tmp_baseline(tmp_path),
        program_md="opt", n=2, gen_fn=_mock_gen, out_root=tmp_path / "gu",
        auto=True, gate_fn=t1_gate,
        lodo_gate_fn=_stub_lodo("unverifiable", n_valid=0, n_designs=2),
        reviewer_fn=lambda p: '{"approve": true, "reasons": "x"}', do_git=False,
    )
    gen = json.loads((tmp_path / "gu" / "gen-004" / "generation.json").read_text())
    assert gen["status"] == "rejected_lodo"
    assert gen["lodo_verdict"] == "unverifiable"
    assert t1_calls == []  # T1 미호출


def test_auto_gate_lodo_mixed_proceeds_to_t1(tmp_path):
    baseline = _tmp_baseline(tmp_path)
    before = baseline.read_bytes()
    run_generation(
        gen_no=4, dataset=_dataset(tmp_path), baseline_train_py=baseline,
        program_md="opt", n=2, gen_fn=_marker_gen, out_root=tmp_path / "gm",
        auto=True, gate_fn=_stub_gate("distinguishable"), lodo_gate_fn=_stub_lodo("mixed"),
        reviewer_fn=lambda p: '{"approve": true, "reasons": "ok"}', do_git=False,
    )
    gen = json.loads((tmp_path / "gm" / "gen-004" / "generation.json").read_text())
    assert gen["status"] == "promoted"  # mixed + 전 fold 유효 → T1·Codex 통과
    assert gen["lodo_verdict"] == "mixed"
    assert baseline.read_bytes() != before


def test_auto_gate_single_design_skips_lodo(tmp_path):
    # 단일 설계면 LODO 생략 — 실제 run_crossdesign_gate(주입 안 함)는 <2설계서 ValueError이므로
    # 이 테스트가 통과한다는 것 자체가 "LODO 미호출"을 증명한다.
    run_generation(
        gen_no=4, dataset=_dataset_single(tmp_path), baseline_train_py=_tmp_baseline(tmp_path),
        program_md="opt", n=2, gen_fn=_marker_gen, out_root=tmp_path / "gs",
        auto=True, gate_fn=_stub_gate("distinguishable"),
        reviewer_fn=lambda p: '{"approve": true, "reasons": "ok"}', do_git=False,
    )
    gen = json.loads((tmp_path / "gs" / "gen-004" / "generation.json").read_text())
    assert gen["status"] == "promoted"
    assert gen["lodo_verdict"] is None  # LODO 생략
    assert "교차설계" not in (tmp_path / "gs" / "gen-004" / "report.md").read_text()
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/pipeline/test_orchestrator.py -q`
Expected: FAIL — 신규 테스트가 `lodo_gate_fn` 미지원으로 `TypeError: run_generation() got an unexpected keyword argument 'lodo_gate_fn'`.

- [ ] **Step 3: orchestrator import 확장**

`src/pipeline/orchestrator.py` 상단 import 교체:

```python
from pipeline.validation import render_validation_report, run_validation_gate
```
→
```python
from pipeline.validation import (
    render_crossdesign_report,
    render_validation_report,
    run_crossdesign_gate,
    run_validation_gate,
)
```

- [ ] **Step 4: run_generation 시그니처에 lodo_gate_fn 추가**

`def run_generation(...)` 키워드 인자 블록에서 `gate_fn=None,` 아래 줄에 추가:

```python
    *,
    auto=False,
    gate_fn=None,
    lodo_gate_fn=None,
    reviewer_fn=None,
    do_git=True,
```

- [ ] **Step 5: auto 블록을 LODO 게이트 포함으로 교체**

현재 `status = "awaiting_operator"` 부터 `(gdir / "report.md").write_text(...)` 까지의 블록을 아래로 교체:

```python
    status = "awaiting_operator"
    lodo_res = None
    if auto and winner is None:
        status = "no_winner"
    if auto and winner is not None:
        rows = [json.loads(line) for line in Path(dataset).read_text().splitlines() if line.strip()]

        # --- LODO 교차설계 게이트 (T1 앞, 설계 ≥2일 때만) ---
        lodo_report = None
        if len({r["group_key"] for r in rows}) >= 2:
            lgate = lodo_gate_fn or run_crossdesign_gate
            with tempfile.TemporaryDirectory(prefix=f"lodo-gen{gen_no:03d}-") as _ldir:
                lodo_res = lgate(Path(winner.src_path), Path(baseline_train_py), rows, Path(_ldir))
            lodo_report = render_crossdesign_report(lodo_res)

        # 실패 fold(부분 포함) 또는 worse/unverifiable → 차단(T1·Codex 생략, fail-fast).
        # "모든 fold가 유효해야 함"은 승격 게이트 정책 — probe 함수가 아니라 호출자(여기)가 강제.
        lodo_blocked = lodo_res is not None and (
            lodo_res["n_valid"] < lodo_res["n_designs"]
            or lodo_res["verdict"] in ("worse", "unverifiable")
        )

        if lodo_blocked:
            status = "rejected_lodo"
            t1_report = "LODO 게이트 미통과 — T1 생략."
            codex_verdict = {"approve": False, "reasons": "LODO 미통과 — 심사 생략"}
        else:
            gate = gate_fn or run_validation_gate
            # T1 fold 작업물(50 fold × jsonl/joblib, 100MB+)은 임시 — tempdir에 쓰고 자동 정리.
            with tempfile.TemporaryDirectory(prefix=f"t1-gen{gen_no:03d}-") as _t1dir:
                t1 = gate(Path(winner.src_path), Path(baseline_train_py), rows, Path(_t1dir))
            t1_report = render_validation_report(t1)
            verdict = t1.get("verdict_vs_baseline")
            codex_verdict = {"approve": False, "reasons": "T1 미통과 — 심사 생략"}
            if verdict == "distinguishable":
                winner_src = Path(winner.src_path).read_text(encoding="utf-8")
                baseline_src_now = Path(baseline_train_py).read_text(encoding="utf-8")
                rfn = reviewer_fn
                if rfn is None:
                    from pipeline.sdk import codex_review_fn as rfn  # 실제 Codex (구독)
                codex_verdict = review_promotion(
                    winner_src, baseline_src_now, t1_report, reviewer_fn=rfn
                )
                if codex_verdict["approve"]:
                    operator_gate.promote(
                        Path(winner.src_path),
                        Path(baseline_train_py),
                        gen_no,
                        approved=True,
                        do_git=do_git,
                    )
                    status = "promoted"
                else:
                    status = "rejected_codex"
            else:
                status = "rejected_t1"

        report_md = render_generation_report(
            gen_no,
            [(c.id, c.sdk, c.strategy, v) for c, v, _ps in ranking],
            winner.id,
            t1_report,
            codex_verdict,
            status,
            lodo_report=lodo_report,
        )
        (gdir / "report.md").write_text(report_md, encoding="utf-8")
```

- [ ] **Step 6: generation.json에 LODO 필드 추가**

`generation = { ... "status": status, }` 딕셔너리에서 `"status": status,` 아래에 추가:

```python
        "status": status,
        "lodo_verdict": lodo_res["verdict"] if lodo_res else None,
        "lodo_n_valid": lodo_res["n_valid"] if lodo_res else None,
        "lodo_n_designs": lodo_res["n_designs"] if lodo_res else None,
```

- [ ] **Step 7: 기존 auto 테스트 4개에 통과형 LODO stub 주입**

`_dataset`는 2설계(gcd/ibex)라 LODO 게이트가 활성화된다. 기존 auto 테스트가 실제 학습을 타지 않도록 통과형 stub을 주입한다. 아래 4개 `run_generation(...)` 호출에 각각 `lodo_gate_fn=_stub_lodo("mixed"),` 한 줄을 인자로 추가(예: `gate_fn=...` 줄 다음):

- `test_auto_gate_promoted` (gate_fn=_stub_gate("distinguishable") 호출)
- `test_auto_gate_rejected_codex` (gate_fn=_stub_gate("distinguishable") 호출)
- `test_auto_gate_rejected_t1` (gate_fn=_stub_gate("indistinguishable") 호출)
- `test_auto_gate_fold_workdir_is_tempdir_not_experiments` (gate_fn=spy_gate 호출)

(`test_auto_false_keeps_awaiting_operator`·`test_per_seed_vals_inf_serialized_as_null`·`test_run_generation_end_to_end_mock`은 `auto=False`(기본) → LODO 미발동, 수정 불필요.)

- [ ] **Step 8: 통과 확인 (전체 회귀 포함)**

Run: `uv run pytest tests/pipeline/test_orchestrator.py -q && uv run pytest -q`
Expected: 신규 5 + 기존 전체 green.

- [ ] **Step 9: 커밋**

```bash
uv run ruff check src/pipeline/orchestrator.py tests/pipeline/test_orchestrator.py
git add src/pipeline/orchestrator.py tests/pipeline/test_orchestrator.py
git commit -m "feat(loop): T1 앞 LODO 게이트 + 실패-fold 차단(orchestrator 층) — 루프 환류 Task 2"
```

---

### Task 3: Makefile — loop DATASET 기본값 3설계 혼합본

**Files:**
- Modify: `Makefile`

- [ ] **Step 1: 기본값 교체**

`Makefile`에서:
```make
DATASET ?= dataset.jsonl
```
→
```make
# gen-004+ 루프 dataset: 3설계 혼합(gcd+aes+ibex). gen-001~003 val_mae와 직접 비교 금지(설계 교체).
DATASET ?= experiments/multidesign/dataset-3design.jsonl
```

- [ ] **Step 2: 확인**

Run: `make -n loop`
Expected: 출력에 `--dataset experiments/multidesign/dataset-3design.jsonl` 포함.

- [ ] **Step 3: 데이터 존재 확인**

Run: `test -f experiments/multidesign/dataset-3design.jsonl && wc -l experiments/multidesign/dataset-3design.jsonl`
Expected: 2784 (gcd 53 + aes 691 + ibex 2040).

- [ ] **Step 4: 커밋**

```bash
git add Makefile
git commit -m "chore(loop): make loop DATASET 기본값 → 3설계 혼합본 (루프 환류 Task 3)"
```

---

### Task 4: program.md — 다설계 입력 설명 + 관찰 힌트

**Files:**
- Modify: `program.md`

- [ ] **Step 1: 입력 데이터 섹션에 다설계 주석 추가**

`program.md`의 "## 입력 데이터 (frozen 계약 — 변경 금지)" 섹션 본문 끝(마지막 줄) 뒤에 추가:

```markdown

dataset은 **다설계 혼합**일 수 있다(`group_key`로 설계 구분). 그 경우 `train.py`의 val split은
**설계-분리**(GroupShuffleSplit)라 `val_mae`는 *학습에서 안 본 설계*에 대한 예측 성능 — 즉 selection
지표 자체가 교차설계 일반화를 측정한다. 승격 전 별도 LODO 게이트가 일반화 후퇴를 한 번 더 차단한다.
```

- [ ] **Step 2: 관찰 힌트 섹션 신설** (파일 끝 "## Operator 감독" 섹션 앞에 추가)

```markdown
## 관찰 힌트 (probe 실측 — 지시 아님, 참고용)

아래는 Operator의 교차설계 probe(`experiments/multidesign/probe/probe.md`,
`probe-3design.md`)에서 관찰된 *사실*이다. 전략 선택은 너에게 맡긴다 — 따라야 할 지시가 아니다.

- 델타 label(`post_route_slack_ns − synth_slack_ns` 잔차 학습)은 드리프트가 안정적인 설계(aes)에서
  naive를 37% 이겼으나, 드리프트가 자릿수로 다른 설계(ibex)에선 약했다.
- 혼합 분포 훈련은 절대 스케일 모델의 미관측 설계 전이를 회복시켰다(ibex held-out서 naive 4.3× 격파).
- held-out 설계별 최선 전략이 갈렸다 — 단일 정답 축은 없었다.

```

- [ ] **Step 3: 확인**

Run: `grep -c "관찰 힌트\|설계-분리" program.md`
Expected: `2`.

- [ ] **Step 4: 커밋**

```bash
git add program.md
git commit -m "docs(program): 다설계 입력 설명 + probe 관찰 힌트(지시 아님) — 루프 환류 Task 4"
```

---

### Task 5: 최종 검증 + push

**Files:** (없음 — 검증·push만)

- [ ] **Step 1: 전체 게이트**

Run: `uv run pytest -q && uv run ruff check src tests`
Expected: 전체 green (기존 94 + 신규 7 = 101).

- [ ] **Step 2: frozen 무변경 확인**

Run: `git diff --name-only origin/main..HEAD -- train.py prepare.py src/prepare_lib`
Expected: 빈 출력(frozen 미변경).

- [ ] **Step 3: push**

```bash
git push && git status -sb
```
Expected: `## main...origin/main` (ahead 0 after push).

- [ ] **Step 4: 구현 산출물을 codex-review-approval 스킬로 검토** (artifact = code/diff)

diff(`origin/main..HEAD` 직전 vs 현재 코드 변경 전체)를 `codex-review-approval` 스킬로 검토 게이트에 건다.
verdict `approve`면 완료, `request_changes`면 must_fix 반영 후 재검토.

---

## 범위 밖 (spec §9)

- gen-004 실제 실행(승인 후 운영 — LLM 구독, AWS 불필요).
- 교차설계 게이트의 통계 검정 승격(4+ 설계 확보 후), 설계별 샘플 불균형 가중, reasoning trace.
