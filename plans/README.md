# 4트랙 병렬 개발 포트폴리오 — 총괄

작성: 2026-08-25 · 상태: Operator 승인 (A/B/C/D 전 트랙 병렬, [`issues/001`](../issues/001-build-target-selection-brief.md))
가설 연동: [`research-tree.yaml`](../research-tree.yaml) — A=H1/H1.1, B=H2, C=H3, D=H5

| 트랙 | 산출물 | 유형 | 유용성 판정 축 | 계획서 |
|---|---|---|---|---|
| A | RTL-to-GDS 실험 추적 도구 → QoR 조기 예측기 | 도구+모델 | 수집 정합성 → 시간 절감 → 예측 MAE(공개 베이스라인 비교) | [A-run-tracker.md](A-run-tracker.md) |
| B | STA 리포트 분석기 | 도구 | golden diff 100% + 외부 사용 증거 | [B-sta-analyzer.md](B-sta-analyzer.md) |
| C | 플로우 실패 진단기 (flow doctor) | 도구 | 공개 실패 사례 백테스트 적중률 | [C-flow-doctor.md](C-flow-doctor.md) |
| D | IR drop 경량 예측 모델 | 모델 | ICCAD'23 공개 리더보드 직접 비교 | [D-irdrop-model.md](D-irdrop-model.md) |

H4(검증 관리 도구)는 DEFER — 신생 경쟁(xevdb·TraceWeave) 관찰 후 재입장.

## 공통 방법론 (전 트랙 강제 — 조사 ⑤ 실증 패턴)

1. **게이트 기반 바이브 코딩**: 라인 리뷰 대신 기계적 게이트 — 자동 테스트+CI(도구 트랙: 라인 커버리지 ≥80% 게이트), golden 대조, 외부 벤치마크. Normal Computing·CoreSmith 패턴.
2. **사전 고정 판정**: 각 트랙의 유용성 판정 기준은 구현 착수 전 protocol로 LOCK(Codex 게이트 심사 후). 결과 확인 후 변경 금지, 이탈은 EXPLORATORY.
3. **생성≠심사**: 구현은 Claude 에이전트, 설계·판정·릴리스 게이트 리뷰는 Codex.
4. **공개 우선**: 각 트랙 독립 공개 저장소(Apache-2.0), 첫 동작 버전부터 public. WOSET(도구 논문)/JOSS(도구 피어리뷰) 제출을 트랙별 최종 마일스톤으로.
5. **채택 측정 준비**: 릴리스 시점부터 사용 증거(이슈 유입·외부 인용·다운로드)를 기록 — JOSS impact statement 요건 대비.
6. **제약 불변**: 구독 CLI만(metered API 금지) · 로컬 컴퓨트만 · 웹 조사는 exa만.

## 병렬 운영 모델

- **트랙 = 독립 저장소 + 독립 에이전트 작업 흐름.** 본 리포는 연구 관리(계획·프로토콜·결과·로그)만 보유.
- 트랙 간 의존성은 **없음** (전부 병렬 착수 가능). 단 공유 인프라 1개가 선행: **`INFRA-0` 로컬 EDA 환경 구축**(LibreLane/ORFS + SKY130 + OpenSTA + iverilog/Verilator) — A·B·C가 의존. D는 Python/ML 스택만 필요해 INFRA-0와 독립.
- 착수 우선순위(구독 사용량 배분): **A ≥ D > B > C.** A는 데이터 수집(플로우 run)에 캘린더 시간이 걸려 최우선 착수, D는 완전 독립이라 즉시 병행, C는 코퍼스 수집이 선행이라 조사성 작업부터.
- 트랙별 착수 시 이 리포에 protocol(판정 기준 LOCK) 커밋 → 구현은 트랙 저장소에서 → 결과는 이 리포 `experiments/`에 research(results) 커밋.

## 전체 태스크 의존성 그래프 (요약)

```
INFRA-0 (EDA 환경) ──┬─→ A1(수집기) → A2(CLI/대시보드) → A3(도그푸딩+스윕 데이터) → A4(QoR 예측기) → A5(AutoTuner 통합)
                     ├─→ B1(파서+스키마) → B2(golden diff 하네스) → B3(HTML/MCP) → B4(공개·채택 측정)
                     └─→ C2(재현 하네스) ← C1(실패 사례 코퍼스; INFRA-0와 병행 가능) → C3(룰 DB) → C4(백테스트)
D1(데이터 파이프라인) → D2(GBDT/U-Net 변형) → D3(공식 스플릿 평가·점수표 비교)   [INFRA-0와 독립]
공통: 각 트랙 Pn 착수 전 protocol LOCK(Codex 게이트) / 최종: WOSET·JOSS 제출
```
