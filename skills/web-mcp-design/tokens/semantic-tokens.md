# Semantic Tokens

Output path: `tokens/semantic-tokens.md`

## Semantic Intent Map

| Semantic token | Intent | Default value | State | Mode | Required contrast/behavior |
| --- | --- | --- | --- | --- | --- |
| `semantic.surface.canvas` | primary field | `{alias.field.base}` | default | all | full viewport or major region; no shadow |
| `semantic.surface.raised` | secondary grouping | `{alias.surface.raised}` | default | all | one tonal step or frame; cannot replace spacing hierarchy |
| `semantic.surface.signal` | bounded emphasis | `{alias.field.inverse}` | selected/active | all | invert text and geometry; keep region bounded |
| `semantic.text.primary` | readable content | `{alias.ink.primary}` | default | all | at least 4.5:1 for ordinary text |
| `semantic.text.strong` | compact active label | `{alias.ink.strong}` | active/focus | all | maximum contrast; do not use for large background matter |
| `semantic.text.recessive` | nonessential metadata | `{alias.ink.recessive}` | inactive | all | verify at least 4.5:1 if informative; otherwise decorative only |
| `semantic.text.on-signal` | content on inverse field | `{alias.field.base}` | selected/active | all | resolve against `semantic.surface.signal` with 4.5:1 minimum |
| `semantic.border.structure` | quiet containment | `{alias.line.quiet}` + `{alias.ink.recessive}` | default | all | one-pixel, device-aligned |
| `semantic.border.focus` | keyboard destination | `{alias.line.assertive}` + `{alias.ink.strong}` | focus-visible | all | 2px, offset 2px, at least 3:1 against adjacent colours |
| `semantic.icon.default` | functional icon | `{alias.ink.primary}` | default | all | inherits `currentColor`; visible label when metaphor is abstract |
| `semantic.action.primary` | main action field | `{alias.field.inverse}` | default | all | paired with explicit verb/object label |
| `semantic.action.secondary` | quiet action | transparent + `{semantic.border.structure}` | default | all | hover/focus cannot rely on opacity alone |
| `semantic.state.current` | active step/object | closed node + `{alias.ink.strong}` | current | all | pair with `aria-current` or equivalent and visible label |
| `semantic.state.complete` | finished step | closed node + stable path | complete | all | pair with result copy; no transient colour |
| `semantic.state.pending` | not yet active | open node + quiet path | pending | all | distinguish from disabled through label and operability |
| `semantic.state.error` | failed/unresolved | double rule or diagonal hatch + `{alias.ink.strong}` | error | all | persistent label, recovery action, live announcement when appropriate |
| `semantic.state.warning` | consequence needs attention | double open node + assertive border | warning | all | copy names consequence; never colour-only |
| `semantic.state.disabled` | unavailable | recessive ink + no fill | disabled | all | retain readable label and reason where useful; remove pointer response |
| `semantic.data.grid` | table/measurement structure | `{semantic.border.structure}` | default | all | must not compete with values |
| `semantic.overlay.scrim` | interruption boundary | opaque `{alias.field.base}` | modal | all | no translucent blur; preserve visible focus containment |
| `semantic.motion.response` | immediate feedback | `{alias.motion.immediate}` | interaction | normal | reduce to 0ms in reduced-motion mode where meaning survives |
| `semantic.motion.transition` | causal/spatial change | `{alias.motion.causal}` | state change | normal | replace with immediate final state under reduced motion |

## Intent Families

- Text separates primary, strong, recessive, and on-signal roles.
- Surfaces separate canvas, raised grouping, and bounded signal inversion.
- Border, icon, action, focus, data, and overlay roles resolve from aliases rather than primitives.
- Status uses geometry, pattern, label, and accessibility semantics because no status hue exists.
- Motion semantics describe response purpose and reduced-mode behavior, not visual decoration.

## Mode Contract

Light and dark resolve polarity through aliases. High contrast replaces values with system colours while retaining state geometry and labels. Reduced motion resolves transition duration to immediate state change without removing focus, progress values, or completion semantics.

## Anti-Patterns

- Semantic names containing visible colours; “success-green” or “error-red”; status without redundant geometry/copy; recessive text used for required instructions; transparent modal scrims; primitive references; and components that override focus or mode behavior locally.
