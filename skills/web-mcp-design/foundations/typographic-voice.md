# Typographic Voice

Output path: `foundations/typographic-voice.md`

## Voice Weight

- Weight personality: precise and editorial at reading scale; architectural at display scale.
- The voice is cool, factual, and visibly measured. Authority comes from alignment and restraint, while display energy comes from crop and disproportion rather than novelty glyphs.
- Use 400 for body, 500 for labels and controls, 600 for headings, and 700 for isolated display anchors. Disabled states change contrast before weight; selected states may invert or move from 500 to 600.

## Voice Classification

| Type category | Role in the language | Why it fits |
| --- | --- | --- |
| Monospace: JetBrains Mono | every textual role, including display, body, data, labels, code, and word treatment | its disciplined rhythm, differentiated characters, broad weight range, and technical precision support both factual microcopy and monumental scale without copying a custom display alphabet |

## Type Pairing Logic

- Primary face: JetBrains Mono, with local or webfont delivery chosen by the implementation.
- Secondary face: none. Native monospace is an emergency loading fallback, not a designed pairing.
- Pairing contrast: hierarchy is internal—size, weight, tracking, case, orientation, brightness, and clipping.
- Pairing boundary: do not introduce sans, serif, geometric display, or faux-tech alternates for campaigns.

## Text As Spatial Element

- Small type behaves as annotation and interface. Large type behaves as architecture: a word, numeral, or short phrase may touch or exceed one boundary.
- Body and controls align to the content grid. Display matter may intentionally overflow only one axis. Vertical text is limited to side rails, scale labels, and specimens.
- Type may sit beside a halftone field but not over its active texture. Measurement labels attach to grid lines, nodes, or media bounds.

## Dialogue Density

- Default to one concise body block, a small set of labels, and one dominant anchor per viewport.
- Low verbosity: use concrete nouns, active verbs, exact counts, and state names. Long prose is permitted only in dedicated editorial reading regions.
- Labels may be dense at edges but must not surround every object.
- A label must answer what, where, how much, or what state. Remove ornamental pseudo-data.

## Silence As Whitespace

- Absence signals confidence and lets scale carry tone. Do not explain a state twice when its label and geometry already communicate it.
- Preserve at least one quiet region equivalent to three spacing units around the primary reading block.
- Keep text out of active halftone texture, path intersections, focus rings, and cropped display counters.

## Scale Relationship

| Role | Size/range | Weight | Line height | Behavior |
| --- | --- | --- | --- | --- |
| Display | `clamp(4rem, 16vw, 18rem)` | 600-700 | 0.78-0.88 | uppercase or product-case; negative tracking to `-0.07em`; crop one edge, never impair essential reading |
| Heading | `clamp(1.75rem, 4vw, 4.5rem)` | 600 | 0.95-1.05 | short, usually sentence case; may align with a node or rule |
| Body | `1rem` to `1.125rem` | 400 | 1.5-1.65 | normal case for sustained reading; maximum 72 characters per line |
| Caption/label | `0.6875rem` to `0.8125rem` | 500 | 1.25-1.4 | uppercase with `0.06em` to `0.12em` tracking; numbers use tabular figures |

## Optical And Platform Considerations

- JetBrains Mono has no required optical-size axis; inspect actual rendering at each role and avoid synthetic bold.
- Never render interface text below 11 CSS pixels. Distinguish `0/O`, `1/l/I`, punctuation, and braces at target resolution.
- In dark mode, paper-white rather than pure white reduces bloom; use 500 instead of 400 only if the display or size loses strokes.
- Web should preload only used weights and use `font-display: swap`. Native platforms may substitute only when JetBrains Mono cannot be shipped. Below 480 pixels, remove vertical labels, reduce display to `clamp(3rem, 20vw, 7rem)`, and preserve body size.

## Anti-Patterns

- Custom techno fonts, outlined display alphabets, oblique body copy, all-uppercase paragraphs, letterspacing on body text, centred long copy, more than four simultaneous weights, tiny grey labels, fake hexadecimal filler, or random code used as atmosphere.
- Do not distort glyphs to mimic geometric symbols. Build original symbols as SVG; keep textual content textual and selectable.
