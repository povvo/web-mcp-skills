# Surface Language

Output path: `foundations/surface-language.md`

## Material Quality

- Dominant materials: matte screen-black, uncoated off-white paper, crisp plotted lines, and coarse one-bit print raster.
- Finish: low-gloss and absorptive. White elements appear bright by contrast, never through bloom.
- Weight: the canvas feels dense and heavy; rules and nodes feel light but exact; signal fields feel compressed and granular.
- Temperature: optically cool neutral.
- Tactility: subtle dry grain at the field level and visibly discrete dots inside bounded media. Interactive controls remain crisp, not distressed.

## Environmental Materiality

- Hard geometry sits on a faintly imperfect substrate. Rounded turns relieve mechanics without making the system soft.
- Lived-in only at macro surface scale; text and interaction geometry stay clean.
- Industrial-editorial rather than clinical: measured, reproduced, and slightly tactile, with no luxury gloss.
- Translate this as generated monochrome grain below 2% opacity, one-bit image rasterization, device-pixel rules, and flat tonal layers.

## Damage And Wear

- The system is operationally pristine with restrained print-like residue.
- Allow non-directional micrograin, occasional sparse dot dropout inside generated halftone, and subtly uneven large fields.
- Forbid scratches, torn edges, film burns, paper scans, water stains, chromatic aberration, compression glitches, and damage that compromises a label, icon, focus ring, or data value.

## Surface Hierarchy

| Surface role | Material behavior | Depth behavior | Token implication |
| --- | --- | --- | --- |
| Base | matte neutral field with optional micrograin | plane zero; no shadow | `surface.canvas`, `texture.grain.quiet` |
| Raised | one neutral step or one-pixel frame | plane one by tone and overlap | `surface.raised`, `border.structure` |
| Overlay | fully opaque inverse field | plane two by interruption and edge | `surface.overlay`, `color.ink.inverse` |
| Critical | high-contrast bounded field with double rule or hatch | same plane as content; prominence without elevation | `surface.critical`, `pattern.critical` |

## Craft Signal

- Maximum polish belongs to typography rendering, line joins, node alignment, halftone thresholds, focus geometry, and responsive crops.
- Restraint belongs to canvas texture, depth, and state surfaces: no effect should announce its own technique.
- Visible construction belongs in diagrams, progress routes, brand specimens, and diagnostic views where nodes and measurements communicate how the object works.

## Transparency And Opacity

- All semantic surfaces are opaque.
- Translucency is limited to nonessential grain or a dim background crop; it must never create a new stacking ambiguity.
- Do not use backdrop blur, glass, frosted panels, or alpha-layered cards.
- A surface fails when body text sees texture through it, an overlay loses its boundary, or transparency makes mode contrast unpredictable.

## Texture Dosage

- Quiet grain: 0-2% apparent contrast. Signal halftone: 20-70% dot coverage inside one bounded media region.
- Grain is subpixel-to-2px and non-directional; halftone cells are 4-10px depending on output scale.
- Generate texture procedurally with a stable seed or SVG/CSS pattern; avoid obvious tiling seams and source-image reuse.
- Mask texture away from body text, small labels, icons, one-pixel paths, and focus indicators by at least 4px.

## Anti-Patterns

- Glassmorphism, soft drop shadows, bevels, glossy metal, neon bloom, gradient mesh, skeuomorphic panels, vintage grunge packs, indiscriminate noise, texture on every component, or distressed interactive geometry.
