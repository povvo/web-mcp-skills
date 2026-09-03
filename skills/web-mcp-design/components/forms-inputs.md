# Forms And Inputs

Output path: `components/forms-inputs.md`

## Inputs Covered

- Text fields, text areas, search fields, checkboxes, radio buttons, toggles, switches.
- Selects, dropdowns, comboboxes, autocomplete, date pickers, file uploaders.
- Validation, helper text, error recovery.


## User Or Maker Problem

- Let users enter, choose, validate, and recover structured information in a visually exact system. Fields remain recognizably native in behavior while adopting square geometry, measured labels, and redundant monochrome states.

## Anatomy And Boundaries

| Component or module | Anatomy | Boundary | Related component |
| --- | --- | --- | --- |
| Text field/area | visible label, control, optional prefix/suffix, helper, count, error | owns one value and local validation; not form submission | form group, status |
| Choice control | native checkbox/radio/switch, visible label, optional help | owns a boolean or single/multiple choice | fieldset, segmented choice |
| Combobox | input, popup list, active option, clear control, status | owns filtering/selection and keyboard model | listbox, text field |
| File input | native picker/drop target, accepted formats, queue, progress/error | owns selection and upload status; not downstream processing | progress route, status field |

## Variants

| Variant | Purpose | Visual difference | Behavioral difference |
| --- | --- | --- | --- |
| Standard | ordinary text/value | one-pixel square field | native editing and validation |
| Dense | data-table/filter context | compact vertical inset, same readable type | pointer-first but full keyboard and target support |
| Code/data | IDs, JSON, URLs, headers | tabular alignment, optional line numbers | copy affordance; no syntax colour dependency |
| Search | filters a current collection | leading search icon and result count | Escape clears/closes according to context |

## States

| State | Visual behavior | Interaction behavior | Content behavior |
| --- | --- | --- | --- |
| Default | canvas field, structural boundary, persistent label | editable/selectable | help states format or consequence |
| Hover/focus | hover strengthens edge; focus adds 2px independent outline | standard keyboard behavior | label never floats or disappears |
| Active/pressed | choice node fills or option region inverts | one input event per action | selected value remains readable |
| Disabled | recessive boundary and text, no hover | native disabled semantics | explain reason when useful; use readonly for selectable data |
| Loading | adjacent labelled progress node; value remains visible | prevent conflicting edit only when necessary | name the operation, never fake percent |
| Error | double boundary/hatch plus persistent linked message | preserve value; focus first invalid field on submit only | name problem and repair, not “Invalid” alone |

## Content And Naming Rules

- Every field has a visible label; placeholder text is an example, never the label. Required/optional status is explicit and consistent.
- Helper text states format before entry. Validation runs on submit or after meaningful interaction, not on each keystroke for incomplete values.
- Error recovery preserves all valid and invalid input, identifies scope, and supplies a concrete correction. Reserve 35% expansion for localized labels.

## Token Dependencies

| Part | Required token | Override boundary |
| --- | --- | --- |
| Field | `semantic.surface.canvas`, `semantic.border.structure` | no shadow, unsupported hue, or pill radius |
| Label/value | `semantic.text.primary` | recessive only for optional metadata |
| Focus | `semantic.border.focus` | independent from error and hover |
| Error | `semantic.state.error` | geometry + message + programmatic invalid state |
| Selected choice | `semantic.state.current` | fill/inversion must preserve label contrast |

## Accessibility And Localization

- Use native controls where possible. Associate labels, help, errors, fieldsets, and legends programmatically. Follow established combobox/listbox keyboard patterns.
- Maintain 44px touch targets, visible focus, 4.5:1 text contrast, 3:1 boundaries where needed, zoom/reflow, browser autofill, password managers, and font scaling.
- Announce async validation/status without stealing focus. Reduced motion renders selection/progress state immediately.

## Code And API Contract

- Shared API: `name`, `label`, `value/defaultValue`, `required`, `disabled`, `readOnly`, `description`, `error`, `onChange`, `onBlur`. Complex fields add documented native-equivalent properties.
- Do not expose raw style props for colour/radius. Distinguish invalid, pending validation, uploading, and processing.

## Examples And Anti-Patterns

- Do: a labelled “Project name” field with format help, preserved value, inline repair message, and “Create project” action.
- Avoid: placeholder-only Fields, colour-only Validation, clearing input after failure, custom keyboard-hostile selects, immediate red error while typing, drag-only upload, tiny toggles, floating labels, or disabled text that cannot be copied.

## Related Patterns

- `patterns/behavioral-states.md`, `components/actions-triggers.md`, `components/feedback-status.md`, and `accessibility/accessibility-matrix.md`.
