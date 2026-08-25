# 조사 ④: 설계 워크플로우 자동화·실험 관리 도구 수요 (2024-2026)

> 조사 에이전트 원본 결과 (2026-08-25, exa 검색 6회, 기각 없음)

## 요약

오픈소스 RTL-to-GDS 생태계(ORFS/LibreLane/Tiny Tapeout)의 페인포인트는 (1) 툴체인·PDK 설치/버전 정합, (2) 수 시간짜리 run의 실패 진단·조기 피드백 부재, (3) 다중 run 실험 관리가 수작업(로그 파싱 스크립트 자작)이라는 세 축으로 수렴한다. METRICS2.1이라는 표준 포맷과 AutoTuner(DSE)는 존재하지만, MLflow/W&B식 **로컬 run 추적·비교 대시보드는 부재** — 포맷은 있고 도구가 없는 전형적 공백. Tiny Tapeout은 매 셔틀 수백 명의 실사용자가 있고 제출 실패 모드가 문서화되지 않아, 1인 개발 규모의 도구로 즉시 사용자를 확보할 수 있는 경로다.

## 공백·수요 목록

| 공백 | 수요 근거 (URL) | 기존 대안 | 1인 개발 가능성 |
|---|---|---|---|
| run 비교·실험 추적 (METRICS2.1 뷰어/디프) | oharboe "bazel-orfs로 PLACE_DENSITY 탐색에 며칠": OpenROAD #7482 / 개인이 tcl+python 로그 파싱 자작: endraws.me/posts/tinytapeout-08/ | ORFS 골든 비교(CI용), AutoTuner+TensorBoard(무겁고 Ray 의존) | **높음** — JSON 파싱+로컬 웹UI |
| TT 제출 프리플라이트 진단 | "TT 문서는 실패 모드에 침묵" (verilator -Wall, config.json, Pages 함정): plawanrath.com/articles/grammartile-tinytapeout-walkthrough/ | tt_tool.py --harden 가이드는 있으나 실패 원인 진단 없음 | **높음** — 체크 스크립트 집합 |
| 플로우 실패 조기 진단·knob 제안 | 7시간 후 GRT 실패, "actionable advice 없음", "AI가 읽을 수 있는 경고 필요": OR #7482 / 라우팅 실패가 수 시간 뒤 판명: a1k0n.net/2025/12/19/tiny-tapeout-demo.html | 없음 | **중간** — 휴리스틱+로그 파싱 가능 |
| 툴체인 버전 정합·환경 재현 | Yosys 버전 불일치: waleed-vlsi.hashnode.dev / 프리빌트 불일치: OR #10033 / "12시간 디버깅" 사례 | Docker(ORFS), nix(LibreLane) 부분 해결 | **중간** — doctor CLI는 쉬움 |
| HW용 CI 셋업 보일러플레이트 | 레포마다 Verilator 소스빌드+캐시 재발명: tiny-tpu rtl.yml 등 / "HW는 SW보다 CI 후진": sistenix.com/docker_ci.html | cocotb pytest 통합 진행 중(#5090), 표준 액션 부재 | **높음** — 재사용 Action+템플릿 |
| PDK 설치(아날로그 멀티툴) | open_pdks 빌드 4회 실패: skywater-pdk-users 스레드 | **ciel**이 디지털용 거의 해결 | 낮은 우선순위 |

## 도구 지형과 빈 자리

- **ORFS**: METRICS2.1 수집 + 골든 비교(내부 CI). 공식 문서 "QoR 추적은 개발 중" — 사용자용 대시보드 부재. 내부 Jenkins는 비공개.
- **AutoTuner**: Ray Tune 기반 DSE. TensorBoard 유용(流用), ORFS 종속, 서버 지향 — 개인 로컬 실험 관리용 아님.
- **SiliconCompiler**: flowgraph+manifest 우수, 내부 복잡도 최대급(arxiv 2504.09642).
- **FuseSoC/Edalize**: 코어 관리·툴 추상화. HBS 논문 전수 비교에서도 **run 추적·실험 비교는 어느 도구에도 없음**.
- **빈 자리**: ① METRICS2.1 위 로컬 실험 추적 UI(하드웨어판 MLflow — 이식 사례 미발견) ② TT 제출 진단 ③ 플로우 로그 actionable 해석 ④ HDL CI 표준 템플릿.

## 유망 후보 Top 3

1. **로컬 run 추적·비교 도구 ("MLflow for RTL-to-GDS")**: ORFS/LibreLane run 디렉토리·METRICS2.1 JSON 자동 수집 → run 목록·PPA 디프·파라미터-결과 상관 로컬 웹 대시보드 + CLI(`runs diff A B`). 검증: 자기 TT 프로젝트 도그푸딩 → TT Discord·ORFS 이슈 공유 → 채택·실데이터 제보 측정.
2. **Tiny Tapeout 프리플라이트 닥터(`tt-doctor`)**: 제출 전 GDS 액션 실패 모드를 로컬 재현·진단. 매 셔틀 수백 명 사용자 풀. 검증: 공개 tt-* 레포 수십 개에 실패 예측 정확도 측정, TT 공식 툴 PR 경로.
3. **플로우 실패 조기 진단 어시스턴트**: 스테이지별 로그·중간 메트릭 파싱 → "라우팅 실패 확률 높음, PLACE_DENSITY 조정 권고" 조기 출력. 메인테이너 본인이 명시 요청(#7482). 검증: 공개 실패 사례 백테스트 적중률 사전 고정.

## 검색 로그

| 쿼리 | 결과 수 |
|---|---|
| OpenLane/OpenROAD RTL-to-GDS pain points, setup, run management | 8 |
| Tiny Tapeout participant workflow difficulties, GDS submission, local hardening | 8 |
| experiment tracking / run comparison for chip design, METRICS2.1 dashboard | 8 |
| SiliconCompiler vs Edalize vs FuseSoC limitations, flow orchestration | 8 |
| open PDK installation pain: volare/ciel, open_pdks, sky130 setup | 8 |
| hardware CI/regression: GitHub Actions + cocotb + Verilator 2024-2025 | 8 |
