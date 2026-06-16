# program.md — 에이전트 baseline 지시문

AutoResearch 루프의 에이전트가 `train.py`를 변형할 때 따르는 baseline 지시·맥락·제약.

## 목표
surrogate val 지표 **`val_mae`(ns) 최소화**. train.py는 per-endpoint timing slack 회귀
모델을 학습하고 stdout에 `{"val_mae": <float>}` 한 줄을 출력한다 (낮을수록 좋음).

## 입력 데이터 (frozen 계약 — 변경 금지)
`--data <dataset.jsonl>`: prepare.py 출력. 각 행은 8 feature
(`num_stages, synth_slack_ns, synth_arrival_ns, max_stage_delay_ns, mean_stage_delay_ns,
startpoint_is_ff, endpoint_is_ff, path_group`) + 라벨 `post_route_slack_ns` + `group_key`.

dataset은 **다설계 혼합**일 수 있다(`group_key`로 설계 구분). 그 경우 `train.py`의 val split은
**설계-분리**(GroupShuffleSplit)라 `val_mae`는 *학습에서 안 본 설계*에 대한 예측 성능 — 즉 selection
지표 자체가 교차설계 일반화를 측정한다. 승격 전 별도 LODO 게이트가 일반화 후퇴를 한 번 더 차단한다.

## 변형 허용 범위 (이 안에서 자유롭게)
- 모델 종류: sklearn 내 교체 (HistGradientBoostingRegressor / RandomForest / ExtraTrees /
  GradientBoosting / MLPRegressor 등).
- 하이퍼파라미터, feature 엔지니어링/선택/인코딩, train/val split 전략.

## 절대 제약 (위반 시 후보 무효)
- `train.py` **단일 파일**만. 신규 의존성 금지 — `sklearn`, `numpy`, `joblib`, `click`,
  stdlib만 import.
- stdout 출력 계약: `{"val_mae": <float>}` 한 줄. `--out <dir>/model.joblib` 저장.
- CLI `--data`/`--out`/`--seed` 시그니처 불변. 8 FEATURE_NAMES 불변.
- 고정 CPU 학습 예산 (분 단위). GPU·딥러닝 프레임워크 금지.

## 전략 힌트
- conservative: baseline에 가까운 소폭 튜닝.
- moderate: 모델 교체 또는 feature 엔지니어링.
- aggressive: 둘 다 + 비표준 조합 시도.

## 출력 형식
마크다운/설명/펜스 없이 **변형된 train.py 전체 소스만** 출력.

## 관찰 힌트 (probe 실측 — 지시 아님, 참고용)

아래는 Operator의 교차설계 probe(`experiments/multidesign/probe/probe.md`,
`probe-3design.md`)에서 관찰된 *사실*이다. 전략 선택은 너에게 맡긴다 — 따라야 할 지시가 아니다.

- 델타 label(`post_route_slack_ns − synth_slack_ns` 잔차 학습)은 드리프트가 안정적인 설계(aes)에서
  naive를 37% 이겼으나, 드리프트가 자릿수로 다른 설계(ibex)에선 약했다.
- 혼합 분포 훈련은 절대 스케일 모델의 미관측 설계 전이를 회복시켰다(ibex held-out서 naive 4.3× 격파).
- held-out 설계별 최선 전략이 갈렸다 — 단일 정답 축은 없었다.

## Operator 감독
winner 승격은 **자동 게이트(median + LODO 교차설계 + T1 통계 검증 + Codex 승격 심사관)** 가 판정한다.
Operator는 `program.md`로 *방향*을 잡고 세대 리포트(`gen-NNN/report.md`)로 *큰 흐름을 이해*한다 —
per-winner 승인은 없음(2026-06-08 재피벗). 본 지시는 후보 *생성*에만 적용.
