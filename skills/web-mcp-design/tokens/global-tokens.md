# Global Tokens

Output path: `tokens/global-tokens.md`

## Global Scale Contract

| Token | Scale | Value | Scope | Reference |
| --- | --- | --- | --- | --- |
| `global.color.black` | neutral | `{neutral.0}` | all modes | primitive endpoint |
| `global.color.raised-dark` | neutral | `{neutral.10}` | dark mode surfaces | primitive tonal lift |
| `global.color.graphite` | neutral | `{neutral.28}` | structure and display crop | primitive recessive value |
| `global.color.mid` | neutral | `{neutral.48}` | nonessential structure | contrast-gated primitive |
| `global.color.paper` | neutral | `{neutral.90}` | readable foreground | primitive soft light |
| `global.color.white` | neutral | `{neutral.97}` | light canvas and active signal | primitive endpoint |
| `global.type.family` | family | `{font.family.mono}` | every text role | JetBrains Mono stack |
| `global.type.micro` | fluid type | `clamp(0.6875rem, .65rem + .1vw, .8125rem)` | metadata and captions | 11-13px primitives |
| `global.type.body` | fluid type | `clamp(1rem, .96rem + .2vw, 1.125rem)` | reading and controls | 16-18px primitives |
| `global.type.heading` | fluid type | `clamp(1.75rem, 1rem + 3vw, 4.5rem)` | section headings | hand-tuned optical scale |
| `global.type.display` | fluid type | `clamp(4rem, 16vw, 18rem)` | nonessential display anchor | viewport-relative scale |
| `global.space.inline` | responsive space | `clamp(16px, 4vw, 72px)` | viewport safe edge | `{space.4}` to `{space.18}` |
| `global.space.section` | responsive space | `clamp(48px, 9vw, 144px)` | major vertical rhythm | doubles beyond `{space.18}` at wide screens |
| `global.space.component` | space | `{space.6}` | component groups | 24px primitive |
| `global.shape.square` | radius | `{radius.0}` | panels and signal fields | hard container default |
| `global.shape.turn` | radius | `{radius.2}` | controls and line turns | technical 4px radius |
| `global.stroke.structure` | border | `{stroke.hairline}` | rules, frames, paths | one CSS pixel |
| `global.stroke.emphasis` | border | `{stroke.focus}` | focus and critical boundary | two CSS pixels |
| `global.motion.response` | duration | `{duration.instant}` | press and node response | 90ms primitive |
| `global.motion.transition` | duration | `{duration.path}` | trace and field transition | 240ms primitive |
| `global.grid.columns` | responsive grid | `4 / 8 / 12` | mobile / tablet / desktop | breakpoint-selected count |
| `global.density.quiet` | ratio | `0.25-0.45 occupied` | editorial and default UI | majority negative space |
| `global.density.signal` | ratio | `0.60-0.80 occupied within one bound` | media and diagnostics | local, never viewport-wide |

## Scale Families

- Colour is one six-step neutral ramp; mode aliases choose direction rather than duplicate raw values.
- Type is hand-tuned and fluid. Micro and body preserve legibility; display supplies the radical scale interval.
- Space uses a 4px base with responsive inline and section scopes.
- Shape is square by default, with 2-8px technical turns and true circles for nodes.
- Elevation is tonal only. Motion has response and transition bands, with no spring family.
- Density and grid adapt at approximately 480px and 960px, but content—not device labels—determines the actual breakpoint.

## Reference Discipline

Global tokens may reference primitives only. Semantic tokens may reference globals. Components must never bypass semantic intent to reach this layer. Values that require mode inversion remain aliases rather than hard-coded global duplicates.

## Anti-Patterns

- Adding ad hoc global aliases for one component, turning viewport-relative display sizes into body sizes, exposing raw neutrals directly to components, device-named breakpoints, arbitrary column counts, or using a global “accent” token that introduces unsupported hue.
