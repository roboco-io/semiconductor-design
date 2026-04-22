---
type: "query"
date: "2026-04-22T11:14:40.938273+00:00"
question: "L2 Interface Contract v2 hyperedge와 Phase 1a 계약은 어디에서 binding되는가?"
contributor: "graphify"
source_nodes: ["L2.skill_library.query", "L2.memory.recall", "L2.lint.check", "graphify_3tier", "graphify_mcp"]
---

# Q: L2 Interface Contract v2 hyperedge와 Phase 1a 계약은 어디에서 binding되는가?

## Answer

v2 5 nodes (skill_library.query, memory.recall, lint.check, graphify 3-tier, graphify MCP server)는 Phase 1a code(lint_wiki, sync_index, init_wiki, frontmatter, schemas)와 3 hops 내 edge 0건. v2의 전체 이웃은 {L2 Substrate, graphify/*, scripts/graph_integrity_check.py(S3 신규)}뿐. Binding은 한 곳뿐: L2.lint.check() --implements--> scripts/graph_integrity_check.py (아직 존재하지 않는 파일, S3 Task 9-10에서 TDD로 생성 예정). 결론: graphify 전환은 이미 계약 수준에서 완전 disjoint. S3 code swap은 orphaned legacy 제거에 불과, v2 contract 무효화 리스크 없음.

## Source Nodes

- L2.skill_library.query
- L2.memory.recall
- L2.lint.check
- graphify_3tier
- graphify_mcp