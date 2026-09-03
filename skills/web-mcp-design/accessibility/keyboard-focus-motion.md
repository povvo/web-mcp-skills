# Keyboard, Focus, And Motion

Output path: `accessibility/keyboard-focus-motion.md`

## Keyboard And Focus Contract

| Element family | Focus order | Focus visual | Keyboard behavior | Escape/recovery |
| --- | --- | --- | --- | --- |
| Page/landmarks | DOM reading/task order; skip link first | 2px strong outline on skip target and focused controls | Tab/Shift+Tab traverse interactive elements; headings/landmarks support assistive navigation | browser back/history remains valid; skip link bypasses repeated chrome |
| Buttons and links | visual order equals DOM order | independent 2px offset path/rectangle, never hover-only | Enter activates links/buttons; Space activates buttons per native behavior | action-specific undo/recovery; no Escape behavior for ordinary controls |
| Forms | label, control, help/error relationship remains logical | field outline plus unhidden caret/selection | native editing; groups use fieldset/legend; combobox/listbox follows established key model | Escape closes popup/reverts transient suggestion, not committed value without warning |
| Tabs/menus/disclosures | trigger before owned content | focused item outlined; selected/current remains separately filled/inverted | arrow-key roving where platform pattern requires; Home/End when established; Enter/Space activate | Escape closes menu/disclosure layer and restores Focus to trigger |
| Data table/list | actions follow row content; avoid every cell in tab order | focused actionable cell/row gets visible outline without hiding selection | semantic table browsing; sorting/filtering controls keyboard accessible | restore prior stable sort/filter/selection on failed mutation where possible |
| Modal/dialog | trigger to first meaningful control or heading; focus contained while open | high-contrast outline inside opaque shell | Tab cycles inside; initial focus reflects purpose/consequence | Escape closes only when safe; on close return to trigger or logical successor |
| Drag/drop | source, move controls, destinations in task order | source and valid destination have independent focus/state outlines | keyboard move/upload alternative required | cancel returns item and focus to source; announce result |

## Motion Accessibility

- Reduced motion replacement: line traces become fully visible paths, translations become immediate placement, halftone thresholds become a static final image, stagger becomes simultaneous reveal, and inversion switches without interpolation.
- Motion duration limits: direct response 80-160ms, ordinary structural transition 180-320ms, routine action ceiling 500ms. User-controlled media and necessary instructional animation require separate controls.
- Forbid parallax, scroll-linked scale, full-screen zoom, repeated shake, cursor followers, flicker, rapid inversion, and any flash pattern that approaches seizure-risk thresholds. Avoid large white flashes in dark mode.
- Non-motion state cues: open/filled/double/stop node, one/two-pixel boundary, hatch, stable path, visible label, count/percentage when real, and programmatic state.

## Focus Rules

Focus can coexist with selected, current, error, loading, or disabled-adjacent states and must remain visually independent. Do not move Focus when live content updates unless the user's task requires entering a new managed context. Keep focused items unobscured by sticky bars and overlays; scroll with space around the indicator. Decorative giant type, rails, grain, and halftone are never focusable.

## Keyboard Validation

Test forward/reverse traversal, activation, cancellation, error recovery, retry/resume, overlays, responsive navigation, dynamic insertion/removal, and 200-400% zoom using keyboard only. Then test a screen reader because a plausible tab order does not prove names, roles, states, or relationships.

## Anti-Patterns

- `outline: none`; focus identical to hover; DOM order changed to match a dramatic visual crop; tabindex values above zero; keyboard trap; icon button without name; drag-only interaction; status update stealing focus; Reduced motion implemented by hiding content; or a path animation required to understand direction/state.
