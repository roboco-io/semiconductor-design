# real-gcd-fargate — F4/F1/F3 end-to-end 검증 성공 (2026-06-06)

> native x86 ECS Fargate(`semi-design-eda-dev`, ap-northeast-2)에서 ORFS gcd 완주 →
> 진짜 두-시점 `report_checks` → S3 → **frozen prepare.py 파서로 53 샘플 생성**.
> 설계: `docs/superpowers/specs/2026-06-06-eda-flow-fargate-oneshot-design.md`. 이슈: `issues/006`.

## 결과
- ORFS gcd: synth→floorplan→place→**CTS→route**→fill→GDS 완주. **QEMU illegal instruction 없음** → **F4 해결**(로컬 emulation의 CTS 사망이 native Fargate에서 사라짐).
- `report_checks`(minimal, no -fields): synth.rpt 2853줄(125KB) / route.rpt 3549줄(161KB).
- **prepare.py 파싱: `n_samples = 53`** (flow_lockfile_sha `bff0e2e5…`). 두-줄 Startpoint/Endpoint 헤더(F1) + endpoint 단위 join(F3) 실데이터 검증.
- 첫 샘플 예: endpoint `dpath.b_reg.out[0]$_DFFE_PP_`, num_stages 11, synth_slack −3.68 ns, **post_route_slack −1.24 ns**(실제 violation, heavy-tailed label — OD-4 tabular 근거와 정합).

## 배포 iteration (DEPLOY.md step-5 검증 루프)
실행으로만 드러나는 EDA-flow 문제를 5회 iter로 수렴:
1. `openroad: command not found` → entrypoint에 `source env.sh`.
2. exit 1 (redirect로 에러 가림) → openroad 출력 CloudWatch 직결 + Tcl read 순서 `read_db→liberty→sdc`.
3. OpenROAD usage 출력 → cmd_file 뒤 트레일링 argv 미지원, 인자를 **env로 전달**.
4. `aws` urllib3 `DEFAULT_CIPHERS` ImportError → apt awscli → **awscli v2 번들**.
5. rpt 1 byte → `report_checks`는 stdout 출력·빈 반환 → openroad **stdout을 .rpt로 리다이렉트**.

## 정정
- region: spec의 us-east-1 → 실제 **ap-northeast-2**(roboco 프로필 기본 region이 우선). 한국 사용자에 유리, 무손실.
- `flow_lockfile_sha`는 현재 versions.txt(이미지 digest + 도구 버전) 기반. SDC는 route 단계 `5_1_grt.sdc` 사용.

## 잔여
- post-route SDC를 `6_final.sdc`로 정밀화(현재 grt sdc) — 정확도 향상 여지(라벨 품질).
- 다설계 batch(OD-3) — 동일 task를 design 파라미터화해 반복.
