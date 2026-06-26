# T4-lite Sub-A 다설계 데이터 획득 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.
> **혼합 plan**: Task 1~2·5는 **무비용 코드(TDD)**. Task 3·4·6·7은 **AWS 실 과금 운영 — 각 run-task/destroy 전 Operator 명시 동의 필수**(D4). 코드 subagent에 위임 가능, 운영 task는 Operator가 직접/감독.

**Goal:** aes·ibex 설계 데이터를 Fargate로 획득해 gcd와 결합한 다설계 dataset을 만들고, Sub-B 교차설계 게이트로 *실제* 일반화를 측정한다.

**Architecture:** 무비용 코드(`combine_datasets` 결합 유틸 + gcd 불변 가드 테스트)를 먼저 TDD로 확정하고, 그 위에 cost-gated 운영 절차(run-task→수집→prepare→결합→교차설계 게이트→destroy)를 얹는다. gcd frozen 보존, 파서 additive.

**Tech Stack:** Python 3.12, 기존 `prepare.py`/`prepare_lib`/`pipeline.validation.run_crossdesign_gate`, AWS ECS Fargate(`cdk/DEPLOY.md`), pytest/ruff.

**Spec:** `docs/superpowers/specs/2026-06-09-t4-lite-suba-multidesign-data-design.md`

**계약(확인됨):**
- `prepare.py --synth <synth.rpt> --route <route.rpt> --lockfile <versions.txt> --design-id <d> --out-dir <dir>` → `<dir>/dataset.jsonl` + `manifest.json`. report 포맷 설계 무관 동일.
- dataset 행 키(12): endpoint·endpoint_is_ff·group_key·max_stage_delay_ns·mean_stage_delay_ns·num_stages·path_group·post_route_slack_ns·startpoint·startpoint_is_ff·synth_arrival_ns·synth_slack_ns.
- `run_crossdesign_gate(winner_train_py, baseline_train_py, rows, workdir) -> dict` · `render_crossdesign_report(res) -> str` (Sub-B 완료).
- 운영: `cdk/DEPLOY.md`. **region 주의**: roboco 프로필 기본 ap-northeast-2가 DEPLOY.md의 us-east-1을 덮음 — 실행 시 실제 배포 region 확인(운영 invariant).

---

### Task 1: `combine_datasets` 결합 유틸 (무비용, TDD)

**Files:** Create `src/prepare_lib/combine.py` · Test `tests/prepare/test_combine.py`

- [ ] **Step 1: 실패 테스트 작성** — `tests/prepare/test_combine.py`

```python
# tests/prepare/test_combine.py
import json
import pytest
from pathlib import Path
from prepare_lib.combine import combine_datasets

KEYS = ["endpoint", "endpoint_is_ff", "group_key", "max_stage_delay_ns", "mean_stage_delay_ns",
        "num_stages", "path_group", "post_route_slack_ns", "startpoint", "startpoint_is_ff",
        "synth_arrival_ns", "synth_slack_ns"]


def _row(gk, i):
    return {k: (gk if k == "group_key" else (f"e{i}" if k in ("endpoint", "startpoint") else 0.1))
            for k in KEYS}


def _jsonl(tmp_path, name, rows):
    p = tmp_path / name
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return p


def test_combine_concats_and_preserves_order(tmp_path):
    a = _jsonl(tmp_path, "a.jsonl", [_row("gcd", 0), _row("gcd", 1)])
    b = _jsonl(tmp_path, "b.jsonl", [_row("aes", 0)])
    rows = combine_datasets([a, b])
    assert len(rows) == 3
    assert [r["group_key"] for r in rows] == ["gcd", "gcd", "aes"]  # 입력 순서 보존


def test_combine_rejects_schema_mismatch(tmp_path):
    a = _jsonl(tmp_path, "a.jsonl", [_row("gcd", 0)])
    bad = _jsonl(tmp_path, "bad.jsonl", [{"group_key": "aes", "x": 1}])  # 스키마 다름
    with pytest.raises(ValueError):
        combine_datasets([a, bad])


def test_combine_rejects_duplicate_group_key(tmp_path):
    # 서로 다른 파일이 같은 group_key → LODO 성립 안 함 → 거부
    a = _jsonl(tmp_path, "a.jsonl", [_row("gcd", 0)])
    b = _jsonl(tmp_path, "b.jsonl", [_row("gcd", 1)])
    with pytest.raises(ValueError):
        combine_datasets([a, b])
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/prepare/test_combine.py -v`
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: 구현** — `src/prepare_lib/combine.py`

```python
"""combine — 설계별 dataset.jsonl을 다설계 결합 dataset으로 concat (Operator-owned).

각 파일은 한 설계(group_key 단일). 스키마 일치·설계 간 group_key 분리를 검증해 LODO 성립을 보장.
설계: docs/superpowers/specs/2026-06-09-t4-lite-suba-multidesign-data-design.md
"""

from __future__ import annotations

import json
from pathlib import Path

_KEYS = frozenset([
    "endpoint", "endpoint_is_ff", "group_key", "max_stage_delay_ns", "mean_stage_delay_ns",
    "num_stages", "path_group", "post_route_slack_ns", "startpoint", "startpoint_is_ff",
    "synth_arrival_ns", "synth_slack_ns",
])


def combine_datasets(paths: list[Path]) -> list[dict]:
    """여러 설계 dataset.jsonl을 입력 순서대로 concat. 스키마·group_key 분리 검증."""
    out, seen_groups = [], set()
    for path in paths:
        rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
        if not rows:
            raise ValueError(f"빈 dataset: {path}")
        file_groups = {r.get("group_key") for r in rows}
        for r in rows:
            if frozenset(r.keys()) != _KEYS:
                raise ValueError(f"스키마 불일치 {path}: {sorted(r.keys())}")
        if len(file_groups) != 1:
            raise ValueError(f"한 파일은 단일 설계여야 함 {path}: {file_groups}")
        g = next(iter(file_groups))
        if g in seen_groups:
            raise ValueError(f"group_key 중복(LODO 불가): {g}")
        seen_groups.add(g)
        out.extend(rows)
    return out
```

- [ ] **Step 4: 통과 확인**

Run: `uv run pytest tests/prepare/test_combine.py -v`
Expected: 3 PASS

- [ ] **Step 5: 커밋**

```bash
git add src/prepare_lib/combine.py tests/prepare/test_combine.py
git commit -m "feat(prepare_lib): combine_datasets — 다설계 결합 유틸 (T4-lite Sub-A)"
```

---

### Task 2: gcd 불변 가드 (무비용, TDD — D6 비교성 보호)

**Files:** Test `tests/prepare/test_gcd_invariance.py`

- [ ] **Step 1: 가드 테스트 작성** — `tests/prepare/test_gcd_invariance.py`

```python
# tests/prepare/test_gcd_invariance.py
# 파서(prepare_lib) 변경이 gcd 파싱을 바꾸지 않음을 보장(D6: frozen 비교성).
import json
from pathlib import Path
from prepare_lib.dataset import build_dataset

REPO = Path(__file__).resolve().parents[2]
GCD = REPO / "experiments/real-gcd-fargate"


def test_gcd_dataset_is_invariant():
    rows, _manifest = build_dataset(
        str(GCD / "synth.rpt"), str(GCD / "route.rpt"),
        str(GCD / "versions.txt"), "gcd",
    )
    committed = [json.loads(line) for line in
                 (GCD / "dataset/dataset.jsonl").read_text().splitlines() if line.strip()]
    assert rows == committed, "파서 변경이 gcd dataset을 바꿈 — frozen 비교성 위반(D6)"
```

(주의: `build_dataset` 시그니처는 prepare.py:29 `build_dataset(synth, route, lockfile, design_id)` 와 일치. 반환이 `(rows, manifest)` 인지 확인 후 맞춤.)

- [ ] **Step 2: 실행 — 현재 파서로 통과해야 함(회귀 안전망)**

Run: `uv run pytest tests/prepare/test_gcd_invariance.py -v`
Expected: PASS (현 파서는 gcd dataset을 재현). 만약 FAIL이면 `build_dataset` 반환형/정렬을 테스트에 맞춰 조정(파서는 바꾸지 말 것).

- [ ] **Step 3: 커밋**

```bash
git add tests/prepare/test_gcd_invariance.py
git commit -m "test(prepare): gcd dataset 불변 가드 — 파서 변경이 비교성 깨면 실패(D6)"
```

---

### Task 3: ⚠️ Fargate run-task — DESIGN=aes (AWS 실 과금, Operator 동의 필수)

**이 task는 비용 발생. Operator 명시 "실행" 동의 없이는 진행 금지(D4). 마찰 시 정지·보고(D5).**

- [ ] **Step 1: 스택 상태 확인(D7)** — EdaFlowStack 배포 여부·region 확인

```bash
cd cdk && AWS_PROFILE=roboco aws cloudformation describe-stacks --stack-name EdaFlowStack \
  --query 'Stacks[0].StackStatus' --region ap-northeast-2 2>/dev/null || echo "미배포 — DEPLOY.md로 배포 필요"
```
없으면 `cdk/DEPLOY.md` 절차로 배포(Operator 동의).

- [ ] **Step 2: 설계 가용성 확인** — aes가 ORFS 이미지에 있는지(run-task 로그 또는 사전 확인). 없으면 정지·보고(D5).

- [ ] **Step 3: ⚠️ run-task DESIGN=aes (Operator 동의 후)** — `cdk/DEPLOY.md` §4에 **DESIGN env override** 추가:

```bash
AWS_PROFILE=roboco aws ecs run-task --cluster <CLUSTER> --task-definition <TASKDEF> \
  --launch-type FARGATE --region ap-northeast-2 \
  --network-configuration 'awsvpcConfiguration={subnets=[<PUBLIC_SUBNET>],assignPublicIp=ENABLED}' \
  --overrides 'containerOverrides=[{name=<CONTAINER>,environment=[{name=DESIGN,value=aes}]}]'
# CloudWatch /eda-flow 로그로 완주 확인. CTS·route 실패 시 정지·보고(D5).
```

- [ ] **Step 4: 수집·prepare** — S3 → `experiments/real-aes-fargate/` → prepare

```bash
AWS_PROFILE=roboco aws s3 cp --recursive s3://<BUCKET>/runs/aes/<RUN_ID>/ experiments/real-aes-fargate/
uv run python prepare.py --synth experiments/real-aes-fargate/synth.rpt \
  --route experiments/real-aes-fargate/route.rpt \
  --lockfile experiments/real-aes-fargate/versions.txt \
  --design-id aes --out-dir experiments/real-aes-fargate/dataset
# → "N samples" (N>0). 파싱 실패 시 정지·보고(D5) — 파서 additive 수정은 Operator 판단(D6).
```

- [ ] **Step 5: 검증·커밋** — 행 수·group_key=aes 확인 후 산출물 커밋(대용량 임시 제외)

```bash
python3 -c "import json,collections; r=[json.loads(l) for l in open('experiments/real-aes-fargate/dataset/dataset.jsonl')]; print('n=',len(r), collections.Counter(x['group_key'] for x in r))"
git add experiments/real-aes-fargate/dataset/ experiments/real-aes-fargate/*.rpt experiments/real-aes-fargate/versions.txt
git commit -m "experiment(aes): Fargate 실데이터 → dataset (T4-lite Sub-A)"
```

---

### Task 4: ⚠️ Fargate run-task — DESIGN=ibex (AWS 실 과금, Operator 동의 필수)

Task 3과 동일 절차를 `DESIGN=ibex`로 반복(순차, D2). ibex는 크므로 runtime·비용↑·마찰 위험↑ — 각 단계 Operator 동의·마찰 정지보고(D5).

- [ ] **Step 1: ⚠️ run-task DESIGN=ibex** (Operator 동의 후) — Task 3 Step 3에서 `value=ibex`.
- [ ] **Step 2: 수집·prepare** — `experiments/real-ibex-fargate/`, `--design-id ibex`.
- [ ] **Step 3: 검증·커밋** — group_key=ibex 확인 후 커밋.

(ibex가 ORFS 이미지에 없거나 flow 실패 시: 정지·보고. Operator가 다른 설계(jpeg 등)로 대체하거나 aes만으로 LODO 2 fold 진행 결정.)

---

### Task 5: 결합 dataset 생성 (무비용)

**Files:** Create `experiments/multidesign/dataset.jsonl`

- [ ] **Step 1: 결합** — combine_datasets로 gcd+aes+ibex concat

```bash
mkdir -p experiments/multidesign
PYTHONPATH=src uv run python -c "
import json, sys; sys.path.insert(0,'src')
from pathlib import Path
from prepare_lib.combine import combine_datasets
paths = [Path('experiments/real-gcd-fargate/dataset/dataset.jsonl'),
         Path('experiments/real-aes-fargate/dataset/dataset.jsonl'),
         Path('experiments/real-ibex-fargate/dataset/dataset.jsonl')]
rows = combine_datasets([p for p in paths if p.exists()])
Path('experiments/multidesign/dataset.jsonl').write_text('\n'.join(json.dumps(r) for r in rows)+'\n')
import collections; print('n=',len(rows), collections.Counter(r['group_key'] for r in rows))
"
```

- [ ] **Step 2: 검증·커밋** — 설계 ≥2, group_key 분리 확인

```bash
git add experiments/multidesign/dataset.jsonl
git commit -m "data(multidesign): gcd+aes+ibex 결합 dataset (T4-lite Sub-A)"
```

---

### Task 6: payoff — 교차설계 일반화 실측 (무비용, Operator 게이트)

**Files:** Create `experiments/multidesign/crossdesign.md`

- [ ] **Step 1: 교차설계 게이트 실행** — gen-001 winner(현 train.py) vs pre-gen-001 baseline

```bash
git show 619e24f~1:train.py > /tmp/pre_gen001_train.py
PYTHONPATH=src uv run python -c "
import json, sys; sys.path.insert(0,'src')
from pathlib import Path
from pipeline.validation import run_crossdesign_gate, render_crossdesign_report
rows=[json.loads(l) for l in open('experiments/multidesign/dataset.jsonl')]
res=run_crossdesign_gate(Path('train.py'), Path('/tmp/pre_gen001_train.py'), rows, Path('/tmp/xdesign'))
Path('experiments/multidesign/crossdesign.md').write_text(render_crossdesign_report(res)+'\n')
print('verdict:', res['verdict'], '| winner better:', res['n_winner_better'], '/', res['n_designs'])
"
```

- [ ] **Step 2: Operator 보고** — verdict + crossdesign.md 제시. 결과 해석(일반화 경향?)은 Operator와 함께. **임시 /tmp/xdesign 작업물은 커밋 안 함.**

- [ ] **Step 3: 커밋(Operator 승인 시)** — crossdesign.md + INTENT Learnings(교차설계 첫 실측)

```bash
git add experiments/multidesign/crossdesign.md
git commit -m "experiment(multidesign): 교차설계 일반화 첫 실측 — verdict <...>"
```

---

### Task 7: ⚠️ 정리 — cdk destroy (D7, 비용 종료)

- [ ] **Step 1: ⚠️ destroy (Operator 동의 후)**

```bash
cd cdk && CDK_DEFAULT_ACCOUNT=AWS_ACCOUNT_ID CDK_DEFAULT_REGION=ap-northeast-2 \
  npx cdk destroy --profile roboco
```

- [ ] **Step 2: 전체 회귀 + ruff**

Run: `uv run pytest -q && make lint`
Expected: 모든 테스트 PASS(기존 79 + combine 3 + gcd 불변 1 = ~83), ruff 통과.

---

## Self-Review

- **Spec coverage**: D1 aes+ibex(Task3·4) · D2 순차(Task3→4) · D3 결합 dataset(Task5, gcd frozen 미변경) · D4 건별 동의(Task3·4·7 ⚠️ 표기) · D5 정지·보고(Task3 Step3/4·Task4 주석) · D6 additive+gcd불변(Task2 가드) · D7 재사용→destroy(Task3 Step1·Task7). payoff=Task6. ✓
- **Placeholder scan**: `<CLUSTER>`/`<TASKDEF>`/`<BUCKET>` 등은 *런타임 환경값*(DEPLOY.md에서 채움) — 코드 placeholder 아님. 무비용 코드 task(1·2·5·6)는 실제 코드/명령 완비. ✓
- **Type consistency**: `combine_datasets(paths)->list[dict]`, `build_dataset(synth,route,lockfile,design_id)->(rows,manifest)`(Task2에서 반환형 확인 명시), `run_crossdesign_gate->dict[verdict/n_winner_better/n_designs]`. ✓
- **frozen 주의**: gcd dataset 무변경(Task2 가드). 파서 변경은 additive·Operator 판단(D6). train.py/기존 prepare.py 계약 무변경. ✓
- **비용 게이트**: Task3·4·7은 ⚠️ + "Operator 동의 필수" 명시 — 자율 무인 $ 지출 차단. 코드 task는 무비용. ✓
