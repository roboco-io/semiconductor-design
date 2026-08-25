# D1 데이터 정찰 보고 — ICCAD23 Problem C (ML for Static IR Drop)

- 작성: 2026-08-25, 트랙 D 데이터 파이프라인 정찰 에이전트
- 대상 저장소: https://github.com/ASU-VDA-Lab/ML-for-IR-drop
- 로컬 클론: `/Users/dohyunjung/Workspace/roboco-io/research/semiconductor-design-tracks/D-irdrop/ML-for-IR-drop`
  (shallow clone, `--depth 1`, main)

## 판정 요약

| 항목 | 판정 |
|---|---|
| 데이터 접근성 | **가능 — 전량 repo 내 포함** (외부 다운로드·git-LFS 없음). 클론 완료. |
| 규모 | GitHub pack 약 652MB → 체크아웃 후 **3.9GB**, 617파일 |
| 라이선스 | **BSD-3-Clause 단일** (LICENSE 1개, 코드·벤치마크 데이터 공통, (c) 2023 ASU-VDA-Lab) |
| 공식 평가 스크립트 | **repo에 없음** — 지표 정의는 `doc/contest-description.pdf` §4에 수식·예제로 완결. 자체 구현 용이 |
| 공개 점수표 | **있음** — `doc/ICCAD-Final-Scores-Release.xlsx` (hidden 10케이스별 MAE/F1/TIME, 팀별) |
| hidden 정답 | **공개됨** — `hidden-real-circuit-data/`에 `ir_drop_map.csv` 포함 → 로컬 재현 채점 가능 |
| CircuitNet 대안 필요성 | **불필요** (콘테스트 데이터 접근 리스크 해소) |

## 저장소 구조

```
ML-for-IR-drop/
├── LICENSE                  # BSD-3-Clause
├── README.md
├── doc/
│   ├── contest-description.pdf        # 문제·데이터 포맷·평가 지표 정의 (v4, 2023-06-22)
│   ├── invited-paper.pdf              # ICCAD23 초청 논문
│   ├── ICCAD23-Contest-ProblemC.pdf/.pptx
│   └── ICCAD-Final-Scores-Release.xlsx  # 최종 점수표
├── src/                     # 벤치마크 "생성" 스크립트 (평가 스크립트 아님)
│   ├── ir_solver.py         # GV=J 골든 솔버 (ground truth 생성용)
│   ├── current_mapgen.py, grid.py, node.py
│   └── generate_benchmark_maps{,_asap7,_nangate45}.py, generate_gan_maps_nangate45.py
└── benchmarks/
    ├── fake-circuit-data/          2.8GB, 합성 100회로 (BeGAN 기반, nangate45)
    ├── real-circuit-data/          225MB, 실회로 10 (tc 1-6, 11, 12, 17, 18) = 공개 학습 스플릿
    └── hidden-real-circuit-data/   272MB, 실회로 10 (tc 7-10, 13-16, 19, 20) = 콘테스트 hidden 테스트
```

## 데이터 스키마

케이스당 5파일 (fake는 `current_mapXX_*` 접두, real은 `testcaseN/` 디렉토리):

| 파일 | 역할 | 형식 |
|---|---|---|
| `current_map.csv` | 입력 1: 전류 맵 (A) | N×M float CSV, 1um/픽셀 |
| `pdn_density.csv` | 입력 2: PDN 밀도 맵 (3단계 region-wise) | 동일 크기 |
| `eff_dist_map.csv` | 입력 3: 전압원까지 유효 거리 맵 | 동일 크기 |
| `netlist.sp` | 입력 대안: SPICE 저항망 (R/I/V, 노드명 = `층_x_y`, 2000dbu/um) | 예: tc1 약 3.6만 라인 |
| `ir_drop_map.csv` | **출력(정답): IR drop 맵 (V)** | 동일 크기 |

- 맵 크기는 케이스마다 다름(칩 크기): 관측치 298×298 (tc1, tc2), 641×641 (tc5, tc6),
  835×835 (hidden tc10), 870×870 (hidden tc20), fake 예 821×821.
- 회로 수: fake 100 + real 공개 10 + real hidden 10 = **총 120 데이터포인트**.
- 스플릿 규약(콘테스트·후속 논문 공통): fake 100 사전학습 → real 공개 10 파인튜닝 → hidden 10 평가.

## 평가 지표 (contest-description.pdf §4 — 사전 고정 근거)

1. **MAE** (가중 60%): 예측 vs 정답 맵 원소별 절대차 평균 (mV 단위 보고).
2. **F1** (가중 30%): hotspot 이진 분류 — 임계값 = **해당 테스트케이스 정답 최대 IR drop의 90%**
   초과 픽셀이 positive. F1 = 2PR/(P+R).
3. **런타임** (가중 10%): 추론 시간.

공식 채점 코드는 미공개이나 위 정의로 수 라인 구현 가능. 3위 팀 공개 구현
(github.com/Alpha-Chip/Alpha-ML-IRDrop, `data_preproc/metrics.md` + `inference.py`)을
교차 검증 레퍼런스로 사용 가능. 점수표 xlsx로 우리 결과를 콘테스트 참가팀(약 24팀)과
케이스 단위 직접 비교 가능.

## BeGAN 합성 데이터 (사전학습 확장용)

- 위치: https://github.com/UMN-EDA/BeGAN-benchmarks (BSD-3-Clause)
- 규모: GitHub API size **약 22GB** — **클론하지 않음** (1GB 초과 정책). 필요 시 기술 노드별
  서브디렉토리 선별 다운로드(sparse checkout) 권장.
- 내용: `BeGAN-circuit-benchmarks/` + `real-circuit-benchmarks/`, FreePDK45(Nangate45)·
  SkyWater130·ASAP7 3개 오픈 노드, 수천 개 SPICE PDN 벤치마크 (ICCAD'21 논문).
- 단, 본 repo의 fake-circuit-data 100케이스가 이미 BeGAN 방법론(nangate45)으로 생성된
  콘테스트 규격 데이터라 **초기 사이클에는 추가 다운로드 불필요**.

## 리스크 체크포인트 판정

- 콘테스트 데이터 접근 불가 리스크: **해소**. 전 데이터(정답 포함) repo 내 존재, 인증·외부
  링크·LFS 없음. CircuitNet IR 서브셋 대안 검토 불필요.
- 다음 단계(D1 후반 전처리) 착수 가능: CSV → 텐서 로더(가변 크기 처리), fake/real/hidden
  스플릿 고정, MAE·F1 채점기 자체 구현 + Alpha-Chip 구현과 교차 검증.
