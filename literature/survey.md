# Literature Survey: EDA × AI 연구 지형 (2024-2026)

날짜: 2026-08-25 · 도구: exa MCP (병렬 조사 에이전트 5기) · 원본: `literature/raw/01`-`05`

## 1. Review Protocol (사전 고정)

- **Research area**: EDA 전 영역에서 novel·important·feasible한 연구 주제 발굴
- **제약 조건**: 1인 Operator + AI 에이전트, 오픈소스 툴체인, 로컬·무료 컴퓨트, 구독 CLI만(metered API 금지)
- **Key questions**: 하위 분야별 SOTA / open problems / underexplored areas
- **Inclusion**: 2024-2026 우선, 재현 가능성(코드·벤치마크 공개) 가점
- **Exclusion**: 대규모 GPU 학습 필수 영역은 "실행 불가"로 표기만
- **검색**: exa 검색 27회 + 원문 fetch 6회, citation 0건 응답 기각 규칙(기각 발생 0건)

## 2. 스크리닝 요약 (PRISMA 근사)

- 검색 결과 노출: 약 220건 (27개 쿼리 × 6-10건)
- 제목/초록 스크리닝 후 추출 대상: 약 60건
- 최종 synthesis 포함: **46편** (raw 파일의 논문 표 기준)
- 한계: 병렬 에이전트 조사라 중복 제거·제외 사유 기록이 개별 로그 수준 — 엄밀 PRISMA 아님 (EXPLORATORY 라벨)

## 3. Evidence Map — 5개 테마

### T1. RTL 생성: "작은 모듈은 풀린 문제" ([raw/01](raw/01-rtl-generation.md))
- 구세대 벤치마크(VerilogEval v1, RTLLM) 95%+ **포화**, 오염도 정량 확인(VeriContaminated)
- 신세대(CVDP ≤34%, RealBench 시스템 레벨 **0%**, ChipBench 30.74%)로 전선 이동
- Gap: 멀티모듈/시스템 설계, 기능 버그 수리, sign-off 이후 품질

### T2. 검증: 최대 병목이자 최저 성능 ([raw/02](raw/02-verification.md))
- 검증 = 개발 주기 약 70%인데 연구 밀도는 생성 대비 2년 뒤처짐
- SVA 유효율 약 44%, 구문↔의미 괴리(유효 SVA의 최대 24%가 formal 반증)
- self-validation은 스펙 오해에 취약(CorrectBench) — **생성≠심사 구도의 체계 평가는 공백**
- 커버리지 클로저·formal 전략 자동화·비Verilog 언어 거의 공백

### T3. 물리 설계·오픈소스 EDA: 평가 방법론이 화두 ([raw/03](raw/03-opensource-eda-physical.md))
- AlphaChip 재현성 논쟁의 교훈: **중간 지표 개선 ≠ 최종 PPA 개선** (ChiPBench 실증)
- 2025년 최초의 상용 툴 공개 벤치마크(Aprisa) — 상용 대비 측정 기반 개막
- 로컬 CPU로 가능: AutoTuner 파라미터 튜닝(다목적은 2026 신생), QoR 예측(EDA-Schema-V2), LLM 플로우 에이전트
- 불가: RL placement 원조건 재현(수십 GPU)

### T4. 에이전틱 플로우: 하네스가 성능을 지배 ([raw/04](raw/04-agentic-chip-design.md))
- 자율성 현주소: 모듈 L3, 플로우 L2 (Agentic EDA 서베이)
- **FluxBench: 동일 모델에서도 하네스 아키텍처 차이로 86% 성능 격차, 범용 Claude Code+스킬은 전용 시스템에 최대 8.4배 열세** — 그러나 "범용 에이전트를 EDA에 최적화하는 하네스 설계" 자체를 연구한 논문은 부재
- Token ROI(비용 대비 개선) 계측은 FluxBench가 최초 시도, 구독 요금제 실측은 전무
- 실리콘 실증은 전부 대화형+인간 개입 — 자율 에이전트 산출물 tapeout 공개 사례 없음

### T5. 주변부: 교육 축이 최대 공백 ([raw/05](raw/05-periphery-benchmark-gaps.md))
- Analog+LLM: 급성장 중이나 실데이터 성공률 ≤23%, 로컬 재현 용이(ngspice)
- HLS+LLM: "HLS판 VerilogEval" 부재
- 벤치마크 오염·포화 연구는 2025년에야 시작 — Tiny Tapeout 코퍼스(2,000+ 설계)는 living benchmark 원료로 미개발
- **교육·학습 측정: 경쟁 밀도 최저.** 설계 성과 측정은 있어도 학습(개념 습득) 정량 측정은 사실상 전무 — Krupp et al. 2026이 명시적 future work로 남김

## 4. Cross-Cutting Open Problems

1. **평가 위기**: pass@k 포화 + 데이터 오염 + sign-off/PPA 게이트 부재 + 중간지표-최종성능 해리 (T1·T3·T4 공통)
2. **검증 병목**: 자동·신뢰 가능한 검증 환경 부재가 RLVR 학습·에이전트 루프·실무 채택 모두의 병목 (T1·T2·T4 공통)
3. **하네스 설계 지식 부재**: 성능 격차의 지배 변수임이 실증됐지만(86% 격차) 설계 원리는 미연구 (T4)
4. **비용 계측 부재**: 반복 횟수·토큰·인간 개입량이 평가에서 누락 (T4)
5. **인간 학습 축 부재**: AI 협업 설계에서 성과-학습 해리 측정 도구 없음 (T5)

## 5. Underexplored Areas × 제약 적합성

| 영역 | 연구 밀도 | 로컬 실행 | 근거 |
|---|---|---|---|
| 범용 CLI 에이전트 + EDA 스킬/하네스 설계 연구 | **공백** | 가능 | FluxBench가 공백 명시 |
| 교차 엔진(생성≠심사) 검증 체계 평가 | **공백** | 가능 (Verilator/Yosys) | CorrectBench 초기 시도뿐 |
| 기능 정합 통과 RTL의 sign-off 게이트 통과율 | 초기 | 가능 (LibreLane) | TuRTLe·CLOSER-Bench가 갭 지적 |
| Tiny Tapeout 코퍼스 living benchmark | 초기 | 가능 (Yosys 등가성) | NotSoTiny 신생 — novelty 재확인 필요 |
| AI 협업 설계의 학습 축 정량 측정 | **공백** | 가능 (N=1 종단) | Krupp 2026 future work |
| 구독 요금제 Token ROI 실측 | **공백** | 가능 | FluxBench가 지표만 제안 |
| LLM ORFS 파라미터 다목적 튜닝 | 보통 | 가능 | ORFS-agent 존재(개선폭 1-3%) |
| RL placement 재현 | 활발(논쟁) | **불가** | 수십 GPU 필요 |

## 6. 시사점 (가설 생성 원료)

이전 사이클 INTENT(바이브 코딩 × 학습 축)와 독립적으로 수행한 이번 제로베이스 조사가, 결과적으로 **"범용 에이전트 하네스" + "생성≠심사 검증" + "sign-off 게이트 평가" + "학습 축 측정"** 이 문헌상 실제 공백임을 교차 확인했다. 특히 FluxBench(2026)의 등장으로 하네스 설계 연구는 비교 가능한 공인 지표(완주율·QoR·Token ROI)를 갖게 되어, 1인 연구자의 기여가 측정 가능한 형태로 열렸다.
