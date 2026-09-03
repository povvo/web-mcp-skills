# Tool surface and schema

Read this reference after `product-compiler.md` when deciding which product capabilities become tools, writing names/descriptions, defining JSON Schema, shaping results, or testing selection and chaining.

## Start from critical user journeys

A tool surface is not an inventory of endpoints or controls. Begin with critical user journeys (CUJs):

```text
goal
→ information the user already supplied
→ page state the site already knows
→ actions the site can perform
→ review/confirmation points
→ observable completion
```

For a shared mutable product, prefer an inspect–act–verify topology:

```text
inspect current state → perform one coherent operation → return changed IDs/revision → inspect or validate the visible result
```

Example dashboard journey:

```text
“Compare revenue and cost for last quarter”
→ current dashboard and visible series
→ set visible date range
→ inspect plotted values and sources
→ user sees updated chart and receives bounded structured data
```

Possible tools:

- `set_dashboard_date_range`
- `inspect_dashboard_series`

Not useful:

- `click_date_picker`
- `set_start_input`
- `set_end_input`
- `click_apply`
- `read_canvas_pixels`

WebMCP should expose application capabilities, not recreate low-level actuation.

## Granularity

A good tool performs one coherent function with one completion boundary.

Too broad:

```text
manage_dashboard
```

The model cannot predict whether this reads, filters, exports, shares, or deletes.

Too narrow:

```text
set_start_date
set_end_date
refresh_chart
```

The model must orchestrate state transitions the application already encapsulates.

Coherent:

```text
set_dashboard_date_range
```

It accepts both dates, performs the existing validated update, refreshes the chart, and returns the applied range/revision.

### Combining operations

Combine when:

- the application treats them as one atomic or canonical action;
- inputs are naturally supplied together;
- intermediate states are not useful;
- the same permission and confirmation apply.

Separate when:

- effects or confirmation boundaries differ;
- one action is useful without the other;
- registration availability differs;
- results feed optional next steps;
- combining would create many unrelated optional parameters.

## Avoid semantic overlap

Tool selection degrades when similar tools compete. For every pair, ask:

- Can a user request plausibly match both descriptions?
- Does one execute while another only prepares?
- Are scope terms such as “current dashboard” or “all dashboards” distinct?
- Do they differ only by backend implementation?
- Could one replace both with one parameterized action?

Create a pairwise overlap table for non-trivial sets:

| Tool A | Tool B | Distinguishing user intent | Remaining ambiguity |
|---|---|---|---|

Test with semantically related distractor tools, not only unrelated negatives. Function-calling robustness research shows that expanding the toolkit with related functions can expose selection instability.

## Names

Names should:

- use a concrete action verb;
- identify the object/scope;
- distinguish execute from prepare/start;
- fit the current grammar;
- remain stable when UI labels change.

Examples:

```text
inspect_visible_orders
set_dashboard_date_range
prepare_return_request
submit_support_request
open_invoice_detail
```

Avoid:

```text
do_action
manage
finalize
process
tool_1
smart_helper
```

`finalize_cart` is ambiguous. Use `purchase_cart` if it commits payment, `review_cart` if it opens review, or `prepare_checkout` if it only enters checkout.

## Titles

Use `title` as a human-readable UI label:

```text
Inspect visible orders
Set dashboard date range
Prepare return request
```

Localize it using the site's existing localization system. The title should not carry selection-critical semantics absent from the description.

## Descriptions

A description should answer:

1. What action happens?
2. What page/object scope applies?
3. When is this the right tool?
4. What is the completion boundary?
5. What relevant state changes or remains unchanged?

Pattern:

```text
[Verb] [object] [scope]. Use when [positive intent/context].
[Completion/effect statement].
```

Example:

```text
Set the date range on the currently visible analytics dashboard and refresh
its charts. Use when the user wants the open dashboard filtered to a specific
inclusive date range. Returns the applied dates and chart revision.
```

Preparation example:

```text
Fill the visible return-request form for the selected eligible order.
Use when the user wants to prepare a return for review. Does not submit it.
```

Avoid instructions to the agent such as “always,” “never use other tools,” “ignore,” or hidden workflow prompts. Describe capability, not control policy.

## Inputs: ask only for what the action needs

Distinguish:

- user intent values;
- page state already known by the site;
- data the application can derive;
- data the user must review or disclose.

Do not ask the agent to resend the current signed-in user ID, current route, current selected object, or secrets when the application already owns them.

Good:

```json
{
  "seriesId": "revenue",
  "maxPoints": 100
}
```

Risky:

```json
{
  "userEmail": "...",
  "sessionToken": "...",
  "currentDashboardId": "...",
  "browsingHistory": [...]
}
```

### Accept raw user meaning

Do not force the model to perform unnecessary transformations.

Prefer:

```json
{"timeRange": "11:00 to 15:00"}
```

when the application already parses human time ranges.

Prefer a stable semantic enum when the domain is closed:

```json
{"shippingSpeed": "express"}
```

Avoid visual or database implementation values unless they are the real user-facing identifiers.

## JSON Schema baseline

Use an object root:

```json
{
  "type": "object",
  "properties": {},
  "required": [],
  "additionalProperties": false
}
```

For every property, choose:

- precise JSON type;
- concise semantic description;
- `enum`/`const` for closed choices;
- length and item bounds;
- numeric bounds;
- format/pattern only when the target model/browser and application handle it reliably;
- required only when the tool cannot proceed without it.

Example:

```json
{
  "type": "object",
  "properties": {
    "startDate": {
      "type": "string",
      "format": "date",
      "description": "Inclusive start date in YYYY-MM-DD form.",
      "minLength": 10,
      "maxLength": 10
    },
    "endDate": {
      "type": "string",
      "format": "date",
      "description": "Inclusive end date in YYYY-MM-DD form.",
      "minLength": 10,
      "maxLength": 10
    }
  },
  "required": ["startDate", "endDate"],
  "additionalProperties": false
}
```

Validate cross-field rules such as `startDate <= endDate` in application code.

### Required fields and insufficient information

Do not make a field optional merely to avoid a model asking the user. If the action cannot proceed safely, require it and test that the agent asks rather than guesses.

Conversely, do not require personalization fields that are merely convenient. Defaults should come from visible application state or explicit site policy, not hidden agent context.

### Bounds

Bounds improve reliability and resource control:

- `minLength`/`maxLength`;
- `minItems`/`maxItems`;
- `minimum`/`maximum`;
- bounded pagination and result sizes.

The schema can guide a call but cannot guarantee enforcement. Enforce again in code.

### Closed versus open values

Use `enum` when the set is genuinely stable and manageable. Avoid huge dynamic enums for every record on a page; they consume context and become stale. For dynamic resources, use a stable visible ID plus callback validation, or register a state-scoped tool.

### Nested structures

Use nested objects only when they mirror a real domain structure. Deep, optional trees increase argument errors. Consider separate tools or a simpler canonical action.

### Arrays

Define item schema and bounds:

```json
{
  "type": "array",
  "items": {"type": "string", "minLength": 1, "maxLength": 80},
  "minItems": 1,
  "maxItems": 20,
  "uniqueItems": true
}
```

Application code should canonicalize duplicates and ordering if meaning requires it.

## Schema and code have different jobs

A useful rule from current browser guidance is: validate strictly in code and keep the schema understandable.

This does not mean “omit constraints.” It means:

- schema communicates shape and helps call construction;
- code enforces binary and domain rules;
- errors explain repair;
- tests cover invalid and stale state.

Overly intricate schemas can reduce model reliability without eliminating runtime validation.

## Tool state and registration

A description such as “current selection” is only truthful while the correct selection owner is active. Pair metadata with registration scope.

Build-time manifest fields should capture:

- `registration.lifetime`;
- owner;
- exact `exposedTo`;
- preconditions;
- visible effect;
- success evidence;
- failure modes.

The browser sees only current tool metadata and schema; the application still re-checks state.

## Results

A result is part of the interaction design even though the current publisher dictionary does not declare a normative `outputSchema`.

The platform JSON-serializes callback results. Test the exact result values and reject cycles, `BigInt`, functions, symbols, DOM nodes, and unsupported class instances before treating the operation as successful.

Return:

- status;
- canonical applied values;
- stable object/operation IDs;
- relevant revision/version;
- accepted and rejected items for partial batches;
- bounded data;
- visible-state evidence;
- next required human/agent step;
- provenance for inspected external/user content.

Example read:

```json
{
  "status": "ok",
  "dashboardId": "d-17",
  "seriesId": "revenue",
  "pointCount": 90,
  "points": [],
  "sourceIds": ["warehouse:finance"],
  "truncated": false
}
```

Example preparation:

```json
{
  "status": "ready_for_review",
  "orderId": "o-42",
  "formVisible": true,
  "submitted": false,
  "requiredReviewFields": ["reason", "refundMethod"]
}
```

Example committed write:

```json
{
  "status": "submitted",
  "requestId": "r-91",
  "submittedAt": "2026-08-27T09:15:00Z",
  "visible": true
}
```

Avoid `{"success": true}` without evidence.

For revision-protected writes, a conflict result should include the current revision and enough bounded state to inspect or retry. Do not silently overwrite intervening human changes.

## Errors and self-correction

Error output should identify:

- stable code;
- human-readable message;
- affected field/state;
- whether retry is safe;
- acceptable values or next action;
- operation ID if outcome is uncertain.

Example:

```json
{
  "status": "rejected",
  "code": "SERIES_NOT_VISIBLE",
  "message": "The requested series is no longer visible on this dashboard.",
  "retryable": true,
  "availableSeries": ["revenue", "cost"]
}
```

Do not expose stack traces, tokens, internal SQL, or authorization details.

## Read, local write, and durable write

The `readOnlyHint` describes whether state is modified. It is a hint, not enforcement.

Classify effects:

- **read** — no application or remote state change;
- **local write** — changes visible/ephemeral page state;
- **remote write** — changes durable service state;
- **communication** — sends/publishes/shares;
- **purchase**;
- **permission change**;
- **destructive**.

A local filter change is not read-only merely because it does not reach a server.

For output containing external or user-generated content, set `untrustedContentHint` according to the current API semantics and handle it as data.

## Composition and chaining

Design tools so results provide the state needed for legitimate next steps without forcing hidden workflow instructions.

Example:

```text
search_flights → returns stable offer IDs
select_flight_offer → updates visible itinerary
prepare_booking → fills traveler review form
purchase_itinerary → distinct confirmed action
```

Do not collapse preparation and purchase into one ambiguous tool.

Test:

- correct order;
- invalid order;
- state dependency;
- repeated call;
- changed user goal;
- insufficient information;
- cancellation;
- stale ID;
- no-tool response.

ToolSandbox, τ-bench, API-Bank, and related evaluation work show why single-turn argument accuracy is insufficient: state, dialogue, policy, and final environment state matter.

## Toolset size

There is no useful universal maximum. Every tool consumes selection context and creates competition.

Keep a tool when it has:

- a distinct user intent;
- a clear owner/lifetime;
- an authoritative canonical operation;
- independent utility;
- testable completion.

Merge, parameterize, dynamically scope, or omit tools that do not.

## Design review questions

1. What user sentence should select this tool?
2. What close sentence should select a different tool or no tool?
3. Does the name reveal execute versus prepare?
4. Does the description match the actual handler?
5. Are all inputs necessary and derivable only from the user?
6. Can the application validate every dynamic identifier?
7. Does registration match current availability?
8. Does the result prove the visible/durable outcome?
9. Can the call be repeated safely?
10. What happens when the page state changes before invocation?
11. What does cancellation mean at each commit stage?
12. Which semantically related tool is the hardest distractor?

A tool is ready when these questions have evidence-backed answers.
