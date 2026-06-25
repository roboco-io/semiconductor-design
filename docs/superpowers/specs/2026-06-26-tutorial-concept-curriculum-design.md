# Tutorial Concept Curriculum — 설계 spec

> created: 2026-06-26 · status: approved-pending-user-review
> 대상 산출물: 루트 `tutorial/` 폴더 (개념 커리큘럼)
> 정합: [`INTENT.md`](../../../INTENT.md) (비전문가 empowerment + 이해가능성 novelty 축), CLAUDE.md

## 1. 목표

ML은 알지만 **반도체/EDA는 처음인 개발자**가, 이 저장소를 이해하는 데 필요한 *전이 가능한 개념*을
다이어그램 중심으로 단계별 학습하는 커리큘럼. 프로젝트 서사가 아니라 **개념 교재**다.

## 2. 학습자 가정 / 비목표

**가정(이미 앎)**: MAE·과적합·train/val split·교차검증·통계 유의성·일반화 — 다시 가르치지 않는다.
재좌표화만 한다(무작위 split → *설계 단위* LODO, in-distribution → *교차설계*).

**비목표(YAGNI)**:
- ML 기초 재교육.
- `docs/TUTORIAL.md`(프로젝트 서사)·`experiments/README.md`(세대 해설) 내용 복제 → **링크**로 연결.
- 기존 용어 사전 복제 → `docs/TUTORIAL.md` 용어 사전 **링크**(필요 시 EDA 항목만 보강).
- AWS 인프라 레슨(범위 제외 — Q3에서 드롭).
- 전체 파이프라인 재현 실습(AWS·실데이터 의존이라 무거움). "이 repo에선" 포인터 + 1줄 명령 예시 수준만.

## 3. 구조

루트 `tutorial/` 아래 linear 5레슨 + 인덱스 + 다이어그램 자산 폴더.

```
tutorial/
  README.md              # 커리큘럼 맵·대상·사용법·개념 의존 그래프(Mermaid)
  00-orientation.md      # 큰 그림: 이 repo가 한 일 1장 + 독자 포지셔닝
  01-eda-flow.md         # 반도체 EDA 기초
  02-surrogate-models.md # surrogate 개념 + ML-for-EDA landscape
  03-autoresearch-loop.md# AutoResearch 진화 루프
  04-gates-and-the-wall.md # (capstone) 권력분립 게이트 + 교차설계 벽
  assets/                # 커스텀 일러스트 .drawio 소스 + export된 .svg
```

**레슨 공통 골격**: ① 직관(ML 개념을 EDA 두 축으로 재좌표화) → ② 다이어그램 → ③ "이 repo에선"
실제 파일/Learning 포인터 → ④ grounded 더 읽을거리 → ⑤ 짧은 이해 점검(2~3문, 개발자용·선택).

## 4. 다이어그램 매체 규칙 (하이브리드)

- **Mermaid (구조·흐름)**: 마크다운 내장, GitHub/IDE 자동 렌더. 파이프라인·진화루프·게이트체인·의존맵.
- **draw-diagram(.drawio → .svg export, 직관 은유)**: 커스텀 시각 은유 2~3장. `.drawio` 소스와
  export한 `.svg`를 둘 다 `tutorial/assets/`에 커밋, 레슨에서 `![](assets/xxx.svg)`로 인라인.
  draw-diagram 스킬로 제작.

**커스텀 일러스트 3장(draw-diagram)**:
1. `slack-margin.svg` (01) — 클럭 주기 막대에 required vs arrival, slack = 여유 마진(양수=통과).
2. `feature-label-timeline.svg` (02) — EDA 흐름 시간축; feature=합성 직후 캡처, label=최종 라우팅,
   surrogate가 그 *시간 간극*을 예측.
3. `the-wall.svg` (04) — 2선 그래프: 세대축에서 in-loop val_mae 하강 vs 교차설계 T1 평탄(indistinguishable).

**Mermaid 6장**: 의존맵(README)·큰그림(00)·RTL→GDSII 파이프라인(01)·느린sim vs 빠른예측(02)·
진화루프 ratchet + "이 repo가 바꾼 점"(03)·4단 게이트 체인(04).

## 5. 레슨별 명세

### 00-orientation.md
- 한 장 큰 그림: EDA flow 1회 → prepare(고정) → train(변형) → 진화루프+게이트.
- 독자 포지셔닝: "당신은 ML은 안다. 새로운 건 (1) feature/label의 *시간 분리*, (2) fold가 *설계 단위*."
- 커리큘럼 사용법 + 기존 문서와의 관계(서사는 docs/TUTORIAL.md, 세대는 experiments/README.md).

### 01-eda-flow.md
- RTL→GDSII: 합성(Yosys)→배치·라우팅(OpenROAD)→STA(OpenSTA). 오픈소스 앵커.
- 핵심 숫자: **타이밍 슬랙**(여유 마진, 양수=통과), PPA, routability.
- 다이어그램: 파이프라인(Mermaid) + `slack-margin.svg`.
- repo 포인터: `docker/eda-flow*`, `cdk/`, `experiments/real-*-fargate/`.

### 02-surrogate-models.md
- 왜 시뮬 대신 예측: 느린 sign-off를 빠른 근사로. feature(합성직후)→label(최종 슬랙).
- ML-for-EDA landscape: CircuitNet/2.0, RouteNet, Net2, MasterRTL. (SNS는 grounded 미검증 → 제외/표기.)
- 다이어그램: 느린sim vs 빠른예측(Mermaid) + `feature-label-timeline.svg`.
- repo 포인터: `prepare.py`(frozen 계약), `data/`, `docs/TRAIN.md`.

### 03-autoresearch-loop.md
- Karpathy AutoResearch: 연구=검색, 단일 `train.py` 변형, 고정 예산, git ratchet(개선시 keep/아니면 revert).
- 이 repo가 바꾼 점: 단일 lineage → population + **median 선택** + **객관적 게이트** + 교차설계 축.
- 정직성: AutoResearch 원본은 *no human in loop*("human asleep"); 이 repo는 *비전문가가 방향만*.
- 다이어그램: 진화루프 ratchet + 변경점 대비표(Mermaid).
- repo 포인터: `program.md`, `train.py`, `src/pipeline/`, `config.yaml`.

### 04-gates-and-the-wall.md (capstone)
- 4단 권력분립: median → LODO → 교차설계 T1 → Codex. 생성자≠판정자.
- 교차설계 벽: in-loop val_mae↓인데 교차설계 일반화는 평탄.
- **정직성 프레이밍(핵심)**: 이 벽("in-distribution 최적화 ≠ 교차설계 일반화")은 이 프로젝트의
  신규 발견이 *아니라* ML-for-EDA의 **알려진 현상**(SwiftCTS·EDALearn·robustness 문헌). 본 repo의
  기여는 *발견*이 아니라 (1) **자율 루프가 이 벽을 스스로 재현**, (2) **게이트가 5건 위양성 승격 차단**.
- 다이어그램: 4단 게이트 체인(Mermaid) + `the-wall.svg`.
- repo 포인터: `wiki/gate-chain.md`, `src/pipeline/` 게이트, `experiments/gen-004~008`, INTENT Learnings.

## 6. Grounded 출처 (더 읽을거리, Perplexity citation 검증)

OpenROAD(RTL→GDSII)·OpenROAD-flow-scripts·CircuitNet 2.0(ICLR2024)·Xie ML-for-EDA survey·
MasterRTL(ICCAD2023)·Circuit-as-Set-of-Points(NeurIPS2023)·AutoResearch 해설·
SwiftCTS(2026 OOD/LODO)·EDALearn·NSF robustness. (URL은 구현 시 각 레슨 §4에 인용.)

## 7. 기존 문서와의 관계

| 문서 | 역할 | tutorial/와 관계 |
|---|---|---|
| `docs/TUTORIAL.md` | 프로젝트 서사 + 용어 사전 | 개념 학습 후 "전체 서사" 링크. 용어 사전 재사용 |
| `experiments/README.md` | 세대별 해설 | capstone에서 "실제 세대 증거" 링크 |
| `wiki/gate-chain.md` | 게이트 정의 | 04 레슨이 인용 |

## 8. 검증 (완료 기준)

- 5레슨 + README + assets 존재, 내부 링크·repo 파일 포인터 유효(끊긴 링크 0).
- Mermaid 6장 렌더 가능(문법 유효), .svg 3장 인라인 표시.
- 개념 서술이 grounded 출처와 모순 없음(특히 SNS 미사용, 교차설계=알려진 현상 프레이밍).
- INTENT 정합: prepare.py frozen 등 *사실*을 왜곡하지 않음. 비전문가 이해가능성 축에 기여.

## 9. INTENT 정합

본 산출물은 INTENT "비전문가 empowerment + 이해가능성" novelty 축의 직접 구현이다(What §"방향·이해
인터페이스"). Not 위반 없음 — 코드/게이트/frozen 계약 불변, 문서만 추가. 정량 임계값 재정의 없음.
