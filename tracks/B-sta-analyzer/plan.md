# 트랙 B 계획서 — STA 리포트 분석기

가설: H2 · 근거: [raw/01](../literature/raw/01-tool-gaps-demand.md) (OR #1759·#10020·#9371·#4633, openroad-mcp #96 "Impact: High")

## 목표

OpenSTA/OpenROAD의 `report_checks` 계열 텍스트 리포트를 **구조화 JSON**으로 파싱하고, 자체완결 HTML 시각화(slack 히스토그램, 경로 그룹별 스택, 경로 드릴다운)와 **MCP 서버**(AI 에이전트가 타이밍 데이터를 질의)로 제공. "타이밍 리포트의 Surfer" — 기존 포맷 그대로 + 나은 UX + 임베드 가능이라는 Surfer 성공 공식을 따른다.

## MVP 스코프

- 파서: `report_checks -path_delay min/max`, `report_tns/wns`, `report_power` 텍스트 → 검증된 JSON 스키마 (신호명·셀·slew·cap·delay·slack 전 필드)
- `sta-view <report>`: 단일 HTML 출력 — slack 히스토그램, 위반 경로 테이블, 경로 상세(스테이지별 delay 분해)
- `sta-view diff <A> <B>`: 두 리포트 간 경로별 slack 변화
- MCP 서버 모드: `worst_paths(n)`, `path_detail(endpoint)`, `slack_histogram()` 등 질의 도구
- 지원: OpenSTA 단독 + ORFS/LibreLane run 산출물 자동 탐지

비스코프: 상용 툴(PrimeTime 등) 리포트, 타이밍 수정 제안(진단은 트랙 C 영역), GUI 앱.

## 유용성 판정 기준 (protocol LOCK 항목 — 초안)

| 축 | 기준(초안) | 방법 |
|---|---|---|
| 정합성 (필수) | ORFS 예제 설계 전수의 리포트에서 파싱 수치 100% 일치 (**golden diff**) | 원본 텍스트 재생성 대조 + 수치 필드 전수 비교 |
| 견고성 | OpenSTA 최소 2개 버전 출력 형식에서 회귀 통과 | 버전 매트릭스 CI |
| 외부 사용 | 수요 이슈 스레드(OR #1759 등) 공개 후 사전 고정 기간 내 외부 사용 증거 | GitHub 지표 + 이슈 스레드 반응 |

## 태스크 그래프

```
INFRA-0 ─→ B1 ─→ B2 ─→ B3 ─→ [H2 판정] ─→ B4
```

| ID | 태스크 | 산출물 | 의존 |
|---|---|---|---|
| B1 | 리포트 코퍼스 수집(ORFS 예제 전수 실행) + JSON 스키마 설계 + 파서 | 파서 + 스키마 문서 | INFRA-0 |
| B2 | golden diff 하네스 + OpenSTA 버전 매트릭스 CI | 테스트 스위트 (정합성 게이트) | B1 |
| B3 | HTML 시각화 + diff + MCP 서버 | v0.1 릴리스 (public) | B2 |
| B4 | 수요 이슈 스레드·openroad-mcp에 공개, 채택 측정, WOSET 제출 준비 | 공개 포스트 + 측정 기록 | B3 |

## 리스크

- **코어팀 선점**: OpenROAD가 자체 구현할 수 있음(이슈 공개 상태). 완화: 빠른 v0.1 공개 + openroad-mcp와 상호보완 포지셔닝(파서 라이브러리로 기여 가능하게 설계). 선점당해도 파서·스키마는 업스트림 기여물로 전환 — negative가 아니라 경로 변경.
- **텍스트 파싱 취약성**: 버전 매트릭스 CI로 방어, 스키마에 `parser_version`·`unparsed_lines` 필드로 실패를 침묵시키지 않음.
- **참고**: 트랙 A 대시보드의 타이밍 뷰로 B의 파서를 재사용 가능 — 저장소는 분리하되 파서를 독립 라이브러리로.
