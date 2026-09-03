# Platform Tokens

Output path: `tokens/platform-tokens.md`

## Platform Artifact Output Matrix

| Token | Web/CSS | iOS | Android | React Native | Notes |
| --- | --- | --- | --- | --- | --- |
| `semantic.surface.canvas` | `--surface-canvas` | `Color.surfaceCanvas` | `colorSurfaceCanvas` | `tokens.color.surfaceCanvas` | resolve modes natively; forced colours remain a web artifact |
| `semantic.text.primary` | `--text-primary` | `Color.textPrimary` | `colorTextPrimary` | `tokens.color.textPrimary` | verify platform rendering, not just shared hex |
| `semantic.border.focus` | `--focus-ring` + CSS outline | SwiftUI focus effect / custom 2pt outline | Compose focus indication, minimum 2dp | platform focus prop + 2px/dp outline | preserve keyboard/TV focus conventions |
| `global.type.family` | `"JetBrains Mono"` via `@font-face` | bundled `JetBrainsMono` font | bundled `jetbrains_mono` resource | linked asset `JetBrainsMono` | confirm redistribution and weight files before bundling |
| `global.type.body` | rem clamp | Dynamic Type text style with 16pt floor | 16sp with font scaling | 16 logical px with font scaling | platform accessibility scaling overrides fixed rhythm |
| `global.type.display` | viewport clamp | geometry-aware 64-180pt cap | responsive 64-180sp cap | width-derived 64-180 | decorative anchor may shrink before wrapping essential copy |
| `alias.edge.safe` | CSS clamp + safe-area env | layout margins + safe-area inset | window insets + 16-72dp | safe-area context + responsive inset | never hide focus/controls under system chrome |
| `target.touch` | 44 CSS px minimum | 44pt minimum | prefer 48dp, never below 44dp equivalent | platform-select 44/48 | visual mark stays 16-24 units |
| `global.stroke.structure` | 1 CSS px snapped | 1 physical-pixel-aware point where supported | 1dp or hairline with density validation | `StyleSheet.hairlineWidth` after visual test | avoid vanishing lines at scaling boundaries |
| `semantic.motion.transition` | 240ms CSS/WAAPI | 0.24s ease | 240ms tween | 240ms timing | platform Reduce Motion/animation scale overrides |
| `texture.halftone.signal` | SVG/CSS/canvas asset | pre-rendered or Metal/Core Image only if justified | pre-rendered or shader only if justified | pre-rendered asset preferred | deterministic output and performance first |

## Platform Rules

- Preserve semantic intent across platform naming differences; generated artifacts should expose the same stable token path even when the host API differs.
- Transform CSS pixels/rem to points, dp/sp, or logical pixels by purpose. Do not perform blind numeric conversion for hairlines, touch targets, safe areas, or scaled type.
- JetBrains Mono metrics and weight rendering differ across engines. Inspect cap height, baseline, `0/O`, punctuation, dark-mode stroke retention, and clipping on each target.
- Keep native navigation, form controls, focus behavior, pointer/gesture semantics, and accessibility scaling visible. Brand coherence does not justify replacing established platform behavior.
- Web is the primary implementation target for this package. Native mappings are equivalence contracts, not claims that native components or font assets have been delivered.

## Transform Rules

The canonical design-token artifact should preserve type and reference metadata. Platform builds resolve aliases after selecting mode, convert units by semantic category, emit source maps or trace metadata, and fail on unresolved references. Round layout dimensions to the platform pixel grid; do not round duration or ratios into unrelated integer scales.

## Anti-Patterns

- One JSON value copied into every platform; fixed 16px text that ignores user scaling; 44dp assumed equivalent everywhere; web focus styles forced onto touch/native navigation; unlicensed font binaries committed silently; platform components rebuilt as custom monochrome imitations; and missing platform values silently falling back to primitives.
