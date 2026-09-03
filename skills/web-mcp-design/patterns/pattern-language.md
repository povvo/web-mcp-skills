# Pattern Language

Output path: `patterns/pattern-language.md`

## Taxonomy

| Term | Definition | Parent | Related terms | Forbidden synonyms |
| --- | --- | --- | --- | --- |
| Polarity Field | a major neutral field and its bounded inverse used for hierarchy or state | perceptual | Quiet / Signal, Bounded Inversion | dark mode, colour block |
| Quiet / Signal | density alternation between breathable operational space and one concentrated evidence/media region | perceptual | Polarity Field, Signal Preview | minimalism, glitch mode |
| Inspectable Path | meaningful route connecting labelled states, objects, or decisions | perceptual/behavioral | State Node, Operation Trace | circuit, network decoration |
| State Node | circular open/filled/double/stop geometry redundantly encoding a named state | behavioral | Inspectable Path, Step Route | dot, sparkle, bullet |
| Measured Edge | real metadata aligned to a boundary, rail, grid, or object extent | perceptual/data | Evidence Inspector | techno label, coordinates aesthetic |
| Aligned Rupture | one nonessential anchor deliberately breaks an otherwise stable grid | perceptual/layout | Micro / Monument | chaos, collage, broken grid |
| Micro / Monument | radical but controlled scale interval within JetBrains Mono | perceptual/type | Aligned Rupture, Measured Edge | techno typography, word art |
| Bounded Inversion | complete foreground/background polarity swap inside one semantic region | behavioral/surface | Selected State, Polarity Field | highlight colour, negative filter |
| Signal Preview | truthful image/data/diagram inside the single dense region | functional/content | Quiet / Signal, Halftone Translation | hero card, glitch panel |
| Settled Consequence | brief causal feedback followed by durable still result | behavioral/motion | Operation Trace, Completion Record | celebration, microinteraction |
| Domain Shell | product-neutral composition that accepts verified domain schema/content | domain | Object Index, Evidence Inspector, Result Record | MCP dashboard, server card |

## Pattern Grammar

- Naming rules: use purpose or experienced behavior, not visible colour, source-specific labels, implementation class names, or package-name associations.
- Relationship rules: each functional pattern names its perceptual cues, behavioral states, required components/tokens, and platform adaptation. No pattern silently invents a component.
- Functional patterns describe what users do; behavioral patterns describe change/recovery; perceptual patterns describe recognition; domain shells accept verified product truth; platform patterns preserve native conventions.
- Anti-patterns name the tempting misuse and the operational correction. “Do not” without a replacement is insufficient when the capability is needed.
- Rationale states what relationship, hierarchy, evidence, or access need the pattern solves. Avoid mood-only justifications.
- Historical truth: the language rejects custom techno lettering, hue-led status, soft card stacks, generic network symbolism, ambient motion, and source-asset reuse because they either contradict the grammar or fabricate product meaning.

## Pattern Relationships

- Parent-child: `Quiet / Signal` contains a `Signal Preview`; `Inspectable Path` contains `State Node`; `Domain Shell` may contain an `Object Index`, `Operation Trace`, `Evidence Inspector`, or `Result Record`.
- Related: `Micro / Monument` often creates the `Aligned Rupture`; `Measured Edge` explains a `Signal Preview`; `Settled Consequence` completes an `Operation Trace`.
- Conflicting: multiple `Aligned Rupture` instances conflict; multiple active `Signal Preview` regions conflict; decorative node fields conflict with `Inspectable Path`; translucent overlays conflict with `Polarity Field`.
- Deprecated: “techno label,” “MCP card,” “rocket mark,” “glitch texture,” and “dark terminal” are not valid pattern names. Migrate them to the purpose terms above or remove them.

## Selection Rationale

Choose the smallest pattern set that makes content and state clear. A static identity frame may need `Micro / Monument` plus `Measured Edge`; a real operation may need `Inspectable Path`, `State Node`, and `Settled Consequence`. Never add a domain pattern because the package happens to be named Web MCP.

## Anti-Patterns

- Renaming decoration as a pattern; surface-name taxonomy; aliases that imply unsupported product semantics; components that combine conflicting patterns; one-off campaign tricks promoted to reusable rules; and using every signature pattern as a mandatory checklist.
