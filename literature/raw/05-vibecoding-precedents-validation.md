# 조사 ⑤: 바이브 코딩 선례 + EDA 도구의 유용성 검증 경로 (2025-2026)

> 조사 에이전트 원본 결과 (2026-08-25, exa 검색 6회, 기각 없음)

## (A) 바이브 코딩 선례 요약

2025-2026년에 "AI 에이전트가 코드 대부분을 작성하고 인간은 게이트를 소유"하는 실용 소프트웨어 선례가 EDA 인접 영역에서 이미 등장했다. 공통점: **라인 단위 리뷰를 포기하는 대신, 기계적으로 강제되는 검증 게이트(테스트·형식검증·외부 벤치마크)를 품질의 담보로 삼는다.** 특히 시뮬레이터·컴파일러류는 "스펙이 명확하고(IEEE 1800) 테스트 기회가 풍부한, AI에 특히 적합한 문제"로 명시적으로 지목됐다.

| 사례 | 무엇 | 품질 보증 방법 | 결과 | URL |
|---|---|---|---|---|
| Normal Computing CIRCT 포크 (2026) | 1인 엔지니어+AI로 43일간 Verilog 시뮬레이터·형식검증 스택 (580K줄, 2,968커밋; Claude 54%/Codex 46%) | 외부 벤치마크(sv-tests 73%, NVIDIA CVDP), 실제 UVM AVIP 완주, BMC/LEC로 OpenTitan·Ibex 검증, mutation testing, 테스트 987→4,229 | 실사용 가능 오픈소스 검증 스택. "상용 대체는 아님" 명시 | normalcomputing.com/blog/building-an-open-source-verilog-simulator-with-ai-580k-lines-in-43-days |
| vm0 (2025-26) | 에이전트가 대부분 작성하는 프로덕션 코드베이스 (1.3M줄, 주 630 PR, 6명) | strict TS·lint 0 CI, 경계 중심 통합 테스트(36%), 에이전트가 실행 증거 제출, PR 중위 53분 | 프로덕션 운영 중 | vm0.ai/en/blog/posts/engineering-quality-vibe-coded-codebase |
| CoreSmith (Meta, 2026) | 프롬프트→GDS 에이전틱 ASIC 플로우 (Yosys/OpenROAD/Sky130) | byte-exact 참조 모델, 라인 커버리지 90% 게이트, DRC/LVS/STA sign-off, 진단 에이전트 재시도 | 5개 중 4개 backend sign-off | github.com/facebookexperimental/socmate |
| RTLScout (Huawei, 2026) | RTL 생성·최적화 에이전트 | Verilator 정확성 게이트 → Yosys/OpenROAD 비용 평가, CEC 형식 등가 증명 번들 + verify.py | 아티팩트 공개 + arXiv 논문화 | github.com/huawei-csl/rtlscout |
| ACE-RTL (NVIDIA, 2026) | RTL 생성·수리 에이전트 | CVDP 정량 평가, 시뮬레이터 피드백 루프 | Agent4Chip 워크숍 논문 + 코드 | github.com/NVlabs/ACE-RTL |

## (A) AI 생성 코드 기여 정책 현황

거부하는 것은 'AI 사용' 자체가 아니라 '이해·책임 없는 제출'.

- **조건부 수용**: LLVM — human-in-the-loop 필수, `Assisted-by:` 라벨, 자율 에이전트 PR 금지 (llvm.org/docs/AIToolPolicy.html). Linux 커널 — DCO + 생성 비율 비례 검증.
- **공개 의무**: NumPy — AI 사용 공개 필수, 자율 제출 금지. pip — LLM co-author 태그 시 클로즈.
- **사실상 거부**: Pallets, Debezium(보조만), FreeCAD.
- **함의**: **자기 소유 저장소에서 에이전트 주도 개발은 정책 충돌 없음.** 업스트림 기여 시 공개 라벨링 + 전 라인 방어 가능이 통행 조건.

## (B) EDA 도구의 학술·실용 인정 경로

- **WOSET**: 오픈소스 EDA 도구 논문 표준 진입로. 전체 소스 repo + OSI 라이선스 필수, 3-4쪽+영상, 완성도보다 공개성·재현성 중시 (woset-workshop.github.io). 2024 사례: LightningSim(재현성 배지), ORAssistant, SoCMake.
- **ICCAD 정규**: 오픈소스 공개 강력 권장, double-blind, 8쪽. DAC/DATE 유사.
- **JOSS**: 도구 자체를 피어리뷰·DOI. 요건 = OSI 라이선스, 문서화, **자동 테스트+CI**, Research impact statement(실현된 채택 또는 재현 가능 벤치마크 — "장래 쓰일 것"만으로는 기각).
- **산업 실무**: DVCon — 시간 절감 전/후 표가 표준 증거 형식.

## (B) 유용성 객관 지표 목록

1. **벤치마크 성능** (최강): 외부 공인 스위트 대비 수치 + 재현 아티팩트
2. **채택 증거**: 타 그룹 사용, 인용, 의존 패키지, 배포판 편입
3. **다운로드·스타**: proxy로만 공식 한정 (metrics-toolkit.org)
4. **신뢰성**: 크래시 없는 실행률, 커버리지, CI, bus factor
5. **시간 절감 전/후 표** (산업 표준): 예 — TB 생성 2-4일→1시간 미만(DVCon India 2023)

## 본 프로젝트에 주는 시사점

1. "검증 게이트가 품질을 담보한다"는 바이브 코딩 방법론은 이미 실증됨 (CIRCT 포크·CoreSmith)
2. 외부 공인 벤치마크를 초기에 고정하라 — 자체 테스트보다 훨씬 강한 증거
3. 학술 최저 진입로 = WOSET, 도구 피어리뷰 = JOSS (impact 증거를 초기부터 축적)
4. 유용성 주장은 "시간 절감 전/후 표 + 재방문 사용"으로 — 스타는 보조
5. 업스트림 기여 시 AI 공개 라벨·자율 제출 금지 준수. 자기 repo는 제약 없음

## 검색 로그 (쿼리|결과 수)

1. case study of production software built primarily with AI coding agents, quality assurance via test gates | 8
2. open source project policy on AI-generated code contributions 2025 | 8
3. WOSET submission criteria, open source EDA tool papers evaluation | 8
4. LLM agent autonomously built engineering software that reached real users 2025 2026 | 8
5. measuring impact of research software: JOSS criteria, sustainability metrics | 6
6. semiconductor CAD internal tool development practice, measuring engineer time saved | 6
