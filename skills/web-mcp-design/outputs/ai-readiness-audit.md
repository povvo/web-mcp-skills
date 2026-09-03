# AI-Readiness Audit

Output path: `outputs/ai-readiness-audit.md`

## AI-Readiness Controls

| Risk | Prevention rule | Repair rule |
| --- | --- | --- |
| Hallucinated component | generation selects from documented actions, fields, navigation, sequence, feedback, content/data, and product-neutral domain shells; unknown needs are marked as gaps | decompose into existing components or add a reviewed contract before implementation |
| Hallucinated product model | package name contributes naming only; require supplied nouns, schema, states, data, and actions before domain UI | remove inferred browser/protocol/server/AI concepts and replace with verified content or a neutral placeholder marked unknown |
| Raw values | reject hard-coded colour, spacing, radius, shadow, font, duration, and state styling when semantic/component tokens exist | map the purpose to a semantic token; if no purpose exists, review the design need rather than minting a silencing token |
| Unsupported states | component state must appear in its contract and owning operation; unknown, pending, partial, failed, and completed cannot be conflated | use the nearest documented state only if semantically exact; otherwise add a gap and define behavior/recovery first |
| Broken token mapping | validate typed reference graph, mode branches, platform output, and component-to-semantic edges | repair the earliest incorrect source token; regenerate artifacts and rerun drift/contrast checks |
| Inaccessible generated UI | require native semantics, visible labels/focus, keyboard model, contrast thresholds, target sizes, reflow, reduced motion, live-status policy, and media alternatives | fix structure/semantics first, then tokens and visuals; test with keyboard and representative assistive modes |
| Prompt drift | every prompt includes positive facts, negative constraints, exact live-text policy, original-asset rule, density limit, and failure checks | reject output, identify violated invariant, tighten the relevant fact/negative, and regenerate without adding source assets |
| Source leakage | no reference image, name, mark, copy, file path, source ID, or composition appears in design-use generation context | remove leaked material and regenerate from `DESIGN.md` plus source-free support files |
| Typography substitution | JetBrains Mono is explicit and fallback is treated as loading/emergency behavior | install/load the intended weights, fix CSS/native mapping, and visually verify metrics before approval |
| Decorative pseudo-evidence | measurements, IDs, counts, coordinates, and path topology require real content or explicit nonsemantic specimen status | remove fake data; use unlabeled composition geometry only where it remains clearly decorative and accessibility-hidden |

## Machine-Readable Context

- Component contracts live in `components/*.md` and include anatomy, purpose, variants, States, behavior, copy, tokens, accessibility, API, examples, and relationships.
- Pattern schemas live in `patterns/pattern-language.md` with exact taxonomy, parents, relationships, conflicts, and forbidden synonyms.
- Token grammar flows primitive → global → alias → semantic → component, with mode/platform transforms and drift checks in separate files.
- Repository instructions: read `DESIGN.md` first; use source-free support files; never open/copy source assets for ordinary application; preserve user scope and actual product truth.
- Generated-output review checks text accuracy, object binding, state receipts, component validity, token use, layout order, one-rupture/one-signal limits, JetBrains Mono rendering, contrast, focus, reduced motion, crop, media alternatives, and source independence.

## Generation Gate

Before generating, identify deliverable, real content, platform, mode, density, semantic states, and consequence. During generation, bind documented components and tokens. After generation, inspect rendered output at representative widths and modes. Structural validation alone cannot approve typography, hierarchy, crop, halftone quality, interaction, or accessibility.

## Hallucination Stop Conditions

Stop and request missing product input when choosing an object taxonomy, workflow, actor, live data, metric, external state, or consequential action would materially change the result. Do not stop for purely visual choices already covered by this language.
