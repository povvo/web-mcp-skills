# Iconography System

Output path: `foundations/iconography-system.md`

## Icon Set Identity

- Icon set family: original schematic utility icons built from orthogonal segments, one 45-degree diagonal where required, and circular state nodes. Use a consistent library for commodity actions rather than redrawing familiar platform symbols.
- Outline is default; filled geometry denotes selected, active, or completed state. Duotone is unnecessary in a monochrome system.
- Use 1.5px strokes at 24px and 2px at 32px; focus and high-contrast variants use at least 2px.
- Radius is 2px at compact turns and 4px at larger containers. Circles remain circular.
- Square caps on structural paths; round caps only on open endpoints. Use round joins for path turns and bevel joins for deliberate 45-degree cuts.

## Optical Correction

- Circles and diagonal terminals may overshoot the nominal grid by half a stroke.
- Centre by visible mass. A right-pointing arrow or asymmetric branch shifts roughly 0.5-1px opposite its visual pull.
- Shorten dense diagonal clusters or open counters so they do not appear heavier than orthogonal forms.
- At small sizes, inset strokes farther from the container edge than filled forms; never let a focus outline merge with the icon.

## Metaphor Rules

- Literal metaphors: close, search, external link, copy, delete, play/pause, download, and disclosure may follow established platform conventions.
- Abstract metaphors such as relationship, sequence, inspection, transform, and state should use labelled node/path diagrams rather than invented pictograms.
- Avoid rockets, magic wands, brains, robots, plugs, globes, chain links, and “AI sparkle” marks as default shorthand; their meaning is broad or culturally loaded.
- Every domain-specific icon and every icon for an unfamiliar object, action, role, or state requires a visible label at first use.

## Icon And Text Relationship

- Icon-only is allowed for universally recognized actions in a repeated context and only with an accessible name.
- Pair labels to the right in controls and below/alongside in diagrams. Maintain 8px icon-label spacing.
- Tooltips supplement, never replace, accessible names or critical visible labels. Show keyboard shortcuts in tooltips only when accurate.
- In dense UI, simplify geometry before removing labels. Preserve 44px targets even when the visual icon is 16-20px.

## Sizing And Alignment

- Construct on a 24x24 grid with a 2px safe area; use 16, 20, 24, and 32px optical sizes rather than arbitrary scaling.
- Keep nodes and diagonals inside the safe area unless a deliberate path continues into another component.
- Minimum interactive target is 44x44px on touch and at least 32x32px for compact pointer interfaces.
- Align the icon's perceived centre to the cap-height/body centre, not the text baseline.
- At 16px, remove interior nodes, reduce multi-segment paths to the decisive turn, and use a 1.5-2px stroke.

## Brand And Emotional Signal

- Personality is measured, structural, and terse.
- Polish is highest at joins, counters, and repeated state variants.
- Trust comes from familiar action metaphors, stable state mapping, visible labels, and consistent line weight.
- Expressive icons may crop or expand only in noninteractive brand applications. Functional icons remain compact and unmistakable.

## Translation Rules

- Use paths for relationships, nodes for states or decisions, frames for bounded objects, and diagonals for direction or transformation.
- A node is open by default, filled when current/selected/completed, double-ringed for attention, and crossed only when the labelled object is unavailable.
- Build symbols as SVG with `currentColor`; avoid font glyphs for branded or stateful icons.

## Anti-Patterns

- Mixing unrelated icon packs, arbitrary filled/outline variants, unlabeled abstract symbols, ornamental node clusters, rounded cartoon icons, pseudo-3D perspective, emoji, colour-only state, overly intricate 16px drawings, and copying a source emblem as the Web MCP mark.
