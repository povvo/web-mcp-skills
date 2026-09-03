# Alias Tokens

Output path: `tokens/alias-tokens.md`

## Alias Map

| Alias Token | Alias target | Reason | Allowed consumers |
| --- | --- | --- | --- |
| `alias.field.base` | `{global.color.black}` dark / `{global.color.white}` light | gives modes a stable canvas endpoint | semantic surface tokens |
| `alias.field.inverse` | `{global.color.white}` dark / `{global.color.black}` light | provides local polarity without appearance-based component logic | selected and overlay semantics |
| `alias.ink.primary` | `{global.color.paper}` dark / `{global.color.black}` light | softens long-form dark-mode contrast while preserving readable light mode | semantic text and icon tokens |
| `alias.ink.strong` | `{global.color.white}` dark / `{global.color.black}` light | reserves maximum contrast for active nodes, focus, and compact labels | emphasis and focus semantics |
| `alias.ink.recessive` | `{global.color.graphite}` dark / `{global.color.mid}` light | unifies background crops and nonessential structure | decorative and inactive semantics |
| `alias.surface.raised` | `{global.color.raised-dark}` dark / `{global.color.paper}` light | creates depth by one tonal step without shadow | surface semantics |
| `alias.type.ui` | `{global.type.family}` | preserves the single-family invariant | all semantic type roles |
| `alias.type.display-size` | `{global.type.display}` | centralizes the responsive monumental interval | display roles only |
| `alias.type.reading-size` | `{global.type.body}` | protects body legibility across channels | body and control roles |
| `alias.edge.safe` | `{global.space.inline}` | keeps content and edge metadata on the same responsive inset | layout and component shells |
| `alias.gap.group` | `{global.space.component}` | provides one stable inter-item grouping distance | forms, navigation, data blocks |
| `alias.line.quiet` | `{global.stroke.structure}` | distinguishes structural rules from focus/critical boundaries | dividers, diagrams, frames |
| `alias.line.assertive` | `{global.stroke.emphasis}` | guarantees focus and critical visibility | focus, error, current state |
| `alias.motion.causal` | `{global.motion.transition}` | unifies path tracing and panel settlement | semantic motion roles |
| `alias.motion.immediate` | `{global.motion.response}` | keeps direct feedback below perceived lag | press, node, inversion |

## Alias Rules

- Use aliases to shield semantic tokens from raw primitive and mode changes. Mode resolution occurs here for polarity and raised surfaces.
- Keep alias chains one hop from globals and no more than two hops from primitives. Tooling must detect cycles.
- Name aliases by stable design role, not temporary implementation location or visible colour.
- Consumers below the semantic layer may not use aliases directly. The exception is a design-token build transform, which resolves aliases but preserves provenance metadata.
- A missing mode value inherits the default only when contrast and meaning remain intact; otherwise validation fails.

## Resolution Example

`component.button.label` references `semantic.text.on-action`, which references `alias.field.inverse` in the default button state. A dark-mode change therefore updates the field/ink polarity without modifying the component token or its implementation.

## Anti-Patterns

- Aliases named `gray-3`, `dark-bg`, or by file location; chains longer than two references; component-specific aliases; unresolved mode branches; cyclic references; direct component consumption; and duplicate aliases that point to the same target without a distinct stable purpose.
