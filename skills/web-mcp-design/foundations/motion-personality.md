# Motion Personality

Output path: `foundations/motion-personality.md`

## Temporal Character

- Mechanical and restrained, with short linear traces, stepped raster changes, and decisive inversion cuts. Curves decelerate only when a large field settles.
- Dominant pacing is a brief preparation, a crisp state change, then stillness. Typical control feedback completes in 90-160ms; structural transitions complete in 220-320ms.
- The rhythm communicates inspected causality: users can see where a state travelled, but the interface never performs for its own sake.

## Easing Model

| Motion family | Easing or physics | Duration range | Usage |
| --- | --- | --- | --- |
| Node response | linear or `steps(2, end)` | 80-120ms | fill/open change, press, completion tick |
| Path trace | `cubic-bezier(.4,0,.2,1)` | 180-280ms | progress between adjacent states, focus route, diagram reveal |
| Field settle | `cubic-bezier(.16,1,.3,1)` | 240-320ms | panel entry, crop alignment, bounded media reveal |
| Inversion cut | `steps(1, end)` | 0-100ms | selected, confirmed, or mode-switched region |
| Exit | `cubic-bezier(.4,0,1,1)` | 100-180ms | dismiss nonessential overlays and transient feedback |

## Functional Motion

- Orientation: retain the departing outline until the arriving boundary is visible; large surfaces translate no more than 24px.
- State change: pair a label update with node fill, rule weight, or bounded inversion.
- Causality: begin at the acted control or current node and travel toward the affected region.
- Continuity: diagrams reuse the same path; avoid dissolving into unrelated geometry.
- Feedback: press is immediate, processing is persistent but quiet, success settles once, and error remains until resolved.

## Rhythm Pattern

- Metronomic with one interruption: node, line, node; label appears with the destination node.
- Stagger only directly related items, 30-50ms apart, with a maximum of five items and 240ms total delay.
- A hard inversion may interrupt the smooth trace for confirmation or fault. Do not use surprise motion for ordinary hover.

## Transition Type

- Moment-to-moment: node fill or one-pixel rule strengthens.
- Action-to-action: path trace connects control to result.
- Subject-to-subject: hard cut or 16px field translation; preserve shared alignment.
- Scene-to-scene: short black/white field inversion with the title anchored.
- Aspect-to-aspect: stepped halftone threshold or clip reveal inside one bounded media region.

## Entry And Exit Motion

- Entries reveal boundary first, content second; origin follows the reading path or triggering node.
- Exits are faster, collapsing toward the source control where practical.
- Persistent motion is prohibited except determinate progress. Indeterminate work uses a static labelled path with one cycling node no faster than 1.2s.
- New input may interrupt and retarget a path trace; it must not queue a long cinematic sequence.

## Stillness Specification

- Reading surfaces, giant background type, construction grids, and completed states remain still.
- Stillness communicates system confidence and makes the next causal event legible.
- Required feedback wins, but only the smallest meaningful region moves. Background atmosphere never competes with controls.

## Reduced-Motion Translation

- Under `prefers-reduced-motion: reduce`, replace tracing and translation with immediate path visibility, label change, outline strengthening, and bounded inversion.
- Preserve start/end states, focus destination, progress value, and error persistence without relying on temporal order.
- Forbid parallax, zoom, background drift, repeated flicker, marquee text, rapid halftone crawling, and full-screen white flashes.

## Anti-Patterns

- Elastic springs, bouncing icons, liquid morphs, decorative glitch, long scroll choreography, cursor followers, ambient node swarms, infinite type movement, simultaneous panel motion, and transitions longer than 500ms for ordinary actions.
