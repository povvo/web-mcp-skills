# Content And Data Display

Output path: `components/content-data-display.md`

## Display Covered

- Cards, recipe cards, content cards, product cards, event items, list items.
- Tables, charts, graphs, badges, chips, tags, avatars, panels, widgets.
- Dense grids, selectable tiles, thumbnails, market data fields.


## User Or Maker Problem

- Present content and structured data so users can scan, compare, inspect, and act without turning the canvas into a generic Cards dashboard. Hierarchy comes from alignment, type scale, rules, and selective inversion.

## Anatomy And Boundaries

| Component or module | Anatomy | Boundary | Related component |
| --- | --- | --- | --- |
| Content block | heading, metadata rail, body/media, optional actions | owns one editorial unit; not automatically a card | media, action group |
| List row | primary label, secondary facts, state node, action/destination | owns one comparable record | list, navigation item |
| Data table | caption, headers, rows/cells, sort/filter state, summary | owns multidimensional comparison | pagination, filter form |
| Inspector panel | object title, state, key/value groups, raw/copy action | owns detail for one selected object | split view, domain module |
| Signal preview | bounded image/chart/output, label, alt/summary | owns one dense visual region | media, status |

## Variants

| Variant | Purpose | Visual difference | Behavioral difference |
| --- | --- | --- | --- |
| Quiet editorial | reading and narrative | no outer card; generous space and one rule | mostly static |
| Dense table | comparison/operations | compact rows, tabular figures, low-priority grid | sortable/selectable with full keyboard support |
| Selectable tile | spatial selection | square frame; selected region inverts | whole tile may be one control if semantics are singular |
| Raw data | exact structured payload | JetBrains Mono, line wrapping/scroll, copy action | preserve syntax in text; no colour-only highlighting |

## States

| State | Visual behavior | Interaction behavior | Content behavior |
| --- | --- | --- | --- |
| Default | quiet rules and primary/recessive text | readable; only real actions respond | labels and values distinguish type/units |
| Hover/focus | row/tile boundary strengthens; focused action gets 2px outline | keyboard/pointer behavior follows component semantics | no hidden essential actions |
| Active/pressed | selected row/tile inverts as a complete region | selection and activation remain distinct | selected state labelled programmatically |
| Disabled | applicable only to contained actions, not data | data remains readable/copyable | reason shown for unavailable action |
| Loading | preserve dimensions; show labelled region or row-level progress | stale data labelled if retained | no fake skeleton values |
| Error | bounded status replaces only failed region | retry/inspect available | partial data remains and is labelled |

## Content And Naming Rules

- Use real labels, units, timestamps, record IDs, and counts. Align numeric values with tabular figures and decimals where comparison matters.
- Truncate only with a discoverable full value and copy affordance. Keep exact identifiers unlocalized; localize dates/numbers while preserving machine values when useful.
- Badges/chips are rare compact states or filters, not decoration. Avoid pill shape; use short labels and square/4px boundaries.

## Token Dependencies

| Part | Required token | Override boundary |
| --- | --- | --- |
| Canvas/row | semantic surface tokens | no shadowed card stack |
| Values | `semantic.text.primary` | recessive style only for supplementary facts |
| Grid | `semantic.data.grid` | never visually stronger than data |
| Selected | `semantic.surface.signal`, `semantic.text.on-signal` | invert complete region and retain focus |
| State | semantic state family | geometry/copy required |

## Accessibility And Localization

- Use semantic lists/tables/headings. Provide captions, header associations, sort state, summaries/alternatives for charts, and logical DOM order independent of visual rotation.
- Keep horizontal table scrolling inside a labelled region with sticky headers only when they do not obscure focus. Support zoom/reflow and screen-reader browsing.
- Interactive rows require one clear activation model; avoid nested click targets. Density never reduces target or text minimums.

## Code And API Contract

- Data modules accept typed columns/fields, rows/items, state, selection, sort, pagination, render slots, and accessible labels. Raw values and formatted values remain distinct.
- Unsupported: style-by-hex, arbitrary card elevation, DOM-order changes for visual masonry, and charts with no data/summary contract.

## Examples And Anti-Patterns

- Do: a quiet record list beside one selected inverse inspector and one bounded halftone evidence preview.
- Avoid: Cards around every paragraph, dense gridlines, tiny grey data, status colour dots without labels, animated charts by default, fake coordinates, clipped identifiers, hover-only actions, or multiple competing signal panels.

## Related Patterns

- `patterns/perceptual-patterns.md`, `components/domain-modules.md`, `foundations/spatial-grammar.md`, and `accessibility/contrast-and-cvd.md`.
