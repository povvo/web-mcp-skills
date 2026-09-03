# Evidence Map

Output path: `proofs/evidence-map.md`

## Evidence Map

| Source ID | Evidence label | Observed signal | Extracted rule | Output file |
| --- | --- | --- | --- | --- |
| R01, R03 | REPEATED | orthogonal and 45-degree segments, rounded inside turns, modular line construction | Geometry uses right angles and 45-degree cuts; curves only resolve a turn or terminal. | `foundations/visual-dna.md`, `foundations/iconography-system.md` |
| R01 | DIRECT | hairline contours punctuated by circular nodes | Use the inspectable-path motif for diagrams, progress, focus, and construction reveals; nodes mark decisions or state, never random stars. | `foundations/visual-dna.md`, `components/sequence-progress.md` |
| R02, R04 | REPEATED | near-binary black/white fields with controlled dim grey | Use a neutral-only base system. Contrast creates hierarchy; grey lowers priority, and white is not decorative accent colour. | `foundations/palette-architecture.md`, `tokens/primitive-tokens.md` |
| R02 | DIRECT | coarse halftone imagery, inversion, sparse pixel residue | Halftone is a bounded signal surface for media or transition states, with one dot family and deterministic density. | `foundations/imagery-art-direction.md`, `foundations/surface-language.md` |
| R02, R03, R04 | REPEATED | asymmetry, clipped overscale forms, large empty regions, edge metadata | Build on a column grid but allow one deliberate overflow anchor; preserve substantial negative space around it. | `foundations/spatial-grammar.md`, `applications/application-rules.md` |
| R03, R04, B01 | REPEATED | specimen scale ladder, mono-like copy, user-required font | JetBrains Mono is the only type family. Differentiate roles with size, weight, case, spacing, orientation, and clipping. | `foundations/typographic-voice.md`, `tokens/global-tokens.md` |
| R03 | DIRECT | measurements, repeated reductions, vertically rotated specimens | Annotations may expose coordinates, counts, dimensions, or states; rotation is reserved for rails and specimen labels. | `components/content-data-display.md`, `patterns/perceptual-patterns.md` |
| R04 | DIRECT | long uppercase paragraph, low-contrast giant footer crop, sparse anchors | Keep operational copy terse and factual. Large display matter may be dim and cropped; readable content remains foreground. | `foundations/voice-tone-microcopy.md`, `foundations/design-principles.md` |
| B01 | DIRECT | Web MCP context affects only the name; JetBrains Mono specified | Product nouns cannot introduce unsupported motifs or colours. The design language remains source-derived and product-agnostic apart from naming. | `DESIGN.md`, `handoff/generated-skill-readiness.md` |
| corpus | INFERRED | static identity frames imply no interaction timings | Motion uses line tracing, stepped reveal, inversion, and crop shifts derived from visual forms; timings remain reconstruction rules, not observed behavior. | `foundations/motion-personality.md`, `accessibility/keyboard-focus-motion.md` |

## Conflicts

- Custom source lettering conflicts with the required JetBrains Mono family. The extracted system preserves typographic behavior—scale, clipping, case, spacing, specimen orientation—but not source glyph anatomy.
- R02's high texture density conflicts with R04's severe sparsity. The resolution is an explicit density state: `quiet` is default; `signal` is bounded to a single region and never floods text-bearing surfaces.
- Thin source lines can fail interface contrast. Production hairlines use at least one CSS pixel at standard density and strengthen to two pixels for focus, high contrast, or reduced visual acuity modes.

## Gaps

- No UI states, controls, responsive layouts, animation, sound, haptics, or platform behavior are directly shown. These are marked as inferred operational extensions and must be tested in implementation.
- No colour accent, photography usage rights, original vector assets, or font files were supplied. The package uses neutral tokens, generated textures, original geometry, and a system/webfont reference to JetBrains Mono.
- No evidence establishes a logo for Web MCP. The package defines a motif grammar and word treatment, not a copied or newly asserted trademark.
