# 프로젝트 용어집

이 문서는 `semiconductor-design` 연구 프로그램에서 반복적으로 쓰는 약어와 개념을
짧게 정리한 참조 문서다. 자세한 설계 근거는 각 spec과 wiki 문서를 따른다.

## 프로젝트 고유 개념

| 용어 | 뜻 |
|---|---|
| Report-Grounded Vibe-Coded AutoResearch | 이 저장소의 통합 연구 프로그램 이름. EDA 리포트와 실행 trace를 근거로 LLM 에이전트가 작은 실험을 반복하고, 운영자가 감독하는 연구 방식이다. |
| L1 Process | 재현 가능한 실행 환경 계층. SHA-pinned 도구 체인, 로컬 CLI, AWS Fargate Spot, Step Functions, artifact lake를 포함한다. |
| L2 Substrate | 지식·메모리 계층. `.rpt`, `.def`, STA/DRC 결과를 typed-frontmatter 문서와 skill library로 축적한다. |
| L3 Content | 실제 연구 대상 계층. Gemmini, MLPerf Tiny, Open-Ideation DSE 같은 설계·실험 콘텐츠를 다룬다. |
| Open-Ideation DSE | 고정된 parameter sweep만 하지 않고, 에이전트가 구조 아이디어를 제안한 뒤 patch와 sign-off 결과로 채택 여부를 판단하는 DSE 방식이다. |
| Report-grounded agent operation | 에이전트가 추측 대신 synthesis, PnR, STA, DRC 리포트를 읽고 다음 조치를 결정하는 운영 방식이다. |
| Reversible patch | baseline을 직접 덮어쓰지 않고 언제든 되돌릴 수 있는 작은 변경 단위. `program.md`의 핵심 규칙이다. |
| Skill library | sign-off 결과와 함께 검증된 patch, transform, 운영 지식을 재사용 가능한 skill로 저장하는 라이브러리다. |
| Negative result | 실패한 실험 결과. 이 프로젝트에서는 삭제 대상이 아니라 future search와 duplicate detection에 쓰는 자산이다. |
| Reasoning trace | 에이전트가 어떤 입력, 도구 호출, 판단 근거를 거쳐 후보를 채택하거나 기각했는지 남긴 실행 기록이다. |
| Process-as-contribution | 최종 PPA 수치뿐 아니라 재현 가능한 실행 번들, trace, 운영 절차 자체를 연구 기여물로 보는 관점이다. |
| Operator | 칩 설계 전문가가 아니라 에이전트와 EDA 도구 출력을 감독·디버깅하는 사람. Phase 0 학습의 목표 역할이다. |

## 연구 단계와 판단 기준

| 용어 | 뜻 |
|---|---|
| K1 | 초기 지식 수집과 방향 판단 단계. 현재 K1 리포트는 52개 source를 기반으로 한다. |
| H1 | Primary hypothesis. report memory와 reversible-patch skill library가 finding reuse, structural patch, cold-start failure 측면에서 개선을 만든다는 가설이다. |
| H1a Finding reuse rate | 이전 finding이 이후 실험에서 재사용되거나 duplicate로 매칭되는 비율이다. |
| H1b Non-knob structural patch | 단순 knob 조정이 아닌 구조적 RTL/constraint 변경이 sign-off를 통과한 건수다. |
| H1c Cold-start failure rate | 새 디자인에 처음 투입한 초기 run 중 sign-off fail이 나는 비율이다. 낮을수록 좋다. |
| H2 | 여러 디자인을 순차적으로 다룰 때 축적 memory가 실패율을 낮추는지 보는 복리 효과 가설이다. |
| H3 | 비전문가 평가자가 reasoning trace를 읽고 후보 채택·기각 이유를 복원할 수 있는지 보는 process 가설이다. |
| Canonical decision table | H1/H3 결과로 publish, reframed-publish, kill을 결정하는 overview spec의 유일한 판정표다. |
| Kill gate | 다음 단계로 넘어가기 전에 반드시 통과해야 하는 검증 조건. L1에서는 KG-A~KG-F 형태로 정의된다. |
| Pre-registration | 실험 시작 전에 sample size, threshold, seed, exclusion list를 고정하는 절차다. |
| Blinded audit | 독립 평가자가 후보나 결과의 출처를 모른 채 자동 판정의 타당성을 검수하는 절차다. |
| Evaluator separation | trace 생성 LLM과 평가 LLM의 family를 분리하는 규칙. H3 evidence의 오염을 막기 위한 장치다. |

## 반도체·EDA 기본 용어

| 용어 | 뜻 |
|---|---|
| EDA | Electronic Design Automation. RTL부터 물리 구현, 검증까지 칩 설계 도구 체인을 뜻한다. |
| ASIC | Application-Specific Integrated Circuit. 특정 목적에 맞게 제작되는 주문형 반도체다. |
| RTL | Register Transfer Level. 레지스터 사이 데이터 이동과 조합 로직을 기술하는 하드웨어 설계 추상화다. |
| HDL | Hardware Description Language. Verilog, SystemVerilog, VHDL 같은 하드웨어 기술 언어다. |
| Verilog | RTL을 작성하는 대표 HDL. 이 프로젝트에서는 에이전트 출력 검수와 합성 입력으로 중요하다. |
| Chisel | Scala 기반 하드웨어 생성 언어. Gemmini/Chipyard 설정을 이해할 때 필요하다. |
| Synthesis | RTL을 gate-level netlist로 바꾸는 단계. Yosys가 대표 오픈소스 도구다. |
| PnR | Place and Route. 셀 배치와 배선을 수행하는 물리 구현 단계다. |
| STA | Static Timing Analysis. 클럭 제약 아래에서 setup/hold timing violation을 분석하는 절차다. |
| Sign-off | tapeout 또는 최종 승인 전 timing, DRC, LVS 등 필수 검증을 통과했는지 확인하는 단계다. |
| DRC | Design Rule Check. 공정 제조 규칙을 위반한 물리 layout이 있는지 검사한다. |
| LVS | Layout Versus Schematic. layout이 의도한 회로/netlist와 전기적으로 일치하는지 검사한다. |
| PDK | Process Design Kit. 특정 공정에서 설계할 때 필요한 cell, rule, model, tech file 묶음이다. |
| Open PDK | 공개적으로 사용할 수 있는 PDK. 이 프로젝트에서는 sky130A, gf180mcuD가 주요 후보로 언급된다. |
| sky130A | SkyWater 130nm 오픈 PDK. 오픈소스 ASIC 플로우에서 자주 쓰는 공정이다. |
| Liberty `.lib` | 표준 셀의 timing, power, 기능 정보를 담는 파일 포맷이다. |
| LEF | Library Exchange Format. 셀과 macro의 물리적 크기, pin, routing obstruction 정보를 담는다. |
| DEF | Design Exchange Format. 배치·배선 이후 디자인의 물리 구현 결과를 담는다. |
| SDC | Synopsys Design Constraints. 클럭, I/O delay, timing exception 같은 제약을 도구에 전달한다. |
| GDSII | 제조에 넘기는 최종 layout 데이터 포맷이다. |
| QoR | Quality of Results. area, timing, power, runtime 등 도구 결과 품질을 묶어 부르는 말이다. |
| PPA | Power, Performance, Area. 반도체 설계 품질을 보는 대표 3대 지표다. |
| WNS | Worst Negative Slack. 가장 나쁜 timing slack 값이다. 0 이상이면 해당 관점에서 timing clean이다. |
| TNS | Total Negative Slack. 모든 negative slack의 합이다. timing violation의 총량을 나타낸다. |
| Critical path | timing을 제한하는 가장 느린 경로다. STA 리포트에서 우선적으로 봐야 한다. |
| Slack | 요구 도착 시간과 실제 도착 시간의 차이. 음수면 timing violation이다. |

## 도구와 벤치마크

| 용어 | 뜻 |
|---|---|
| OpenROAD | 오픈소스 RTL-to-GDS 물리 구현 도구 체인이다. |
| ORFS | OpenROAD-flow-scripts. OpenROAD 기반 reference flow와 benchmark 실행 스크립트 묶음이다. |
| ORFS-agent | ORFS parameter tuning을 자동화한 2025년 agentic EDA baseline. 이 프로젝트에서는 novelty 비교 기준으로 다룬다. |
| OpenLane2 | 과거 오픈 ASIC flow. K1 이후 spec에서는 LibreLane으로 이동한 것으로 정리한다. |
| LibreLane | OpenLane 계열의 FOSSi Foundation 관리 flow. L1 도구 체인의 주요 후보로 쓰인다. |
| Yosys | 오픈소스 RTL synthesis 도구다. |
| Verilator | Verilog/SystemVerilog simulation과 lint에 쓰이는 오픈소스 도구다. |
| cocotb | Python으로 HDL testbench를 작성하는 프레임워크다. |
| Chipyard | RISC-V SoC와 accelerator를 생성·통합하는 연구 플랫폼이다. |
| Gemmini | Chipyard 기반 systolic-array DNN accelerator generator다. L3 Content의 핵심 대상이다. |
| MLPerf Tiny | 초저전력/임베디드 ML benchmark suite. 이 프로젝트에서는 KWS와 streaming wakeword가 중요하다. |
| KWS | Keyword Spotting. 작은 음성 명령이나 wakeword를 감지하는 ML task다. |
| gcd/ibex/aes | L1/L3 평가에 쓰는 대표 디자인 대상. gcd는 smoke test, ibex/aes는 더 복잡한 RTL target이다. |

## 실행 인프라와 저장소 용어

| 용어 | 뜻 |
|---|---|
| `semi-run` | L1 Process의 Python CLI 이름. spec 제출, 상태 확인, artifact 수집을 담당한다. |
| `wiki-init` | wiki 디렉터리 구조를 초기화하는 CLI다. |
| `wiki-sync` | wiki index를 재생성하는 CLI다. |
| `wiki-lint` | wiki frontmatter, 링크, 규칙 위반을 검사하는 CLI다. |
| Frontmatter | Markdown 상단의 YAML metadata. wiki 문서의 type, status, confidence, evidence 등을 구조화한다. |
| QMD | wiki와 원문, 실험 로그 검색을 빠르게 하기 위한 검색 계층이다. 주 기억장치가 아니라 보조 index로 취급한다. |
| Artifact bundle | 한 run의 spec, RTL, report, metrics, provenance, log를 함께 저장한 결과 묶음이다. |
| Provenance | artifact가 어떤 source, SHA, container digest, operator/agent를 통해 만들어졌는지 추적하는 기록이다. |
| Lockfile | 도구, container, PDK, source mirror의 SHA/digest를 고정하는 파일이다. 재현성의 기준점이다. |
| SHA pinning | upstream branch 이름 대신 특정 commit SHA나 digest를 고정해 외부 변경 drift를 막는 방식이다. |
| AWS Fargate Spot | 저렴하지만 회수될 수 있는 serverless container 실행 환경. EDA burst workload에 사용한다. |
| Step Functions Map | 여러 candidate run을 병렬 실행하기 위한 AWS workflow construct다. |
| S3 artifact lake | run artifact를 저장하는 S3 기반 저장소다. |
| DynamoDB | run, candidate, budget, trace metadata를 저장하는 key-value/database 계층이다. |
| Object Lock | S3 객체를 일정 기간 수정·삭제하지 못하게 하는 기능. 성공 artifact의 불변성을 보장한다. |
| DLQ | Dead Letter Queue. 처리 실패한 메시지나 작업을 격리해 나중에 조사할 수 있게 하는 큐다. |

## 자주 헷갈리는 구분

| 구분 | 정리 |
|---|---|
| Wiki vs QMD | Wiki는 정제된 지식의 원본이고, QMD는 검색 가속 계층이다. 새 사실은 QMD가 아니라 wiki에 반영한다. |
| Autotuning vs Open-Ideation | Autotuning은 주어진 knob 탐색이고, Open-Ideation은 구조적 아이디어와 patch까지 탐색한다. |
| Parameter knob vs structural patch | knob은 flow/config 값 변경이다. structural patch는 RTL, constraint, architecture 자체의 의미 있는 변경이다. |
| Clean sign-off vs functional correctness | G1의 sign-off clean은 timing/DRC/LVS 관점의 증거일 수 있지만 functional simulation이 없으면 기능 correctness 증거는 아니다. |
| PPA claim vs process claim | PPA claim은 수치 개선 주장이고, process claim은 trace, 재현성, 운영 가능성에 대한 주장이다. |
| Source vs evidence | Source는 참고 자료이고, evidence는 특정 claim을 뒷받침하도록 연결된 source, report, run artifact다. |
