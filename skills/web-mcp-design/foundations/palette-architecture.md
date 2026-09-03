# Palette Architecture

Output path: `foundations/palette-architecture.md`

## Palette Identity

- Colour story: a binary instrument panel softened by two graphite intermediates. Colour is structure, not decoration.
- Hue family and temperature: achromatic and optically cool; permit only display-calibrated neutral drift, never an intentional blue or warm tint.
- Saturation and chroma behavior: target zero chroma. Imported media becomes monochrome before halftone treatment.
- Lightness range: near-black `#0A0A0A`, raised black `#141414`, graphite `#3A3A3A`, dim text `#777777`, paper `#E8E8E4`, and signal white `#F7F7F2`.
- Emotional role of colour: polarity communicates activation and field change; greys communicate depth, priority, and inactive structure.

## Palette Separation

| Territory | Owned colours | Boundary rule | Emotional or functional role |
| --- | --- | --- | --- |
| Base field | near-black or paper | one base per viewport region | establishes quiet, matte ground |
| Foreground | signal white or near-black | must meet readable contrast against base | carries active type, paths, and controls |
| Recessive structure | graphite and dim text | never for essential small text without contrast verification | measurements, giant crops, grids, disabled content |
| Signal field | base/foreground binary pair | bounded rectangle; may invert locally | media, progress, diagnostics, selected region |

## Convergence Behaviour

- Territories remain separate until a state change deliberately inverts a complete component or bounded region.
- Selection, confirmation, mode switch, or media threshold may trigger inversion. Hover alone should not flip a large region.
- Interface equivalent: foreground and background exchange roles while border, icon, and copy remain semantically intact.
- Forbidden convergence: low-contrast grey-on-grey body copy, uncontrolled transparency, gradients between modes, or texture that erodes letterforms.

## Container Principle

- Shells are absorptive matte fields. Cards are created by spacing, a one-pixel rule, or inversion—not shadows.
- The container is neutral and quiet. Signal white is luminous only by contrast, not glow.
- Nested surfaces may move one neutral step, but no more than three simultaneous surface values should be visible.

## Light Quality

- Direction: flat and frontal.
- Hardness: hard-edged for regions; dithered at media transitions.
- Temperature: neutral-cool.
- Intensity: restrained across large fields, maximal at small nodes or active copy.
- Behavior: static by default; inversion cuts or stepped halftone thresholds may change state without a glow or pulse.

## Mode Adaptation

| Mode | Palette translation | Risk control |
| --- | --- | --- |
| Light | paper base, near-black foreground, graphite recessive structures | avoid expansive pure white; preserve 4.5:1 text contrast and suppress faint grid noise |
| Dark | near-black base, paper foreground, graphite raised surfaces | avoid pure black/white across long text; test halation and strengthen one-pixel lines where needed |
| High contrast | system Canvas/CanvasText/Highlight values; remove grain and dim decoration | never depend on inversion alone; retain labels, outlines, underlines, and state icons |

## CVD And Ambient Robustness

- There are no hue-only distinctions. Success, warning, error, selected, and loading states require text plus a distinct node, line, or fill pattern.
- Use solid, diagonal hatch, dot fill, double rule, and open/closed node alternatives, with adequate lightness separation.
- In bright environments, increase rule thickness and use near-black/paper endpoints; remove mid-grey essential copy.
- In low light, use paper rather than pure white, widen text tracking sparingly, and avoid large full-white flashes.

## Token Translation

| Token role | Candidate values or ranges | Usage rule |
| --- | --- | --- |
| `color.canvas` | `#0A0A0A` dark / `#F7F7F2` light | viewport and primary shell |
| `color.ink` | `#E8E8E4` dark / `#0A0A0A` light | readable copy and active geometry |
| `color.structure` | `#3A3A3A` dark / `#777777` light | large crop, grid, inactive line |
| `color.signal` | inverse of current canvas | active node, focus, selected block |
| `color.surface.raised` | `#141414` dark / `#E8E8E4` light | bounded secondary surface only |

## Anti-Patterns

- Accent hues, rainbow syntax colours, status traffic lights, blue links without another cue, gradients, glow, glass transparency, warm cream nostalgia, or grey values too close to distinguish.
- Never simulate sophistication by reducing required contrast. Never place halftone noise under body text or focus indicators.
