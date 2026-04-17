---
name: semi-design-wiki
description: Semiconductor design domain wiki management - init / sync / lint / ingest / query. Triggers when user mentions wiki, page ingestion, domain knowledge for chip design. Full content of pages and ingest workflow is defined in references/ and filled in Phase 1b.
---

# semi-design-wiki

Phase 1a scaffolds the scripts (`wiki-init`, `wiki-sync`, `wiki-lint`).
Phase 1b will populate `references/page-templates.md`, `references/ingest-workflow.md`, `references/semiconductor-ontology.md`.

## Commands

- `wiki-init --root wiki` — create directory structure
- `wiki-sync --root wiki` — regenerate `wiki/index.md`
- `wiki-lint --root wiki` — health check (exit 1 on issues)

## Ingest / Query (Phase 1b)

Not yet implemented. See Phase 1b plan.
