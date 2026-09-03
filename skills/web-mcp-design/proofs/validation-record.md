# Validation Record

Output path: `proofs/validation-record.md`

## Validation Commands

| Command | Result | Date | Notes |
| --- | --- | --- | --- |
| `python .agents/skills/pastiche/scripts/reference_pipeline.py doctor` | PASS — Pipeline OK: 50 fixed steps | 2026-08-29 | executed from repository root with Windows Python 3.12 |
| `python .agents/skills/pastiche/scripts/validate_reference_catalog.py` | PASS — 26 references, 50 templates, 50 fixed outputs | 2026-08-29 | validates parent Pastiche toolkit catalog |
| `python .agents/skills/pastiche/scripts/taxonomy_coverage_check.py` | PASS — 23 terms, 50 outputs | 2026-08-29 | validates parent toolkit coverage |
| `python .agents/skills/pastiche/scripts/validate_skill.py .agents/skills/pastiche` | PASS — Skill validation OK | 2026-08-29 | validates parent extraction skill before use |
| `Get-FileHash -Algorithm SHA256` on R01-R04 | PASS — four unique full SHA-256 identifiers recorded | 2026-08-29 | source files remained external to package |
| `reference_pipeline.py complete` for each authored step | PASS for every step recorded before this validation record | 2026-08-29 | checks depth, terms/headings, placeholders, and source-free category at the time of completion |
| `python .agents/skills/pastiche/scripts/validate_design_output.py .agents/skills/web-mcp-design` | PASS — `Output package OK.` | 2026-08-29 | rerun after final product-semantic cleanup; 51 fixed files present, `DESIGN.md` 4,292 words |
| `python .agents/skills/pastiche/scripts/evidence_map_check.py .agents/skills/web-mcp-design` | PASS — `Evidence files OK.` | 2026-08-29 | rerun after final source/proof/handoff edits |
| `python D:/povvo/.codex/skills/.system/skill-creator/scripts/quick_validate.py .agents/skills/web-mcp-design` | FAIL — Windows cp1252 decode error | 2026-08-29 | validator inherited legacy Windows encoding and could not read a UTF-8 punctuation byte; package content was not identified as invalid |
| `python -X utf8 D:/povvo/.codex/skills/.system/skill-creator/scripts/quick_validate.py .agents/skills/web-mcp-design` | PASS — `Skill is valid!` | 2026-08-29 | explicit UTF-8 is the permanent command form on this Windows environment |
| `python .agents/skills/pastiche/scripts/validate_skill.py .agents/skills/web-mcp-design` | PASS — `Skill validation OK.` | 2026-08-29 | run after correcting the `Use when` description and removing the temporary pipeline-state directory |

## Interpretation

A PASS proves the structural contract named in the row, not rendered visual quality, typography, usability, browser behavior, accessibility, or production delivery. The initial system-validator failure was an environment decoding issue and is preserved above; the explicit UTF-8 rerun is the observed passing result.
