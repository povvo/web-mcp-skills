# Token Transforms

Output path: `tokens/token-transforms.md`

## Transform Pipeline

| Input token | Transform | Output artifact | Consumer | Constraint |
| --- | --- | --- | --- | --- |
| primitive token JSON | validate `$type`, `$value`, description, and raw unit | normalized primitive graph | all downstream builds | reject unknown types and stringified numbers |
| global token references | resolve one hop to primitives while preserving reference metadata | normalized global graph | alias build | no cycles or missing references |
| alias token + selected colour mode | resolve polarity, raised surface, and ink branches | mode-specific alias graph | semantic build | light/dark/high-contrast branch must be explicit |
| semantic token references | kebab-case intent path | CSS custom properties | web application | emit `--wmd-*`; never expose primitive names to components |
| semantic duration + reduced-motion mode | replace causal duration with `0ms`, retain final-state rule metadata | reduced-motion CSS/media block | web application | no transition may be required to understand state |
| semantic colour + forced-colours mode | map to `Canvas`, `CanvasText`, `Highlight`, or `GrayText` | `forced-colors` overrides | web application | preserve geometry, labels, and focus; remove grain |
| dimension in rem | multiply by user/root scale only at runtime | CSS rem | web text/layout | do not bake 16px assumption into accessibility scaling |
| touch target semantic | choose 44 CSS px/pt or 48dp by platform | platform dimension artifact | control library | semantic minimum wins over compact layout |
| font family token | quote and escape family, append system mono fallbacks | CSS/Swift/Android/RN font artifact | typography layer | bundled font files require separate rights/custody check |
| cubic-bezier token | serialize platform-native timing function | CSS/Swift/Compose/RN motion artifact | motion layer | approximate only when platform lacks exact curve; document delta |
| path/node geometry metadata | round strokes/positions to device pixel grid | SVG or native vector constants | diagram/icon layer | do not alter semantic node topology |
| media focal point and ratio | emit object-position/crop metadata | responsive media artifact | media component | never infer a focal point from filename or aspect ratio |

## Transform Requirements

- Canonical Input uses W3C Design Tokens-style `$type`, `$value`, `$description`, and reference syntax where practical.
- CSS Output emits documented variables by semantic and component path, plus mode blocks for user preference and explicit data attributes.
- Platform artifacts preserve semantic names even when Swift, Android, or React Native casing changes.
- Expand mode before resolving semantics; expand platform after semantic resolution; apply density and reduced-motion adaptations last.
- Normalize paths to lowercase kebab-case in CSS, lower camel case in Swift/Kotlin/JavaScript, and preserve a machine-readable mapping file.
- Convert units by category. Colour conversion must be gamut-checked; typography respects platform scaling; hairlines and touch targets use physical/semantic rules rather than arithmetic.

## Failure Contract

The transform fails on cycles, unresolved references, a component-to-primitive edge, missing mode branches, unsupported colour gamut, invalid unit/type combinations, or duplicate output names. Warnings are permitted for platform curve approximation and display-font metric drift, but builds must surface them with the affected token path.

## Anti-Patterns

- Regex-only reference replacement, flattening away type/provenance, silent fallback to default mode, values rounded before platform selection, primitive CSS variables consumed by components, non-deterministic output order, unchecked font-file copying, and minified artifacts without a readable mapping or validation report.
