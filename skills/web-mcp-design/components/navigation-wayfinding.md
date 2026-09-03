# Navigation And Wayfinding

Output path: `components/navigation-wayfinding.md`

## Navigation Covered

- Headers, navigation bars, app bars, side navigation, menus.
- Breadcrumbs, tabs, accordions, pagination, footers.
- Wayfinding, platform navigation, responsive behavior.


## User Or Maker Problem

- Keep users oriented across pages, regions, and task depth without converting every route into a decorative network map. Wayfinding uses labels first and reserves the node/path grammar for current location, sequence, or inspectable relationships.

## Anatomy And Boundaries

| Component or module | Anatomy | Boundary | Related component |
| --- | --- | --- | --- |
| Global header | product name, primary destinations, utility actions, current cue | owns top-level location; not task progress | menu, account utilities |
| Side navigation | section label, links, current node/path, optional collapse | owns sibling destinations; not arbitrary actions | disclosure, tooltip |
| Breadcrumb | ordered ancestor links, current page | owns hierarchy; never replaces the page heading | heading, link |
| Tabs | labelled peer views and active panel | owns in-page view selection; not multi-step completion | tablist/panel |
| Pagination | current page, nearby pages, previous/next | owns result-page position; not content filtering | result count, status |

## Variants

| Variant | Purpose | Visual difference | Behavioral difference |
| --- | --- | --- | --- |
| Editorial header | sparse marketing/docs entry | product word, edge metadata, minimal links | may collapse into labelled menu |
| Application rail | persistent section/task navigation | vertical rule and current filled node | resizable/collapsible only with preserved labels |
| Compact tabs | dense inspector views | horizontal path with active closed node | arrow-key roving focus where platform pattern expects it |
| Breadcrumb | deep hierarchy | micro label scale and separators | first items may collapse into accessible menu on mobile |

## States

| State | Visual behavior | Interaction behavior | Content behavior |
| --- | --- | --- | --- |
| Default | text and quiet rule/open node | follows native link/tab/menu behavior | concise destination noun |
| Hover/focus | hover strengthens underline/rule; focus gets independent 2px outline | keyboard activation and expected arrow keys | label stays stable |
| Active/pressed | compact inversion during activation | one navigation event | no premature current-state change |
| Disabled | use rarely; recessive with reason | unavailable and noninteractive | prefer hiding impossible destinations only when discoverability is not harmed |
| Loading | old location remains until new context is viable; local route label processes | allow safe cancellation/back behavior | state destination being opened |
| Error | retain prior viable location plus persistent route failure | recovery action and URL/history remain coherent | name failed destination and retry scope |

## Content And Naming Rules

- Use destination nouns users recognize. Current labels match page/view headings. Avoid protocol jargon in primary navigation unless the audience uses it.
- Keep visible labels for abstract nodes. Reserve uppercase microtype for group labels, not every link. Support 35% expansion and two-line items where needed.

## Token Dependencies

| Part | Required token | Override boundary |
| --- | --- | --- |
| Shell | `semantic.surface.canvas` | may become opaque overlay on mobile, never glass |
| Link | `semantic.text.primary` | underline/path cue required where link identity is ambiguous |
| Current cue | `semantic.state.current` | must pair with `aria-current` or selected semantics |
| Structure | `semantic.border.structure` | node/path only when it communicates relation |
| Focus | `semantic.border.focus` | always distinct from current and hover |

## Accessibility And Localization

- Provide skip links and landmarks. Preserve logical focus/DOM order when visual rails rotate or reposition labels.
- Follow platform Navigation conventions: native back/history, tab keyboard behavior, menu dismissal, touch targets, and focus restoration after overlays close.
- Current location is exposed programmatically and visually. Responsive collapse retains all destinations and names; it does not create icon-only mystery navigation.

## Code And API Contract

- Shared items expose `id`, `label`, `href`, `current`, `disabled`, optional `icon`, and children. Tabs expose controlled selection and stable panel IDs.
- Unsupported: raw path geometry props, decorative pseudo-coordinates, multiple current items, links without destinations, and router state inferred from label text.

## Examples And Anti-Patterns

- Do: `WEB MCP / OVERVIEW / DETAILS`, with the current destination marked by a filled node and `aria-current="page"`.
- Avoid: every destination as an unlabeled dot, a hamburger on wide screens without need, vertical text in the reading order, navigation that animates for longer than content load, custom back behavior, or copied browser chrome.

## Related Patterns

- `patterns/domain-platform-patterns.md`, `patterns/behavioral-states.md`, `components/actions-triggers.md`, and `accessibility/keyboard-focus-motion.md`.
