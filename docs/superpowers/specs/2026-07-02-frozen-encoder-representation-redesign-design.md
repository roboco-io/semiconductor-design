# 설계 spec — Frozen Encoder 표현 재설계 (surrogate v2)

> 작성: 2026-07-02 · status: 설계 승인됨(브레인스토밍 Q&A 6문항) · Codex 검토 게이트 대기
> 선행: [2026-05-29 피벗 설계](2026-05-29-autoresearch-eda-surrogate-pivot-design.md) ·
> [PAPER.ko.md](../PAPER.ko.md) §7–8 · INTENT.md Learnings 2026-06-24
> 후속: 구현 plan(writing-plans) → spec/plan/code 각 단계 Codex 검토 게이트

## 1. 배경과 문제

8세대(gen-001~008) 자율 진화의 가장 견고한 발견은 **"in-loop val_mae 개선 ≠ 교차설계 일반화
우위"**다 — median val_mae는 3.7→0.53까지 내려갔지만 교차설계 T1은 7세대 연속
`indistinguishable`. 양적 조정(재추첨·데이터 추가)으로는 이 벽을 못 넘는다는 것이 논문(PAPER)의
결론이며, 향후 연구로 **질적 전환(설계-불변 표현 명시 유도)**을 지목했다.

본 spec은 그 질적 전환의 실행 설계다: **표현(representation)·데이터·모델 계열을 재설계**하되,
루프/게이트 프레임(AutoResearch 4-step + 4단 게이트)은 유지한다.

## 2. 결정 lineage (브레인스토밍 Q&A)

| # | 질문 | 결정 |
|---|---|---|
| 0 | 리포 전략 | **현재 리포 유지** + archive 브랜치 패턴 |
| 1 | 재설계 동기 | 표현 + 문제/데이터 + 모델 계열 (루프 프레임은 유지) |
| 2 | 데이터 축 | 하이브리드 → **조사 후 수정: 자가생성 self-supervised 사전학습** (§3) |
| 3 | 예측 타깃 | **타이밍 유지** (합성 직후 → post-route endpoint slack) |
| 4 | 모델/컴퓨트 | **사전학습 encoder 분리** — 사람 1회 학습 후 frozen, 루프는 head만 탐색 |
| 5 | 성공 정의 | **판정 지향** — "질적 전환이 벽을 넘는가"의 사전 고정 게이트 판정 자체가 산출물 |

## 3. CircuitNet 2.0 기각 사유 (grounded 조사 결과)

당초 "CircuitNet 표현 학습 + 자가생성 held-out" 하이브리드를 선택했으나, grounded 조사가
전제를 반증해 **자가생성 사전학습으로 수정**했다:

1. **라벨 불일치** — CircuitNet 2.0 타이밍 태스크는 net delay(4코너, SDF 기반) 예측이고
   endpoint slack 라벨은 미제공 ([공식 문서](https://circuitnet.github.io/feature/timing%20features.html)).
2. **단면 불일치** — 입력이 post-placement 핀 좌표(DEF)로, 우리의 "합성 직후 feature" 정식화와
   다름 (동일 출처).
3. **도메인 갭 미검증** — 상용 14nm PDK(sanitize) → sky130/OpenROAD 전이는 검증 연구 부재.
   AdaTimer([TCAD 2025](https://www.cse.cuhk.edu.hk/~byu/papers/J131-TCAD2025-AdaTimer.pdf))는
   노드 간 naive 전이가 실패하고 명시적 정렬이 필요함을 실증 — 표현 효과와 도메인 갭이
   교란 중첩되어 "판정 지향" 목표와 상충. 용량 314GB도 부담.
4. **대안 근거** — PreRoutGNN([AAAI 2024](https://arxiv.org/html/2403.00012v2))이
   self-supervised graph autoencoder 사전학습 → freeze → slack head fine-tune으로 최대 29%
   개선을 실증. 사전학습은 라벨이 불필요하므로 **값싼 합성만으로 코퍼스 확보 가능**.

CircuitNet 전이는 폐기가 아니라 **2차 probe로 연기** — 본 사이클 판정 후 별도 결정.

## 4. 아키텍처 (3단, frozen 경계 확장)

```
[1] pretrain/            신규 · 사람 소유 · frozen
    ORFS sky130 설계 ~20개 → Yosys 합성만(place&route 없음) → netlist 그래프 코퍼스
    → self-supervised graph autoencoder 사전학습
    → models/encoder-v1.pt + SHA 앵커

[2] prepare.py           재작성 · frozen 유지
    라벨 4설계(gcd/aes/ibex/jpeg) → endpoint별 (구 표형식 feature ‖ encoder 임베딩)
    + post-route endpoint slack 라벨 → surrogate-v2 데이터셋

[3] 진화 루프             src/pipeline 대부분 유지
    train.py: 임베딩·표형식 feature 조합 위 head 탐색 (encoder read-only)
    → 기존 4단 게이트(median → LODO → 교차설계 T1 → Codex) → 승격
```

원칙:
- **frozen 경계의 확장**: prepare.py(데이터·평가)에 더해 encoder도 frozen 자산.
  공정 비교 보장 논리 동일.
- **비용 분리**: 사전학습 층은 라벨 불필요 → 합성(수 분/설계, CPU)만으로 20+설계.
  비싼 place&route 완주는 라벨 4설계로 유지.
- **판정의 깨끗함**: 전 구간 sky130/ORFS 단일 도메인 → 결과가 표현 효과로 귀속.

## 5. 데이터 파이프라인

- **코퍼스 manifest 선커밋 (사전 고정)**: encoder 학습·probe 실행 **전에**
  `pretrain/corpus_manifest.yaml`을 커밋한다 — ① 설계 목록(ORFS 동봉 sky130 호환 설계,
  목표 ~20개; 목록 확정은 plan 단계의 ORFS 리포 조사로 하되 *확정본이 먼저 커밋*되어야 학습 시작
  가능), ② encoder-val 설계 지정(§6), ③ 제외 규칙. 제외 규칙은 다음 둘로 사전 고정:
  (a) Yosys 합성 exit code ≠ 0, (b) 추출 endpoint 수 < 10. 그 외 사유의 사후 임의 제외 금지 —
  코퍼스 구성이 사후 튜닝 노브가 되는 것을 차단한다. 제외 발생 시 manifest에 사유를 append해
  커밋(조용한 누락 금지).
- **그래프 변환**: netlist → endpoint 중심 그래프(셀 타입, 팬인/팬아웃 연결, 타이밍 아크 통계).
  결정성 보장: 동일 netlist → 동일 그래프 (테스트로 강제).
- **라벨 데이터셋**: 기존 4설계 7194행 자산 재사용. prepare.py가 endpoint별로 구 표형식
  feature와 frozen encoder 임베딩을 **병기** 추출 — 같은 행·같은 라벨에서 표현만 다른
  직접 비교(B0 vs 새 후보)를 가능케 한다.
- **재현성 앵커**: `DATASET` 엔티티(PRD **§7 데이터 모델**의 속성 표: id, source_design,
  feature_set, label_metric, s3_uri, flow_lockfile_sha)에 두 필드를 추가한다 —
  `encoder_sha`(models/encoder-v1.pt의 SHA-256), `corpus_manifest_sha`(corpus_manifest.yaml의
  SHA-256). 신규 엔티티 없음(경량 확장).

## 6. Encoder 사전학습

- **방식**: self-supervised graph autoencoder(마스킹-재구성). 근거: PreRoutGNN.
  contrastive(CircuitEncoder식)는 대안으로 기록만 — 본 사이클 미채택(YAGNI).
- **의존성**: PyTorch(+PyG)를 `pyproject.toml` optional-deps 그룹 `pretrain`으로 격리 추가.
- **컴퓨트**: 로컬 Mac(MPS) 우선(비용 0). 부족 시에만 SageMaker Spot GPU 1회 —
  실 과금이므로 실행 전 Operator 동의(기존 D4 비용 게이트 관례).
- **encoder 채택 게이트 (사전 고정 — 본 spec이 임계값의 single source, 학습 전 커밋)**:
  1. **코퍼스 분리**: corpus_manifest.yaml이 지정한 encoder-val 설계 2개는 사전학습에서 제외하고
     검증 전용으로 사용(설계 단위 분리 — 라벨 4설계와도 겹치지 않아야 함).
  2. **reconstruction 수렴**: encoder-val loss가 10 epoch 연속 개선 없으면(patience=10) 학습 종료.
     채택 조건: 최종 encoder-val reconstruction loss < **naive 상수 재구성 baseline**(encoder-train
     노드 feature 평균으로 일괄 예측했을 때의 loss). 미달 = 기각.
  3. **붕괴 진단**: encoder-val 임베딩에서 ① 차원별 표준편차의 중앙값 > 1e-6, ② 무작위 endpoint
     쌍 1000개의 평균 pairwise cosine similarity < 0.99. 하나라도 위반 = 기각(모든 입력이 같은
     벡터로 붕괴하는 trivial 해 차단).
  4. **선형 probe**: 라벨 4설계 데이터셋에서 "임베딩만 → 선형 회귀"의 **5-seed(0,1,2,3,4) median
     val MAE**가 "구 표형식 feature만 → 선형 회귀"의 동일 프로토콜 값 **이하**일 것. seed 집합은
     기존 harness의 평가 seed(`src/pipeline/runner.py` `run_candidate_multiseed` 기본값
     `(0,1,2,3,4)`)를 그대로 사용하고, split은 train.py 계약의 seed 기반 내부 split 방식을 따른다
     (복사 인용 — 재정의 금지).
  5. **판정 artifact 커밋**: loss curve·진단 수치·probe 결과를 `models/encoder-v1.report.json`으로
     커밋 — 판정 근거가 사후 검사 가능해야 한다.
  - 1–4 중 하나라도 미달이면 encoder를 루프에 투입하지 않는다(사전학습 반복/중단은 Operator 결정).
- **버전 관리**: `models/encoder-v1.pt` + SHA. encoder 교체는 세대 내 변형이 아니라
  **새 사이클(v2, v3…)** — 세대 간 비교 가능성 보존.

## 7. 루프 계약 변경

- **train.py 계약 유지**: 단일 파일 변형 · 고정 학습 예산 · 신규 의존성 *설치* 금지.
  허용 import 목록에 사전 설치된 torch 추가.
- **encoder read-only 강제**: 에이전트의 encoder 가중치 변경/재학습(unfreeze) 시도는 harness가
  게이트 이전에 차단. 구현 방식(파일 권한/SHA 재검증/import 가드)은 plan에서 확정.
- **탐색 표면**: (구 표형식 feature) × (임베딩) 조합 위 head — 회귀 모델, feature 결합,
  임베딩 활용 전략.
- **baseline 이원화 (사전 고정)**:
  - **B0 (역사 baseline)** — 현행 표형식 baseline(gen-001 promoted winner; gen-002~008 무승격으로
    유지). "벽" 그 자체.
  - **B1 (새 표현 naive)** — 임베딩 + 사람이 1회 작성한 단순 head. 임베딩 기본 기여도 측정.
- **판정 질문 (사전 고정)**: 새 루프 winner가 교차설계 T1에서 **B0 대비 `distinguishable`** 인가.
  게이트 프로토콜은 기존 코드가 single source이며 본 spec은 **복사 인용만** 한다(재정의 금지):
  - median 선발: 후보별 5-seed `(0,1,2,3,4)` median val_mae 최저
    (`src/pipeline/runner.py` `run_candidate_multiseed`/`run_all` 기본값).
  - LODO probe: `src/pipeline/validation.py` `run_crossdesign_gate` — 방향성 probe,
    `n_valid < n_designs`면 orchestrator가 `rejected_lodo`로 차단.
  - 교차설계 T1: `src/pipeline/validation.py` `run_crossdesign_validation_gate` —
    scheme `repeated_design_lodo`, `repeats=10`(fold 수 = 설계 수 D×10; D=4 → 40 fold),
    `base_seed=0`, `n_boot=10000`, `alpha=0.05`. winner/baseline이 한 fold라도 실패(inf)하면
    보수적으로 `verdict='worse'`.
  - verdict 기준: 같은 파일 `verdict()` — `distinguishable` = Wilcoxon p < 0.05 **AND**
    bootstrap 95% CI 전체 < 0. `worse` = p < 0.05 AND CI 전체 > 0. 그 외 `indistinguishable`.
  - yes → 질적 전환이 벽을 넘음(H-A′ 지지).
  - no → "표현 전환으로도 못 넘는 벽" — 더 강한 negative result.
  - 어느 쪽이든 판정 지향 성공 기준 충족. B1 대비 결과는 보조 진단(임베딩 vs head 기여 분리).
- **program.md 재작성**: 새 표현 컨텍스트 + 8세대 교훈(in-loop 지표 맹신 금지) 힌트 이식.
- **게이트 체인 불변**: median → LODO → 교차설계 T1 → Codex 4단 그대로.

## 8. 에러 처리 · 테스트 · 비용

**에러 처리**
- 루프 시작 전 fail-fast: encoder 파일 존재 + SHA 일치 + 임베딩 차원 일치. 불일치 시 세대
  시작 차단.
- 임베딩 NaN/inf는 기존 harness `inf→null` 가드 패턴 재사용.
- 합성 실패 설계: manifest에 사유 기록 후 제외.

**테스트**
- 기존 123 tests 전부 유지(게이트 체인 불변).
- 신규: ① 그래프 변환 결정성, ② 선형 probe 게이트 로직, ③ encoder read-only 강제,
  ④ prepare.py 재작성분. pytest + tmp_path, 실데이터 미접촉 관례 유지.

**비용**
- 합성 20설계: CPU 수 분×20 — 로컬 또는 Fargate 몇 $ 이내.
- 사전학습: 로컬 MPS 우선(0원), SageMaker Spot 1회 fallback(사전 동의 게이트).
- 루프 head 학습: CPU 경량 — 기존 비용 구조 유지. LLM은 구독-only 불변.

## 9. 마이그레이션 (리포 유지 결정의 실행 순서)

1. `archive/surrogate-v1-8gen` 브랜치 생성 + push — 현 main 무손실 보존.
2. main은 삭제가 아니라 증축: `experiments/gen-001~008`·논문·wiki·게이트 코드는 main 유지
   (v1 기록이 v2의 비교 대상 B0). 변경: `pretrain/` 신설, `prepare.py` 재작성,
   `program.md`·`PRD.md`·`CLAUDE.md` 갱신.
3. INTENT.md 갱신: 재설계 결정을 Learnings(2026-07-02)로 기록, What에 encoder 층 추가,
   Not에 "encoder frozen — 에이전트 변형 금지" 추가, 기술 제약 의존성 조항 갱신.
   status `exploring` 유지.
4. spec(본 문서) → plan → code 각 단계에 Codex 검토 게이트(codex-review-approval) 적용.

## 10. 범위 밖 (본 사이클)

- CircuitNet 전이 실험(2차 probe로 연기), contrastive 사전학습, 멀티태스크(routability 등),
  encoder 미세조정(unfreeze), auto-gate 코드화(operator_gate→auto-gate 전환은 별도 spec 유지),
  reasoning trace 증거 평면(기존 연기 유지).

## 11. 참고문헌 (grounded 조사, 2026-07-02)

- CircuitNet 2.0: [ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/file/464917b6103e074e1f9df7a2bf3bf6ba-Paper-Conference.pdf) · [timing features 문서](https://circuitnet.github.io/feature/timing%20features.html) · [HF 데이터셋](https://huggingface.co/datasets/CircuitNet/CircuitNet)
- PreRoutGNN: [arXiv 2403.00012](https://arxiv.org/html/2403.00012v2) (AAAI 2024)
- AdaTimer: [DAC 2024](https://www.cse.cuhk.edu.hk/~byu/papers/C225-DAC2024-AdaTimer.pdf) · [TCAD 2025](https://www.cse.cuhk.edu.hk/~byu/papers/J131-TCAD2025-AdaTimer.pdf)
- MasterRTL: [GitHub](https://github.com/hkust-zhiyao/MasterRTL) · [TCAD 2025](https://zhiyaoxie.com/files/TCAD25_MasterRTL.pdf)
- RTL-Timer: [arXiv 2403.18453](http://arxiv.org/pdf/2403.18453.pdf) (DAC 2024)
- CircuitEncoder: [ASPDAC 2025](https://zhiyaoxie.com/files/ASPDAC25_CircuitEncoder.pdf)
