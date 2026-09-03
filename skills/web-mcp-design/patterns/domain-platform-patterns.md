# Domain And Platform Patterns

Output path: `patterns/domain-platform-patterns.md`

## Platform Conventions

| Platform | Navigation | Forms | Feedback | Native behavior | Exceptions |
| --- | --- | --- | --- | --- | --- |
| Web | semantic links/buttons, landmarks, URL/history, visible focus, responsive header/rail | native HTML controls first; browser autofill and validation semantics | persistent inline status, polite live regions, accessible dialogs | pointer + keyboard + touch, zoom/reflow, `prefers-*`, forced colours | clipped display type and vertical labels remain decorative and outside reading order |
| iOS | native stacks, tab bars, sheets, back gesture, safe areas | native controls, keyboards, autofill, Dynamic Type | native alert/sheet when behavior matters; in-view labelled geometry for status | 44pt targets, VoiceOver order, Reduce Motion, haptics by preference | preserve path/node semantics without replacing familiar navigation icons |
| Android | native app bars, back handling, navigation rail/bar, insets | Material/Compose control behavior with visual tokens adapted | snackbar/dialog conventions plus durable in-view status | prefer 48dp targets, TalkBack, font scaling, animation scale | square/monochrome styling cannot remove native affordance or ripple without replacement |
| Windows | title/app bars, command patterns, keyboard accelerators, visible selection | native text/input behavior, high contrast, scaling | InfoBar/dialog patterns or equivalent with durable result | keyboard-first, Narrator, forced colours/high contrast, pointer density | compact mode keeps at least 32px pointer targets and clear focus |
| React Native | host-platform navigation rather than web imitation | native-backed controls and keyboard management | host-equivalent alerts/status plus accessible announcements | Platform selection for target, focus, motion, and safe area | parity is semantic; avoid one identical geometry implementation that breaks host behavior |

## Domain Patterns

| Domain | Module | Vocabulary | Constraint | Example |
| --- | --- | --- | --- | --- |
| Unspecified product | Domain Shell | supplied by the actual product model | the package name contributes no product semantics | compose verified objects, operations, evidence, and result records only when real data exists |
| E-commerce | not prescribed | none extracted | do not infer catalogue, basket, checkout, price, inventory, or order states | requires a separate product brief before applying the visual language |
| Education | not prescribed | none extracted | do not infer course, lesson, learner, grade, or progress semantics | requires a separate product brief |
| Finance | not prescribed | none extracted | do not infer balances, markets, transactions, performance, or risk | requires a separate product brief and data contract |
| Cooking | not prescribed | none extracted | do not infer recipe, ingredient, timer, nutrition, or serving units | requires a separate product brief |
| Service journey | not prescribed | none extracted | do not infer stages, appointments, cases, agents, or omnichannel handoff | requires a separate service blueprint |

## Cross-Platform Coherence

- Preserve JetBrains Mono where deliverable, neutral polarity, state redundancy, quiet/signal density, original path/node grammar, factual copy, and one bounded rupture.
- Adapt navigation, form controls, focus, target size, safe areas, font scaling, overlays, feedback channels, motion settings, and back/escape behavior to the host Platform.
- Never flatten native semantics into web-style div controls or flatten the visual language into a generic host theme. Semantic equivalence matters more than pixel identity.

## Domain Gate

Before selecting a Domain Module, obtain the real domain nouns, object schema, state machine, actions, consequences, evidence source, localization needs, and platform surface. Until those exist, use generic content blocks only and show the name “Web MCP” solely where a product/brand name belongs.

## Anti-Patterns

- Inferring browser tabs, servers, protocol diagrams, or developer tools from “Web MCP”; importing domain colour/status conventions without a brief; custom controls that fight native behavior; ignoring Dynamic Type/font scaling; 44px copied as 44dp everywhere; web modal behavior on mobile; and claiming cross-platform readiness from one web screenshot.
