# Proof Report

Output path: `proofs/proof-report.md`

## Proof Summary

| Check | Result | Repair |
| --- | --- | --- |
| Toolkit reference catalog | PASS — `validate_reference_catalog.py` reported 26 references, 50 templates, and 50 fixed outputs | rerun after any toolkit/catalog change |
| Toolkit taxonomy coverage | PASS — `taxonomy_coverage_check.py` reported 23 terms and 50 outputs | repair missing ontology-to-output mapping in the toolkit, not the generated package |
| Toolkit doctor and skill validation | PASS — pipeline reported 50 fixed steps; parent skill validation passed | rerun with the same interpreter before a future extraction |
| Source evidence binding | PASS — R01-R04 have filenames, dimensions, SHA-256 identities, custody, rights, modes, signals, and exclusions; B01 records the written constraint | re-hash and re-inspect if source files change |
| Seven-domain extraction | PASS by pipeline contracts — visual DNA precedes palette, typography, space, motion, surface, interaction, and principles | repair the owning foundation and dependent tokens/patterns if a domain rule changes |
| Reconstructive DESIGN.md | PASS by step contract — 4,280 words before final minor edits, exact values, recipes, states, drift boundaries, checks | rerun output validator after any manual edit |
| Source-free design-use boundary | PASS — output-package and evidence validators passed after final semantic cleanup | rerun both validators after any design-use or evidence change |
| Generated skill router | PASS — root `SKILL.md` routes to `DESIGN.md`; system UTF-8 quick validation and Pastiche skill validation passed | rerun both validators after router or metadata changes |
| Rights and production asset safety | PASS for package content — no source image copied; no source mark/wordmark prescribed | obtain separate rights review before any later use of reference pixels or proprietary assets |

## Mechanical Proofing

- Contrast: numeric thresholds, semantic pairs, high-contrast mapping, CVD-safe redundant encoding, and repair order are specified. Runtime/rendered contrast testing has not yet been performed because no implementation artifact was requested.
- Token drift: nine token layers include typed values, semantic references, modes, platform transforms, raw-value scanning, geometry/surface/source-leak checks, and repair rules. No generated code artifact exists to scan.
- Fixed package completeness: all 50 pipeline steps passed individual contracts, the temporary state was removed, 51 fixed files remain, and package/evidence validators passed.
- Generated skill routing: `SKILL.md` reads `DESIGN.md` first, distinguishes design-use from evidence files, encodes the name-only boundary, and aligns with the completed `agents/openai.yaml` metadata.
- Prompt failure checks: the prompt pack rejects copied marks/compositions, product clichés inferred from the name, hue, multiple focal/signal regions, malformed text, fake data, source dependencies, inaccessible crop, and texture failure.

## Residual Risk

The static reference corpus does not directly prove UI behavior, motion timing, responsive rendering, accessibility, native-platform parity, or font licensing/delivery. Those rules are operational reconstructions and must be validated in the first real artifact. Visual review remains necessary even when every structural validator passes.
