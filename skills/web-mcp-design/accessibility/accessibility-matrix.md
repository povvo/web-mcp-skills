# Accessibility Matrix

Output path: `accessibility/accessibility-matrix.md`

## Accessibility Requirements Matrix

| Criterion | Threshold or requirement | Design rule | Token/component implication |
| --- | --- | --- | --- |
| Ordinary text contrast | WCAG 2.2 AA: at least 4.5:1; large text at least 3:1 | use primary ink for required copy; recessive values need measured proof at actual size/weight | semantic text pairs validated in every mode |
| Non-text contrast | at least 3:1 for essential control boundaries, icons, state, and focus against adjacent colours | one-pixel decoration may disappear; functional paths/nodes strengthen to two pixels where necessary | focus/state semantics use assertive stroke and redundant label |
| Colour vision deficiency | no meaning by hue alone; test protan, deutan, and tritan confusions if future hue is introduced | current system uses lightness, open/filled/double node, hatch, boundary, and text | status tokens contain geometry/pattern/copy, not colour names |
| Keyboard | all functionality operable without pointer; logical sequence; no trap except managed modal | native controls first; disclosure, tabs, menus, drag/drop, and dialogs follow established keyboard models | component API exposes focus/keyboard state and alternatives |
| Focus | visible, unobscured, distinct from hover/selected; target contrast at least 3:1 | 2px offset path/outline; maintain under inversion, error, high contrast, and zoom | `semantic.border.focus` cannot be overridden away |
| Motion | honor `prefers-reduced-motion`/platform setting; avoid flashing above accessibility thresholds | replace traces/translations with immediate final path, label, node, and inversion | mode transform resolves causal motion to 0ms with state intact |
| Touch target | design target 44x44 CSS px/pt; prefer 48dp on Android; pointer compact minimum 32px | visible icon may be 16-24px inside the larger target; keep 8px between adjacent targets | platform target token selects host-appropriate value |
| Text sizing and reflow | body floor 16 CSS px; metadata floor 11px; support 200% text zoom and 400% reflow where applicable | display crop shrinks/removes before essential text; no horizontal scroll except intrinsically wide data regions | fluid type/space tokens and responsive component rules |
| Cognitive load | one dominant action, one signal region, stable labels, explicit state/recovery | preserve quiet field; do not add fake data, duplicate status, or unexpected focus movement | quiet/signal density and feedback contracts |
| Copy and labels | visible labels for fields and abstract icons; plain-language errors with recovery | uppercase only for micro metadata; live text instead of text in images | voice rules and component content contracts |
| Media alternatives | meaningful images have purpose-focused alt; charts/diagrams have summaries/data; texture is hidden | preserve truthful non-halftoned alternative where transformation loses essential evidence | media component accepts alt/summary and decorative flag |
| Live status | announce necessary asynchronous change without repetition or focus theft | `status` for polite updates, `alert` only for urgent events; durable visual record remains | feedback component owns live-region policy |
| High contrast | system colours and semantics survive forced-colours mode | remove grain/recessive decoration; retain outlines, labels, open/filled state, and hatches | mode tokens map to Canvas/CanvasText/Highlight |

## Compliance Frame

Use WCAG 2.2 AA as the web floor, then test actual content, browsers, zoom, operating-system modes, and assistive technology. Structural conformance does not prove usability: perform keyboard, screen-reader, high-contrast, reduced-motion, and visual inspection on representative pages and components.

## Ownership Of Gaps

Sound, haptic, voice control, native font delivery, complex charts, and domain-specific cognitive requirements are not established by the visual corpus. Implementations must define and test them for the target platform rather than assuming silence equals coverage.
