# EDA AI Research Agent 핸드오프 문서

## 1. 문서 목적
이 문서는 지금까지의 논의를 정리해, 후속 AI 에이전트 또는 연구/플랫폼 구축 담당자가 바로 작업을 시작할 수 있도록 하는 핸드오프 문서다.

이 프로젝트의 목표는 **오픈소스 EDA를 AI 에이전트로 강화해 상용 EDA 대비 의미 있는 출력을 만드는 것**이다. 다만 목표는 상용 EDA 전체 대체가 아니라, **OpenROAD/OpenLane 중심의 디지털 ASIC 플로우에서 특정 병목을 공략해 측정 가능한 개선을 만드는 것**이다.

---

## 2. 북극성
- 상용 EDA 전체 대체가 아니라 **좁고 측정 가능한 병목 개선**에 집중한다.
- 초기 승부처는 코드 생성형 에이전트보다 **ORFS 스타일 autotuning + 폐루프 실험 운영**이다.
- 제품의 핵심은 단순 설명형 챗봇이 아니라 **실제로 QoR/runtime를 개선하는 실행 시스템**이다.

---

## 3. 지금까지의 핵심 판단

### 3.1 오픈소스 EDA의 현재 위치
- OpenROAD/OpenLane는 충분히 성숙한 오픈소스 디지털 플로우다.
- 하지만 상용 EDA 대비 전면 parity는 아직 아니다.
- 따라서 **전면 대체 전략보다, 특정 benchmark class에서 반복 가능한 개선을 쌓는 전략**이 현실적이다.

### 3.2 초기 공략점
- 첫 번째 승부처는 **autotuning**이다.
- 이후에 **repo-grounded code agent**로 특정 엔진 모듈을 개선하는 방향으로 확장한다.
- 즉, 순서는 다음과 같다.
  1. ORFS/플로우 레벨 최적화
  2. 특정 엔진 단위 코드 수정형 에이전트
  3. 장기적으로 broader OpenROAD-agent

### 3.3 RAG 챗봇의 위치
- RAG 챗봇은 문서/로그/옵션 이해를 돕는 **설명 계층**으로는 유용하다.
- 하지만 차별화 포인트로는 약하다.
- 핵심은 아래다.
  - 문제를 설명하는 AI가 아니라
  - **파라미터를 바꾸고, 실행하고, 평가하고, 개선을 채택하는 AI**

---

## 4. 핵심 개념 정리

### 4.1 LLM Wiki의 역할
LLM Wiki는 정제된 지속 기억 계층이다.

원문을 매번 다시 RAG로 질의하는 대신,
- 개념
- 방법론
- 벤치마크
- 가설
- 검증된 finding
- 실패 사례
를 지속적으로 누적하는 **정제된 연구 기억 저장소**로 사용한다.

### 4.2 QMD의 역할
QMD는 주 기억장치가 아니라 **검색 가속 계층**이다.

용도:
- 위키 검색
- 원문 문서 검색
- 실험 로그 검색
- finding/failure 추적

권장 원칙:
1. 먼저 위키에서 찾는다.
2. 위키의 evidence를 따라 원문을 확인한다.
3. 부족하면 QMD로 확장 검색한다.
4. 새 사실이 있으면 위키를 갱신한다.

### 4.3 AutoResearch의 역할
AutoResearch 방식은 EDA 연구 운영에 적합하다.

핵심 패턴:
- 작은 변경
- 제한된 탐색 공간
- 고정된 평가 함수
- 짧은 실험 루프
- 채택/폐기 반복

이를 EDA에 적용하면 다음과 같다.
- `program.md`로 연구 조직의 규칙을 정의
- 에이전트가 가설을 세우고
- 작은 patch 또는 파라미터 변경을 시도하고
- benchmark를 실행하고
- baseline 대비 개선 여부를 평가하고
- 결과를 위키에 반영한다

---

## 5. 제품/연구 원칙
- **위키가 중심, 검색은 보조, 실험은 폐루프**라는 원칙을 유지한다.
- 모든 claim은 evidence와 연결되어야 한다.
- 위키 문서는 최소한 `confidence`, `contradiction`, `last_verified`를 가져야 한다.
- negative result도 자산이므로 반드시 `failures/`에 축적한다.
- 작은 reversible patch만 허용하고, baseline overwrite는 승격 절차를 거친다.
- 고객 IP/비공개 PDK 유입 이전부터 provenance, 권한 분리, promotion gate를 설계한다.

---

## 6. 권장 저장소 구조

```text
eda-research/
├─ program/
│  ├─ program.md
│  ├─ scoring.md
│  ├─ safety.md
│  ├─ benchmark_policy.md
│  └─ promotion_policy.md
│
├─ sources/
│  ├─ papers/
│  ├─ docs/
│  ├─ repos/
│  ├─ issues/
│  ├─ runs/
│  └─ imports_manifest.yaml
│
├─ wiki/
│  ├─ concepts/
│  ├─ methods/
│  ├─ tools/
│  ├─ benchmarks/
│  ├─ metrics/
│  ├─ hypotheses/
│  ├─ findings/
│  ├─ failures/
│  ├─ decisions/
│  ├─ entities/
│  └─ index/
│
├─ experiments/
│  ├─ proposals/
│  ├─ active/
│  ├─ completed/
│  ├─ archived/
│  └─ templates/
│
├─ artifacts/
│  ├─ logs/
│  ├─ reports/
│  ├─ patches/
│  ├─ metrics/
│  └─ snapshots/
│
├─ qmd/
│  ├─ corpus/
│  ├─ config/
│  ├─ indexes/
│  └─ queries/
│
├─ agents/
│  ├─ roles/
│  ├─ prompts/
│  ├─ tools/
│  ├─ skills/
│  └─ workflows/
│
└─ infra/
   ├─ aws/
   ├─ containers/
   ├─ orchestration/
   └─ observability/
```

---

## 7. 문서 스키마

### 7.1 위키 문서 공통 프론트매터
모든 위키 문서는 최소한 다음 필드를 가져야 한다.

- `id`
- `title`
- `type`
- `status`
- `confidence`
- `last_verified`
- `owners`
- `tags`
- `entities`
- `claims`
- `contradictions`
- `related`

### 7.2 hypothesis 문서 템플릿
가설 문서는 아래 항목을 반드시 포함한다.

- Mechanism
- Prior evidence
- Counter-evidence
- Experiment plan
- Success criteria
- Applicability

예시 구조:

```yaml
id: hypothesis-h-0042
title: Macro-heavy designs benefit more from congestion-weighted placement
type: hypothesis
status: proposed
confidence: low
last_verified: 2026-04-19
target_metrics: [route_completion, wns, runtime]
applicable_to: [macro-heavy, utilization-high]
```

### 7.3 finding / failure 원칙
- 성공만 기록하지 말고 실패도 별도 문서로 남긴다.
- `finding`과 `failure`는 모두 `derived_from hypothesis`와 `evidence run 목록`을 포함한다.
- 위키 갱신은 실험 평가 완료 후에만 허용한다.

---

## 8. AWS 기반 멀티에이전트 아키텍처

### 8.1 상위 구조
시스템은 세 계층으로 나눈다.

1. **Control Plane**
   - API / workflow engine
   - metadata DB
   - auth / policy / audit

2. **Execution Plane**
   - AWS ParallelCluster + Slurm
   - CPU queues
   - GPU queues
   - FSx for Lustre
   - S3 artifact lake

3. **Knowledge Plane**
   - git-backed wiki
   - qmd index
   - raw sources
   - experiment registry

### 8.2 권장 AWS 매핑

#### Control Plane
- ECS Fargate 또는 EKS
- RDS PostgreSQL
- CloudWatch
- Secrets Manager

#### Execution Plane
- AWS ParallelCluster
- Slurm queues
- FSx for Lustre
- S3

#### Knowledge Plane
- Git-backed wiki repo
- QMD index/service
- raw source mirror

---

## 9. 큐 설계

### cpu-regression
- baseline 회귀 검증
- 온디맨드 인스턴스 우선
- 승격 후보 최종 검증

### cpu-search
- 대량 파라미터 sweep
- Spot 우선
- 짧은 탐색 실험

### gpu-modeling
- surrogate model 학습
- embedding
- reranking 보조 작업

### gpu-rerank
- 선택적 검색/재정렬 가속

---

## 10. 스토리지 전략

### FSx for Lustre
- 실행 중 작업의 hot working set
- OpenROAD/OpenLane intermediate files
- 병렬 I/O가 필요한 영역

### S3
- raw source
- run artifact
- wiki snapshot
- patch archive
- 장기 보관

### RDS/PostgreSQL
- experiment registry
- lineage
- queue state
- promotion state

---

## 11. 에이전트 역할 정의

### 11.1 Reader Agent
- 새 논문/문서/이슈/로그 ingest
- source card 생성
- imports manifest 갱신

### 11.2 Synthesizer Agent
- 기존 위키와 새 source를 대조
- claim, contradiction, gap 생성
- wiki draft 생성

### 11.3 Hypothesis Agent
- findings, failures, recent source를 바탕으로
- 다음 실험 후보를 제안

### 11.4 Planner Agent
- 가설을 실행 가능한 실험 계획으로 변환
- benchmark, seed, compute budget, stop condition 정의

### 11.5 Runner Agent
- Slurm에 job 제출
- 상태 추적
- artifact 수집

### 11.6 Evaluator / Wiki Maintainer
- baseline 대비 개선/회귀를 판정
- keep / discard / retry 결정
- findings / failures / decisions / wiki 갱신

---

## 12. 운영 워크플로우

1. **Import**
   - 새 source 유입
   - Reader가 source card 작성
   - QMD index 갱신

2. **Synthesis**
   - Synthesizer가 wiki와 비교
   - claim / contradiction / gap 업데이트

3. **Planning**
   - Hypothesis Agent가 후보 제안
   - Planner가 실험 설계 및 proposal 생성

4. **Execution**
   - Runner가 Slurm job 제출
   - FSx workdir에서 실행
   - 결과를 S3 / artifacts에 저장

5. **Evaluation**
   - Evaluator가 baseline 대비 개선/회귀 판정

6. **Memory Update**
   - Wiki Maintainer가 finding / failure / decision 갱신
   - QMD reindex

---

## 13. 관측성과 승격 게이트

### 수집할 핵심 지표
- 실험 성공률
- route completion rate
- baseline 대비 WNS/TNS 변화
- baseline 대비 wirelength/power/runtime 변화
- 동일 가설의 반복 재현율
- wiki update latency
- source-to-finding conversion rate
- false promotion rate

### 승격 게이트
1. single-run improvement observed
2. 3 seeds reproducible
3. no critical regression on holdout benchmarks
4. finding/failure 문서 업데이트 완료
5. promotion_policy 만족 시 baseline profile로 승격

---

## 14. 초기 MVP 범위
- 대상 툴: **OpenROAD + OpenLane**
- 대상 문제: **ORFS 스타일 autotuning**
- 대상 디자인: **3-5개 공개 benchmark**
- 핵심 지표: **route success, effective clock period, WNS/TNS, runtime**
- 지식 계층: **Git-backed wiki + QMD**
- 실행 환경: **AWS ParallelCluster + Slurm + FSx for Lustre + S3**
- 에이전트 구성: **Reader / Synthesizer / Planner / Runner / Evaluator**

---

## 15. 바로 지시할 작업 목록
- 저장소 skeleton 생성: `program/`, `sources/`, `wiki/`, `experiments/`, `artifacts/`, `qmd/`, `agents/`, `infra/`
- `program.md`, `scoring.md`, `promotion_policy.md` 초안 작성
- QMD corpus/index 구성을 위한 ingest 스크립트 설계
- 위키 템플릿(`hypothesis`, `finding`, `failure`, `decision`) 생성
- ParallelCluster + Slurm 초기 배포 정의 작성
- OpenROAD/OpenLane benchmark harness 구축
- baseline run 1세트 수행 및 `experiments/completed/`에 기록
- 첫 번째 hypothesis 3개를 작성하고 우선순위 지정
- `cpu-search` queue에서 소규모 autotuning 실험 시작
- 실험 평가 후 wiki와 findings/failures 갱신

---

## 16. 금지 사항 및 주의점
- RAG 챗봇만으로 제품 가치를 정의하지 말 것
- evidence 없이 위키에 단정적 claim을 올리지 말 것
- 실패한 가설을 삭제하지 말고 failure로 남길 것
- baseline을 직접 덮어쓰지 말고 promotion gate를 거칠 것
- 고객 IP 또는 비공개 자산이 섞이면 public wiki와 분리할 것

---

## 17. 최종 한 줄 요약
이 프로젝트는 **검색 가능한 위키**를 만드는 것이 아니라, **오픈소스 EDA를 대상으로 실험으로 검증되며 스스로 자라나는 연구 기억체계**를 만드는 것이다.
