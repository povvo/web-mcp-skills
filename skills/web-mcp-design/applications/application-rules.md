# Application Rules

Output path: `applications/application-rules.md`

## Composition Rules

| Use case | Required foundations | Required components | Required patterns | Constraint |
| --- | --- | --- | --- | --- |
| Naming/identity lockup | typography, palette, visual DNA, brand expression | none required | Micro / Monument, Aligned Rupture | render “Web MCP” in JetBrains Mono; original geometry only; no source mark or custom glyph imitation |
| Brand hero/landing section | typography, spatial grammar, imagery, surface | content block, actions when real | Quiet / Signal, Measured Edge | one cropped anchor, one factual copy block, one bounded signal region; product context contributes content only when supplied |
| Editorial/documentation page | typography, voice, palette, spatial grammar | navigation, content display | Polarity Field, Measured Edge | readable line length and quiet density take priority; halftone never under body copy |
| Application shell | interaction, accessibility, palette, typography | navigation, actions, feedback | Settled Consequence, Bounded Inversion | host-platform semantics remain visible; no inferred browser/protocol UI from the package name |
| Data/inspection view | spatial grammar, typography, iconography | table/list, inspector, forms, status | Quiet / Signal, Inspectable Path | use real labels/values/provenance; no fake coordinates or metrics; maximum one selected inverse region |
| Operation/progress view | interaction, motion, voice | sequence/progress, feedback, actions | Inspectable Path, State Node, Settled Consequence | steps and values must be real; preserve partial results and recovery; reduced motion shows final path immediately |
| Campaign/social graphic | typography, palette, imagery, surface | none required | Micro / Monument, Polarity Field | live/selectable text where medium permits; one rupture; adapt crop per aspect ratio rather than stretching |
| Generated image/asset | imagery, palette, surface, brand expression | none required | Signal Preview, Aligned Rupture | original subject/geometry; prompt negatives enforced; embedded essential text prohibited |
| Presentation/print cover | typography, spatial grammar, surface | content block | Micro / Monument, Measured Edge | account for trim/safe area, paper/ink contrast, and actual output resolution; grain/halftone generated for target size |

## Adaptation Rules

- Platform adaptation: preserve semantic intent and perceptual invariants while using native navigation, forms, focus, targets, safe areas, scaling, feedback, and back/escape behavior. Web is not the universal interaction template.
- Domain adaptation: begin with a verified product schema, nouns, states, actions, consequence, and content. The words “Web MCP” affect naming only and cannot generate modules or metaphors.
- Density adaptation: default `quiet`; switch one bounded region to `signal` for active evidence, selection, processing, or a campaign focal point. Dense task views may reduce whitespace but not type/target/focus requirements.
- Theme adaptation: light/dark resolve neutral polarity, high contrast resolves system colours and removes grain, and reduced motion replaces transitions with stable state geometry.
- Channel adaptation: keep at least two recognition cues and one quiet region. Print uses physical dot/stroke tests; social uses safe zones; web uses live text/semantics; video includes reduced/static endpoint; native uses platform behavior.

## Reconstruction Sequence

Choose the factual use case and content first. Select one dominant composition and density. Apply semantic tokens and real components. Add no more than one expressive rupture and one signal region. Validate reading order, contrast, modes, crop, font rendering, and source independence. Remove every node, measurement, or texture element that does not communicate content, state, or composition.

## Global Constraint

The design language is not a license to make every artifact look like a technical diagram. Brand recognition should survive in a quiet page with only JetBrains Mono, neutral polarity, disciplined alignment, extreme scale, and one measured edge.
