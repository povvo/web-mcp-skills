# Sequence And Progress

Output path: `components/sequence-progress.md`

## Sequences Covered

- Step controls, ordered flows, wizards, guided tasks.
- Progress indicators, timers, completion states.
- Resume, retry, and exit behavior.


## User Or Maker Problem

- Expose where a user or operation is, what has completed, what remains, and how to recover without inventing progress. Steps use the path/node grammar literally: topology represents real sequence and state.

## Anatomy And Boundaries

| Component or module | Anatomy | Boundary | Related component |
| --- | --- | --- | --- |
| Step route | ordered labels, nodes, connectors, current marker, optional summary | owns finite ordered position; not navigation hierarchy | wizard controls |
| Determinate progress | label, value/max, path/fill, elapsed/remaining when real | owns measured completion | status field |
| Indeterminate activity | operation label, one current node, elapsed time | owns unknown-duration activity; never implies percent | cancel/retry action |
| Completion record | result label, closed endpoint, timestamp/ID, next action | owns durable end state | feedback status, data display |

## Variants

| Variant | Purpose | Visual difference | Behavioral difference |
| --- | --- | --- | --- |
| Linear task | user advances through known screens | labelled horizontal/vertical nodes | previous steps revisitable only when valid |
| Operation trace | system runs known phases | path segments reveal causally | user may inspect details, cancel, retry, or resume as supported |
| Compact meter | bounded quantitative progress | single rule with current node and numeric label | updates only from real measured values |
| Static timeline | history/audit | settled path and timestamps | read-only; no implied pending animation |

## States

| State | Visual behavior | Interaction behavior | Content behavior |
| --- | --- | --- | --- |
| Default | pending open nodes, quiet connector | no activation unless step is a real link/action | ordinal and concise label |
| Hover/focus | interactive step gets underline/2px focus | Enter activates valid revisitable step | current state stays distinct |
| Active/pressed | chosen node closes briefly | one transition | action label remains specific |
| Disabled | unavailable branch remains labelled/recessive | not activatable | explain prerequisite when useful |
| Loading | current node and preceding path are strong; trace may animate once | cancel/retry rules explicit | `Step 2/4 · Inspecting item`; no fake percent |
| Error | path stops at double-ring/hatch node | preserve prior completion; offer scoped retry | identify failed step and retained results |

## Content And Naming Rules

- Name Steps with concrete outcomes or present-tense operations. Show numeric position for known sequences and real percent only when numerator/denominator are meaningful.
- Completion copy names the result plus a durable timestamp, identifier, or count. Distinguish partial completion from success.

## Token Dependencies

| Part | Required token | Override boundary |
| --- | --- | --- |
| Pending node/path | `semantic.state.pending`, `semantic.border.structure` | cannot resemble disabled if still expected |
| Current | `semantic.state.current` | label and ARIA state required |
| Complete | `semantic.state.complete` | closed node plus stable path |
| Error | `semantic.state.error` | double rule/hatch and recovery copy |
| Motion | `semantic.motion.transition` | immediate final geometry in reduced mode |

## Accessibility And Localization

- Expose an ordered list, current step (`aria-current="step"`), progressbar value/min/max when determinate, and live status updates at a non-disruptive cadence.
- Do not announce every animation frame. Maintain keyboard access and 44px targets for interactive nodes; keep labels visible under zoom/reflow.
- Reduced motion presents all current geometry instantly; meaning never depends on trace direction alone.

## Code And API Contract

- `steps` entries contain `id`, `label`, `state`, and an optional `href`; the module also accepts `currentId`, `value`, `max`, `status`, `onCancel`, `onRetry`, and `onResume`. Validate that exactly one current step exists and completion cannot precede unresolved required steps.
- Unsupported: fake progress increments, unlabeled dots, decorative branching, and state derived solely from array index when backend receipts disagree.

## Examples And Anti-Patterns

- Do: `PREPARED → RUNNING → RESULT → COMPLETE`, with real timestamps and an error endpoint that preserves the verified partial result.
- Avoid: endless crawling dots, a percent that rises on a timer, Completion before receipt, restarting at zero after retry, animated paths behind prose, or every checklist presented as a dramatic route.

## Related Patterns

- `patterns/behavioral-states.md`, `components/feedback-status.md`, `components/domain-modules.md`, and `foundations/motion-personality.md`.
