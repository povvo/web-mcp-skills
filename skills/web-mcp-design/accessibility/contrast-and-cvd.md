# Contrast And CVD

Output path: `accessibility/contrast-and-cvd.md`

## Contrast System

| Pair | Minimum contrast | Preferred contrast | Use case | Repair |
| --- | --- | --- | --- | --- |
| Primary text / canvas | 4.5:1 ordinary; 3:1 large text | 7:1 for body where halation remains acceptable | body, labels, controls | move to primary ink, increase weight/size, remove texture, or change surface |
| Recessive text / canvas | 4.5:1 when informative | 5:1 | metadata and secondary facts | promote to primary; if purely decorative, hide from accessibility tree |
| Icon / canvas | 3:1 when needed to identify control/state | 4.5:1 | functional icons and state nodes | strengthen ink/stroke and add visible label |
| Control boundary / adjacent colours | 3:1 when boundary is needed to identify component/state | 4.5:1 | fields, unchecked controls, modal edge | use assertive 2px rule or stronger surface separation |
| Focus indicator / adjacent colours | 3:1 | 4.5:1 | all keyboard-focusable elements | use 2px offset strong ink/Highlight; prevent clipping |
| Signal text / inverse surface | 4.5:1 ordinary | 7:1 body | primary action, selected region, overlay | invert complete pair; do not mix mode endpoints |
| Data grid / canvas | no ratio if decorative; 3:1 if required to parse | 3:1 | tables and measurement structure | use spacing/header associations or stronger rule |
| Halftone subject / field | task-specific; essential features must remain distinguishable | direct visual inspection at target scale | media and data preview | use larger cells, clean binary threshold, or provide original/summary |

## CVD-Safe Encoding

- The base system has no hue pairs, so protan, deutan, and tritan CVD do not collapse status categories. Future accents must be tested against these confusion axes and cannot replace current semantics.
- Redundant encoding is mandatory: label + open/filled/double/stop node + boundary/pattern + programmatic state. Inversion alone indicates emphasis but not the reason for it.
- Pending uses open node; current uses filled node plus label; complete uses filled endpoint and stable path; warning uses double open node; error uses stop node with double rule or diagonal hatch; disabled uses operability semantics and explanation.
- In dark mode, control halation with paper-white body text and avoid thin grey essential copy. Strengthen functional hairlines from 1px to 2px when display testing shows loss.
- In high contrast/forced colours, map canvas and ink to system values, focus to `Highlight`, and nonessential grey to `GrayText` only when permitted. Remove grain and preserve state geometry/labels.

## Contrast Procedure

Test computed foreground/background pairs at actual font size and weight in light, dark, signal, selected, error, disabled, hover, focus, and forced-colour states. Include opacity, antialiasing, overlays, texture, and neighboring colours. Automated ratios are the floor; inspect JetBrains Mono on representative Windows, macOS, Android, and iOS displays for stroke retention and bloom.

## Repair Order

First remove nonessential texture/transparency. Then promote semantic ink or strengthen the boundary. Next increase size/weight without distorting hierarchy. Finally alter the surface pair at the semantic token layer. Never solve Contrast by adding an unsupported status hue or by hiding required content.

## CVD Anti-Patterns

- Adding red/green status because the base is monochrome; treating black/white inversion as sufficient status meaning; low-contrast grey labels; pattern cells too fine to distinguish; colour simulation without real target-state testing; and high-contrast mode that discards selected, current, warning, or error labels.
