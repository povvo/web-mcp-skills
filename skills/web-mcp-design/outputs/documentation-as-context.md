# Documentation As Context

Output path: `outputs/documentation-as-context.md`

## Documentation Contract

| Artifact | Human guidance | Machine guidance / readable context | Rationale |
| --- | --- | --- | --- |
| `DESIGN.md` | start here for the complete source-free language, recipes, states, drift boundaries, and reconstruction checks | canonical conceptual contract; headings and token paths are stable retrieval anchors | prevents agents/designers from reopening references or reducing the language to mood adjectives |
| `SKILL.md` | routes use cases to the minimum relevant support files | concise invocation scope plus conditional file routing | keeps discovery cheap and avoids loading the entire package unnecessarily |
| `foundations/*.md` | explains colour, type, space, motion, surface, interaction, imagery, voice, and expression decisions | operational invariants, values, and anti-patterns by domain | separates stable design forces from component implementations |
| `tokens/*.md` | defines typed raw-to-platform token architecture | token names, references, modes, transform order, and drift checks | gives code generation a traceable value graph and blocks hard-coded drift |
| `components/*.md` | documents purpose, anatomy, variants, states, copy, access, API, examples, and relationships | reusable contracts and semantic-token bindings | keeps generated UI behaviorally complete rather than visually approximate |
| `patterns/*.md` | helps choose patterns by intent and relationship | taxonomy, parent/related/conflict/deprecation mappings | stops decorative motifs from becoming unsupported components |
| `accessibility/*.md` | supplies thresholds and test obligations | contrast, focus, target, mode, keyboard, and alternative constraints | makes accessibility part of construction instead of final polish |
| `applications/application-rules.md` | maps real deliverables to compositions and constraints | use-case selection and reconstruction sequence | adapts the language without inferring product semantics from its name |
| `outputs/prompt-pack.md` | provides source-free generation prompts and rejection criteria | positive facts, negatives, variable slots, and review gates | generates original assets without source leakage or visual cliché |
| `proofs/*.md` | records evidence, coverage, validation, caveats, and readiness | source IDs, labels, commands, outcomes, and unresolved gaps | keeps provenance out of design-use guidance while preserving accountability |
| `handoff/*.md` | communicates rights, custody, package status, and repair path | readiness state, missing inputs, and release boundary | prevents “files exist” from being confused with rights-cleared production readiness |

## Required Documentation Sections

- Component and pattern docs include when to use/not use, anatomy, variants, states, accessibility, token use, code/API contract, examples, anti-patterns, and relationships.
- Source-free design docs state operational truth. Proof/handoff docs state evidence, validation, rights, gaps, and historical rationale.
- Machine guidance uses exact token/pattern names and distinguishable state vocabulary. Do not depend on prose similarity or hidden context.
- Last reviewed: 2026-08-29. Package owner is the repository maintainer unless later metadata names another owner. Review dates are status signals, not expiry guarantees.

## Retrieval Order

Read `DESIGN.md`, then select one application use case. Load the relevant foundation, component, pattern, and accessibility files. Consult tokens for implementation values. Read proofs/handoff only for evidence, rights, or readiness questions. Never copy proof rationale into production prompts or UI copy.

## Drift Signals

Documentation is stale when token paths no longer resolve, component states differ from code, a platform mapping is absent, the package name begins driving product metaphors, accessibility thresholds conflict, prompt outputs violate negatives, or the last-reviewed context predates a material implementation change.
