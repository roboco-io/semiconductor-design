# 프로젝트 용어집

이 문서는 `semiconductor-design` 연구 프로그램에서 자주 쓰는 용어를 한 줄로
정리한 reference다. 12살 독자도 따라올 수 있게 풀어 적되, 정확한 설계 근거는
**`wiki/index.md`** 와 `docs/superpowers/specs/` 의 spec을 따른다.

> **읽는 순서 권장**: 먼저 `wiki/index.md` 에서 관련 페이지(`[[wiki-link]]`)를
> 본 뒤, 모르는 용어가 나오면 본 glossary로 돌아온다. graphify 그래프 쿼리는
> cross-component 경로 탐색이 필요할 때만 보조로 쓴다 (2026-05-09 wiki-first
> hybrid 정책).

## 프로젝트 고유 개념

| 용어 | 뜻 |
|---|---|
| Report-Grounded Vibe-Coded AutoResearch | 본 저장소의 통합 연구 프로그램 이름. EDA 도구가 만든 리포트(`*.rpt`)와 실행 trace를 근거로 LLM 에이전트가 작은 실험을 반복하고, 사람(operator)이 감독한다. 비유 — 요리사 로봇이 매번 시식·온도 측정 결과를 보고 다음 단계를 정하고, 주방장이 그 결정을 검토한다. |
| L1 Process | 재현 가능한 실행 환경 계층. SHA-pinned 도구 체인, 로컬 CLI, AWS Fargate Spot, Step Functions, artifact lake를 묶어 부른다. "어디서 돌려도 같은 결과"를 보장하는 부엌. |
| L2 Substrate | 지식·메모리 계층. 리포트, patch, 결정 기록을 typed-frontmatter 문서와 skill library로 축적한다. 부엌이 매번 새 요리 시작하지 않게 해주는 *레시피 노트*. |
| L3 Content | 실제 연구 대상 계층. Gemmini, MLPerf Tiny, Open-Ideation DSE 같은 설계·실험 콘텐츠. 부엌·노트가 갖춰졌으니 "오늘 뭘 만들 것인가". |
| 4-plane | 실행 substrate를 보는 다른 시각. Local · AWS · Tool · Knowledge. 3-layer가 *연구 프로그램의 층*이라면 4-plane은 *실행 인프라의 면*이다. 두 시각은 overview spec §3에서 동시에 정의된다. |
| Open-Ideation DSE | 정해진 knob만 휘두르는 게 아니라, 에이전트가 *구조 아이디어*(예: 파이프라인 깊이를 바꾸자)를 제안한 뒤 patch와 sign-off 결과로 채택 여부를 판단하는 DSE 방식. ORFS-agent(2025)가 못 다룬 영역 — H1b 차별화 축. |
| Report-grounded agent operation | 에이전트가 추측하지 않고 synthesis · PnR · STA · DRC 리포트를 *읽어보고* 다음 조치를 결정하는 운영 방식. "감으로 말고 영수증 보고 결정해". |
| Reversible patch | baseline을 직접 덮지 않고 언제든 되돌릴 수 있는 작은 변경 단위. 게임 세이브 포인트와 같다 — 망하면 세이브로 복귀. `program.md` 핵심 규칙. |
| Skill library | sign-off로 검증된 patch · transform · 운영 지식을 재사용 가능한 skill로 저장하는 라이브러리. K2 η가 "Voyager × SEVerA × RSR" 교집합으로 정량화. |
| Negative result | 실패한 실험 결과. 본 프로젝트에서는 *지우는 대상이 아니라 자산* — 다음 search에서 같은 막힘을 피하고, 중복 candidate를 빠르게 걸러낸다. |
| Reasoning trace | 에이전트가 어떤 입력 · 도구 호출 · 판단 근거로 후보를 채택·기각했는지 남긴 실행 기록. H3 가설 평가의 직접 증거. |
| Process-as-contribution | 최종 PPA 수치만이 아니라 재현 가능한 실행 번들 · trace · 운영 절차 자체를 *연구 기여물*로 본다는 관점. 본 프로젝트의 publish 축. |
| Operator | 칩 설계 전문가가 아니라 에이전트와 EDA 도구 출력을 *감독·디버깅*하는 사람. 셰프가 아니라 주방장 — 직접 칼질이 아니라 흐름이 옳은지 본다. Phase 0 학습의 목표 역할. |
| Operator lens | Phase 0 학습 우선순위의 별명. "이론을 깊이 파는 게 아니라 리포트(`*.rpt`)와 파일 포맷(`.v/.lib/.lef/.def/.sdc`)을 비판적으로 *읽어내는* 능력". `[[phase-0-eda-operator-lens]]` 정책 페이지. |

## 연구 단계와 판단 기준

| 용어 | 뜻 |
|---|---|
| K1 | 초기 지식 수집·방향 판단 단계. 4축(α/β/γ/δ) × 평균 13 paper = 52 source. "뭘 할지" 그림. wiki에 4 evidence 페이지로 컴파일됨 (`[[k1-{alpha,beta,gamma,delta}-evidence]]`). |
| K2 | K1 이후 spec 결정의 *backing evidence* 단계. 4축(ε/ζ/η/θ) × 평균 15 paper = 61 source. K1이 *forward synthesis*라면 K2는 그림에 맞게 자료 *역으로 묶기*. wiki 4 evidence 페이지. |
| Evidence cascade | K1의 큰 방향("LLM이 RTL을 어느 정도 만든다")이 K2의 spec 결정("그러므로 reversible patch + SISA mutation으로 구체화")으로 이어지는 자료 흐름. wiki에서 `[[k1-α]]`→`[[k2-η]]` 같은 cross-link로 추적. |
| H1 | Primary hypothesis. report memory + reversible-patch skill library가 (a) finding 재사용, (b) structural patch, (c) cold-start 실패 측면에서 ORFS-agent baseline 대비 개선을 만든다는 가설. |
| H1a Finding reuse rate | 이전에 발견한 finding이 이후 실험에서 재사용되거나 duplicate로 매칭되는 비율. 높을수록 좋음. |
| H1b Non-knob structural patch | 단순 knob 조정이 아닌 *구조적* RTL/constraint 변경이 sign-off를 통과한 건수. ORFS-agent가 못 다룬 영역. K2 η에서 SISA array-partitioning이 첫 entry. |
| H1c Cold-start failure rate | 새 디자인에 처음 투입한 초기 run 중 sign-off fail이 나는 비율. 낮을수록 좋음. |
| H2 | 여러 디자인을 순차적으로 다룰 때 축적 memory가 실패율을 낮추는지 보는 *복리 효과* 가설. 보조 지표. |
| H3 | 비전문가 평가자가 reasoning trace를 읽고 후보 채택·기각 이유를 *복원*할 수 있는지 보는 process 가설. K2 ε에서 LLM-as-judge κ ≥ 0.6 falsifier로 정량화. |
| Canonical decision table | overview spec §5.3. publish · reframed-publish · kill 분기를 결정하는 *유일한* 판정표 — `H1 pass count × H3 validity` 조합. 다른 문서는 자체 publish/kill 기준을 선언하지 않는다. |
| Kill gate | 다음 단계로 가기 전 반드시 통과해야 하는 검증 조건. L1에서는 **KG-A ~ KG-E** 형태로 정의된다 (KG-E까지가 spec 기준). |
| KG-A ~ KG-E | L1 단계의 5개 kill gate. 각각 toolchain reproducibility · candidate execution · artifact integrity · cost containment · DDB write amplification 등을 검증. K2 ζ가 직접 backing. |
| Pre-registration | 실험 시작 전 sample size · threshold · seed · exclusion list를 *고정*하는 절차. 결과 본 뒤 기준을 바꾸는 부정행위 차단. |
| Blinded audit | 독립 평가자가 후보·결과의 출처를 모른 채 자동 판정의 타당성을 검수하는 절차. |
| Evaluator separation | trace 생성 LLM과 평가 LLM의 family를 분리하는 규칙. "자기 답을 자기가 채점하지 않는다" — H3 evidence 오염 방지 장치. |

## 반도체·EDA 기본 용어

| 용어 | 뜻 |
|---|---|
| EDA | Electronic Design Automation. 칩을 손으로 그리는 대신 *프로그램으로* 설계·검증하는 도구 모음. 종이 → 그림판 비유. |
| ASIC | Application-Specific Integrated Circuit. 특정 목적에 맞춰 만든 주문형 반도체. 만능 칼이 아닌 *전용 가위*. |
| RTL | Register Transfer Level. "데이터가 A 레지스터에서 B 레지스터로 옮겨가는" 단계를 글로 적은 하드웨어 설계 추상화. 레고 설명서의 중간 단계. |
| HDL | Hardware Description Language. Verilog · SystemVerilog · VHDL 같은 *하드웨어를 글로 적는* 언어. |
| Verilog | RTL 작성용 대표 HDL. 본 프로젝트에선 에이전트 출력 검수와 합성 입력으로 핵심. |
| Chisel | Scala 기반 하드웨어 생성 언어. Gemmini/Chipyard 설정 이해에 필요. |
| Synthesis | RTL을 gate-level netlist로 바꾸는 단계. "글로 적힌 설계 → 실제 게이트 부품 목록". Yosys가 대표 오픈소스 도구. |
| PnR | Place and Route. 셀을 배치하고 배선을 까는 물리 구현 단계. 게이트들을 칩 위 어디에 놓고 어떻게 잇느냐. |
| STA | Static Timing Analysis. 칩이 정해진 시간 안에 신호를 다 전달할 수 있는지, 한 번도 *실제로 돌리지 않고* 표만 가지고 검사하는 일. |
| Sign-off | 출시 전 마지막 도장. timing · DRC · LVS 등 필수 검증을 모두 통과해야 "OK 만들어도 돼" 도장. |
| DRC | Design Rule Check. 공정 제조 규칙을 어긴 layout이 있는지 검사. "공장이 만들 수 있는 모양인가?" |
| LVS | Layout Versus Schematic. 그려진 layout이 의도한 회로/netlist와 *전기적으로* 일치하는지 검사. |
| PDK | Process Design Kit. 특정 공정에서 설계할 때 필요한 cell · rule · model · tech file 묶음. "이 공장에서 빵 구울 때 쓰는 레시피 + 오븐 사양 + 재료 카탈로그". |
| Open PDK | 공개적으로 쓸 수 있는 PDK. sky130A, gf180mcuD가 본 프로젝트 후보. |
| sky130A | SkyWater 130nm 오픈 PDK. 오픈소스 ASIC 플로우의 *기본값*. K1 γ에서 stack 결정, K2 ζ에서 ciel SHA-pin으로 재현성 확보. |
| Liberty `.lib` | 표준 셀의 timing · power · 기능 정보를 담는 텍스트 파일. "이 부품 얼마나 빠르고 얼마나 전력 먹는지" 사양서. |
| LEF | Library Exchange Format. 셀과 macro의 *물리적 크기* · pin · routing 장애물 정보. |
| DEF | Design Exchange Format. 배치·배선 *결과*. "이 셀은 칩 위 (x,y) 좌표에 놓였고 이 선이 어떻게 깔렸다". |
| SDC | Synopsys Design Constraints. 클럭 · I/O delay · timing exception 같은 *제약*을 도구에 알려주는 파일. |
| GDSII | 제조 공장에 넘기는 *최종* layout 데이터 포맷. 도면 PDF의 칩 버전. |
| QoR | Quality of Results. area · timing · power · runtime을 묶어 도구 결과 품질을 부르는 말. |
| PPA | Power · Performance · Area. 반도체 설계 품질 *3대 지표*. |
| WNS | Worst Negative Slack. 가장 나쁜 timing slack. 0 이상이면 timing clean. |
| TNS | Total Negative Slack. 모든 negative slack의 합. timing 위반 *총량*. |
| Critical path | timing을 가장 많이 잡아먹는 가장 느린 경로. STA 리포트에서 우선 봐야 할 후보. |
| Slack | "필요 도착 시간 − 실제 도착 시간". 음수면 timing 위반. 시험 끝나기 전 도착하느냐 늦느냐. |

## 도구와 벤치마크

| 용어 | 뜻 |
|---|---|
| OpenROAD | 오픈소스 RTL-to-GDS 물리 구현 도구 체인. PnR · STA · DRC 등 종합. |
| ORFS | OpenROAD-flow-scripts. OpenROAD 기반 reference flow와 benchmark 실행 스크립트 묶음. |
| ORFS-agent | ORFS parameter tuning을 자동화한 2025년 agentic EDA baseline. 본 프로젝트의 *기준 비교 대상* — 우리는 H1b structural patch 축에서 차별화. |
| OpenLane2 → LibreLane | Efabless 2025-02 셧다운으로 `efabless/openlane2` namespace 회수 불가 → FOSSi Foundation 이관 + rename. K1 γ Trigger 2. |
| LibreLane 3.0.2 | OpenLane 계열 FOSSi 관리 flow의 본 프로젝트 표적 버전 (2026-04-02). Synlig→Slang, nix-eda 6, Python 3.10+, KLayout DRC/LVS. K2 ζ §6.2 lockfile 갱신 trigger. |
| Yosys | 오픈소스 RTL synthesis 도구. |
| Verilator | Verilog/SystemVerilog simulation과 lint에 쓰이는 오픈소스 도구. |
| cocotb | Python으로 HDL testbench를 작성하는 프레임워크. |
| Chipyard | RISC-V SoC와 accelerator를 *생성·통합*하는 연구 플랫폼. 본 프로젝트는 1.13.0 SHA `69eba86` pin. |
| Gemmini | Chipyard 기반 systolic-array DNN accelerator generator. L3 Content 핵심 대상. |
| MLPerf Tiny v1.3 | 초저전력/임베디드 ML benchmark suite의 본 프로젝트 표적 버전. **streaming wakeword (Marvin)** 가 핵심 작업. K2 θ가 §13 License Gate와 함께 backing. |
| KWS | Keyword Spotting. 작은 음성 명령·wakeword 감지 ML task. MLPerf Tiny 항목. |
| gcd / ibex / aes | L1/L3 평가용 디자인 대상. gcd = smoke test (가장 단순), ibex = RISC-V 코어, aes = 암호화 — 복잡도가 단계적으로 올라감. |

## 실행 인프라와 저장소 용어

| 용어 | 뜻 |
|---|---|
| `semi-run` | L1 Process의 Python CLI 이름. spec 제출 · 상태 확인 · artifact 수집을 담당. `pyproject.toml` entry point. |
| Artifact bundle | 한 run의 spec · RTL · report · metrics · provenance · log를 함께 저장한 결과 묶음. 한 끼 식사 기록 일체. |
| Provenance | artifact가 어떤 source · SHA · container digest · operator/agent를 통해 만들어졌는지 *족보* 기록. "이 빵 어디서 사 왔어?"의 도구·SHA·운영자 버전. |
| Lockfile | 도구 · container · PDK · source mirror의 SHA/digest를 *고정*한 파일. "이 케이크는 우유 X 브랜드 + 설탕 Y 봉지로 만들었다"를 한 달 뒤에도 그대로 재현. K2 ζ §6.2가 LibreLane 3.0.2 + ephemeral 200 GiB + Distributed Map + SHA-pin 강제로 갱신. |
| SHA pinning | upstream branch 이름(`main`) 대신 *특정 commit SHA*나 digest를 고정해 외부 변경 drift를 막는 방식. |
| ciel | open_pdks 기반 PDK installer + 패키지 매니저 (`commit-hash` 형태로 sky130A 핀). K2 ζ에서 SHA-pin 메커니즘으로 채택. |
| AWS Fargate Spot | 저렴하지만 회수될 수 있는 serverless 컨테이너 실행 환경. EDA burst workload에 사용. |
| Step Functions Map | 여러 candidate run을 병렬 실행하는 AWS workflow 구조. K2 ζ에서 Distributed Map으로 확장. |
| S3 artifact lake | run artifact를 저장하는 S3 기반 저장소. |
| DynamoDB | run · candidate · budget · trace metadata를 저장하는 key-value DB. |
| Object Lock | S3 객체를 일정 기간 수정·삭제 못하게 막는 기능. 성공 artifact의 *불변성* 보장. |
| DLQ | Dead Letter Queue. 처리 실패한 메시지·작업을 격리하는 큐. 나중에 원인 조사. |

## 위키와 지식 그래프 (2026-05-09 wiki-first hybrid)

| 용어 | 뜻 |
|---|---|
| Wiki-first hybrid 정책 | 본 프로젝트의 *default 컨텍스트 라우팅* 정책 (CLAUDE.md L13 갱신). 답변 작성 시 `[[wiki/페이지]]` 인용을 강제. graphify는 *보조* — cross-component path 탐색이나 wiki 미컴파일 영역에 한해 사용. |
| Karpathy LLM Wiki | 본 정책의 출처 패턴. wiki에 "검색이 아닌 *컴파일된 지식*"을 누적해 재활용. [72-run 벤치마크](https://roboco.io/posts/karpathy-llm-wiki-72-run-benchmark/)에서 graphify 대비 토큰 −53.6% · 시간 −39.3% · 품질 +6% (p<0.01). |
| `wiki/index.md` | 페이지 라우팅 hub. type별로 그룹화된 `[[wiki-link]]` 목록. **수동 편집 금지** (`sync` 시 덮어씌워짐). |
| `wiki/{slug}.md` | 컴파일된 위키 페이지. type은 concept · decision · entity · meeting · policy · synthesis · comparison. frontmatter `sources:` / `related_specs:` 필수. |
| `wiki/raw/**` | 불변(read-only) seed corpus. K1+K2 papers, Phase-0 sessions, blogs, repos, docs, benchmarks가 카테고리별로 드롭됨. wiki 페이지로 *컴파일*되는 원료. |
| Page frontmatter | wiki 페이지 상단 YAML metadata. `title` · `type` · `status` · `confidence` · `created` · `updated` · `sources` · `related_specs`. lint 검사 대상 (Phase 1a 엔진과 무관하게 부활). |
| Confidence (페이지) | `high` / `medium` / `low` / `tentative`. low/tentative 페이지는 lint가 플래그. K2 evidence 일부는 "medium → spec 채택 시 high"로 *조건부 승급* 패턴. |
| Backlink density | 한 페이지를 다른 content 페이지가 얼마나 가리키는가. lint가 잡는 broken link와 별개로 *cluster isolation*(K2가 자기들끼리만 cross-ref하는 패턴 등)을 잡는 별도 신호. 2026-05-10 K1↔K2 1:1 backlink로 해소. |
| Graphify | tree-sitter AST + Claude subagent 의미 추출 + Leiden 커뮤니티 탐지를 결합한 지식 그래프 도구 (MIT, v0.4.25). **2026-05-09 이후 *보조* 도구로 격하** — default 라우팅은 wiki, graphify는 cross-component path 쿼리에 한정 사용. |
| `graphify-out/GRAPH_REPORT.md` | graphify가 만드는 사람용 요약. god-node 목록 · 커뮤니티 라벨 · surprising connections. 보조 entrypoint. |
| `graphify-out/graph.json` | NetworkX 기반 구조 데이터(node/link/hyperedge). `graphify query` · MCP 서버의 소스. version control 대상. |
| EXTRACTED / INFERRED / AMBIGUOUS | graphify 신뢰도 3-tier. 소스에 명시된 관계 / 합리적 추론 / 검토 대기. AMBIGUOUS는 human review 후 승격. |
| Graph integrity check | `scripts/graph_integrity_check.py`. L2.lint.check() interface. orphan 노드=0 · dangling edge=0 · AMBIGUOUS 비율 ≤ 0.3. |
| God node | degree·centrality 상위 노드. 시스템 허브. |
| `graphify query` / `path` / `explain` | BFS/DFS 질의 / 두 노드 간 최단 경로 / 노드의 사람용 설명. L2.memory.recall 사용자 경로. wiki에 답이 부족할 때만 사용. |

## Phase 1a Wiki Engine (폐기, 단 wiki 자체는 운영 부활)

`src/semi_design_wiki/` Python *엔진* 코드는 2026-04-22 graphify 전환 시
폐기됨. 그러나 **마크다운 위키 자체는 2026-05-09 wiki-first hybrid 정책으로
운영 부활** — frontmatter · `[[wiki-link]]` · lint는 살아있다.
새 작성자는 "Phase 1a 폐기"를 *엔진 폐기*로만 좁게 해석할 것.

| 용어 | 뜻 |
|---|---|
| `wiki-init` / `wiki-sync` / `wiki-lint` (Python CLI) | ⛔ 폐기. 단 plugin skill의 `documentation:llm-wiki` (`init` / `sync` / `lint` 등 8 명령)는 별개로 살아있음 — 본 프로젝트는 후자를 사용. |
| QMD | ⛔ 미구현 폐기. graphify MCP가 검색 측면을 일부 대체. wiki는 INDEX.md 라우팅으로 graceful degrade. |
| `promotion_policy` / `scoring` (구 wiki 엔진) | ⛔ 폐기. 현 wiki는 frontmatter `confidence`로 단순화 + lint 플래그. |

## 자주 헷갈리는 구분

| 구분 | 정리 |
|---|---|
| Wiki vs Graphify | Wiki = *default 컨텍스트 라우팅* (사람·LLM이 답변 작성 시 우선 참조). Graphify = *보조 path 탐색* (cross-component 의존성, wiki 미컴파일 영역). 2026-05-09부터 분명한 우선순위. |
| Wiki *엔진* vs Wiki *자체* | 엔진(`src/semi_design_wiki/`)은 폐기. 위키 자체(`wiki/**.md`)는 운영. 이 둘을 섞어 "Phase 1a 전체가 죽었다"라고 읽으면 오류. |
| K1 vs K2 | K1 = *방향 판단* forward synthesis (52 source, 4 evidence 페이지). K2 = *spec 결정 backing* backward evidence binding (61 source, 4 evidence 페이지). 시간 축으로 K1 → K2. |
| Autotuning vs Open-Ideation | Autotuning은 주어진 knob 탐색 (ORFS-agent 영역). Open-Ideation은 *구조 아이디어*와 patch까지 탐색 (H1b 차별화 축). |
| Parameter knob vs Structural patch | knob = flow/config 값 변경. structural patch = RTL · constraint · architecture *자체*의 의미 있는 변경. K2 η에서 SISA array-partitioning이 첫 entry. |
| Clean sign-off vs Functional correctness | G1의 sign-off clean은 timing/DRC/LVS *관점*의 증거. functional simulation이 없으면 기능 correctness 증거는 *아니다*. |
| PPA claim vs Process claim | PPA claim = 수치 개선 주장. Process claim = trace · 재현성 · 운영 가능성에 대한 주장. 본 프로젝트의 publish 축은 Process claim이 본진. |
| Source vs Evidence | Source = 참고 자료 (raw paper). Evidence = 특정 claim을 *뒷받침하도록 연결된* source · report · run artifact. K1/K2 evidence 페이지가 후자의 컴파일 결과. |
| Layer routing vs Agent recall API | wiki-first 정책은 *사람/LLM의 답변 컨텍스트 라우팅*에만 적용. agent 시스템 내부 API인 `L2.memory.recall` / `L2.skill_library.query` / `L2.lint.check`는 graphify 백엔드로 spec-freeze (overview spec §3.2 + L2-substrate-design §5.1). 이 두 layer는 독립. |
