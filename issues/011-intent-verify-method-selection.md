# Issue 011 — 새 의도(반도체 설계 × 바이브 코딩)의 확인 방법 선정

> status: decided (2026-08-22 — 이중 축 조합) · created: 2026-08-22
> 전제: 새 INTENT.md (status: exploring) — Why의 `확인 방법: (?)` 해소용.
> 근거: exa grounded 조사 (citation 18건, 2026-08-22, verify-method-research 에이전트).

## 조사 핵심 발견 (요약)

1. **LLM-RTL 성공 측정의 표준**: 테스트벤치 기능 정합 + pass@k (VerilogEval →
   NVIDIA CVDP 783문제, SOTA pass@1 ≤34%). 2026-07 Si2 LBC-bench 공개 리더보드가
   CVDP 채택. 더 강한 기준으로 Yosys 형식 등가성 검사.
2. **오픈소스 flow의 재현 가능 품질 보고 표준 존재**: IEEE CEDA DATC **METRICS2.1**
   (RTL-to-GDS 단계별 PPA/타이밍/DRC를 JSON 표준화, 커밋 해시 고정 → 제3자 재현).
   ORFS는 golden 지표 + rules.json 회귀 게이트를 이미 운영 — 본 리포의 게이트 패턴과 동형.
3. **"실무 사용 가능"의 업계 기준**: OpenTitan V1→V3 검증 성숙도(커버리지 90→100%) +
   sign-off 체크리스트 + silicon-proven(Chromebook 양산). OpenHW: 오픈소스 IP 채택
   장벽 = 검증 품질. 개인 IP 실무 인정 단독 사례는 미발견.
4. **학습 측정의 표준**: pre/post 지식 검사 + 상호작용 패턴 분류. TUM RCT의
   "성과-학습 해리"(AI가 점수는 올려도 학습은 못 올림), Anthropic RCT의 "개념 질문형
   패턴은 학습 보존". 하드웨어 전용 검증 도구 **DLCI** 존재.
   LLM+TinyTapeout 교육 논문이 "학습 곡선 정량화 = future work" 명시 → **novelty 공백**.
5. **"학습+설계 단일 사이클" 선행**: human-AI co-learning 프레임은 있으나,
   칩 설계 객관 게이트 × 설계자 학습 측정을 하나의 진화 사이클로 묶은 연구 미발견 (추정).

## 확인 방법 후보 5개

| # | 후보 | 측정 | 객관성 | 실무성 | 비용 |
|---|---|---|---|---|---|
| 1 | METRICS2.1 세대별 PPA + sign-off 게이트 | WNS/전력/면적 + DRC·LVS 위반 0 | 표준 JSON·커밋 고정·결정론적 | sign-off = tapeout 전제 | 0 (로컬) |
| 2 | 기능 정합 pass@k + Yosys 형식 등가성 | 테스트벤치 통과율·등가성 통과 | 자동 채점, LBC-bench 비교 가능 | 업계 표준 측정법 정렬 | 0 |
| 3 | OpenTitan식 검증 성숙도 축소판 | 커버리지 % + 사전 고정 체크리스트 | 시뮬레이터 정량값 | "실무 채택 가능 IP" 기준 그대로 | 0 (100% 기준은 1인에 과도 — 축소 필요) |
| 4 | Tiny Tapeout 실리콘 실증 | GDSII → 제출 → 실칩 동작 | 실리콘 = 궁극의 외부 판정 | silicon-proven 증빙 | 타일 €70+ |
| 5 | Operator 학습 pre/post (DLCI + 패턴 로그) | 개념 검사 gain + 상호작용 패턴 분포 | 심리측정 검증 도구·RCT 방법론 재사용 | "비전문가 성장" 직접 측정 | 0 (N=1 한계 명시) |

**조사팀 조합 제안**: 1+2 = 설계 축(자동 게이트), 5 = 학습 축, 4 = 최종 실무성
마일스톤, 3 = 1·2의 임계값 출처. — 가설이 "학습과 설계를 하나의 사이클로"이므로
설계 축과 학습 축을 모두 측정해야 가설 전체를 판정 가능.

## Citation (18건)

1. https://arxiv.org/abs/2309.07544 — VerilogEval v1 (ICCAD 2023)
2. https://arxiv.org/abs/2408.11053 — VerilogEval v2 (2024)
3. https://arxiv.org/abs/2506.14074 — CVDP (NVIDIA, 2025)
4. https://si2.org/introducing-the-lbc-bench-leaderboard-a-new-public-benchmark-for-llms-in-chip-design/ — Si2 LBC-bench (2026-07)
5. https://arxiv.org/html/2603.19347v3 — CVDP 에이전트 평가 + VeriThoughts 등가성
6. https://github.com/AUCOHL/RTL-Repo — RTL-Repo (IEEE LAD'24)
7. https://vlsicad.ucsd.edu/Publications/Conferences/388/c388.pdf — METRICS2.1 (ICCAD 2021)
8. https://github.com/ieee-ceda-datc/datc-rdf-Metrics4ML — 재현 가능 지표 아카이브
9. https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts/blob/master/docs/contrib/Metrics.md — golden/rules 회귀 게이트
10. https://openlane.readthedocs.io/en/latest/reference/datapoint_definitions.html — DRC/LVS 리포트 정의
11. https://opentitan.org/book/doc/project_governance/development_stages.html — V1-V3 단계 기준
12. https://opentitan.org/book/doc/project_governance/checklist/index.html — sign-off 체크리스트
13. https://opentitan.org/faq/ — silicon-proven 양산 사례
14. https://openhwfoundation.org/resources/blog/openhw-industrial-grade-verification-for-open-source-core-v-ip-cores/ — OpenHW 검증 기준
15. https://arxiv.org/html/2601.13815v1 — LLM+Tiny Tapeout 교육 (학습곡선 측정 갭 명시)
16. https://portal.fis.tum.de/en/publications/less-stress-better-scores-same-learning-the-dissociation-of-perfo/ — TUM RCT 성과-학습 해리
17. https://www.anthropic.com/research/AI-assistance-coding-skills — 상호작용 패턴별 학습 보존 (arXiv: https://arxiv.org/html/2601.20245)
18. https://www.jair.org/index.php/jair/article/view/16846 — co-learning 실험 평가 (JAIR 2025); 보조: https://doi.org/10.48550/arxiv.1910.12544, https://dl.acm.org/doi/10.1145/1734263.1734298 (DLCI), https://www.tandfonline.com/doi/abs/10.1080/08993408.2014.970781 (DLCI 심리측정), https://terpconnect.umd.edu/~weintrop/papers/Kazemitabaar_et_al_CHI_2023.pdf (CHI 2023)

## 결정

- [x] Operator 선택 (2026-08-22): **이중 축 조합** — 설계 축(pass@k + METRICS2.1
  PPA/sign-off) + 학습 축(DLCI pre/post + 패턴 로그), Tiny Tapeout = 실무성 마일스톤,
  OpenTitan 기준 = 임계값 출처. → INTENT.md Why 갱신 완료.
