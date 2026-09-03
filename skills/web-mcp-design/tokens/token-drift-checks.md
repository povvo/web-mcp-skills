# Token Drift Checks

Output path: `tokens/token-drift-checks.md`

## Drift Detection Rules

| Drift type | Detection method | Repair action |
| --- | --- | --- |
| Hard-coded raw value | scan CSS/JS/templates for hex, rgb, pixel spacing, duration, radius, font-family, and shadow values outside the token source; allow documented data-derived values | replace with the nearest semantic/component token or document a genuinely dynamic value; never create a token solely to silence the scan |
| Broken alias | resolve the token graph in every mode; fail on missing target, cycle, type mismatch, or chain deeper than two references from primitive | repair the alias target, flatten the unnecessary hop, and rerun every mode build |
| Mode divergence | snapshot token keys and component states across light, dark, high contrast, reduced motion, quiet, and signal; compare missing roles and state semantics | add the missing mode branch or remove the unsupported role; do not fall back silently |
| Component override sprawl | count local custom properties and component-level token overrides; flag repeated raw values or more than two undocumented overrides per component | promote a repeated stable purpose to component semantics or remove one-off decoration |
| Contrast failure | test text, icon, focus, boundary, and state pairs in every mode; include actual font weight/size and forced-colours inspection | adjust the semantic pair, strengthen geometry, or remove recessive styling; retain redundant labels/patterns |
| Typography drift | scan for non-JetBrains families, synthetic bold/italic, body below 16px, labels below 11px, and display rules applied to wrapping content | restore type role tokens and verify actual rendering across browsers/platforms |
| Geometry drift | detect radius above 8px, unsnapped one-pixel paths, random node sizes, and diagonals outside the 45-degree grammar | bind to shape/stroke tokens and optically correct the vector at each size |
| Surface drift | scan for box-shadow, backdrop-filter, gradients, unsupported hue, opacity-based semantic surfaces, and texture under text | replace with tonal surface, one-pixel frame, bounded inversion, or remove the effect |
| Density drift | visual regression or DOM metrics show multiple signal fields, lost quiet region, or metadata on every object | restore one bounded signal region and remove decorative labels/texture |
| Source leakage | hash/name scan finds reference image, copied wordmark, emblem, copy, or extracted source pixels in design-use/assets | remove the material, rebuild with original geometry/procedural texture, and regenerate proofs |

## Hygiene Rules

- Keep primitive, global, alias, semantic, component, mode, platform, transform, and drift documents separate in source and merge only in generated artifacts.
- Reject orphan primitives, unused semantic tokens, undocumented overrides, duplicate output names, and tokens referenced by no component/pattern/application.
- Run raw-value scanning on code, generated CSS, templates, SVG, design exports, and prompt packs before handoff.
- Store an allowlist beside the scanner with path, value, purpose, reviewer, and expiry; an unscoped ignore comment is not a Repair.
- Compare generated artifacts deterministically so changes reveal actual token drift rather than file-order noise.

## Review Cadence

Run structural checks on every build, mode/contrast checks on every visual change, and cross-platform rendering checks before a platform release. A visual regression is evidence, not an automatic failure: review intended crop, font rendering, and dynamic content before updating a baseline.

## Anti-Patterns

- A single giant token file, global scanner ignores, tokens invented for every pixel, snapshots updated without inspection, “close enough” mode fallback, lint passing while design-use files disagree, and repairs that patch a component instead of correcting the semantic source of truth.
