# Behavioral States

Output path: `patterns/behavioral-states.md`

## State Inventory

| State | Trigger | Visual response | Interaction contract | Recovery |
| --- | --- | --- | --- | --- |
| Hover | pointing device enters an enabled target | boundary/underline strengthens by one neutral step; no layout shift | optional affordance only; never sole cue or action | disappears immediately on leave without changing state |
| Focus | keyboard/script places focus on an interactive element | independent 2px offset outline/path at 3:1 minimum | `:focus-visible` or platform equivalent; logical order and no obscuration | follows deliberate navigation; returns to trigger after a dismissed overlay |
| Active/pressed | accepted pointer/key press begins | node closes or compact region inverts for roughly 90ms | one activation; Space/Enter follow native semantics | releases to prior, loading, selected, or result state based on real outcome |
| Selected | user chooses an item/view or application confirms current choice | complete bounded region inverts or current node fills; label remains readable | programmatic selected/current state; distinct from focus | explicit deselect/change or context removal |
| Disabled | real prerequisite or permission makes action unavailable | readable recessive label, no pointer response; never opacity alone | native disabled semantics; not focusable unless platform pattern requires discoverability | explain cause when non-obvious and update immediately when prerequisite resolves |
| Loading | operation exceeds immediate response threshold | labelled current node/path; determinate value only when measured | duplicate mutation prevented; cancel/retry/resume defined by operation | resolves to durable completion, scoped error, partial state, or cancelled state |
| Error | validation or operation cannot reach intended result | persistent double rule or hatch with stop node and message | announce appropriately without repeated alerts; preserve input/results | concrete repair, scoped Retry, resume, or safe exit; unknowns remain explicit |
| Expanded/collapsed | disclosure control changes visibility | endpoint turns and bounded content appears/disappears with short settle | `aria-expanded`/relationship maintained; focus stays on control unless task requires otherwise | Escape or same control collapses; removed content cannot retain focus |

## Interaction Contracts

- Drag and drop: always provide keyboard/pointer alternatives such as move controls or file picker. Show valid drop boundary with an assertive rule and state label, not colour.
- Reveal and hide: boundary first, content second; reduced motion renders the final visibility immediately. Hidden content leaves accessibility and focus trees.
- Confirmation: proportionate to consequence. Routine reversible actions confirm inline; consequential or irreversible actions show target, scope, consequence, and recovery before execution.
- Undo: preserve a real inverse operation and name its time/scope. Do not offer cosmetic undo after an external side effect cannot be reversed.
- Retry: declare exactly which failed step repeats and whether side effects can duplicate. Retain successful prior steps.
- Resume: restart from the last verified durable state, not an optimistic local animation state.
- Responsive behavior: state meaning, labels, focus order, and touch targets remain invariant. Rotation and overflow may collapse, while current/error/completion geometry persists.

## State Precedence

Focus may coexist with hover, Selected, error, or loading and must remain independently visible. Disabled suppresses hover/active but not readable explanation. Error overrides ordinary boundary styling; loading cannot overwrite a known partial result; completion requires evidence from the owning operation rather than elapsed animation.

## Anti-Patterns

- Treating hover as focus; removing outlines; selected and active as synonyms; disabled data that cannot be copied; fake loading percentages; optimistic success without receipt; auto-dismissing errors; focus moved merely because status updated; motion-only disclosure; retrying an entire consequential operation when only one step failed; or clearing useful state during Recovery.
