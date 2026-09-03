# Actions And Triggers

Output path: `components/actions-triggers.md`

## Actions Covered

- Primary, secondary, tertiary, ghost, destructive, disabled, icon, and floating action buttons.
- Links and button groups.
- Trigger hierarchy and action risk.


## User Or Maker Problem

- Provide unambiguous actions and navigation while preserving the language's sparse field, binary hierarchy, and visible causal feedback. Buttons perform actions; links navigate. A trigger must not masquerade as the other merely to obtain a visual style.

## Anatomy And Boundaries

| Component or module | Anatomy | Boundary | Related component |
| --- | --- | --- | --- |
| Button | container, live label, optional leading/trailing icon, focus outline, processing node | owns press/disabled/loading state; does not own confirmation copy or page navigation | status field, dialog |
| Link | live text, optional direction/external icon, underline or path cue, focus outline | owns navigation intent; does not submit or mutate | navigation item, breadcrumb |
| Icon button | target, familiar icon, accessible name, tooltip when helpful | limited to established actions in repeated contexts; abstract concepts need visible labels | toolbar, button |
| Button group | labelled group, related actions, stable order | groups peer actions; does not hide consequence hierarchy | segmented control, menu |

## Variants

| Variant | Purpose | Visual difference | Behavioral difference |
| --- | --- | --- | --- |
| Primary | one main action in a region | inverse field, strong label, square/4px turn | may show causal node/path after press |
| Secondary | available alternative | transparent field, one-pixel boundary | same action behavior, lower visual priority |
| Tertiary/ghost | low-emphasis local action | text plus underline/path cue | cannot be sole high-consequence action |
| Destructive | action with material removal | double boundary plus explicit consequence label; no required red | confirmation/recovery proportional to consequence |
| Icon | compact repeated utility | familiar icon in target, no decorative frame unless selected | tooltip/accessibility name required |

## States

| State | Visual behavior | Interaction behavior | Content behavior |
| --- | --- | --- | --- |
| Default | stable field/boundary, open endpoint where causal feedback is available | ready | specific verb + object |
| Hover/focus | hover strengthens rule; focus adds independent 2px outline | Enter/Space activates buttons; Enter follows links | label does not jump or change |
| Active/pressed | compact inversion or node closes for 90ms | action accepted locally once | retain original verb until operation state is known |
| Disabled | recessive but readable, no pointer response | removed from activation; native disabled semantics | reason appears nearby when non-obvious |
| Loading | labelled current node/path, fixed control width | suppress duplicate activation; allow safe cancel where supported | present-tense operation and determinate value when real |
| Error | persistent double rule/hatch linked to status region | focus remains logical; recovery action becomes available | state failure scope; never replace label with “Error” alone |

## Content And Naming Rules

- Labels use a specific active verb and object: “Inspect details,” “Run operation,” “Copy value.” Links describe destination, not “Click here.”
- Keep visible labels stable across loading to avoid layout shift; add status adjacent or through `aria-describedby`.
- Reserve at least 35% expansion and permit wrapping to two lines on mobile. Do not compress tracking below legibility.

## Token Dependencies

| Part | Required token | Override boundary |
| --- | --- | --- |
| Primary field | `semantic.action.primary` | may invert as whole; no local hue/shadow |
| Label/icon | `semantic.text.on-signal` or `semantic.text.primary` | icon uses `currentColor` |
| Boundary | `semantic.border.structure` | destructive/current may select assertive semantic rule |
| Focus | `semantic.border.focus` | cannot be disabled or merged with hover |
| Motion | `semantic.motion.response`, `semantic.motion.transition` | reduced mode renders final state immediately |

## Accessibility And Localization

- Use native `button` and `a` semantics. Maintain 44px touch targets, 32px compact pointer targets, 8px between targets, and visible `:focus-visible`.
- Announce loading/result in an associated status region, not by changing the accessible name repeatedly. Icon buttons require names.
- Ensure 4.5:1 label contrast and 3:1 focus/boundary contrast. Do not rely on inversion or motion alone.

## Code And API Contract

- Recommended API: `variant`, `size`, `disabled`, `loading`, `icon`, `children`, `type`, `href`, `target`, `onPress`, `aria-describedby`. Prevent invalid link/button prop combinations.
- Expose `data-state="idle|pressed|loading|error|complete"`. Do not expose styling props for raw colour, radius, shadow, or duration.

## Examples And Anti-Patterns

- Do: one “Run analysis” primary Button, one “Review input” secondary Button, and a separate “Documentation” Link.
- Avoid: “GO,” unlabeled abstract icon buttons, disabled controls with no reason, a link styled as destructive action, three equal primaries, pill buttons, bounce, glow, or a loading spinner that erases the label.

## Related Patterns

- `patterns/behavioral-states.md`, `components/feedback-status.md`, `components/navigation-wayfinding.md`, and `accessibility/keyboard-focus-motion.md`.
