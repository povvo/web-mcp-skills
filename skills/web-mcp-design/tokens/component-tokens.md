# Component Tokens

Output path: `tokens/component-tokens.md`

## Component Token Contract

| Component | Part | Property | Semantic token | State or variant | Override rule |
| --- | --- | --- | --- | --- | --- |
| Button | container | background | `semantic.action.primary` | primary/default | may invert only as a complete container |
| Button | label/icon | colour | `semantic.text.on-signal` | primary/default | never reference a neutral primitive |
| Button | outline | border | `semantic.border.focus` | focus-visible | cannot be removed or replaced by colour alone |
| Button | container | min target | platform semantic target | all | visual mark may be smaller; hit area may not |
| Text input | field | surface | `semantic.surface.canvas` | default | raised surface permitted only inside an inverse parent |
| Text input | boundary | border | `semantic.border.structure` | default | error/focus override with semantic state boundary |
| Text input | message | colour/pattern | `semantic.state.error` | invalid | include message ID association and recovery text |
| Navigation item | label | colour | `semantic.text.primary` | default | current item uses state token, not weight alone |
| Navigation item | node/rule | state geometry | `semantic.state.current` | current | pair with `aria-current` or platform equivalent |
| Progress route | path | stroke | `semantic.border.structure` | pending | current/completed segments become strong, not coloured |
| Progress route | node | fill | `semantic.state.current` | current | state label remains visible or accessible |
| Status field | container | surface | `semantic.surface.raised` | informative | error/warning may add double rule or hatch |
| Status field | title | text | `semantic.text.strong` | all | no uppercase paragraph styling |
| Data table | grid | border | `semantic.data.grid` | default | row selection must not erase cell boundaries |
| Data table | value | text | `semantic.text.primary` | default | identifiers and numerals use tabular figures |
| Modal | shell | surface | `semantic.surface.signal` | open | fully opaque, traps focus, labelled by visible heading |
| Modal | backdrop | surface | `semantic.overlay.scrim` | open | no blur or transparent glass |
| State node | state | geometry | semantic state family | pending/current/complete/error | label and owning state must match geometry |
| Operation trace | connector | motion | `semantic.motion.transition` | running | reduced motion renders final segment immediately |

## Component Token Families

- Action controls bind field, text, focus, and target dimensions through semantic roles.
- Form controls share structure, focus, error, and help semantics; validation never invents local red/green values.
- Navigation uses the same node/path/current-state grammar as progress without turning every link into a diagram.
- Feedback and status use persistent labelled geometry, bounded surfaces, and optional patterns.
- Content and data display use primary/recessive text plus low-priority grid boundaries.
- Domain modules compose existing state and data semantics only for objects, operations, results, and boundaries defined by the verified product model.

## Override Contract

Component variants may select a different semantic token but may not change primitive values. Platform overrides can adjust target size, font rendering, and focus mechanism while preserving contrast and meaning. A component-specific token exists only when the property is genuinely unique and repeated across instances; one-off spacing remains a layout decision, not a token.

## Anti-Patterns

- Component tokens referencing primitives or aliases; local hex, shadow, radius, or duration overrides; variants named by colour; focus tokens shared with hover; status encoded by fill alone; domain modules inventing new button/input semantics; and token proliferation for single-instance decorative details.
