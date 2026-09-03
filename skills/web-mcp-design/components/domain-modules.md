# Domain Modules

Output path: `components/domain-modules.md`

## Domain Modules Covered

- No product-domain module is prescribed by this language. The name “Web MCP” identifies the package but does not justify protocol, browser, network, developer-tool, e-commerce, education, finance, cooking, or service-journey components.
- The reusable modules below are perceptual shells for any truthful domain content: object index, operation trace, evidence inspector, and result record.
- Domain vocabulary and constraints must come from the actual product brief at application time.


## User Or Maker Problem

- Extend the visual language into a real product without smuggling assumptions from the package name into information architecture. A Domain Module composes existing components only after product nouns, states, data, and actions are known.

## Anatomy And Boundaries

| Component or module | Anatomy | Boundary | Related component |
| --- | --- | --- | --- |
| Object index | heading, filters, labelled records, state/count, selection | owns a collection of real domain objects; does not invent object taxonomy | list/table, forms |
| Operation trace | real steps, current state, retained result, recovery | owns one consequential process; does not imply a specific protocol | sequence, feedback |
| Evidence inspector | selected object title, factual metadata, primary evidence, raw/copy affordance | owns inspectable detail; does not fabricate fields | data display, media |
| Result record | outcome, timestamp/identifier, scope, next action | owns a durable receipt; does not claim success without evidence | status, content block |

## Variants

| Variant | Purpose | Visual difference | Behavioral difference |
| --- | --- | --- | --- |
| Quiet | reading, overview, or low activity | large negative space and sparse metadata | mostly static |
| Signal | selected evidence or active operation | one bounded inverse/halftone region | state may trace once then settle |
| Dense | comparison or inspection | aligned grid, compact labels, no decorative crop | keyboard scanning, sort/filter where real |
| Campaign | naming/identity application | “Web MCP” as monumental JetBrains Mono anchor | no product behavior implied |

## States

| State | Visual behavior | Interaction behavior | Content behavior |
| --- | --- | --- | --- |
| Default | quiet field and factual labels | composed component behavior | real domain nouns |
| Hover/focus | only actionable children respond visibly | preserve platform keyboard model | labels remain stable |
| Active/pressed | selected bounded region may invert | selection/action remain distinct | do not rename state early |
| Disabled | only child actions become unavailable | explain real Constraint | object evidence remains readable |
| Loading | current module region is labelled and stable | cancellation/retry follow operation truth | no inferred percent or field |
| Error | failed region gets persistent stop geometry | preserve prior evidence and recovery | state scope and unknowns explicitly |

## Content And Naming Rules

- Use nouns from the product's verified domain model, not decorative technical vocabulary. “Web MCP” may appear as the package/product name only.
- Do not generate IDs, coordinates, metrics, status, actors, claims, or operational detail to fill the composition. Unknown content remains visibly unknown or absent.

## Token Dependencies

| Part | Required token | Override boundary |
| --- | --- | --- |
| Shell | semantic surfaces and spacing | no domain colour palette unless separately specified |
| State | semantic state family | map only real domain states |
| Data | semantic text/grid tokens | types, units, and provenance remain product-owned |
| Signal region | `semantic.surface.signal` | maximum one per module view |

## Accessibility And Localization

- Each composed component retains its semantic, keyboard, focus, target, contrast, motion, and localization contract. Composition must not create nested interactive rows, duplicate live announcements, or visual/DOM order divergence.
- Dense variants still support 200% zoom, reflow, actual-language expansion, text alternatives, and nonvisual state labels.

## Code And API Contract

- A module schema declares `domainName`, typed entities/fields, supported actions, known states, evidence provenance, and recovery behavior before visual rendering.
- Reject unsupported fields/states instead of filling them with plausible examples. Raw style overrides do not belong in the domain schema.

## Examples And Anti-Patterns

- Do: apply the object index to a verified catalogue, or use “WEB MCP” only as a cropped naming anchor on a brand surface.
- Avoid: inferring browser tabs, network maps, protocol nodes, server cards, AI agents, transactions, courses, recipes, or any other product model from the package name; decorative pseudo-data; and unsupported success records.

## Related Patterns

- `patterns/domain-platform-patterns.md`, `patterns/pattern-language.md`, `components/content-data-display.md`, and `outputs/ai-readiness-audit.md`.
