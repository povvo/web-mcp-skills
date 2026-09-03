# Declarative forms

Read this reference only under the `webmcp-declarative` experimental compatibility profile when creating or enhancing a semantic HTML form, comparing form and imperative approaches, or debugging target-specific registration, focus, submit, or cancellation behavior.

## Compatibility status

In the supplied WebMCP draft, the normative declarative section and schema-synthesis/execute algorithms are still incomplete. A browser may nevertheless implement an experimental declarative API.

Therefore:

- verify the exact target browser and documentation date;
- treat attributes, events, and pseudo-classes below as a named browser branch;
- preserve native form behavior as the fallback;
- do not claim portable declarative conformance from one browser demo.

Imperative `document.modelContext.registerTool()` remains the current production-oriented document baseline for JavaScript actions, subject to target support.

## When a form is a good tool

Choose declarative enhancement when the application has, or CREATE mode first implements:

- a real `<form>`;
- correctly associated labels;
- named controls;
- native or application validation;
- a meaningful submit action;
- visible focus and review;
- a human workflow that remains useful without an agent.

Examples:

- search/filter forms;
- support requests;
- reservation requests;
- application forms;
- order lookup;
- a human-reviewed “prepare and submit” flow.

Do not create a fake form solely to avoid writing a proper imperative adapter for a map, canvas, editor command, store action, or multi-state workflow.

## Browser-specific attribute model

A currently documented implementation uses:

```html
<form
  toolname="createSupportRequest"
  tooldescription="Submit a support request for the current signed-in customer.">
  ...
</form>
```

Removing either `toolname` or `tooldescription` unregisters the form tool in that implementation.

Fields become schema properties primarily through their `name`. Parameter descriptions may come from:

1. `toolparamdescription`;
2. the associated `<label>`;
3. an accessibility description, depending on implementation.

Example:

```html
<label for="support-team">Support area</label>
<select
  id="support-team"
  name="team"
  required
  toolparamdescription="Routes the request to the responsible support team.">
  <option value="returns">Returns</option>
  <option value="delivery">Delivery</option>
  <option value="website">Website help</option>
</select>
```

Use semantic values such as `delivery`, not visual indexes such as `option-2`.

## Form semantics are the contract

Before adding tool attributes, audit:

- every submitted control has a stable `name`;
- labels are programmatically associated;
- required state matches business requirements;
- option values are meaningful;
- disabled/hidden controls behave as intended;
- conditional fields expose and hide predictably;
- native constraints are not the only server validation;
- the submit button label describes the actual effect;
- the form's action or submit handler is authoritative;
- errors are visible and associated with fields;
- keyboard, screen-reader, and focus behavior remain correct.

A synthesized schema cannot repair an inaccessible or ambiguous form.

## Execution versus preparation

The form can support two interaction models.

### Human completes submission

The agent focuses and fills the form. The user reviews and presses Submit.

Use this for:

- purchases;
- external communication;
- destructive or permission-changing actions;
- legally or financially meaningful submissions;
- workflows where visual review is a product requirement.

Describe the tool as preparation:

```text
prepare_support_request
Fill the visible support-request form with the supplied details for user review.
Does not submit the request.
```

Do not call it `submit_support_request` when it stops before submit.

### Agent-triggered submission

A target browser may support a `toolautosubmit` attribute:

```html
<form
  toolname="search_catalog"
  tooldescription="Search the visible catalog using the supplied query."
  toolautosubmit>
```

Use auto-submit only when the normal action is safe to execute without an additional review step and the site's existing policy allows it.

Auto-submit is not permission to bypass confirmations. It should enter the same submit path as a human action.

## SubmitEvent integration

A currently documented browser branch adds:

- `SubmitEvent.agentInvoked` — whether the submit was agent-triggered;
- `SubmitEvent.respondWith(Promise)` — supplies a result to the invoking agent after `preventDefault()`.

Pattern:

```js
form.addEventListener("submit", (event) => {
  event.preventDefault();

  const operation = submitThroughExistingAction(
    new FormData(form),
    { source: event.agentInvoked ? "agent" : "human" },
  );

  if (event.agentInvoked) {
    event.respondWith(operation.then((result) => ({
      status: "submitted",
      requestId: result.id,
      visible: true,
    })));
  }
});
```

Rules:

- keep one authoritative submit action;
- validate on client and server as already required;
- do not branch into weaker validation because `agentInvoked` is true;
- use the flag for presentation, telemetry, or a truthful response—not authorization;
- call `respondWith` only on the target implementation that supports it;
- test rejection and validation-error behavior.

If the normal form navigates, verify what the target browser returns to the agent. Do not assume navigation and a rich response can both complete in every implementation.

## Activation and cancellation events

A documented browser branch exposes events such as:

```js
window.addEventListener("toolactivated", ({ toolName }) => {
  // Form was focused and fields were populated.
});

window.addEventListener("toolcanceled", ({ toolName }) => {
  // Agent/user cancelled or the form was reset.
});
```

The supplied draft has open questions around these events. The official declarative explainer uses `toolcanceled`; verify the exact event name and target in the selected implementation rather than generalizing it.

Use events to:

- reveal a review panel;
- announce agent-populated state accessibly;
- run non-destructive validation;
- clear temporary previews on cancellation;
- collect diagnostics.

Do not commit a side effect merely because a form was activated.

## Focus and visual state

A documented implementation uses pseudo-classes such as:

```css
form:tool-form-active {
  outline: 2px dashed currentColor;
  outline-offset: 4px;
}

button:tool-submit-active {
  outline: 2px solid currentColor;
  outline-offset: 3px;
}
```

Verify exact selectors for the target browser. Preserve visible focus; do not suppress browser defaults without an equally clear replacement.

The shared-page benefit depends on the user seeing what the agent filled and what remains to be submitted.

## Conditional and dynamic forms

Declarative registration follows the form and its attributes. For state-dependent forms:

- add tool attributes only when the form is valid for the current route/state;
- remove them when no longer valid;
- ensure conditional fields have stable names and labels when present;
- test schema updates after DOM changes;
- avoid rapid mutation that leaves an agent with stale metadata;
- revalidate state on submit.

If a form's schema changes substantially across modes, consider separate forms/tools or an imperative tool rather than one ambiguous dynamic contract.

## Schema-synthesis cautions

Because declarative synthesis is not yet fully normative:

- test how input types map to JSON Schema;
- test required fields, `min`, `max`, `minlength`, `maxlength`, `pattern`;
- test radio groups, checkboxes, multi-select, file inputs, dates, times, and custom elements;
- test disabled, hidden, readonly, and conditionally rendered controls;
- test duplicate names and array semantics;
- test labels, `aria-description`, and `toolparamdescription`;
- inspect the browser-produced schema rather than assuming.

Do not rely on a browser-synthesized schema as the application's runtime validator.

## Existing framework forms

### React

Attributes unknown to the React version/toolchain may need careful typing or lower-case passthrough. Event extensions such as `agentInvoked` and `respondWith` may not exist in framework types. Preserve the native event and add a narrow local type augmentation only for the verified target.

Do not replace the component's submit action. Enhance the rendered native form and keep state synchronized.

### Next.js

Declarative attributes render in server HTML, but browser-only event behavior must be attached in a client component. If a Server Action owns submission, determine how agent-triggered results are surfaced without creating a parallel action.

### Vue/Svelte

Bind attributes conditionally to current availability and attach native submit listeners where the implementation-specific event extensions are accessible. Verify compiler preservation of unknown attributes.

### Angular

Angular may offer experimental helpers around forms. Treat the package/API as target-specific. The normal reactive/signal form and validation path should remain authoritative.

## Declarative audit checklist

### Structure

- one semantic form per coherent job;
- `toolname` follows current name grammar;
- `tooldescription` states the actual action and completion boundary;
- all agent-filled controls have stable names;
- labels and descriptions are accessible;
- submitted values are meaningful.

### Behavior

- human submit still works with WebMCP unavailable;
- agent population is visible;
- validation errors are visible and machine-meaningful;
- preparation versus auto-submit is explicit;
- `agentInvoked` does not weaken policy;
- `respondWith` returns serializable evidence;
- reset/cancel clears only temporary state;
- navigation behavior is tested.

### Compatibility

- target browser/version recorded;
- synthesized schema inspected;
- dynamic registration tested;
- event targets and pseudo-classes verified;
- unsupported browsers degrade to a normal form;
- normative gaps recorded.

## Declarative template

Use `assets/templates/declarative-form.html` as a review scaffold, not as drop-in business logic. Replace every placeholder from the existing form and remove target-specific attributes when the target does not support them.

## When to switch to imperative

Prefer imperative registration when:

- field synthesis cannot express the needed input;
- the action is not naturally a form submission;
- tool availability depends on non-form state;
- the result requires explicit structured data;
- cancellation must reach long-running work;
- conditional fields create unstable contracts;
- the framework prevents reliable access to native extensions;
- multiple UI steps are already encapsulated by one application action.

The choice is architectural, not a contest between fewer lines of code and more lines.
