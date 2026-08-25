# INFRA-0: 로컬 오픈소스 EDA 환경 구축 기록

- 작성: 2026-08-25 (EDA 환경 구축 에이전트)
- 시스템: macOS 26.5, Apple Silicon (arm64), 10코어/32GB, Docker Desktop 29.6.1, Homebrew

## 설치 경로 결정 (공식 문서 근거)

LibreLane 3.x 공식 문서(librelane.readthedocs.io, 2026-08 시점 latest) 기준 macOS 설치 경로는
Nix(1급) / AppImage / **Docker 기반** 3종. 본 환경은 nix 미설치·Docker 기설치이므로 공식
Docker-based Installation 경로 채택: `pip install librelane` 후 `--dockerized` 플래그로 실행.
(OpenLane v1 방식 아님 — LibreLane 3.x 공식 지원 경로.)

- 근거: https://librelane.readthedocs.io/en/latest/installation/docker_installation/installation_macos.html
- GitHub: https://github.com/librelane/librelane (Python 3.10+ 요구)

## 설치된 툴

| 툴 | 버전 | 설치 방법 |
|---|---|---|
| Icarus Verilog | 13.0 | `brew install icarus-verilog` |
| Verilator | 5.050 (2026-07-01) | `brew install verilator` |
| Yosys (로컬) | 0.68+post | `brew install yosys` |
| LibreLane | 3.0.11 | pip (venv) |
| Python (venv용) | 3.13.12 | brew `python@3.13` (기존 설치분 활용) |
| Docker 이미지 | `ghcr.io/librelane/librelane:3.0.11` (7.5GB) | 자동 pull |
| ciel (PDK 관리) | 2.6.1 | librelane 의존성으로 자동 설치 |

- venv 경로: `/Users/dohyunjung/Workspace/roboco-io/research/semiconductor-design-tracks/.venv-eda`
  - 실행: `.venv-eda/bin/python -m librelane --docker-no-tty --dockerized <args>`
- Python 3.14(시스템 기본)는 사용하지 않음 — LibreLane 요구는 3.10+이지만 안전하게 brew
  python@3.13으로 venv 구성. 3.13.12에서 설치·실행 모두 정상.

## PDK

- SKY130, ciel 자동 다운로드: `~/.ciel/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/`
  (sky130A·sky130B 포함, 총 약 2.1GB. 버전 = open_pdks commit `8afc8346a57f…`)

## 스모크 테스트 결과 (모두 성공)

1. **시뮬레이터 로컬 테스트**: 4-bit 카운터 — iverilog+vvp 시뮬레이션 `SMOKE_PASS`,
   `verilator --lint-only` 통과, yosys `synth` 10 cells 합성 정상.
2. **LibreLane 공식 스모크 테스트**: `python -m librelane --docker-no-tty --dockerized --smoke-test`
   → **"Smoke test passed."** Classic flow 80/80 스테이지, 플로우 자체 약 57초.
   (이미지 pull + PDK 다운로드 포함 전체 수 분.)
3. **SPM 예제 정식 완주**: `--run-example spm` → 80/80 완료, 산출물 영구 보존.
   - 런 디렉토리: `/Users/dohyunjung/Workspace/roboco-io/research/semiconductor-design-tracks/examples/spm/runs/RUN_2026-08-25_10-25-36/`
   - final/에 gds·def·lef·nl·spef·sdf·metrics.json 등 전체 뷰 생성.
   - 핵심 메트릭: instance 1,226개, route DRC 0, magic DRC 0, LVS error 0,
     setup WS +3.59ns → 클린 sign-off.

## 주의사항

1. **`--docker-no-tty` 필수 (비대화형 실행 시)**: 에이전트/스크립트처럼 TTY 없는 셸에서
   `--dockerized`만 쓰면 "cannot attach stdin to a TTY-enabled container" 오류로 플로우가
   실행되지 않음(그런데 exit code는 0 — 로그 확인 필수). 또한 **플래그 순서 중요**:
   `--docker-no-tty`는 반드시 `--dockerized` **앞에** 와야 함. `--dockerized` 뒤의 인자는
   전부 컨테이너 내부로 전달되기 때문.
2. **Docker Desktop VM 리소스**: 현재 6 CPU / 8GB 할당. SPM 규모는 충분하나, 큰 설계나
   병렬 STA에서는 Docker Desktop 설정에서 CPU/메모리 상향 권장.
3. Docker Desktop이 꺼져 있으면 데몬 연결 실패 — `open -a Docker` 후 데몬 대기 필요.
4. 공식 문서상 Docker File Sharing에 `/Users` 마운트 필요(기본값이면 이미 충족 — 본 환경 정상).
5. `--smoke-test`의 산출물은 임시 폴더에 생성 후 폐기됨. 산출물이 필요하면
   `--run-example spm` 또는 실제 config로 실행할 것.
6. yosys를 brew로 로컬 설치했지만, LibreLane 플로우는 컨테이너 내장 yosys를 사용 —
   로컬 yosys는 빠른 반복(수동 합성 실험)용.
7. 플로우 경고(무해 확인): CustomIOPlacement 핀 간격 override, lib 중복 로드, VSRC_LOC_FILES
   미지정(IR drop 정확도 — 탑레벨 칩 통합 전에는 무시 가능) 등.
