# Mode Tokens

Output path: `tokens/mode-tokens.md`

## Theme Mode Matrix And Override Contract

| Token | Light | Dark | High contrast | Reduced motion | Notes |
| --- | --- | --- | --- | --- | --- |
| `alias.field.base` | `{global.color.white}` | `{global.color.black}` | `Canvas` | unchanged | near-white/near-black endpoint |
| `alias.field.inverse` | `{global.color.black}` | `{global.color.white}` | `CanvasText` | unchanged | bounded signal and primary action |
| `alias.ink.primary` | `{global.color.black}` | `{global.color.paper}` | `CanvasText` | unchanged | ordinary readable content |
| `alias.ink.strong` | `{global.color.black}` | `{global.color.white}` | `CanvasText` | unchanged | focus and compact active geometry |
| `alias.ink.recessive` | `{global.color.mid}` | `{global.color.graphite}` | `GrayText` for nonessential content only | unchanged | never required small text without contrast proof |
| `alias.surface.raised` | `{global.color.paper}` | `{global.color.raised-dark}` | `Canvas` plus 2px `CanvasText` boundary | unchanged | tonal elevation disappears in forced colours |
| `semantic.border.structure` | mid neutral, 1px | graphite, 1px | `CanvasText`, 1-2px | unchanged | decorative grids may be removed in high contrast |
| `semantic.border.focus` | strong ink, 2px | strong ink, 2px | `Highlight`, 2px | unchanged | never suppressed by theme |
| `semantic.state.error` | double black rule + hatch | double paper rule + hatch | `CanvasText` double rule + text | immediate | no red dependency |
| `semantic.state.warning` | double open node + label | double open node + label | double node + label | immediate | geometry persists |
| `semantic.state.complete` | closed node + path | closed node + path | closed node + path | immediate | completion remains durable |
| `semantic.motion.response` | `90ms` | `90ms` | `0ms` when forced-colour transitions obscure state | `0ms` | pressed geometry still changes |
| `semantic.motion.transition` | `240ms` | `240ms` | `0ms` | `0ms` | final path/label must render immediately |
| `texture.grain.quiet` | up to 1% | up to 2% | none | unchanged | nonsemantic only |
| `texture.halftone.signal` | dark dots on paper or inverse | paper dots on black or inverse | solid/pattern fallback | static | no animated dot crawl |

## Adaptation Rules

- Dark mode reverses field polarity but does not blindly invert every grey: reading text uses paper, raised surfaces use a near-black step, and large inactive structure stays graphite to control halation.
- High contrast is a separate mode using system colours, thicker boundaries, and the removal of nonessential grain. It retains labels, node fill/open state, hatches, and focus.
- Reduced motion replaces trace, translation, stagger, and threshold animation with the immediate final path, stable node, updated label, and bounded inversion.
- `quiet` and `signal` are density modes independent from light/dark. Only one signal region may be active per major composition.
- Follow explicit user mode, then operating-system preference, then the product default. Persist user choice where the host platform supports it.

## Mode Precedence

High contrast overrides light/dark surface values. Reduced motion overrides duration/easing only. Density changes layout and texture but never lowers target size, text contrast, focus visibility, or state redundancy. Component-level Override values are forbidden unless documented in the component contract and validated in every mode.

## Anti-Patterns

- CSS filter inversion; pure black/pure white long-form text without halation testing; high contrast implemented as higher opacity; motion simply removed with no final cue; inaccessible recessive labels; status patterns dropped in forced colours; and components with private light/dark values.
