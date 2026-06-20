# 결정 brief — Sub-A 4번째 설계 추가 (2026-06-21)

## 맥락
gen-004~007 네 세대 연속 승격 0건. 게이트는 정상 작동(각기 다른 이유로 위양성 차단)했으나, 일관된
진단은 **저표본(설계 3) + ibex 단독 의존**이다 — 교차설계 LODO/T1이 3 fold뿐이라 Wilcoxon 통계가
사실상 불가하고, ibex(2040행, 자릿수 다른 분포)가 결과를 좌우한다. INTENT Learnings가 반복해서
"강한 결론은 설계 확보(Sub-A) 후"로 미뤄둔 지점.

기존 자산: Sub-A spec/plan(`2026-06-09-t4-lite-suba-*`)이 절차를 완성해 뒀고, gcd+aes+ibex 3설계가
그 산출물. 4번째 추가는 **기존 Fargate flow + prepare.py + combine_datasets 파이프라인 재사용**
(새 코드 거의 불필요). spec이 4번째 후보로 **jpeg**을 명시(옵션 1-C).

## 실행 절차 (설계 1개, 검증됨)
1. CDK 배포(`cdk deploy`) + ECR 이미지 빌드·푸시(native x86) — 1회.
2. `aws ecs run-task` with `DESIGN=jpeg` → ORFS flow 완주 → synth.rpt/route.rpt/versions.txt → S3.
3. S3 → `experiments/real-jpeg-fargate/` 수집 → `prepare.py --design-id jpeg` → dataset.jsonl.
4. `combine_datasets([gcd, aes, ibex, jpeg])` → `dataset-4design.jsonl`.
5. Makefile DATASET 기본값 갱신 → gen-008+ 4설계 LODO(4 fold).
6. **`cdk destroy`로 스택 정리(비용 정지)**.

## 선택지

### A. jpeg 추가 (spec 명시 후보, 권장)
- **요지**: spec이 이미 4번째로 지정. ORFS 표준 세트 포함, ibex와 다른 크기/분포 기대.
- **pros**: LODO/T1 3→4 fold(Wilcoxon 통계력↑). ibex 단독 의존 완화. 절차 검증됨. spec 정합.
- **cons**: AWS 실비용($) + Fargate 1회 실행(jpeg 크기에 따라 ~10~40분 추측). Operator 동의 필요.

### B. 더 큰/다른 설계(riscv 등) 추가
- **요지**: jpeg 대신 분포가 더 극단적인 설계로 일반화 stress를 키움.
- **pros**: 분포 다양성 최대.
- **cons**: spec 미검증(jpeg만 명시). 마찰·비용·시간 위험↑(큰 설계 = CTS/route↑). gcd→ibex에서 겪은
  마찰 재발 가능.

### C. 지금은 보류 — gen-008 재추첨 등 무비용 경로 우선
- **요지**: AWS 비용 없이 생성 전략(program.md)·게이트만 더 탐색.
- **pros**: 무비용. cons: 4세대 패턴상 데이터 없이 통계 벽 돌파 가능성 낮음 — 근본 병목 미해소.

## 비용·안전
- AWS는 **실 과금**(LLM 구독과 다름). Fargate 4vCPU/16GB on-demand 1회 + S3/ECR 소액.
- **D4 비용 게이트**: run-task는 Operator 명시 동의 후에만. 실행 후 `cdk destroy` 필수.
- gcd dataset frozen 불변 — 4번째 추가는 기존 3설계 dataset 무변경(combine은 새 파일 생성).

## 권장
**A(jpeg)** — spec이 지정한 검증된 경로로 통계력을 올리는 게 최소 위험·최대 정합. 단 **AWS 실행은
Operator per-instance 동의가 필수**라, 동의 전까지는 plan 문서화까지만 진행(무비용). 동의 시 CDK
배포→run-task→수집→destroy 순으로 실행하고 비용을 사후 보고.
