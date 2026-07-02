# Frozen Encoder 표현 재설계 (surrogate v2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** self-supervised graph autoencoder를 사람이 1회 사전학습해 frozen encoder로 고정하고, 라벨 4설계 데이터셋에 (구 표형식 feature ‖ 임베딩)을 병기해 루프가 head만 탐색하게 만든다 — "새 winner가 B0 대비 교차설계 T1 `distinguishable`인가"의 사전 고정 판정 준비 완료 상태까지.

**Architecture:** 3단 (spec §4): [1] `pretrain/` 신규(코퍼스 manifest → Yosys 합성-only netlist.json → endpoint 중심 그래프 → autoencoder 사전학습 → 채택 게이트) · [2] `prepare.py` 재작성(표형식‖임베딩 병기, encoder_sha 앵커) · [3] 루프 계약 변경(torch 허용, encoder read-only 가드, 게이트 체인 불변).

**Tech Stack:** Python 3.12 + uv · PyTorch(신규 optional-deps `pretrain`) · 기존 sklearn/numpy/click · Yosys `write_json`(ORFS docker, digest 고정) · pytest.

**Spec:** [`docs/superpowers/specs/2026-07-02-frozen-encoder-representation-redesign-design.md`](../specs/2026-07-02-frozen-encoder-representation-redesign-design.md) (Codex 승인 + 2026-07-02 plan-단계 amendment 2건). 아래 임계값은 전부 spec 복사 인용 — 재정의 금지.

**선행 완료(본 plan 범위 아님):** spec §9.1 archive 브랜치(`archive/surrogate-v1-8gen`)와 §9.3 INTENT.md 갱신은 plan 착수 전 완료(커밋 `94d929d`). §9.2 문서 갱신만 Task 12로 남음.

## Global Constraints

- **frozen 자산과 소유 경계(실행 규칙)**: `prepare.py`·`src/prepare_lib/`·`models/encoder-v1.pt`의 "frozen"은 **루프 내 후보 생성 에이전트** 기준 금지다. 본 plan의 태스크는 Operator 승인 하의 *사람-소유 채널*이 실행하며, 실행 후 재-freeze된다. 단 **Task 9(prepare 계열 재작성)와 Task 13~15(코퍼스·encoder 학습·판정·dataset 생성 실행)는 subagent에 위임하지 않고 주 세션에서 Operator 가시 하에 실행**한다 — 헤더의 "agentic workers task-by-task"는 나머지 태스크(1~8, 10~12)에만 적용.
- **spec amendment 반영(2026-07-02, plan 단계)**: spec §5 그래프 통계(타이밍 아크 → 구조 통계)와 §8 coverage fail-fast(0.95)는 spec에 amendment로 기입 완료 — 본 plan은 그 값을 복사 인용만 한다.
- **train.py(B0) 소스는 본 plan에서 변경하지 않는다** — B0 = 현행 train.py 그대로가 "벽" 비교 대상. 루프 계약 변경은 program.md·가드·데이터셋 스키마로만 표현.
- **게이트 체인 불변**: median → LODO → 교차설계 T1 → Codex. `src/pipeline/validation.py`·`selection.py`의 통계 로직 무변경.
- **임계값 (spec §6 복사 인용)**: patience=**10** epoch · naive 상수 재구성 baseline 미만 · 임베딩 차원별 std 중앙값 > **1e-6** · 무작위 endpoint 쌍 **1000**개 평균 pairwise cosine < **0.99** · 선형 probe **5-seed(0,1,2,3,4) median val MAE ≤ 표형식 동일 프로토콜** · 코퍼스 제외 규칙 (a) Yosys exit≠0 (b) endpoint<10 만.
- **의존성**: torch는 optional-deps `pretrain` 그룹으로 격리. 루프 후보의 신규 의존성 *설치* 금지 — 허용 import에 사전 설치 torch 추가(program.md).
  - **spec 노트와의 편차(명시)**: spec §6 "PyTorch(+PyG)" 중 **PyG는 미채택** — 3-layer mean-aggregation message passing은 순수 torch로 충분하고(YAGNI), PyG wheel은 플랫폼(MPS/arm64) 민감도가 높아 재현성 앵커에 불리. Codex plan 게이트 검증 대상.
- ruff 100자·py312. pytest는 `tmp_path`·fixture만, 실데이터(`experiments/`) 미접촉.
- Direct commit to `main`, conventional prefixes.
- LLM 호출 없음(본 plan 전체) — 구독-only 원칙과 무관한 순수 코드/데이터 작업. AWS 실과금 없음(합성은 로컬 docker; SageMaker fallback은 범위 밖, 필요 시 Operator 동의 후 별도).

## File Structure

```
pretrain/
  corpus_manifest.yaml        # Task 1 — 선커밋 (설계 목록·encoder-val·제외 규칙)
  synth_corpus.py             # Task 8 — docker 합성 드라이버 (netlist.json 생산)
  train_encoder.py            # Task 5 — 사전학습 CLI (사람 소유)
  b1_head.py                  # Task 11 — B1 naive 임베딩 head (train.py CLI 계약 동일)
src/pretrain_lib/
  __init__.py
  manifest.py                 # Task 1 — manifest 로드·검증
  graph.py                    # Task 3 — netlist.json → EndpointGraph (결정적)
  model.py                    # Task 4 — GraphAutoencoder (pure torch)
  encoder_gates.py            # Task 6 — 채택 게이트(naive baseline·붕괴 진단·선형 probe)
  embed.py                    # Task 7 — frozen encoder 로드 → endpoint별 임베딩
src/prepare_lib/dataset.py    # Task 9 — build_dataset_v2 추가 (기존 함수 유지)
prepare.py                    # Task 9 — --netlist/--encoder 옵션 (v2 모드)
src/pipeline/guard.py         # Task 10 — encoder read-only 가드
src/pipeline/orchestrator.py  # Task 10 — fail-fast + 가드 통합 (수정 최소)
program.md / PRD.md / CLAUDE.md  # Task 12
tests/pretrain/…              # Task별 병행
```

---

### Task 1: 코퍼스 manifest 선커밋 (`corpus_manifest.yaml` + validator)

**Files:**
- Create: `pretrain/corpus_manifest.yaml`
- Create: `src/pretrain_lib/__init__.py` (빈 파일)
- Create: `src/pretrain_lib/manifest.py`
- Test: `tests/pretrain/test_manifest.py`

**Interfaces:**
- Produces: `load_manifest(path: str | Path) -> dict` — 검증 통과한 manifest dict. 키: `version, pdk_family, orfs_image_digest, designs(list[{name, platform}]), encoder_val_designs(list[str]), label_designs(list[str]), exclusion_rules(list[str]), exclusions(list[{design, reason}])`. 위반 시 `ValueError`.

- [ ] **Step 1: ORFS 동봉 sky130 설계 목록 조사**

Run (둘 다):
```bash
gh api repos/The-OpenROAD-Project/OpenROAD-flow-scripts/contents/flow/designs/sky130hd --jq '.[] | select(.type=="dir") | .name'
gh api repos/The-OpenROAD-Project/OpenROAD-flow-scripts/contents/flow/designs/sky130hs --jq '.[] | select(.type=="dir") | .name'
```
Expected: 디렉터리명 목록(설계 이름). sky130hd+sky130hs 합산으로 목표 ~20개 확보(spec §5 "목표 ~20"; 합산이 20 미만이면 있는 만큼 전부 채택하고 manifest에 실제 수를 기록 — 임의 추가 금지). `label_designs`(gcd/aes/ibex/jpeg)와 겹치는 이름은 designs에 포함하되 encoder-val로 지정 금지.

- [ ] **Step 2: 실패하는 테스트 작성**

```python
# tests/pretrain/test_manifest.py
from pathlib import Path

import pytest

from pretrain_lib.manifest import load_manifest

GOOD = """\
version: 1
pdk_family: sky130
orfs_image_digest: "sha256:b19fe0a514a87aee0f97073797395c0ca489c45406b526bc75fd2038c82fdf69"
designs:
  - {name: gcd, platform: sky130hd}
  - {name: aes, platform: sky130hd}
  - {name: riscv32i, platform: sky130hd}
  - {name: chameleon, platform: sky130hd}
encoder_val_designs: [riscv32i, chameleon]
label_designs: [gcd, aes, ibex, jpeg]
exclusion_rules:
  - "yosys synth exit code != 0"
  - "extracted endpoints < 10"
exclusions: []
"""


def _write(tmp_path: Path, text: str) -> Path:
    p = tmp_path / "corpus_manifest.yaml"
    p.write_text(text, encoding="utf-8")
    return p


def test_load_manifest_ok(tmp_path):
    m = load_manifest(_write(tmp_path, GOOD))
    assert m["orfs_image_digest"].startswith("sha256:")
    assert {d["name"] for d in m["designs"]} >= {"gcd", "riscv32i"}


def test_encoder_val_must_be_in_designs(tmp_path):
    bad = GOOD.replace("encoder_val_designs: [riscv32i, chameleon]",
                       "encoder_val_designs: [riscv32i, notexist]")
    with pytest.raises(ValueError, match="encoder_val"):
        load_manifest(_write(tmp_path, bad))


def test_encoder_val_disjoint_from_label_designs(tmp_path):
    bad = GOOD.replace("encoder_val_designs: [riscv32i, chameleon]",
                       "encoder_val_designs: [riscv32i, gcd]")
    with pytest.raises(ValueError, match="label"):
        load_manifest(_write(tmp_path, bad))


def test_exclusion_rules_are_fixed(tmp_path):
    bad = GOOD.replace('  - "extracted endpoints < 10"', '  - "operator judgement"')
    with pytest.raises(ValueError, match="exclusion_rules"):
        load_manifest(_write(tmp_path, bad))
```

- [ ] **Step 3: 실패 확인**

Run: `uv run pytest tests/pretrain/test_manifest.py -v`
Expected: FAIL — `ModuleNotFoundError: pretrain_lib`

- [ ] **Step 4: 구현**

```python
# src/pretrain_lib/manifest.py
"""corpus_manifest.yaml 로드·검증 — 코퍼스 구성이 사후 튜닝 노브가 되는 것을 차단 (spec §5)."""

from __future__ import annotations

from pathlib import Path

import yaml

# spec §5 사전 고정 — 이 둘 외의 제외 사유 금지.
FIXED_EXCLUSION_RULES = [
    "yosys synth exit code != 0",
    "extracted endpoints < 10",
]


def load_manifest(path: str | Path) -> dict:
    m = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    names = [d["name"] for d in m["designs"]]
    if len(names) != len(set(names)):
        raise ValueError("designs: 중복 설계 이름")
    if not str(m["orfs_image_digest"]).startswith("sha256:"):
        raise ValueError("orfs_image_digest: sha256 digest 필요")
    ev = m["encoder_val_designs"]
    if len(ev) != 2 or not set(ev) <= set(names):
        raise ValueError("encoder_val 설계는 designs 안의 2개여야 함 (spec §6.1)")
    if set(ev) & set(m["label_designs"]):
        raise ValueError("encoder_val 설계는 label 4설계와 겹칠 수 없음 (spec §6.1)")
    if m["exclusion_rules"] != FIXED_EXCLUSION_RULES:
        raise ValueError("exclusion_rules: spec §5 사전 고정 2건만 허용")
    for ex in m.get("exclusions", []):
        if not ex.get("design") or not ex.get("reason"):
            raise ValueError("exclusions: design·reason 필수")
    return m
```

- [ ] **Step 5: `pretrain/corpus_manifest.yaml` 작성**

Step 1 조사 결과로 실제 목록을 채운다. 형식은 테스트 `GOOD`과 동일하되:
- `designs`: 조사된 sky130hd/sky130hs 설계 전부(각 `{name, platform}`), 목표 ~20.
- `encoder_val_designs`: 라벨 4설계와 겹치지 않는 2개 — 크기가 서로 다른 것 우선(예: 소형 1 + 중형 1). 지정 근거를 yaml 주석 한 줄로.
- `orfs_image_digest`: `sha256:b19fe0a514a87aee0f97073797395c0ca489c45406b526bc75fd2038c82fdf69` (라벨 4설계 versions.txt의 image_digest — endpoint 이름 결정성을 위해 동일 이미지 고정).
- `exclusions: []` (append-only, 합성 실행 시 채움).

Run: `uv run python -c "from pretrain_lib.manifest import load_manifest; print(len(load_manifest('pretrain/corpus_manifest.yaml')['designs']))"`
Expected: 설계 수 출력, 예외 없음.

- [ ] **Step 6: 테스트 통과 확인 + 커밋**

Run: `uv run pytest tests/pretrain/ -v && uv run ruff check src/pretrain_lib tests/pretrain`
Expected: PASS

```bash
git add pretrain/corpus_manifest.yaml src/pretrain_lib tests/pretrain
git commit -m "feat(pretrain): corpus manifest 선커밋 + 검증 로더 — 제외 규칙 사전 고정 (spec §5)"
```

---

### Task 2: pyproject `pretrain` 그룹 + torch 설치

**Files:**
- Modify: `pyproject.toml:21-23` (optional-dependencies)

**Interfaces:**
- Produces: `uv sync --extra pretrain`으로 torch 사용 가능. 이후 Task 4~7·11의 import 전제.

- [ ] **Step 1: pyproject 수정**

```toml
ml = [
    "scikit-learn>=1.4",
]
pretrain = [
    # spec §6 — 사람 소유 사전학습 전용 격리. PyG는 미채택(plan Global Constraints 편차 노트).
    "torch>=2.3",
]
```

- [ ] **Step 2: 설치 검증**

Run: `uv sync --all-extras && uv run python -c "import torch; print(torch.__version__, torch.backends.mps.is_available())"`
Expected: 버전 출력 (MPS는 macOS에서 True 기대 — False여도 CPU로 진행 가능, 학습 실행 Task 14에서 재확인).

- [ ] **Step 3: 기존 테스트 회귀 확인 + 커밋**

Run: `uv run pytest -q`
Expected: 기존 123+ tests PASS

```bash
git add pyproject.toml uv.lock
git commit -m "chore(deps): optional-deps pretrain 그룹(torch) 추가 — PyG 미채택 편차는 plan에 기록"
```

---

### Task 3: `graph.py` — netlist.json → endpoint 중심 그래프 (결정적)

**Files:**
- Create: `src/pretrain_lib/graph.py`
- Test: `tests/pretrain/test_graph.py`
- Create: `tests/pretrain/fixtures/mini_netlist.json`

**Interfaces:**
- Consumes: Yosys `write_json` 출력 dict (모듈 1개 top, 셀은 blackbox — `port_directions` 없음).
- Produces:
  - `Node = tuple[str, str, int, int, int]` — `(inst_name, cell_norm, fanin, fanout, depth)`
  - `@dataclass(frozen=True) EndpointGraph: endpoint: str; nodes: tuple[Node, ...]; edges: tuple[tuple[int, int], ...]` (edges는 nodes 인덱스, driver→sink 방향)
  - `build_endpoint_graphs(netlist: dict, max_depth: int = 8, max_nodes: int = 256) -> dict[str, EndpointGraph]` — key = endpoint 셀 인스턴스명(STA `Endpoint:` 필드와 동일 규약)
  - `normalize_cell(cell_type: str) -> str` — `sky130_fd_sc_hd__and2_1` → `and2_1`
  - `is_ff(cell_norm: str) -> bool`

**설계 결정 (spec §5 "그래프 변환"의 구체화)**:
- 입력은 Yosys `write_json`의 netlist.json. 셀은 미해석 blackbox이므로 포트 방향은 **규약 상수**로 판정: `OUTPUT_PORTS = {"X", "Y", "Q", "Q_N", "Z", "COUT", "SUM", "GCLK"}` — sky130_fd_sc 표준셀 출력 포트 명명 규약(단일 진리원으로 상수 1곳 정의, 테스트로 고정).
- endpoint = FF 셀(정규화 이름이 `df`/`sdf`/`edf`/`dl`로 시작) + top output port. FF endpoint 키는 인스턴스명(예: `_9422_`) — STA report_checks의 `Endpoint: _9422_ (...)` 첫 토큰과 일치.
- 그래프 = endpoint에서 driver 방향 역방향 BFS fan-in cone, `max_depth=8`, `max_nodes=256`(초과 시 BFS 순서로 절단). node feature: `(cell_norm, fanin, fanout, depth)` — fanout은 전체 netlist 기준.
- **결정성**: BFS 이웃 확장·노드 나열 모두 인스턴스명 `sorted()` 순서. 동일 netlist → 동일 출력 (spec §5, 테스트로 강제).
- 노드 통계는 fanin/fanout·depth — spec §5 amendment(2026-07-02) 그대로: 합성 시점 타이밍은 이미 표형식 8 feature로 같은 행에 병기되므로 임베딩은 구조 신호 전담(복사 인용).

- [ ] **Step 1: 미니 netlist fixture 작성**

```json
{
  "modules": {
    "top": {
      "ports": {
        "clk": {"direction": "input", "bits": [2]},
        "in_a": {"direction": "input", "bits": [3]},
        "out_z": {"direction": "output", "bits": [7]}
      },
      "cells": {
        "_and_": {"type": "sky130_fd_sc_hd__and2_1",
                  "connections": {"A": [3], "B": [4], "X": [5]}},
        "_inv_": {"type": "sky130_fd_sc_hd__inv_2",
                  "connections": {"A": [5], "Y": [6]}},
        "_ff1_": {"type": "sky130_fd_sc_hd__dfxtp_1",
                  "connections": {"CLK": [2], "D": [6], "Q": [4]}},
        "_buf_": {"type": "sky130_fd_sc_hd__buf_1",
                  "connections": {"A": [4], "X": [7]}}
      }
    }
  }
}
```

- [ ] **Step 2: 실패하는 테스트 작성**

```python
# tests/pretrain/test_graph.py
import json
from pathlib import Path

from pretrain_lib.graph import build_endpoint_graphs, is_ff, normalize_cell

FIX = Path(__file__).parent / "fixtures" / "mini_netlist.json"


def _netlist():
    return json.loads(FIX.read_text())


def test_normalize_and_ff():
    assert normalize_cell("sky130_fd_sc_hd__dfxtp_1") == "dfxtp_1"
    assert normalize_cell("sky130_fd_sc_hs__and2_1") == "and2_1"
    assert is_ff("dfxtp_1") and not is_ff("and2_1")


def test_ff_endpoint_cone():
    graphs = build_endpoint_graphs(_netlist())
    g = graphs["_ff1_"]  # FF endpoint = 인스턴스명
    names = [n[0] for n in g.nodes]
    # D-입력 cone: _inv_ ← _and_ ← (_ff1_.Q 재진입) — endpoint 자신 포함
    assert "_ff1_" in names and "_inv_" in names and "_and_" in names
    depths = {n[0]: n[4] for n in g.nodes}
    assert depths["_ff1_"] == 0 and depths["_inv_"] == 1 and depths["_and_"] == 2


def test_output_port_endpoint_exists():
    graphs = build_endpoint_graphs(_netlist())
    assert "out_z" in graphs  # top output port endpoint
    assert any(n[0] == "_buf_" for n in graphs["out_z"].nodes)


def test_determinism():
    a = build_endpoint_graphs(_netlist())
    b = build_endpoint_graphs(_netlist())
    assert a == b


def test_max_nodes_cap():
    graphs = build_endpoint_graphs(_netlist(), max_nodes=2)
    assert len(graphs["_ff1_"].nodes) == 2
```

- [ ] **Step 3: 실패 확인**

Run: `uv run pytest tests/pretrain/test_graph.py -v`
Expected: FAIL — `ImportError`

- [ ] **Step 4: 구현**

```python
# src/pretrain_lib/graph.py
"""netlist.json(Yosys write_json) → endpoint 중심 그래프. 결정성 보장 (spec §5)."""

from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass

# sky130_fd_sc 표준셀 출력 포트 명명 규약 (blackbox라 port_directions 부재 — 규약 판정).
OUTPUT_PORTS = frozenset({"X", "Y", "Q", "Q_N", "Z", "COUT", "SUM", "GCLK"})
_CELL_PREFIX_RE = re.compile(r"^sky130_fd_sc_[a-z]+__")
_FF_PREFIXES = ("df", "sdf", "edf", "dl")

Node = tuple[str, str, int, int, int]  # (inst, cell_norm, fanin, fanout, depth)


@dataclass(frozen=True)
class EndpointGraph:
    endpoint: str
    nodes: tuple[Node, ...]
    edges: tuple[tuple[int, int], ...]  # (driver_idx, sink_idx)


def normalize_cell(cell_type: str) -> str:
    return _CELL_PREFIX_RE.sub("", cell_type)


def is_ff(cell_norm: str) -> bool:
    return cell_norm.startswith(_FF_PREFIXES)


def _top_module(netlist: dict) -> dict:
    mods = netlist["modules"]
    # 셀을 가진 모듈이 top (write_json 후 hierarchy -auto-top 전제로 1개).
    withcells = [m for m in mods.values() if m.get("cells")]
    if len(withcells) != 1:
        raise ValueError(f"top 모듈 판별 실패: cells 보유 모듈 {len(withcells)}개")
    return withcells[0]


def _index(mod: dict):
    """bit → driver inst, inst → (fanin bits, fanout count) 색인. 이름 정렬로 결정성."""
    driver_of: dict[int, str] = {}
    fanin_bits: dict[str, list[int]] = {}
    fanout: dict[str, int] = {}
    for inst in sorted(mod["cells"]):
        cell = mod["cells"][inst]
        ins, outs = [], []
        for port in sorted(cell["connections"]):
            bits = [b for b in cell["connections"][port] if isinstance(b, int)]
            (outs if port in OUTPUT_PORTS else ins).extend(bits)
        fanin_bits[inst] = ins
        for b in outs:
            driver_of[b] = inst
    sink_count: dict[int, int] = {}
    for inst in sorted(mod["cells"]):
        for b in fanin_bits[inst]:
            sink_count[b] = sink_count.get(b, 0) + 1
    for port in mod.get("ports", {}).values():
        if port["direction"] == "output":
            for b in port["bits"]:
                if isinstance(b, int):
                    sink_count[b] = sink_count.get(b, 0) + 1
    for inst in sorted(mod["cells"]):
        cell = mod["cells"][inst]
        outs = [b for p, bs in cell["connections"].items() if p in OUTPUT_PORTS
                for b in bs if isinstance(b, int)]
        fanout[inst] = sum(sink_count.get(b, 0) for b in outs)
    return driver_of, fanin_bits, fanout


def _cone(start_insts, driver_of, fanin_bits, fanout, cells, max_depth, max_nodes):
    nodes: list[Node] = []
    edges: list[tuple[str, str]] = []
    seen: dict[str, int] = {}
    q = deque((i, 0) for i in start_insts)
    while q and len(nodes) < max_nodes:
        inst, depth = q.popleft()
        if inst in seen:
            continue
        seen[inst] = len(nodes)
        cn = normalize_cell(cells[inst]["type"])
        nodes.append((inst, cn, len(fanin_bits[inst]), fanout[inst], depth))
        if depth >= max_depth:
            continue
        drivers = sorted({driver_of[b] for b in fanin_bits[inst] if b in driver_of})
        for d in drivers:
            edges.append((d, inst))
            q.append((d, depth + 1))
    idx = {n[0]: i for i, n in enumerate(nodes)}
    eidx = tuple(sorted((idx[a], idx[b]) for a, b in edges if a in idx and b in idx))
    return tuple(nodes), eidx


def build_endpoint_graphs(
    netlist: dict, max_depth: int = 8, max_nodes: int = 256
) -> dict[str, EndpointGraph]:
    mod = _top_module(netlist)
    driver_of, fanin_bits, fanout = _index(mod)
    cells = mod["cells"]
    graphs: dict[str, EndpointGraph] = {}
    for inst in sorted(cells):
        if is_ff(normalize_cell(cells[inst]["type"])):
            nodes, edges = _cone([inst], driver_of, fanin_bits, fanout, cells,
                                 max_depth, max_nodes)
            graphs[inst] = EndpointGraph(inst, nodes, edges)
    for pname in sorted(mod.get("ports", {})):
        port = mod["ports"][pname]
        if port["direction"] != "output":
            continue
        drivers = sorted({driver_of[b] for b in port["bits"]
                          if isinstance(b, int) and b in driver_of})
        if drivers:
            nodes, edges = _cone(drivers, driver_of, fanin_bits, fanout, cells,
                                 max_depth - 1, max_nodes)
            graphs[pname] = EndpointGraph(pname, nodes, edges)
    return graphs
```

주의: output-port cone의 depth는 driver부터 0이라 FF cone과 의미 정합( endpoint 노드=depth 0)이 되도록 `max_depth - 1`로 보정. `test_ff_endpoint_cone`의 depth 기대값이 계약.

- [ ] **Step 5: 통과 확인 + 커밋**

Run: `uv run pytest tests/pretrain/test_graph.py -v && uv run ruff check src/pretrain_lib`
Expected: PASS

```bash
git add src/pretrain_lib/graph.py tests/pretrain/test_graph.py tests/pretrain/fixtures/mini_netlist.json
git commit -m "feat(pretrain): netlist.json → endpoint 중심 그래프 변환 (결정성 테스트 포함)"
```

---

### Task 4: `model.py` — GraphAutoencoder (pure torch)

**Files:**
- Create: `src/pretrain_lib/model.py`
- Test: `tests/pretrain/test_model.py`

**Interfaces:**
- Consumes: `EndpointGraph` (Task 3).
- Produces:
  - `class GraphAutoencoder(torch.nn.Module)` — `__init__(vocab_size: int, hidden: int = 64, emb_dim: int = 32, n_layers: int = 3)`
  - `.forward(g: EndpointGraph, vocab: dict[str, int], mask_idx: list[int]) -> tuple[Tensor, Tensor]` — (masked 노드 type logits `[len(mask_idx), vocab_size]`, 전 노드 degree 예측 `[N, 2]`)
  - `.encode(g: EndpointGraph, vocab: dict[str, int]) -> Tensor` — endpoint 임베딩 `[emb_dim]` (endpoint 노드 표현 ‖ mean-pool 후 사영)
  - `recon_loss(logits, deg_pred, g, vocab, mask_idx) -> Tensor`
  - `graph_tensors(g, vocab) -> (type_ids[N], numeric[N,3], adj_pairs[E,2])` — 헬퍼(테스트·게이트 공용)
  - vocab 규약: `dict[cell_norm, int]`, index 0 = `"<mask>"`, 1 = `"<unk>"`.

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/pretrain/test_model.py
import json
from pathlib import Path

import torch

from pretrain_lib.graph import build_endpoint_graphs
from pretrain_lib.model import GraphAutoencoder, recon_loss

FIX = Path(__file__).parent / "fixtures" / "mini_netlist.json"


def _graph():
    graphs = build_endpoint_graphs(json.loads(FIX.read_text()))
    return graphs["_ff1_"]


VOCAB = {"<mask>": 0, "<unk>": 1, "and2_1": 2, "inv_2": 3, "dfxtp_1": 4, "buf_1": 5}


def test_encode_shape_and_determinism():
    torch.manual_seed(0)
    m = GraphAutoencoder(vocab_size=len(VOCAB))
    m.eval()
    g = _graph()
    e1 = m.encode(g, VOCAB)
    e2 = m.encode(g, VOCAB)
    assert e1.shape == (32,)
    assert torch.allclose(e1, e2)


def test_masked_recon_loss_decreases():
    torch.manual_seed(0)
    m = GraphAutoencoder(vocab_size=len(VOCAB), hidden=32, emb_dim=16, n_layers=2)
    g = _graph()
    opt = torch.optim.Adam(m.parameters(), lr=0.01)
    mask_idx = [1]  # _inv_ 노드 type을 가리고 재구성
    first = last = None
    for _ in range(30):
        opt.zero_grad()
        logits, deg = m(g, VOCAB, mask_idx)
        loss = recon_loss(logits, deg, g, VOCAB, mask_idx)
        loss.backward()
        opt.step()
        first = first if first is not None else float(loss)
        last = float(loss)
    assert last < first
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/pretrain/test_model.py -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: 구현**

```python
# src/pretrain_lib/model.py
"""self-supervised graph autoencoder — 마스킹-재구성 (spec §6, PreRoutGNN 근거).

pure torch 3-layer mean-aggregation message passing (PyG 미채택 — plan 편차 노트).
"""

from __future__ import annotations

import torch
from torch import nn

from pretrain_lib.graph import EndpointGraph

MASK, UNK = 0, 1


def graph_tensors(g: EndpointGraph, vocab: dict[str, int]):
    type_ids = torch.tensor([vocab.get(n[1], UNK) for n in g.nodes], dtype=torch.long)
    numeric = torch.tensor(
        [[float(n[2]), float(n[3]), float(n[4])] for n in g.nodes], dtype=torch.float32
    )
    numeric = torch.log1p(numeric)  # fanin/fanout/depth 스케일 안정화
    adj = torch.tensor(g.edges, dtype=torch.long).reshape(-1, 2)
    return type_ids, numeric, adj


class GraphAutoencoder(nn.Module):
    def __init__(self, vocab_size: int, hidden: int = 64, emb_dim: int = 32, n_layers: int = 3):
        super().__init__()
        self.type_emb = nn.Embedding(vocab_size, hidden)
        self.num_proj = nn.Linear(3, hidden)
        self.layers = nn.ModuleList(
            [nn.Linear(2 * hidden, hidden) for _ in range(n_layers)]
        )
        self.out_proj = nn.Linear(2 * hidden, emb_dim)
        self.type_head = nn.Linear(hidden, vocab_size)
        self.deg_head = nn.Linear(hidden, 2)

    def _node_repr(self, g: EndpointGraph, vocab, mask_idx=()):
        dev = self.type_emb.weight.device  # MPS/CPU — 입력 텐서를 모델 디바이스로 정렬
        type_ids, numeric, adj = (t.to(dev) for t in graph_tensors(g, vocab))
        if len(mask_idx):
            type_ids = type_ids.clone()
            type_ids[list(mask_idx)] = MASK
        h = self.type_emb(type_ids) + self.num_proj(numeric)
        n = h.shape[0]
        for layer in self.layers:
            agg = torch.zeros_like(h)
            cnt = torch.zeros(n, 1, device=dev)
            if adj.numel():
                agg = agg.index_add(0, adj[:, 1], h[adj[:, 0]])  # driver → sink
                cnt = cnt.index_add(0, adj[:, 1], torch.ones(adj.shape[0], 1, device=dev))
            agg = agg / cnt.clamp(min=1.0)
            h = torch.relu(layer(torch.cat([h, agg], dim=1)))
        return h

    def forward(self, g: EndpointGraph, vocab, mask_idx: list[int]):
        h = self._node_repr(g, vocab, mask_idx)
        return self.type_head(h[mask_idx]), self.deg_head(h)

    def encode(self, g: EndpointGraph, vocab) -> torch.Tensor:
        h = self._node_repr(g, vocab)
        ep = h[0]  # BFS 시작 = endpoint 노드 (graph.py 계약)
        pooled = h.mean(dim=0)
        return self.out_proj(torch.cat([ep, pooled]))


def recon_loss(logits, deg_pred, g: EndpointGraph, vocab, mask_idx) -> torch.Tensor:
    type_ids, numeric, _ = graph_tensors(g, vocab)
    ce = nn.functional.cross_entropy(logits, type_ids[list(mask_idx)])
    mse = nn.functional.mse_loss(deg_pred, numeric[:, :2])
    return ce + 0.1 * mse
```

`encode`의 `h[0]` 전제(endpoint = nodes[0])는 Task 3 BFS 구현이 보장 — FF cone은 자기 자신에서 시작. output-port cone은 첫 driver 노드가 대표(허용 — endpoint 자체가 셀이 아님).

- [ ] **Step 4: 통과 확인 + 커밋**

Run: `uv run pytest tests/pretrain/test_model.py -v && uv run ruff check src/pretrain_lib`
Expected: PASS

```bash
git add src/pretrain_lib/model.py tests/pretrain/test_model.py
git commit -m "feat(pretrain): pure-torch graph autoencoder (마스킹 재구성 + endpoint encode)"
```

---

### Task 5: `train_encoder.py` — 사전학습 CLI (patience·naive baseline·리포트)

**Files:**
- Create: `pretrain/train_encoder.py`
- Create: `src/pretrain_lib/pretrain_loop.py` (학습 로직 — CLI에서 분리해 테스트 가능하게)
- Test: `tests/pretrain/test_pretrain_loop.py`

**Interfaces:**
- Consumes: `pretrain/corpus/<design>/netlist.json` (Task 8 산출 규약), `load_manifest`, `GraphAutoencoder`.
- Produces:
  - `build_vocab(graphs_by_design: dict[str, dict]) -> dict[str, int]` — `<mask>`=0, `<unk>`=1, 이후 corpus 등장 cell_norm `sorted()` 순.
  - `naive_baseline_loss(train_graphs, val_graphs, vocab) -> float` — encoder-train 노드 type 빈도 분포 CE + degree 평균 MSE (spec §6.2 "naive 상수 재구성 baseline").
  - `train_encoder(graphs_by_design, encoder_val_designs, seed=0, max_epochs=200, patience=10, device="cpu") -> tuple[GraphAutoencoder, dict, dict]` — (모델, vocab, report). vocab은 **encoder-train 설계만으로** 구축(spec §6.1 — val-only 셀 타입은 `<unk>`). report = `train_curve, val_curve, best_val_loss, naive_baseline_loss, stopped_epoch`.
  - CLI: `uv run python pretrain/train_encoder.py --corpus-dir pretrain/corpus --manifest pretrain/corpus_manifest.yaml --out models/ --seed 0` → `models/encoder-v1.pt`(state_dict+vocab+config), `models/encoder-v1.report.json`.
  - checkpoint 규약(`embed.py`가 소비): `torch.save({"state_dict":…, "vocab":…, "config": {"hidden":64, "emb_dim":32, "n_layers":3, "max_depth":8, "max_nodes":256}}, path)`.

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/pretrain/test_pretrain_loop.py
import json
from pathlib import Path

from pretrain_lib.graph import build_endpoint_graphs
from pretrain_lib.pretrain_loop import build_vocab, naive_baseline_loss, train_encoder

FIX = Path(__file__).parent / "fixtures" / "mini_netlist.json"


def _corpus():
    g = build_endpoint_graphs(json.loads(FIX.read_text()))
    # 미니 netlist 하나를 3개 설계처럼 복제 — 학습/검증 분리 로직 검증용
    return {"d1": g, "d2": g, "dval": g}


def test_vocab_deterministic():
    v1 = build_vocab(_corpus())
    v2 = build_vocab(_corpus())
    assert v1 == v2 and v1["<mask>"] == 0 and v1["<unk>"] == 1


def test_train_encoder_early_stop_and_report():
    corpus = _corpus()
    model, vocab, report = train_encoder(corpus, encoder_val_designs=["dval"],
                                         seed=0, max_epochs=5, patience=2)
    assert report["stopped_epoch"] <= 5
    assert len(report["val_curve"]) == report["stopped_epoch"]
    assert isinstance(report["naive_baseline_loss"], float)
    assert report["best_val_loss"] > 0


def test_vocab_built_from_train_designs_only():
    # spec §6.1 — encoder-val 전용 셀 타입은 vocab에 들어가면 안 된다 (<unk> 처리).
    from pretrain_lib.graph import EndpointGraph

    g_train = EndpointGraph("e", (("a", "and2_1", 1, 1, 0),), ())
    g_val = EndpointGraph("e", (("b", "xor2_1", 1, 1, 0),), ())
    _model, vocab, _report = train_encoder(
        {"t": {"e": g_train}, "v": {"e": g_val}},
        encoder_val_designs=["v"], seed=0, max_epochs=1, patience=1,
    )
    assert "and2_1" in vocab and "xor2_1" not in vocab


def test_naive_baseline_is_finite():
    corpus = _corpus()
    vocab = build_vocab(corpus)
    nb = naive_baseline_loss({"d1": corpus["d1"]}, {"dval": corpus["dval"]}, vocab)
    assert nb > 0
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/pretrain/test_pretrain_loop.py -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: 구현**

```python
# src/pretrain_lib/pretrain_loop.py
"""encoder 사전학습 루프 — patience 조기 종료 + naive baseline (spec §6.2)."""

from __future__ import annotations

import torch

from pretrain_lib.model import GraphAutoencoder, graph_tensors, recon_loss

MASK_FRAC = 0.15


def build_vocab(graphs_by_design: dict[str, dict]) -> dict[str, int]:
    cells = sorted({n[1] for graphs in graphs_by_design.values()
                    for g in graphs.values() for n in g.nodes})
    return {"<mask>": 0, "<unk>": 1, **{c: i + 2 for i, c in enumerate(cells)}}


def _mask_indices(n: int, rng: torch.Generator) -> list[int]:
    k = max(1, int(n * MASK_FRAC))
    return torch.randperm(n, generator=rng)[:k].tolist()


def _epoch_loss(model, graphs, vocab, rng=None) -> float:
    total, count = 0.0, 0
    for design in sorted(graphs):
        for ep in sorted(graphs[design]):
            g = graphs[design][ep]
            if not g.nodes:
                continue
            if rng is None:  # 검증: 결정적 마스크(첫 노드)
                mask = [0]
            else:
                mask = _mask_indices(len(g.nodes), rng)
            logits, deg = model(g, vocab, mask)
            loss = recon_loss(logits, deg, g, vocab, mask)
            if model.training:
                loss.backward()
            total += float(loss.detach())
            count += 1
    return total / max(count, 1)


def naive_baseline_loss(train_graphs, val_graphs, vocab) -> float:
    """encoder-train 노드 feature 평균(type 빈도분포·degree 평균)으로 일괄 예측한 val loss."""
    freq = torch.zeros(len(vocab))
    degs = []
    for graphs in train_graphs.values():
        for g in graphs.values():
            ti, num, _ = graph_tensors(g, vocab)
            for t in ti:
                freq[t] += 1
            degs.append(num[:, :2])
    probs = (freq / freq.sum()).clamp(min=1e-9)
    mean_deg = torch.cat(degs).mean(dim=0)
    total, count = 0.0, 0
    for graphs in val_graphs.values():
        for g in graphs.values():
            ti, num, _ = graph_tensors(g, vocab)
            ce = -torch.log(probs[ti]).mean()
            mse = ((num[:, :2] - mean_deg) ** 2).mean()
            total += float(ce + 0.1 * mse)
            count += 1
    return total / max(count, 1)


def train_encoder(graphs_by_design, encoder_val_designs, seed=0, max_epochs=200,
                  patience=10, device="cpu", hidden=64, emb_dim=32, n_layers=3):
    torch.manual_seed(seed)
    train_g = {d: g for d, g in graphs_by_design.items() if d not in encoder_val_designs}
    val_g = {d: g for d, g in graphs_by_design.items() if d in encoder_val_designs}
    # spec §6.1: encoder-val은 검증 전용 — vocab 등 사전학습 산출물에 미기여(val-only 셀은 <unk>).
    vocab = build_vocab(train_g)
    model = GraphAutoencoder(len(vocab), hidden=hidden, emb_dim=emb_dim, n_layers=n_layers)
    model.to(device)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    rng = torch.Generator().manual_seed(seed)

    best, best_state, since_best = float("inf"), None, 0
    train_curve, val_curve = [], []
    for epoch in range(1, max_epochs + 1):
        model.train()
        opt.zero_grad()
        train_curve.append(_epoch_loss(model, train_g, vocab, rng))
        opt.step()
        model.eval()
        with torch.no_grad():
            vl = _epoch_loss(model, val_g, vocab)
        val_curve.append(vl)
        if vl < best:
            best, since_best = vl, 0
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        else:
            since_best += 1
        if since_best >= patience:  # spec §6.2: patience=10 (호출자가 전달)
            break
    if best_state is not None:
        model.load_state_dict(best_state)
    report = {
        "train_curve": train_curve,
        "val_curve": val_curve,
        "best_val_loss": best,
        "naive_baseline_loss": naive_baseline_loss(train_g, val_g, vocab),
        "stopped_epoch": len(val_curve),
        "seed": seed,
    }
    return model, vocab, report
```

```python
# pretrain/train_encoder.py
"""encoder 사전학습 CLI — 사람 소유 1회 실행 (spec §6). 에이전트 실행 금지."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import torch  # noqa: E402
from pretrain_lib.graph import build_endpoint_graphs  # noqa: E402
from pretrain_lib.manifest import load_manifest  # noqa: E402
from pretrain_lib.pretrain_loop import train_encoder  # noqa: E402

CONFIG = {"hidden": 64, "emb_dim": 32, "n_layers": 3, "max_depth": 8, "max_nodes": 256}


@click.command()
@click.option("--corpus-dir", required=True, type=click.Path(exists=True))
@click.option("--manifest", required=True, type=click.Path(exists=True))
@click.option("--out", required=True, type=click.Path())
@click.option("--seed", default=0, type=int)
@click.option("--max-epochs", default=200, type=int)
def main(corpus_dir: str, manifest: str, out: str, seed: int, max_epochs: int) -> None:
    m = load_manifest(manifest)
    excluded = {e["design"] for e in m.get("exclusions", [])}
    graphs_by_design = {}
    for d in m["designs"]:
        name = d["name"]
        if name in excluded:
            continue
        nl = Path(corpus_dir) / name / "netlist.json"
        graphs = build_endpoint_graphs(
            json.loads(nl.read_text()), CONFIG["max_depth"], CONFIG["max_nodes"]
        )
        if len(graphs) < 10:  # spec §5 제외 규칙 (b) — manifest append는 Operator가 커밋
            raise SystemExit(f"{name}: endpoints {len(graphs)} < 10 — manifest 제외 필요")
        graphs_by_design[name] = graphs
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model, vocab, report = train_encoder(
        graphs_by_design, m["encoder_val_designs"], seed=seed,
        max_epochs=max_epochs, patience=10, device=device, **{
            k: CONFIG[k] for k in ("hidden", "emb_dim", "n_layers")
        },
    )
    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": model.state_dict(), "vocab": vocab, "config": CONFIG},
               out_dir / "encoder-v1.pt")
    (out_dir / "encoder-v1.report.json").write_text(json.dumps(report, indent=2))
    click.echo(json.dumps({"best_val_loss": report["best_val_loss"],
                           "naive_baseline_loss": report["naive_baseline_loss"],
                           "stopped_epoch": report["stopped_epoch"]}))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 통과 확인 + 커밋**

Run: `uv run pytest tests/pretrain/ -v && uv run ruff check src/pretrain_lib pretrain`
Expected: PASS

```bash
git add pretrain/train_encoder.py src/pretrain_lib/pretrain_loop.py tests/pretrain/test_pretrain_loop.py
git commit -m "feat(pretrain): 사전학습 루프 + CLI — patience 조기종료·naive baseline·리포트 (spec §6)"
```

---

### Task 6: `encoder_gates.py` — 채택 게이트 (spec §6.1~6.4)

**Files:**
- Create: `src/pretrain_lib/encoder_gates.py`
- Test: `tests/pretrain/test_encoder_gates.py`

**Interfaces:**
- Consumes: Task 5 report dict, 임베딩 행렬(numpy), 라벨 데이터셋 rows(list[dict], `emb_*` 키 포함 — Task 9 산출 규약).
- Produces:
  - `collapse_diagnostics(embs: np.ndarray, seed: int = 0) -> dict` — `{"median_dim_std", "mean_pairwise_cosine", "pass"}` (spec §6.3: std 중앙값 > 1e-6 AND 1000쌍 평균 cosine < 0.99)
  - `linear_probe(rows: list[dict], seeds=(0, 1, 2, 3, 4)) -> dict` — `{"emb_median_mae", "tab_median_mae", "pass"}` (spec §6.4: 임베딩만 선형회귀 5-seed median ≤ 표형식만 동일 프로토콜; split은 train.py `split()` 방식 복사 인용)
  - `encoder_verdict(report: dict, diag: dict, probe: dict) -> dict` — `{"adopt": bool, "reasons": list[str]}` (§6.2 재구성 + §6.3 + §6.4 전부 통과 시 adopt)

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/pretrain/test_encoder_gates.py
import numpy as np

from pretrain_lib.encoder_gates import collapse_diagnostics, encoder_verdict, linear_probe


def test_collapse_detects_constant_embeddings():
    embs = np.ones((50, 8))
    d = collapse_diagnostics(embs)
    assert not d["pass"]


def test_collapse_passes_diverse_embeddings():
    rng = np.random.default_rng(0)
    d = collapse_diagnostics(rng.normal(size=(50, 8)))
    assert d["pass"] and d["median_dim_std"] > 1e-6 and d["mean_pairwise_cosine"] < 0.99


def _rows(n=120, emb_informative=True):
    rng = np.random.default_rng(1)
    rows = []
    for i in range(n):
        y = float(rng.normal())
        emb = [y + rng.normal(0, 0.01), rng.normal()] if emb_informative \
            else [rng.normal(), rng.normal()]
        rows.append({
            "num_stages": 3, "synth_slack_ns": rng.normal(), "synth_arrival_ns": 1.0,
            "max_stage_delay_ns": 0.2, "mean_stage_delay_ns": 0.1,
            "startpoint_is_ff": 1, "endpoint_is_ff": 1, "path_group": "clk",
            "post_route_slack_ns": y, "group_key": f"d{i % 3}",
            "emb_00": emb[0], "emb_01": emb[1],
        })
    return rows


def test_linear_probe_informative_embeddings_pass():
    p = linear_probe(_rows(emb_informative=True))
    assert p["pass"] and p["emb_median_mae"] <= p["tab_median_mae"]


def test_verdict_requires_all_gates():
    report = {"best_val_loss": 0.5, "naive_baseline_loss": 1.0}
    diag_ok = {"pass": True}
    probe_ok = {"pass": True}
    assert encoder_verdict(report, diag_ok, probe_ok)["adopt"]
    assert not encoder_verdict(
        {"best_val_loss": 1.5, "naive_baseline_loss": 1.0}, diag_ok, probe_ok
    )["adopt"]
    assert not encoder_verdict(report, {"pass": False}, probe_ok)["adopt"]
    assert not encoder_verdict(report, diag_ok, {"pass": False})["adopt"]
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/pretrain/test_encoder_gates.py -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: 구현**

```python
# src/pretrain_lib/encoder_gates.py
"""encoder 채택 게이트 — spec §6.1~6.4가 임계값의 single source (복사 인용)."""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import GroupShuffleSplit, train_test_split

_STD_MIN = 1e-6       # spec §6.3-①
_COS_MAX = 0.99       # spec §6.3-②
_N_PAIRS = 1000       # spec §6.3-②
TAB_FEATURES = [       # train.py FEATURE_NAMES 복사 인용 (path_group은 ordinal 인코딩)
    "num_stages", "synth_slack_ns", "synth_arrival_ns", "max_stage_delay_ns",
    "mean_stage_delay_ns", "startpoint_is_ff", "endpoint_is_ff", "path_group",
]


def collapse_diagnostics(embs: np.ndarray, seed: int = 0) -> dict:
    med_std = float(np.median(embs.std(axis=0)))
    rng = np.random.default_rng(seed)
    i = rng.integers(0, len(embs), size=_N_PAIRS)
    j = rng.integers(0, len(embs), size=_N_PAIRS)
    a, b = embs[i], embs[j]
    denom = np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1)
    cos = float(np.mean((a * b).sum(axis=1) / np.clip(denom, 1e-12, None)))
    ok = med_std > _STD_MIN and cos < _COS_MAX
    return {"median_dim_std": med_std, "mean_pairwise_cosine": cos, "pass": ok}


def _split(X, y, groups, seed):
    # train.py split() 방식 복사 인용 — group ≥2면 GroupShuffleSplit, 아니면 fixed-seed random.
    if len(set(groups)) >= 2:
        gss = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=seed)
        return next(gss.split(X, y, groups=groups))
    idx = np.arange(len(y))
    return train_test_split(idx, test_size=0.25, random_state=seed)


def _probe_mae(rows, cols, seeds) -> float:
    pg = {g: i for i, g in enumerate(sorted({r["path_group"] for r in rows}))}

    def val(r, c):
        return float(pg[r[c]]) if c == "path_group" else float(r[c])

    X = np.array([[val(r, c) for c in cols] for r in rows])
    y = np.array([float(r["post_route_slack_ns"]) for r in rows])
    groups = [r["group_key"] for r in rows]
    maes = []
    for s in seeds:
        tr, va = _split(X, y, groups, s)
        model = LinearRegression().fit(X[tr], y[tr])
        maes.append(mean_absolute_error(y[va], model.predict(X[va])))
    return float(np.median(maes))


def linear_probe(rows: list[dict], seeds=(0, 1, 2, 3, 4)) -> dict:
    emb_cols = sorted(k for k in rows[0] if k.startswith("emb_"))
    emb_mae = _probe_mae(rows, emb_cols, seeds)
    tab_mae = _probe_mae(rows, TAB_FEATURES, seeds)
    return {"emb_median_mae": emb_mae, "tab_median_mae": tab_mae,
            "pass": emb_mae <= tab_mae}


def encoder_verdict(report: dict, diag: dict, probe: dict) -> dict:
    reasons = []
    if not report["best_val_loss"] < report["naive_baseline_loss"]:
        reasons.append("recon: encoder-val loss가 naive 상수 baseline 이상 (spec §6.2)")
    if not diag["pass"]:
        reasons.append("collapse: 붕괴 진단 미달 (spec §6.3)")
    if not probe["pass"]:
        reasons.append("probe: 임베딩 선형 probe가 표형식 초과 (spec §6.4)")
    return {"adopt": not reasons, "reasons": reasons}
```

- [ ] **Step 4: 통과 확인 + 커밋**

Run: `uv run pytest tests/pretrain/test_encoder_gates.py -v && uv run ruff check src/pretrain_lib`
Expected: PASS

```bash
git add src/pretrain_lib/encoder_gates.py tests/pretrain/test_encoder_gates.py
git commit -m "feat(pretrain): encoder 채택 게이트 — naive baseline·붕괴 진단·선형 probe (spec §6)"
```

---

### Task 7: `embed.py` — frozen encoder 로드 + endpoint 임베딩 추출

**Files:**
- Create: `src/pretrain_lib/embed.py`
- Test: `tests/pretrain/test_embed.py`

**Interfaces:**
- Consumes: Task 5 checkpoint 규약(`{"state_dict", "vocab", "config"}`), Task 3 `build_endpoint_graphs`.
- Produces:
  - `load_encoder(path: str | Path) -> tuple[GraphAutoencoder, dict, dict]` — (eval 모드 모델, vocab, config)
  - `embed_endpoints(netlist: dict, model, vocab, config) -> dict[str, list[float]]` — endpoint명 → emb_dim 길이 float 리스트 (결정적)
  - `sha256_file(path) -> str`

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/pretrain/test_embed.py
import json
from pathlib import Path

import torch

from pretrain_lib.embed import embed_endpoints, load_encoder, sha256_file
from pretrain_lib.graph import build_endpoint_graphs
from pretrain_lib.model import GraphAutoencoder
from pretrain_lib.pretrain_loop import build_vocab

FIX = Path(__file__).parent / "fixtures" / "mini_netlist.json"
CONFIG = {"hidden": 32, "emb_dim": 16, "n_layers": 2, "max_depth": 8, "max_nodes": 256}


def _save_ckpt(tmp_path):
    nl = json.loads(FIX.read_text())
    vocab = build_vocab({"d": build_endpoint_graphs(nl)})
    torch.manual_seed(0)
    m = GraphAutoencoder(len(vocab), CONFIG["hidden"], CONFIG["emb_dim"], CONFIG["n_layers"])
    p = tmp_path / "encoder-v1.pt"
    torch.save({"state_dict": m.state_dict(), "vocab": vocab, "config": CONFIG}, p)
    return p, nl


def test_roundtrip_and_determinism(tmp_path):
    p, nl = _save_ckpt(tmp_path)
    model, vocab, config = load_encoder(p)
    e1 = embed_endpoints(nl, model, vocab, config)
    e2 = embed_endpoints(nl, model, vocab, config)
    assert e1 == e2
    assert "_ff1_" in e1 and len(e1["_ff1_"]) == CONFIG["emb_dim"]


def test_sha256_file(tmp_path):
    p, _ = _save_ckpt(tmp_path)
    s = sha256_file(p)
    assert len(s) == 64 and s == sha256_file(p)
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/pretrain/test_embed.py -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: 구현**

```python
# src/pretrain_lib/embed.py
"""frozen encoder 로드 → endpoint 임베딩. prepare.py v2가 소비 (spec §5)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import torch

from pretrain_lib.graph import build_endpoint_graphs
from pretrain_lib.model import GraphAutoencoder


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_encoder(path: str | Path):
    ckpt = torch.load(path, map_location="cpu", weights_only=True)
    vocab, config = ckpt["vocab"], ckpt["config"]
    model = GraphAutoencoder(
        len(vocab), config["hidden"], config["emb_dim"], config["n_layers"]
    )
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    return model, vocab, config


def embed_endpoints(netlist: dict, model, vocab, config) -> dict[str, list[float]]:
    graphs = build_endpoint_graphs(netlist, config["max_depth"], config["max_nodes"])
    out: dict[str, list[float]] = {}
    with torch.no_grad():
        for ep in sorted(graphs):
            if not graphs[ep].nodes:
                continue
            out[ep] = [round(float(x), 6) for x in model.encode(graphs[ep], vocab)]
    return out
```

- [ ] **Step 4: 통과 확인 + 커밋**

Run: `uv run pytest tests/pretrain/test_embed.py -v && uv run ruff check src/pretrain_lib`
Expected: PASS

```bash
git add src/pretrain_lib/embed.py tests/pretrain/test_embed.py
git commit -m "feat(pretrain): frozen encoder 로드 + endpoint 임베딩 추출 (결정성 테스트)"
```

---

### Task 8: `synth_corpus.py` — docker 합성 드라이버 (netlist.json 생산)

**Files:**
- Create: `pretrain/synth_corpus.py`
- Test: `tests/pretrain/test_synth_corpus.py`

**Interfaces:**
- Consumes: `load_manifest`. docker CLI(런타임에만 — 테스트는 subprocess 주입 mock).
- Produces:
  - `synth_one(design: dict, image: str, out_dir: Path, run=subprocess.run) -> dict` — `{"design", "ok", "reason"}`. 성공 시 `out_dir/<design>/netlist.json` 생성.
  - CLI: `uv run python pretrain/synth_corpus.py --manifest pretrain/corpus_manifest.yaml --out pretrain/corpus [--designs gcd,aes]` — 순차 실행, 실패는 exclusion 후보로 stdout 요약(manifest append는 사람이 커밋 — 조용한 누락 금지, spec §5).
- 컨테이너 내부 실행 커맨드(설계별):
  ```
  docker run --rm --platform linux/amd64 -v <out_abs>:/out \
    openroad/orfs@<digest> bash -lc \
    "cd /OpenROAD-flow-scripts/flow && make DESIGN_CONFIG=designs/<platform>/<name>/config.mk synth && \
     yosys -p 'read_verilog results/<platform>/<name>/base/1_synth.v; hierarchy -auto-top; write_json /out/<name>/netlist.json'"
  ```
  (컨테이너 내 flow 경로·이미지 명칭은 실행 시 `docker run … ls`로 1회 확인 후 상수 조정 — versions.txt digest가 이미지 앵커.)

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/pretrain/test_synth_corpus.py
import json
from pathlib import Path
from types import SimpleNamespace

from synth_corpus import synth_one  # pretrain/ 디렉터리 — conftest에서 path 추가


def _fake_netlist(n_ff: int) -> dict:
    cells = {
        f"_ff{i}_": {"type": "sky130_fd_sc_hd__dfxtp_1",
                     "connections": {"D": [2 + i], "Q": [1000 + i]}}
        for i in range(n_ff)
    }
    return {"modules": {"top": {"ports": {}, "cells": cells}}}


def _fake_run(out_dir: Path, n_ff: int):
    def run(cmd, **kw):
        # docker 호출을 흉내: netlist.json을 심고 exit 0
        target = out_dir / "gcd" / "netlist.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(_fake_netlist(n_ff)))
        return SimpleNamespace(returncode=0, stdout="", stderr="")
    return run


def test_synth_one_success(tmp_path):
    r = synth_one({"name": "gcd", "platform": "sky130hd"}, "img@sha256:x",
                  tmp_path, run=_fake_run(tmp_path, n_ff=12))
    assert r["ok"] and (tmp_path / "gcd" / "netlist.json").exists()


def test_synth_one_nonzero_exit_is_exclusion(tmp_path):
    def run(cmd, **kw):
        return SimpleNamespace(returncode=1, stdout="", stderr="boom")
    r = synth_one({"name": "gcd", "platform": "sky130hd"}, "img@sha256:x", tmp_path, run=run)
    assert not r["ok"] and r["reason"] == "yosys synth exit code != 0"


def test_synth_one_too_few_endpoints_is_exclusion(tmp_path):
    # spec §5 제외 규칙 (b) — 합성 단계에서 판정
    r = synth_one({"name": "gcd", "platform": "sky130hd"}, "img@sha256:x",
                  tmp_path, run=_fake_run(tmp_path, n_ff=3))
    assert not r["ok"] and r["reason"] == "extracted endpoints < 10"
```

`tests/pretrain/conftest.py` 생성:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "pretrain"))
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/pretrain/test_synth_corpus.py -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: 구현**

```python
# pretrain/synth_corpus.py
"""코퍼스 합성 드라이버 — ORFS docker(digest 고정)로 Yosys 합성만 → netlist.json (spec §4-[1]).

사람 소유. 실패 설계는 manifest exclusions에 사유 append 후 커밋(조용한 누락 금지, spec §5).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import click

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pretrain_lib.graph import build_endpoint_graphs  # noqa: E402
from pretrain_lib.manifest import load_manifest  # noqa: E402

IMAGE = "openroad/orfs"  # digest가 앵커 — 태그 아님
FLOW = "/OpenROAD-flow-scripts/flow"


def synth_one(design: dict, image: str, out_dir: Path, run=subprocess.run) -> dict:
    name, platform = design["name"], design["platform"]
    (Path(out_dir) / name).mkdir(parents=True, exist_ok=True)
    script = (
        f"cd {FLOW} && make DESIGN_CONFIG=designs/{platform}/{name}/config.mk synth && "
        f"yosys -p 'read_verilog results/{platform}/{name}/base/1_synth.v; "
        f"hierarchy -auto-top; write_json /out/{name}/netlist.json'"
    )
    proc = run(
        ["docker", "run", "--rm", "--platform", "linux/amd64",
         "-v", f"{Path(out_dir).resolve()}:/out", image, "bash", "-lc", script],
        capture_output=True, text=True, timeout=3600,
    )
    if proc.returncode != 0:
        return {"design": name, "ok": False, "reason": "yosys synth exit code != 0"}
    nl = Path(out_dir) / name / "netlist.json"
    if not nl.exists():
        return {"design": name, "ok": False, "reason": "yosys synth exit code != 0"}
    # spec §5 제외 규칙 (b) — 합성 워크플로에서 즉시 판정해 exclusion 기록을 완결.
    n_ep = len(build_endpoint_graphs(json.loads(nl.read_text(encoding="utf-8"))))
    if n_ep < 10:
        return {"design": name, "ok": False, "reason": "extracted endpoints < 10"}
    return {"design": name, "ok": True, "reason": ""}


@click.command()
@click.option("--manifest", required=True, type=click.Path(exists=True))
@click.option("--out", "out_dir", required=True, type=click.Path())
@click.option("--designs", default="", help="쉼표 구분 부분 실행(기본: manifest 전체)")
def main(manifest: str, out_dir: str, designs: str) -> None:
    m = load_manifest(manifest)
    image = f"{IMAGE}@{m['orfs_image_digest']}"
    only = set(designs.split(",")) if designs else None
    results = []
    for d in m["designs"]:
        if only and d["name"] not in only:
            continue
        r = synth_one(d, image, Path(out_dir))
        results.append(r)
        click.echo(json.dumps(r))
    failed = [r for r in results if not r["ok"]]
    if failed:
        click.echo(f"⚠️ {len(failed)}건 실패 — corpus_manifest.yaml exclusions에 append 후 커밋 필요")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 통과 확인 + 커밋**

Run: `uv run pytest tests/pretrain/ -v && uv run ruff check pretrain src/pretrain_lib`
Expected: PASS

```bash
git add pretrain/synth_corpus.py tests/pretrain/test_synth_corpus.py tests/pretrain/conftest.py
git commit -m "feat(pretrain): ORFS docker 합성 드라이버 — netlist.json 생산, 실패는 exclusion 후보"
```

---

### Task 9: prepare v2 — `build_dataset_v2` (표형식 ‖ 임베딩 병기)

**Files:**
- Modify: `src/prepare_lib/dataset.py` (기존 `build_dataset`/`write_dataset` 유지, v2 추가)
- Modify: `prepare.py` (옵션 추가)
- Test: `tests/prepare/test_dataset_v2.py`

**Interfaces:**
- Consumes: 기존 `build_dataset(synth, route, lockfile, design_id)`, Task 7 `load_encoder`/`embed_endpoints`/`sha256_file`.
- Produces:
  - `build_dataset_v2(synth_report, route_report, lockfile, design_id, netlist_json, encoder_path, corpus_manifest_path, min_coverage: float = 0.95) -> tuple[list[dict], dict]` — 각 row에 `emb_00`…`emb_{D-1}`(zero-pad 2자리) 추가. manifest에 `encoder_sha, corpus_manifest_sha, emb_dim, emb_coverage` 추가 (spec §5 "재현성 앵커" — DATASET 속성 경량 확장).
  - endpoint 매칭: row의 `endpoint` 메타키(STA `Endpoint:` 첫 토큰) ↔ `embed_endpoints` 키. 매칭 실패 row는 drop, coverage = matched/total < `min_coverage`(**0.95 — spec §8 amendment 복사 인용**)면 `ValueError` (fail-fast — 재합성 netlist와 원 STA의 이름 불일치 감지, 조용한 행 누락 금지).
  - `prepare.py` CLI: 기존 옵션 + `--netlist`(없으면 v1 동작 유지) + `--encoder` + `--corpus-manifest`.

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/prepare/test_dataset_v2.py
import json
from pathlib import Path

import pytest
import torch

from pretrain_lib.graph import build_endpoint_graphs
from pretrain_lib.model import GraphAutoencoder
from pretrain_lib.pretrain_loop import build_vocab
from prepare_lib.dataset import build_dataset_v2

MINI_NL = Path(__file__).resolve().parents[1] / "pretrain" / "fixtures" / "mini_netlist.json"
FIXTURES = Path(__file__).parent / "fixtures"  # 기존 synth/route report fixture 재사용
CONFIG = {"hidden": 32, "emb_dim": 8, "n_layers": 2, "max_depth": 8, "max_nodes": 256}


@pytest.fixture()
def encoder_ckpt(tmp_path):
    nl = json.loads(MINI_NL.read_text())
    vocab = build_vocab({"d": build_endpoint_graphs(nl)})
    torch.manual_seed(0)
    m = GraphAutoencoder(len(vocab), CONFIG["hidden"], CONFIG["emb_dim"], CONFIG["n_layers"])
    p = tmp_path / "encoder-v1.pt"
    torch.save({"state_dict": m.state_dict(), "vocab": vocab, "config": CONFIG}, p)
    return p


def _reports_for_mini(tmp_path):
    """mini_netlist의 _ff1_ endpoint에 맞춘 synth/route report_checks 최소 fixture."""
    synth = tmp_path / "synth.rpt"
    route = tmp_path / "route.rpt"
    block = (
        "Startpoint: in_a (input port)\n"
        "Endpoint: _ff1_ (rising edge-triggered flip-flop clocked by clk)\n"
        "Path Group: clk\nPath Type: max\n\n"
        "   0.10    0.10 ^ _and_/X (sky130_fd_sc_hd__and2_1)\n"
        "   0.05    0.15 ^ _inv_/Y (sky130_fd_sc_hd__inv_2)\n"
        "   1.00   data arrival time\n"
        "   0.50   slack (MET)\n\n"
    )
    synth.write_text(block)
    route.write_text(block.replace("0.50   slack", "0.30   slack"))
    lock = tmp_path / "lock.txt"
    lock.write_text("orfs-lock")
    return synth, route, lock


def test_v2_rows_have_embeddings_and_manifest_anchors(tmp_path, encoder_ckpt):
    synth, route, lock = _reports_for_mini(tmp_path)
    cm = tmp_path / "corpus_manifest.yaml"
    cm.write_text("version: 1\n")
    rows, manifest = build_dataset_v2(
        synth, route, lock, "mini", MINI_NL, encoder_ckpt, cm
    )
    assert rows and all(f"emb_{i:02d}" in rows[0] for i in range(CONFIG["emb_dim"]))
    assert manifest["emb_dim"] == CONFIG["emb_dim"]
    assert len(manifest["encoder_sha"]) == 64
    assert len(manifest["corpus_manifest_sha"]) == 64
    assert manifest["emb_coverage"] == 1.0


def test_v2_low_coverage_fails_fast(tmp_path, encoder_ckpt):
    synth, route, lock = _reports_for_mini(tmp_path)
    # endpoint 이름을 netlist에 없는 것으로 바꿔 매칭 0% 유도
    synth.write_text(synth.read_text().replace("_ff1_", "_ghost_"))
    route.write_text(route.read_text().replace("_ff1_", "_ghost_"))
    cm = tmp_path / "corpus_manifest.yaml"
    cm.write_text("version: 1\n")
    with pytest.raises(ValueError, match="coverage"):
        build_dataset_v2(synth, route, lock, "mini", MINI_NL, encoder_ckpt, cm)
```

(주: fixture report 형식이 기존 `parse_report` 파서와 안 맞으면 `tests/prepare/fixtures`의 실제 형식을 복사해 조정 — 파서는 frozen이므로 fixture 쪽을 맞춘다.)

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/prepare/test_dataset_v2.py -v`
Expected: FAIL — `ImportError: build_dataset_v2`

- [ ] **Step 3: 구현 — dataset.py에 추가**

```python
# src/prepare_lib/dataset.py 에 append (기존 import에 json/Path 이미 있음)


def build_dataset_v2(
    synth_report,
    route_report,
    lockfile,
    design_id: str,
    netlist_json,
    encoder_path,
    corpus_manifest_path,
    min_coverage: float = 0.95,  # spec §8 amendment 복사 인용 — 재정의 금지
) -> tuple[list[dict], dict]:
    """v1 행에 frozen encoder 임베딩을 병기 — 같은 행·같은 라벨에서 표현만 다른 비교 (spec §5)."""
    from pretrain_lib.embed import embed_endpoints, load_encoder, sha256_file

    rows, manifest = build_dataset(synth_report, route_report, lockfile, design_id)
    model, vocab, config = load_encoder(encoder_path)
    embs = embed_endpoints(
        json.loads(Path(netlist_json).read_text(encoding="utf-8")), model, vocab, config
    )
    import math

    matched = []
    for r in rows:
        e = embs.get(r["endpoint"])
        # spec §8 NaN/inf 가드 — non-finite 임베딩 endpoint는 미매칭과 동일하게 drop(coverage 반영)
        if e is None or not all(math.isfinite(v) for v in e):
            continue
        matched.append({**r, **{f"emb_{i:02d}": v for i, v in enumerate(e)}})
    coverage = len(matched) / len(rows) if rows else 0.0
    if coverage < min_coverage:
        raise ValueError(
            f"emb coverage {coverage:.3f} < {min_coverage} — netlist/STA endpoint 이름 불일치 의심"
        )
    manifest = {
        **manifest,
        "n_samples": len(matched),
        "emb_dim": config["emb_dim"],
        "emb_coverage": round(coverage, 4),
        "encoder_sha": sha256_file(encoder_path),
        "corpus_manifest_sha": sha256_file(corpus_manifest_path),
    }
    return matched, manifest
```

- [ ] **Step 4: prepare.py CLI 확장**

```python
# prepare.py — main() 교체 (기존 옵션 유지 + v2 3옵션)
@click.command()
@click.option("--synth", required=True, type=click.Path(exists=True), help="합성 후 STA report_checks")
@click.option("--route", required=True, type=click.Path(exists=True), help="라우팅 후 STA report_checks")
@click.option("--lockfile", required=True, type=click.Path(exists=True), help="flow lockfile (sha 앵커)")
@click.option("--design-id", required=True, help="source design 식별자")
@click.option("--out-dir", required=True, type=click.Path(), help="dataset.jsonl + manifest.json 출력 디렉터리")
@click.option("--netlist", type=click.Path(exists=True), default=None, help="netlist.json (v2: 임베딩 병기)")
@click.option("--encoder", type=click.Path(exists=True), default=None, help="frozen encoder .pt (v2)")
@click.option("--corpus-manifest", type=click.Path(exists=True), default=None, help="corpus_manifest.yaml (v2 sha 앵커)")
def main(synth, route, lockfile, design_id, out_dir, netlist, encoder, corpus_manifest) -> None:
    v2_opts = (netlist, encoder, corpus_manifest)
    if any(v2_opts) and not all(v2_opts):
        raise click.UsageError("--netlist/--encoder/--corpus-manifest는 셋 다 필요 (v2 모드)")
    if all(v2_opts):
        from prepare_lib.dataset import build_dataset_v2

        rows, manifest = build_dataset_v2(
            synth, route, lockfile, design_id, netlist, encoder, corpus_manifest
        )
    else:
        rows, manifest = build_dataset(synth, route, lockfile, design_id)
    write_dataset(rows, manifest, out_dir)
    click.echo(f"{manifest['n_samples']} samples → {out_dir} (sha {manifest['flow_lockfile_sha'][:12]})")
```

- [ ] **Step 5: combine v2 지원 — `combine.py` 스키마 검증 확장**

현행 `combine_datasets`는 `frozenset(r.keys()) != _KEYS`로 **emb_* 키를 거부**한다. 함수 전체를 아래로 교체(상단 import에 `re` 추가, `_KEYS` 상수 불변):

```python
# src/prepare_lib/combine.py — combine_datasets 전체 교체본
_EMB_RE = re.compile(r"^emb_\d{2}$")


def combine_datasets(paths: list[Path]) -> list[dict]:
    """여러 설계 dataset.jsonl을 입력 순서대로 concat. 스키마·group_key 분리·emb 키 일치 검증."""
    out, seen_groups = [], set()
    emb_keys: frozenset[str] | None = None  # 첫 파일 기준 — 설계 간 emb_dim 불일치 차단
    for path in paths:
        rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
        if not rows:
            raise ValueError(f"빈 dataset: {path}")
        for r in rows:
            keys = frozenset(r.keys())
            extra = keys - _KEYS
            if not _KEYS <= keys or any(not _EMB_RE.match(k) for k in extra):
                raise ValueError(f"스키마 불일치 {path}: {sorted(r.keys())}")
            if emb_keys is None:
                emb_keys = frozenset(extra)
            elif frozenset(extra) != emb_keys:
                raise ValueError(f"emb 키 불일치 {path}: {sorted(extra)}")
        file_groups = {r.get("group_key") for r in rows}
        if len(file_groups) != 1:
            raise ValueError(f"한 파일은 단일 설계여야 함 {path}: {file_groups}")
        g = next(iter(file_groups))
        if g in seen_groups:
            raise ValueError(f"group_key 중복(LODO 불가): {g}")
        seen_groups.add(g)
        out.extend(rows)
    return out
```

테스트 추가 — `tests/prepare/test_combine.py`에 append (기존 `_row`/`_jsonl` 헬퍼 재사용):

```python
def _row_emb(gk, i, dims=(0, 1)):
    return {**_row(gk, i), **{f"emb_{d:02d}": 0.5 for d in dims}}


def test_combine_accepts_uniform_emb_keys(tmp_path):
    a = _jsonl(tmp_path, "a.jsonl", [_row_emb("gcd", 0), _row_emb("gcd", 1)])
    b = _jsonl(tmp_path, "b.jsonl", [_row_emb("aes", 0)])
    rows = combine_datasets([a, b])
    assert len(rows) == 3 and all("emb_00" in r and "emb_01" in r for r in rows)


def test_combine_rejects_mismatched_emb_dims(tmp_path):
    a = _jsonl(tmp_path, "a.jsonl", [_row_emb("gcd", 0, dims=(0,))])
    b = _jsonl(tmp_path, "b.jsonl", [_row_emb("aes", 0, dims=(0, 1))])
    with pytest.raises(ValueError, match="emb"):
        combine_datasets([a, b])


def test_combine_rejects_non_emb_extra_key(tmp_path):
    bad_row = {**_row("aes", 0), "sneaky": 1.0}
    a = _jsonl(tmp_path, "a.jsonl", [_row("gcd", 0)])
    b = _jsonl(tmp_path, "b.jsonl", [bad_row])
    with pytest.raises(ValueError, match="스키마"):
        combine_datasets([a, b])
```

- [ ] **Step 6: 통과 확인 (기존 prepare 테스트 회귀 포함) + 커밋**

Run: `uv run pytest tests/prepare tests/pretrain -v && uv run ruff check prepare.py src`
Expected: PASS (v1 경로 무변경 — emb 없는 기존 dataset은 `extra=∅`로 그대로 통과)

```bash
git add src/prepare_lib/dataset.py src/prepare_lib/combine.py prepare.py \
        tests/prepare/test_dataset_v2.py tests/prepare/test_combine.py
git commit -m "feat(prepare): build_dataset_v2 — 표형식‖임베딩 병기 + sha 앵커 + coverage/NaN fail-fast + combine v2"
```

---

### Task 10: `guard.py` + orchestrator fail-fast — encoder read-only 강제

**Files:**
- Create: `src/pipeline/guard.py`
- Modify: `src/pipeline/orchestrator.py` (run_generation 시그니처에 kwarg 2개 추가 + 3개 삽입 지점)
- Test: `tests/pipeline/test_guard.py`

**Interfaces:**
- Consumes: `Candidate.src_path`(candidate_gen), dataset 옆 `manifest.json`(write_dataset 규약).
- Produces:
  - `check_candidate_source(src: str) -> list[str]` — 금지 패턴 위반 목록. 패턴: `"models/encoder"`, `"encoder-v1"`, `"pretrain/"`, `"pretrain_lib"` (encoder 로드·재학습 시도 정적 차단, spec §7).
  - `verify_frozen(encoder_path, expected_sha) -> None` — SHA 불일치 시 `RuntimeError` (spec §8 fail-fast: 존재+SHA+차원).
  - orchestrator `run_generation(..., encoder_path=None, encoder_sha=None)`:
    1. 시작 시(auto 여부 무관): 둘 다 주어지면 `verify_frozen` — 실패 시 세대 시작 차단(예외 전파).
    2. `generate_candidates` 직후: 위반 후보는 실행에서 제외하고 결과에 `(c, float("inf"), [])`로 합류(“위반 시 후보 무효” — program.md 계약과 일치, selection이 자동 패배 처리).
    3. `run_all` 직후: `verify_frozen` 재검증 — 후보 subprocess가 encoder 파일을 변조했는지 탐지(변조 시 세대 전체 abort).
  - CLI `main()`: dataset 옆 `manifest.json`에 `encoder_sha`가 있으면 `models/encoder-v1.pt`와 함께 자동 전달.

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/pipeline/test_guard.py
import pytest

from pipeline.guard import check_candidate_source, verify_frozen


def test_clean_source_passes():
    src = "import numpy as np\nimport torch\nX = np.zeros((2, 2))\n"
    assert check_candidate_source(src) == []


def test_encoder_access_is_blocked():
    src = "import torch\nw = torch.load('models/encoder-v1.pt')\n"
    v = check_candidate_source(src)
    assert v and any("encoder" in x for x in v)


def test_pretrain_lib_import_is_blocked():
    assert check_candidate_source("from pretrain_lib.embed import load_encoder\n")


def test_verify_frozen_detects_mutation(tmp_path):
    p = tmp_path / "encoder-v1.pt"
    p.write_bytes(b"frozen-weights")
    import hashlib

    good = hashlib.sha256(b"frozen-weights").hexdigest()
    verify_frozen(p, good)  # OK — 예외 없음
    p.write_bytes(b"mutated!")
    with pytest.raises(RuntimeError, match="SHA"):
        verify_frozen(p, good)


def test_verify_frozen_missing_file(tmp_path):
    with pytest.raises(RuntimeError, match="없"):
        verify_frozen(tmp_path / "nope.pt", "0" * 64)
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/pipeline/test_guard.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: guard.py 구현**

```python
# src/pipeline/guard.py
"""encoder read-only 강제 — 게이트 이전 차단 (spec §7·§8).

정적 소스 검사(후보의 encoder 접근/재학습 시도) + SHA 재검증(변조 탐지) 2중.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

FORBIDDEN_PATTERNS = ("models/encoder", "encoder-v1", "pretrain/", "pretrain_lib")


def check_candidate_source(src: str) -> list[str]:
    return [p for p in FORBIDDEN_PATTERNS if p in src]


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_frozen(encoder_path: str | Path, expected_sha: str) -> None:
    p = Path(encoder_path)
    if not p.exists():
        raise RuntimeError(f"frozen encoder 없음: {p}")
    actual = sha256_file(p)
    if actual != expected_sha:
        raise RuntimeError(
            f"frozen encoder SHA 불일치: expected {expected_sha[:12]}… actual {actual[:12]}…"
        )
```

- [ ] **Step 4: orchestrator 통합**

`src/pipeline/orchestrator.py` 수정 — import에 `from pipeline.guard import check_candidate_source, verify_frozen` 추가 후:

(a) 시그니처: `def run_generation(..., do_git=True, encoder_path=None, encoder_sha=None):`

(b) 함수 첫 줄(디렉터리 생성 전):

```python
    if encoder_path is not None and encoder_sha is not None:
        verify_frozen(encoder_path, encoder_sha)  # spec §8: 세대 시작 fail-fast
```

(c) `cands = generate_candidates(...)` 직후:

```python
    blocked, runnable = [], []
    for c in cands:
        violations = check_candidate_source(Path(c.src_path).read_text(encoding="utf-8"))
        (blocked if violations else runnable).append((c, violations))
    results = run_all([c for c, _v in runnable], Path(dataset), cdir, seeds=seeds)
    # 가드 위반 후보는 실행 없이 무효(inf) — program.md "위반 시 후보 무효" 계약.
    results += [(c, float("inf"), []) for c, _v in blocked]
    if encoder_path is not None and encoder_sha is not None:
        verify_frozen(encoder_path, encoder_sha)  # 후보 subprocess 변조 탐지
```

(기존 `results = run_all(cands, ...)` 줄을 위 블록으로 대체. `results.tsv`·selection은 무변경 — inf는 기존 패배 처리 경로.)

(d) CLI `main()` — dataset manifest에서 자동 발견:

```python
    manifest_path = Path(dataset).parent / "manifest.json"
    encoder_path = encoder_sha = None
    if manifest_path.exists():
        m = json.loads(manifest_path.read_text())
        if "encoder_sha" in m:
            encoder_path = Path(__file__).resolve().parents[2] / "models" / "encoder-v1.pt"
            encoder_sha = m["encoder_sha"]
            # spec §8 fail-fast: 임베딩 차원 일치 — dataset 첫 행의 emb_* 개수 == manifest emb_dim
            first = json.loads(Path(dataset).read_text().splitlines()[0])
            n_emb = sum(1 for k in first if k.startswith("emb_"))
            if n_emb != m["emb_dim"]:
                raise SystemExit(f"임베딩 차원 불일치: dataset {n_emb} != manifest {m['emb_dim']}")
    res = run_generation(..., auto=auto, encoder_path=encoder_path, encoder_sha=encoder_sha)
```

- [ ] **Step 5: orchestrator 통합 테스트 추가**

`tests/pipeline/test_guard.py`에 append (기존 `tests/pipeline/test_orchestrator.py`의 fake gen_fn 패턴 참조 — mock gen_fn이 가드 위반 소스를 내놓으면 그 후보가 inf로 기록되는지):

```python
def test_orchestrator_blocks_violating_candidate(tmp_path):
    import csv

    from pipeline.orchestrator import run_generation

    dataset = tmp_path / "dataset.jsonl"
    dataset.write_text(
        '{"num_stages": 3, "synth_slack_ns": 0.5, "synth_arrival_ns": 1.0, '
        '"max_stage_delay_ns": 0.2, "mean_stage_delay_ns": 0.1, "startpoint_is_ff": 1, '
        '"endpoint_is_ff": 1, "path_group": "clk", "post_route_slack_ns": 0.3, '
        '"group_key": "d1"}\n' * 8
    )
    baseline = tmp_path / "train.py"
    baseline.write_text("import json\nprint(json.dumps({'val_mae': 1.0}))\n")

    def gen_fn(strategy, sdk, baseline_src, program_md):
        return "import torch\nw = torch.load('models/encoder-v1.pt')\n"  # 위반 소스

    run_generation(1, dataset, baseline, "prog", 1, gen_fn, tmp_path, auto=False)
    tsv = (tmp_path / "gen-001" / "results.tsv").read_text()
    rows = list(csv.reader(tsv.splitlines(), delimiter="\t"))
    assert rows[1][3] == "inf"  # median_val_mae — 실행 없이 무효
```

- [ ] **Step 6: 전체 회귀 + 커밋**

Run: `uv run pytest tests/pipeline -v && uv run ruff check src/pipeline`
Expected: PASS (기존 orchestrator 테스트는 kwarg 기본값 None이라 무변경 통과)

```bash
git add src/pipeline/guard.py src/pipeline/orchestrator.py tests/pipeline/test_guard.py
git commit -m "feat(pipeline): encoder read-only 가드 — 정적 소스 검사 + SHA 재검증 fail-fast (spec §7·§8)"
```

---

### Task 11: `b1_head.py` — B1 baseline (임베딩 + 단순 head)

**Files:**
- Create: `pretrain/b1_head.py`
- Test: `tests/pretrain/test_b1_head.py`

**Interfaces:**
- Consumes: v2 dataset.jsonl (`emb_*` 컬럼).
- Produces: train.py와 **동일 CLI 계약** (`--data/--out/--seed` → stdout `{"val_mae": <float>}` + `model.joblib`) — 기존 `run_candidate`/validation 게이트가 그대로 평가 가능(보조 진단, spec §7 B1).

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/pretrain/test_b1_head.py
import json
import subprocess
import sys
from pathlib import Path

B1 = Path(__file__).resolve().parents[2] / "pretrain" / "b1_head.py"


def test_b1_cli_contract(tmp_path):
    rows = []
    for i in range(40):
        rows.append({
            "num_stages": 3, "synth_slack_ns": 0.5, "synth_arrival_ns": 1.0,
            "max_stage_delay_ns": 0.2, "mean_stage_delay_ns": 0.1,
            "startpoint_is_ff": 1, "endpoint_is_ff": 1, "path_group": "clk",
            "post_route_slack_ns": 0.1 * i, "group_key": f"d{i % 2}",
            "emb_00": 0.1 * i, "emb_01": -0.05 * i,
        })
    data = tmp_path / "dataset.jsonl"
    data.write_text("\n".join(json.dumps(r) for r in rows))
    out = tmp_path / "out"
    proc = subprocess.run(
        [sys.executable, str(B1), "--data", str(data), "--out", str(out), "--seed", "0"],
        capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 0, proc.stderr
    val = json.loads(proc.stdout.strip().splitlines()[-1])
    assert "val_mae" in val and (out / "model.joblib").exists()
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/pretrain/test_b1_head.py -v`
Expected: FAIL — B1 파일 없음(returncode != 0)

- [ ] **Step 3: 구현**

```python
# pretrain/b1_head.py
"""B1 — 새 표현 naive baseline: 임베딩만 + 사람이 1회 작성한 단순 head (spec §7).

train.py와 동일 CLI 계약 — 기존 runner/validation 게이트가 그대로 평가한다.
사람 소유 · 변형 금지(B1은 고정 비교점).
"""

from __future__ import annotations

import json
from pathlib import Path

import click
import joblib
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import GroupShuffleSplit, train_test_split


def load_rows(p):
    return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]


def build_xy(rows):
    cols = sorted(k for k in rows[0] if k.startswith("emb_"))
    X = np.array([[float(r[c]) for c in cols] for r in rows])
    y = np.array([float(r["post_route_slack_ns"]) for r in rows])
    return X, y, [r["group_key"] for r in rows]


def split(X, y, groups, seed=0):
    # train.py split() 복사 인용 — 동일 프로토콜 비교 보장.
    if len(set(groups)) >= 2:
        gss = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=seed)
        return next(gss.split(X, y, groups=groups))
    idx = np.arange(len(y))
    return train_test_split(idx, test_size=0.25, random_state=seed)


@click.command()
@click.option("--data", required=True, type=click.Path(exists=True))
@click.option("--out", required=True, type=click.Path())
@click.option("--seed", default=0, type=int)
def main(data, out, seed):
    rows = load_rows(data)
    X, y, groups = build_xy(rows)
    tr, va = split(X, y, groups, seed)
    model = Ridge(alpha=1.0).fit(X[tr], y[tr])
    mae = float(mean_absolute_error(y[va], model.predict(X[va])))
    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, out_dir / "model.joblib")
    click.echo(json.dumps({"val_mae": mae}))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 통과 확인 + 커밋**

Run: `uv run pytest tests/pretrain/test_b1_head.py -v && uv run ruff check pretrain`
Expected: PASS

```bash
git add pretrain/b1_head.py tests/pretrain/test_b1_head.py
git commit -m "feat(pretrain): B1 baseline — 임베딩+Ridge head, train.py CLI 계약 동일 (spec §7)"
```

---

### Task 12: 문서 갱신 — program.md 재작성 + PRD.md + CLAUDE.md

**Files:**
- Modify: `program.md` (입력 데이터·변형 허용·절대 제약·관찰 힌트 섹션)
- Modify: `PRD.md` (§7 DATASET 행)
- Modify: `CLAUDE.md` (Implementation Status·Architecture·Repository Map)

**Interfaces:**
- Consumes: Task 9 v2 스키마(`emb_00`…), Task 10 가드 계약.
- Produces: 에이전트/Operator가 읽는 계약 문서 — 코드와 문장 단위로 일치해야 함.

- [ ] **Step 1: program.md 수정**

다음 편집(기존 문구 유지 최대, 변경분만):

- "## 입력 데이터" 문단에 추가:
  ```markdown
  **v2 (2026-07-02~)**: 각 행에 frozen encoder 임베딩 `emb_00`…`emb_31`(32차원 float)이 병기된다.
  임베딩은 합성 netlist의 endpoint 중심 그래프를 self-supervised graph autoencoder로 인코딩한 것 —
  설계-불변 구조 신호를 담으려는 시도다. 활용(그대로/선택/결합/무시)은 전적으로 너의 선택.
  ```
- "## 변형 허용 범위"에 추가: `- 임베딩 활용 전략: emb_* 컬럼 선택·결합·차원 축소, torch 기반 head(MLP 등) 자유.`
- "## 절대 제약" 수정:
  - `신규 의존성 금지 — sklearn, numpy, joblib, click, stdlib만 import.` → `신규 의존성 *설치* 금지 — sklearn, numpy, joblib, click, torch(사전 설치), stdlib만 import.`
  - 추가: `- **frozen encoder 접근 금지**: models/encoder-v1.pt·pretrain/ 참조 시 후보 즉시 무효(가드가 실행 전 차단). 임베딩은 이미 dataset에 있다 — encoder를 다시 부를 이유가 없다.`
  - `GPU·딥러닝 프레임워크 금지` → `GPU 금지(고정 CPU 예산). torch는 CPU 한정 허용.`
- "## 관찰 힌트" 끝에 추가:
  ```markdown
  - gen-002~008 (7세대, v1 표형식): in-loop `val_mae`는 3.7→0.53까지 내려갔지만 교차설계 T1은 7세대
    연속 `indistinguishable` — in-loop 지표 개선을 맹신하지 말 것. v2 임베딩은 이 벽(설계-불변 표현
    부재 가설)에 대한 질적 전환 시도다. B0(현행 표형식 winner) 대비 `distinguishable`이 판정 질문.
  ```

- [ ] **Step 2: PRD.md §7 DATASET 행 수정**

```markdown
| **DATASET** | id, source_design, feature_set, label_metric, s3_uri, **flow_lockfile_sha**, **encoder_sha**, **corpus_manifest_sha** | flow 1회로 생성된 고정 라벨셋. `flow_lockfile_sha`+`encoder_sha`+`corpus_manifest_sha`가 재현성 앵커 (FR-1, v2 spec §5). |
```

- [ ] **Step 3: CLAUDE.md 갱신**

- Implementation Status 표에 행 추가:
  `| pretrain/ encoder 층 (v2) | 코퍼스 manifest·graph AE·채택 게이트·v2 dataset | ✅ 코드 완료 (실행 Task 13~15 상태는 커밋 시점 기준으로 기입) |`
- Architecture 요약에 한 줄: `- pretrain/ — frozen encoder 사전학습 층 (사람 소유·에이전트 변형 금지, v2 spec §4).`
- Repository Map에: `docs/superpowers/specs/2026-07-02-frozen-encoder-representation-redesign-design.md — v2 재설계 spec.`
- Code Conventions/Before Non-Trivial Work의 frozen 목록에 `models/encoder-v1.pt` 추가.

- [ ] **Step 4: 정합 검증 + 커밋**

Run: `grep -n "emb_00\|encoder-v1\|torch" program.md PRD.md CLAUDE.md` — 세 문서가 같은 이름(emb_00…emb_31, models/encoder-v1.pt)을 쓰는지 눈으로 확인.

```bash
git add program.md PRD.md CLAUDE.md
git commit -m "docs: v2 계약 문서화 — program.md 임베딩·torch·가드, PRD DATASET 앵커 확장, CLAUDE.md 갱신"
```

---

### Task 13: [실행] 코퍼스 합성 — 20설계 netlist.json + exclusions 커밋

**Files:**
- Create: `pretrain/corpus/<design>/netlist.json` (manifest 설계 수만큼)
- Modify: `pretrain/corpus_manifest.yaml` (exclusions append — 실패 시)

전제: Task 1·8 완료, 로컬 docker 가동. 비용 0(로컬 CPU). arm64 Mac에서 x86 에뮬레이션이라 설계당 수 분~수십 분 — 백그라운드 배치.

- [ ] **Step 1: 소형 설계 1개로 파이프라인 검증**

Run: `uv run python pretrain/synth_corpus.py --manifest pretrain/corpus_manifest.yaml --out pretrain/corpus --designs gcd`
Expected: `{"design": "gcd", "ok": true, ...}` + `pretrain/corpus/gcd/netlist.json` 생성. 이어서:
`uv run python -c "import json; from pretrain_lib.graph import build_endpoint_graphs; g=build_endpoint_graphs(json.load(open('pretrain/corpus/gcd/netlist.json'))); print(len(g))"`
Expected: endpoint 수 ≥ 10 (gcd는 ~50 기대). 컨테이너 내부 경로(FLOW 상수·이미지명)가 다르면 여기서 수정 후 재시도.

- [ ] **Step 2: 전체 배치 실행**

Run: `uv run python pretrain/synth_corpus.py --manifest pretrain/corpus_manifest.yaml --out pretrain/corpus 2>&1 | tee pretrain/corpus/synth.log`
Expected: 설계별 JSON 라인. 실패 설계는 exclusions에 `{design, reason}` append(사유는 사전 고정 2건 중 하나만).

- [ ] **Step 3: 커밋**

netlist.json은 설계당 수~수십 MB 가능 — 100MB 초과 파일이 있으면 corpus는 커밋하지 않고 `pretrain/corpus/README.md`에 재생성 커맨드만 커밋(결정성은 digest+manifest가 보장). 그 외에는 corpus 전체 커밋.

```bash
du -sh pretrain/corpus/*
git add pretrain/corpus_manifest.yaml pretrain/corpus/synth.log  # (+ corpus if small)
git commit -m "data(pretrain): 코퍼스 합성 완료 — exclusions 기록 (사전 고정 사유만)"
```

---

### Task 14: [실행] encoder 사전학습 + 채택 게이트 판정 + artifact 커밋

**Files:**
- Create: `models/encoder-v1.pt`, `models/encoder-v1.report.json`
- Create: `pretrain/eval_encoder.py` (게이트 판정 스크립트 — 아래 코드)

전제: Task 13 corpus + Task 15의 라벨 4설계 netlist(§선형 probe에 v2 rows 필요 — 이 Task의 probe 단계는 Task 15 Step 1 이후 실행. 순서: 14-1~2 → 15-1 → 14-3~4).

- [ ] **Step 1: 학습 실행 (로컬 MPS, 비용 0)**

Run: `uv run python pretrain/train_encoder.py --corpus-dir pretrain/corpus --manifest pretrain/corpus_manifest.yaml --out models/ --seed 0`
Expected: `{"best_val_loss": …, "naive_baseline_loss": …, "stopped_epoch": …}` — spec §6.2: best_val_loss < naive_baseline_loss 여야 진행.

- [ ] **Step 2: 게이트 판정 스크립트 작성**

```python
# pretrain/eval_encoder.py
"""채택 게이트 일괄 판정 → encoder-v1.report.json에 verdict 병합 (spec §6.5)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pretrain_lib.embed import embed_endpoints, load_encoder  # noqa: E402
from pretrain_lib.encoder_gates import (  # noqa: E402
    collapse_diagnostics,
    encoder_verdict,
    linear_probe,
)
from pretrain_lib.manifest import load_manifest  # noqa: E402


@click.command()
@click.option("--encoder", required=True, type=click.Path(exists=True))
@click.option("--report", required=True, type=click.Path(exists=True))
@click.option("--manifest", required=True, type=click.Path(exists=True))
@click.option("--corpus-dir", required=True, type=click.Path(exists=True))
@click.option("--label-dataset", required=True, type=click.Path(exists=True),
              help="v2 dataset.jsonl (emb_* 포함, 4설계 combine)")
def main(encoder, report, manifest, corpus_dir, label_dataset):
    model, vocab, config = load_encoder(encoder)
    m = load_manifest(manifest)
    embs = []
    for d in m["encoder_val_designs"]:  # spec §6.3: encoder-val 임베딩으로 진단
        nl = json.loads((Path(corpus_dir) / d / "netlist.json").read_text())
        embs += list(embed_endpoints(nl, model, vocab, config).values())
    diag = collapse_diagnostics(np.array(embs))
    rows = [json.loads(x) for x in Path(label_dataset).read_text().splitlines() if x.strip()]
    probe = linear_probe(rows)
    rep = json.loads(Path(report).read_text())
    verdict = encoder_verdict(rep, diag, probe)
    rep.update({"collapse": diag, "linear_probe": probe, "verdict": verdict})
    Path(report).write_text(json.dumps(rep, indent=2))
    click.echo(json.dumps(verdict))
    if not verdict["adopt"]:
        raise SystemExit(1)  # 기각 — 루프 투입 금지 (사전학습 반복/중단은 Operator 결정)


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: 게이트 판정 실행** (Task 15 Step 1 완료 후)

Run: `uv run python pretrain/eval_encoder.py --encoder models/encoder-v1.pt --report models/encoder-v1.report.json --manifest pretrain/corpus_manifest.yaml --corpus-dir pretrain/corpus --label-dataset experiments/multidesign/dataset-v2-4design.jsonl`
Expected: `{"adopt": true, ...}` — 기각 시 여기서 중단하고 Operator에게 보고(반복/중단 결정, spec §6).

- [ ] **Step 4: artifact 커밋 (판정 근거 사후 검사 가능성 — spec §6.5)**

```bash
shasum -a 256 models/encoder-v1.pt   # manifest encoder_sha와 대조
git add models/encoder-v1.pt models/encoder-v1.report.json pretrain/eval_encoder.py
git commit -m "feat(models): encoder-v1 채택 — 게이트(재구성·붕괴·probe) 판정 artifact 포함 (spec §6)"
```

---

### Task 15: [실행] 라벨 4설계 재합성 + v2 dataset 생성 + B1 기록

**Files:**
- Create: `pretrain/corpus/{gcd,aes,ibex,jpeg}/netlist.json` (label 설계 재합성)
- Create: `experiments/multidesign/dataset-v2-4design.jsonl` + `manifest.json`
- Create: `experiments/v2-probe/b1.json` (B1 평가 기록)

- [ ] **Step 1: 라벨 4설계 netlist 재합성 + v2 dataset 생성**

Run (설계별 4회 — synth/route rpt·lockfile은 기존 `experiments/real-<d>-fargate/` 자산 재사용):
```bash
uv run python pretrain/synth_corpus.py --manifest pretrain/corpus_manifest.yaml --out pretrain/corpus --designs gcd,aes,ibex,jpeg
for d in gcd aes ibex jpeg; do
  uv run python prepare.py --synth experiments/real-$d-fargate/synth.rpt \
    --route experiments/real-$d-fargate/route.rpt \
    --lockfile experiments/real-$d-fargate/versions.txt --design-id $d \
    --netlist pretrain/corpus/$d/netlist.json --encoder models/encoder-v1.pt \
    --corpus-manifest pretrain/corpus_manifest.yaml \
    --out-dir experiments/real-$d-fargate/dataset-v2
done
```
Expected: 설계별 `N samples` 출력, **coverage fail-fast 미발동**(<0.95면 여기가 재설계 리스크 실현 지점 — 같은 digest 재합성인데도 이름 드리프트 → Operator 보고 후 매칭 규칙 조정은 별도 결정).
(주: 실제 rpt/lockfile 파일명이 다르면 `ls experiments/real-gcd-fargate/`로 확인 후 치환. gcd는 real-gcd/일 수 있음.)

이후 combine (기존 `prepare_lib/combine.py` 재사용):
```bash
uv run python -c "
from pathlib import Path
from prepare_lib.combine import combine_datasets
import json
rows = combine_datasets([Path(f'experiments/real-{d}-fargate/dataset-v2/dataset.jsonl') for d in ['gcd','aes','ibex','jpeg']])
out = Path('experiments/multidesign/dataset-v2-4design.jsonl')
out.write_text('\n'.join(json.dumps(r, sort_keys=True) for r in rows) + '\n')
print(len(rows))
"
```
Expected: ~7194 이하(coverage 드랍만큼 감소). Task 9 Step 5의 combine v2 확장이 emb_* 키를 보존·검증한다 — 첫 행에 `emb_00`이 있는지 grep으로 재확인.
combine 후 manifest도 생성: 4설계 manifest의 encoder_sha 동일함을 확인하고 대표 manifest를 `experiments/multidesign/manifest.json`으로 복사(orchestrator 자동 발견 규약 — Task 10).

- [ ] **Step 2: (여기서 Task 14 Step 3~4 실행 — 게이트 판정 + encoder 커밋)**

- [ ] **Step 3: B1 평가 기록**

Run:
```bash
mkdir -p experiments/v2-probe
for s in 0 1 2 3 4; do
  uv run python pretrain/b1_head.py --data experiments/multidesign/dataset-v2-4design.jsonl \
    --out /tmp/b1-$s --seed $s
done > experiments/v2-probe/b1.json
```
Expected: seed별 `{"val_mae": …}` 5줄 — B0(train.py) 동일 seed median과 나란히 기록(보조 진단, spec §7: B1 대비는 승격 판정이 아님).

- [ ] **Step 4: 커밋 + 전체 회귀**

Run: `uv run pytest -q && uv run ruff check src pretrain prepare.py`
Expected: 전체 PASS

```bash
git add experiments/real-*/dataset-v2 experiments/multidesign/dataset-v2-4design.jsonl \
        experiments/multidesign/manifest.json experiments/v2-probe/
git commit -m "data(v2): 표형식‖임베딩 병기 4설계 dataset + B1 기록 — gen-009(v2 사이클) 준비 완료"
```

---

## 완료 기준 (판정 준비 상태)

1. `pretrain/corpus_manifest.yaml`이 학습 *이전* 커밋에 존재 (git log로 검증 가능).
2. `models/encoder-v1.pt` + `encoder-v1.report.json`(verdict.adopt=true) 커밋 — 게이트 4종 근거 포함.
3. `experiments/multidesign/dataset-v2-4design.jsonl` — 각 행 8 표형식 + emb_00…31 + 라벨, manifest에 3-sha 앵커.
4. `uv run pytest` 전체 PASS(기존 123 + 신규), ruff clean.
5. 다음 세대(gen-009)는 기존 커맨드 그대로: `uv run python src/pipeline/orchestrator.py --gen 9 --dataset experiments/multidesign/dataset-v2-4design.jsonl --auto` — 게이트 체인 불변, B0 = 현행 train.py.

## 범위 밖 (spec §10 재확인)

CircuitNet 전이, contrastive 사전학습, 멀티태스크, encoder unfreeze, auto-gate 코드화, reasoning trace. SageMaker Spot fallback(로컬 MPS 부족 시)은 Operator 동의 후 별도 — 본 plan은 로컬 전제.
