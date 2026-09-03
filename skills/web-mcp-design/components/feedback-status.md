# Feedback And Status

Output path: `components/feedback-status.md`

## Feedback Covered

- Alerts, banners, inline alerts, toasts, snackbars, dialogs, modals, prompts, popovers.
- Loading, empty, error, success, warning, information states.
- Recovery and escalation.


## User Or Maker Problem

- Communicate asynchronous state, consequence, interruption, and Recovery without relying on hue or transient spectacle. Alerts stay proportional to urgency; durable outcomes stay inspectable.

## Anatomy And Boundaries

| Component or module | Anatomy | Boundary | Related component |
| --- | --- | --- | --- |
| Inline status | state node, concise message, optional detail/action | owns local field/operation feedback | form field, button |
| Banner/alert | labelled region, title, message, actions, dismiss when safe | owns page-level persistent condition | navigation, recovery action |
| Toast | concise message, optional undo, timer/progress pause | owns low-risk transient acknowledgment only | undo action |
| Dialog | opaque shell, heading, consequence, actions, close behavior | owns blocking decision or required input | modal overlay, form |
| Empty state | specific state label, short explanation, valid next action | owns absence category, not decorative illustration | content list, filters |

## Variants

| Variant | Purpose | Visual difference | Behavioral difference |
| --- | --- | --- | --- |
| Informative | explain stable context | one-pixel frame/open node | no urgent announcement |
| Warning | consequence needs review | double open node and assertive rule | persistent until acknowledged/resolved |
| Error | intended result failed | hatch/double rule and stop node | recovery action and scope required |
| Success | durable result reached | closed endpoint and stable label | no forced dismissal; toast only for low-risk acknowledgment |
| Processing | work underway | current node/path and real value/elapsed time | cancel/retry/resume according to operation contract |

## States

| State | Visual behavior | Interaction behavior | Content behavior |
| --- | --- | --- | --- |
| Default | quiet boundary and labelled node | readable; actions keyboard reachable | state + object |
| Hover/focus | only contained actions respond; focus gets 2px outline | no whole-alert click unless truly one action | copy remains stable |
| Active/pressed | action node responds locally | dismiss/retry/undo follows its own button contract | result not claimed early |
| Disabled | not a feedback status; unavailable actions explain why | do not disable the message itself | preserve diagnostic text |
| Loading | path/current node visible, no full-screen animation by default | prevent duplicate mutation; allow safe cancellation | exact step/value when known |
| Error | persistent stop geometry and bounded field | retain data; direct to scoped retry or repair | what failed, what remains, what to do |

## Content And Naming Rules

- Lead with the state and affected object. Follow with retained results or consequence, then one primary Recovery action.
- Loading copy appears by roughly 300ms; beyond two seconds show elapsed time or real progress. Empty states distinguish no data, no match, not loaded, and no permission.
- Avoid “Oops,” praise, exclamation, blame, and false certainty.

## Token Dependencies

| Part | Required token | Override boundary |
| --- | --- | --- |
| Container | `semantic.surface.raised` or `semantic.surface.signal` | modal is opaque; no glass or shadow |
| Message | `semantic.text.primary`/`semantic.text.on-signal` | 4.5:1 minimum |
| State | semantic state family | geometry, pattern, and text remain redundant |
| Focus | `semantic.border.focus` | actions only; dialog focus trap visible |
| Motion | semantic motion family | reduced mode immediate; no flashing |

## Accessibility And Localization

- Use `status` for polite updates and `alert` only for urgent time-sensitive content. Avoid announcing the same message through multiple live regions.
- Dialogs label themselves, trap and restore focus, support Escape when dismissal is safe, and keep destructive confirmation explicit.
- Toast timers pause on hover/focus and meet reading needs; critical errors never auto-dismiss. Reflow and localization must not clip actions.

## Code And API Contract

- `kind`, `title`, `message`, `details`, `actions`, `dismissible`, `duration`, `progress`, `timestamp`, `receiptId`, and callbacks. Validate that error/warning variants include meaningful text.
- Unsupported: colour props, icon-only status, unknown percent, irreversible auto-dismiss, and modal nesting.

## Examples And Anti-Patterns

- Do: “Result saved. Details did not arrive.” with “Retry details” and a copyable operation ID.
- Avoid: red/green-only Alerts, endless Loading spinner, success before an external receipt, error toast that disappears, generic “Something went wrong,” confetti, beeping, or modal confirmation for routine navigation.

## Related Patterns

- `patterns/behavioral-states.md`, `components/sequence-progress.md`, `foundations/interaction-register.md`, and `accessibility/accessibility-matrix.md`.
