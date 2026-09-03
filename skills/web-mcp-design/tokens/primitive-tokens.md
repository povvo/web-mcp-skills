# Primitive Tokens

Output path: `tokens/primitive-tokens.md`

## Primitive Value Inventory

| Token | Category | Raw value | Unit/model | Range role | Notes |
| --- | --- | --- | --- | --- | --- |
| `neutral.0` | colour | `#0A0A0A` | sRGB | black endpoint | dark canvas; avoid pure black for long reading fields |
| `neutral.10` | colour | `#141414` | sRGB | raised dark | one tonal step above canvas |
| `neutral.28` | colour | `#3A3A3A` | sRGB | graphite | dim giant crop and inactive structure |
| `neutral.48` | colour | `#777777` | sRGB | mid neutral | use only after contrast verification |
| `neutral.90` | colour | `#E8E8E4` | sRGB | paper | reading foreground or light raised surface |
| `neutral.97` | colour | `#F7F7F2` | sRGB | white endpoint | light canvas or active signal |
| `alpha.02` | colour alpha | `0.02` | ratio | quiet texture | maximum baseline grain contribution |
| `font.family.mono` | typography | `"JetBrains Mono", ui-monospace, monospace` | CSS family list | only family | fallbacks are loading/emergency behavior, not a visual pairing |
| `font.size.11` | typography | `0.6875rem` | rem | micro | minimum metadata size at 16px root |
| `font.size.13` | typography | `0.8125rem` | rem | label | compact UI and captions |
| `font.size.16` | typography | `1rem` | rem | body | default reading size |
| `font.size.18` | typography | `1.125rem` | rem | large body | editorial lead or spacious UI |
| `font.weight.400` | typography | `400` | numeric | regular | body |
| `font.weight.500` | typography | `500` | numeric | medium | labels and controls |
| `font.weight.600` | typography | `600` | numeric | semibold | headings and selected states |
| `font.weight.700` | typography | `700` | numeric | bold | isolated display anchors only |
| `line-height.tight` | typography | `0.84` | ratio | display | never apply to wrapping prose |
| `line-height.body` | typography | `1.6` | ratio | readable | ordinary body copy |
| `tracking.label` | typography | `0.08em` | em | metadata | uppercase labels |
| `tracking.display` | typography | `-0.05em` | em | display | inspect per word; floor `-0.07em` |
| `space.1` | space | `4px` | px | base | micro gaps and node-label offset |
| `space.2` | space | `8px` | px | compact | adjacent controls and icon-label gap |
| `space.3` | space | `12px` | px | intermediate | compact inset |
| `space.4` | space | `16px` | px | standard | mobile gutter and content gap |
| `space.6` | space | `24px` | px | group | component separation |
| `space.8` | space | `32px` | px | section-small | panel rhythm |
| `space.12` | space | `48px` | px | section | desktop grouping |
| `space.18` | space | `72px` | px | field | maximum desktop safe edge |
| `radius.0` | radius | `0` | px | square | default frames |
| `radius.1` | radius | `2px` | px | line turn | compact geometry |
| `radius.2` | radius | `4px` | px | control | technical corners |
| `radius.3` | radius | `8px` | px | large turn | maximum non-circular radius |
| `stroke.hairline` | border | `1px` | CSS px | structural | snap to device pixels |
| `stroke.focus` | border | `2px` | CSS px | focus | remains visible in high contrast |
| `target.pointer` | dimension | `32px` | px | compact minimum | pointer-dense environments |
| `target.touch` | dimension | `44px` | px | touch minimum | independent of visible icon size |
| `duration.instant` | motion | `90ms` | ms | response | press and inversion |
| `duration.short` | motion | `140ms` | ms | local | hover and compact exits |
| `duration.path` | motion | `240ms` | ms | structural | line trace and field settle |
| `duration.max` | motion | `320ms` | ms | major | ordinary transition ceiling |
| `ease.standard` | motion | `cubic-bezier(.4,0,.2,1)` | curve | path | causal movement |
| `ease.settle` | motion | `cubic-bezier(.16,1,.3,1)` | curve | settle | large field alignment |
| `media.ratio.wide` | media | `16/9` | ratio | wide | hero and feature media |
| `media.ratio.square` | media | `1/1` | ratio | modular | avatar and compact preview |
| `halftone.cell.small` | media | `4px` | px | fine | high-resolution/small fields |
| `halftone.cell.large` | media | `10px` | px | coarse | large hero fields |

## Required Categories

- Colour uses six achromatic primitives plus one optional quiet alpha; no hue primitive exists.
- Typography uses JetBrains Mono, four weights, micro/body sizes, and fluid display values defined at the global layer.
- Space follows a 4px base, with square-to-8px radii and one/two-pixel strokes.
- Elevation uses tonal lift and opaque overlap. Shadow, blur, and glass primitives intentionally do not exist.
- Motion uses short deterministic durations and two curves. Springs and ambient delay are excluded.
- Media uses explicit crop ratios, author-provided focal positions, and 4-10px halftone cells.

## Type Contract

Each primitive retains its declared design-token type—colour, dimension, duration, cubic-bezier, font family, font weight, number, or ratio—through transforms. Do not serialize every raw value as an untyped string.

## Anti-Patterns

- Components referencing raw primitives; local hex values; arbitrary spacing; mode values embedded in components; shadows or blur added as “missing” elevation; extra font families; colour/status primitives; font sizes below 11px; and transforming token names by appearance instead of intent.
