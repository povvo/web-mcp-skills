# Spatial Grammar

Output path: `foundations/spatial-grammar.md`

## Composition Type

- Hybrid field/grid: functional content obeys a twelve-column desktop grid while one display object may behave as a field that crosses columns or exits the viewport.
- Primary law: align the useful, rupture the expressive. Reading order and controls remain stable; only one nonessential anchor may overflow.
- Secondary law: alternate a quiet region with a bounded signal region. Never divide every surface into equally weighted cards.

## Figure-To-Ground

- Use a micro-to-monumental ratio of at least 1:8 between labels and the main display anchor; body copy occupies the middle scale sparingly.
- The display object dominates area but may be subordinate in brightness. Small operational copy remains legible and semantically primary.
- Reversal occurs through local black/white inversion, not shadow or colour accent.
- Background may carry a dim crop, rule, dot field, or grid, but it cannot reduce body or focus contrast.

## Power Axis

- Primary axis is horizontal and off-centre; vertical rails and 45-degree diagonals create controlled counterforce.
- Authority comes from edge alignment, long horizontal runs, large scale, and unbroken negative space.
- Tension comes from a clipped bottom or side edge, a diagonal route, or a label rotated on a rail. Avoid arbitrary tilt.

## Containment

- Barriers are one-pixel rules, tonal steps, or complete inversion. Avoid floating card shadows.
- Frames are square or use a small 4-8px technical radius only where a line must turn.
- Crop one edge of one display object; preserve the identifying core and keep essential copy uncropped.
- Content safe area: `clamp(16px, 4vw, 72px)` inline and at least 24px block. Interactive elements retain 44px minimum targets even when their visible marks are smaller.
- Edge metadata may align to safe-area corners or vertical rails. No more than two edge anchors per viewport quadrant.

## Depth And Layering

| Plane | Contents | Depth mechanism | Interaction rule |
| --- | --- | --- | --- |
| Foreground | readable copy, controls, active nodes, focus path | highest contrast and crisp stroke | always receives input and remains unobscured |
| Midground | bounded media, selected blocks, diagrams, progress routes | inversion, one tonal step, or overlap | may update or reveal; never traps focus beneath it |
| Background | canvas, dim giant crop, construction grid, subtle grain | reduced contrast and extreme scale | decorative only; `pointer-events: none` and hidden from accessibility tree |

## Density Profile

- Variable but predominantly sparse: use roughly 55-75% quiet field in editorial/hero contexts and 25-40% in task-dense views.
- Desktop may use twelve columns; tablet eight; mobile four. At mobile widths, replace side rails with horizontal metadata and remove nonessential overflow.
- `quiet` is default. `signal` density appears during media emphasis, processing, selection, or diagnostics and stays within one bounded region.
- Maintain 44x44px targets, 8px between adjacent targets, 16px body text, and readable line lengths of 45-72 characters.

## Gestalt Relationships

- Proximity: labels sit 4-8px from the rule, node, or value they describe.
- Similarity: nodes with the same state share fill and diameter; lines with the same role share weight.
- Enclosure: use bounded signal fields for media or state groups, not a card around every paragraph.
- Continuity: path lines should lead between meaningful steps without decorative dead ends.
- Common region: inversion or a one-pixel frame groups content; spacing alone groups quiet editorial blocks.

## Optical Notes

- Centre compact symbols optically, accounting for diagonal mass and node protrusions rather than relying on bounding boxes.
- Allow round nodes and curved turns to overshoot their grid line by up to half a stroke.
- One-pixel rules must snap to device pixels; high-density canvases should render at device scale.
- Give the open side of an asymmetric crop 1-2 spacing units more air than the closed side.

## Anti-Patterns

- Symmetric card dashboards, centred everything, masonry collage, equal padding around every object, deep shadow stacks, pill-shaped containers, multiple competing overflows, edge-to-edge dense noise, or decorative diagrams with no reading path.
