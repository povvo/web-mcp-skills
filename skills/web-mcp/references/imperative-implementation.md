# Imperative implementation

Read this reference after the product capability has a canonical operation. Use it when registering JavaScript tools, wiring real handlers, managing dynamic availability, supporting in-page agents, handling cancellation, or debugging execution.

## Current document publisher baseline

Register against the current `Document` surface:

```js
if (typeof document.modelContext?.registerTool === "function") {
  await document.modelContext.registerTool(tool, options);
}
```

Do not put registration at module scope unless the module is guaranteed to run only once in a fully active browser document and the tool is valid for the whole document lifetime.

A reusable baseline:

```js
export async function registerFeatureTools(handlers, options = {}) {
  const modelContext = globalThis.document?.modelContext;
  if (typeof modelContext?.registerTool !== "function") {
    return { supported: false, registered: [], dispose() {} };
  }

  validateHandlersBeforeRegistration(handlers);

  const lifecycle = new AbortController();
  linkAbortSignal(options.signal, lifecycle);
  const registered = [];

  try {
    for (const descriptor of TOOL_DESCRIPTORS) {
      await modelContext.registerTool({
        name: descriptor.name,
        title: descriptor.title,
        description: descriptor.description,
        inputSchema: descriptor.inputSchema,
        annotations: descriptor.annotations,
        execute: (input, execution) => {
          const handler = handlers[descriptor.handler];
          return handler(input, {
            signal: execution.signal,
            toolName: descriptor.name,
          });
        },
      }, {
        signal: lifecycle.signal,
        ...(descriptor.exposedTo.length
          ? { exposedTo: descriptor.exposedTo }
          : {}),
      });
      registered.push(descriptor.name);
    }
  } catch (error) {
    lifecycle.abort(error);
    throw error;
  }

  return {
    supported: true,
    registered,
    signal: lifecycle.signal,
    dispose(reason) {
      lifecycle.abort(reason);
    },
  };
}
```

The bundled generator implements this pattern and framework wrappers around it. The current WebMCP surface remains a draft and target support must be proven through a compatibility profile.

## Registration as a transaction

`registerTool()` is asynchronous and can fail after earlier tools registered. Before registering:

- validate every handler binding in the actual current collection before constructing framework proxy functions;
- validate names and schemas;
- validate exact origins;
- check the external lifecycle signal;
- construct all descriptors without side effects.

During registration, record completed names. On failure, abort the shared lifecycle controller so earlier registrations are removed.

This is a best-effort registration transaction. Do not continue with a silently partial toolset unless the product explicitly designs independent optional tools and reports their availability.

## Tool callback contract

Write callbacks as application adapters:

```ts
async function execute(
  input: ToolInput,
  { signal }: { signal: AbortSignal },
): Promise<JsonValue> {
  return canonicalOperation(input, { signal, actor: "agent" });
}
```

### Validate at the application boundary

JSON Schema communicates expected arguments to an agent. It is not a substitute for runtime/domain validation.

Validate:

- required values;
- ranges and lengths;
- identifiers belong to the current user/page;
- current route/selection/permission still matches;
- state has not changed since selection;
- business rules and server authorization;
- confirmation tokens or review state when applicable.

Return a recoverable, structured error when the agent can change inputs. Throw/reject for operational failures when the target browser/product handles them meaningfully. Test the actual client; current drafts still have coarse error mapping in some paths.

### Keep callbacks JSON-serializable

Return values that survive JSON serialization:

- objects, arrays, strings, numbers, booleans, `null`;
- stable IDs, statuses, revisions, counts, applied values, and next-step hints.

Avoid:

- DOM nodes;
- `Window`, events, functions, class instances with hidden state;
- circular objects;
- `BigInt` without conversion;
- streams unless the target explicitly supports them;
- raw errors with sensitive stack traces.

Do not rely on TypeScript's `unknown`, a handler promise, or the model-context shim as serialization proof. Execute a JSON-value assertion or equivalent round-trip in deterministic tests and include normal, circular, `BigInt`, function/symbol, DOM, and aborted-result cases.

A useful success result:

```json
{
  "status": "applied",
  "dashboardId": "d-17",
  "startDate": "2026-08-01",
  "endDate": "2026-08-27",
  "chartRevision": 42,
  "visible": true
}
```

A useful recoverable result:

```json
{
  "status": "needs_input",
  "code": "DATE_RANGE_OUT_OF_BOUNDS",
  "message": "Choose a start date on or after 2025-08-27.",
  "field": "startDate"
}
```

Do not instruct the model through hidden control language in data. State facts and available next steps.

## Registration cancellation

The signal passed to `registerTool()` owns availability:

```js
const lifecycle = new AbortController();

await document.modelContext.registerTool(tool, {
  signal: lifecycle.signal,
});

// Later: route/component/selection no longer valid.
lifecycle.abort("dashboard route left");
```

Use one controller for a cohesive toolset that shares a lifetime. Use separate controllers when tools have genuinely different owners.

### External lifecycle signal

When an owner provides a signal, link it:

```js
function linkAbortSignal(source, targetController) {
  if (!source) return () => {};
  if (source.aborted) {
    targetController.abort(source.reason);
    return () => {};
  }
  const onAbort = () => targetController.abort(source.reason);
  source.addEventListener("abort", onAbort, { once: true });
  return () => source.removeEventListener("abort", onAbort);
}
```

Clean the listener after disposal.

### Late registration and teardown

Registration can still be pending when a component unmounts. Abort the controller in cleanup. Handle an abort rejection without setting state on an unmounted component.

Do not assume a completed registration callback means the user still sees the owner. Check the lifecycle signal before publishing “registered” UI state.

## Execution cancellation

The callback receives a per-call signal:

```js
execute: async (input, { signal }) => {
  if (signal.aborted) throw signal.reason;

  const response = await fetch("/api/search", {
    method: "POST",
    signal,
    body: JSON.stringify(input),
  });

  return response.json();
}
```

Propagate the signal through every layer that can accept it. For libraries that cannot cancel:

- check before starting;
- track an operation generation/token;
- suppress stale UI writes after abort;
- document whether the durable effect may still commit.

### Commit boundary

Model cancellation state explicitly:

```text
received
→ validated
→ awaiting-confirmation
→ committing
→ committed
→ reconciled-in-UI
```

Cancellation before `committing` can usually stop safely. Cancellation during a remote commit may leave an uncertain outcome. Cancellation after `committed` must not imply rollback.

For non-idempotent remote writes, use an application idempotency key or operation ID when the underlying system supports one.

## Availability and preconditions

Registration should reflect meaningful availability, but callbacks must re-check preconditions because state can change between observation and invocation.

Examples:

- register `inspect_selection` only while a selection exists;
- re-check that the selected resource still exists and remains authorized;
- register `submit_review` only on the review route;
- re-check the review state has not changed;
- register a permissioned tool only while the permission is present;
- still enforce permission at the authoritative action/server.

Dynamic registration improves selection quality; it is not authorization.

## UI synchronization

Use the same action/store path as the UI so tool execution causes normal visible state changes.

Good:

```ts
await dashboardStore.setRange(input, { signal });
return {
  status: "applied",
  revision: dashboardStore.revision,
  visibleRange: dashboardStore.range,
};
```

Risky:

```ts
await api.setRange(input); // UI still displays old state
return { status: "ok" };
```

If server completion precedes UI reconciliation, await the state transition or return an explicit intermediate status. The agent and user share the page; stale visible state undermines the value of WebMCP.

## Result design

Results should answer:

1. Did the requested operation happen?
2. What canonical values were applied?
3. What object or revision identifies the result?
4. What visible state changed?
5. Is another user/agent step required?
6. Is any returned content external or user-generated?

For shared mutable state, also answer whether the expected revision matched. A conflict result should expose the current revision and bounded state required for review or retry instead of silently overwriting human work.

Keep large payloads bounded. Prefer summarized records plus stable IDs over entire page dumps.

For inspection tools, return provenance:

```json
{
  "status": "ok",
  "items": [],
  "source": {
    "page": "orders",
    "filters": {"status": "delayed"},
    "retrievedAt": "2026-08-27T09:00:00Z"
  }
}
```

## In-page agent pattern

An in-page agent can maintain a current registry:

```js
async function readTools(fromOrigins = []) {
  return document.modelContext.getTools(
    fromOrigins.length ? { fromOrigins } : {},
  );
}

document.modelContext.addEventListener("toolchange", refresh);
```

Treat each `RegisteredTool` as ephemeral. Re-query after `toolchange` and before a long-delayed call.

Isolate consumer compatibility:

```js
async function executeRegisteredTool(tool, input, options) {
  // Choose this branch from a tested target profile, not guesswork.
  return TARGET_TAKES_OBJECT
    ? document.modelContext.executeTool(tool, input, options)
    : document.modelContext.executeTool(
        tool,
        JSON.stringify(input),
        options,
      );
}
```

Do not attempt cross-top-level-document execution unless the target explicitly supports it. The supplied draft limits execution to the same traversable.

## Cross-origin publisher pattern

Tool owner:

```js
await document.modelContext.registerTool(tool, {
  exposedTo: ["https://agent-host.example"],
  signal: lifecycle.signal,
});
```

Embedding page:

```html
<iframe
  src="https://tool-owner.example"
  allow="tools">
</iframe>
```

In-page consumer:

```js
const tools = await document.modelContext.getTools({
  fromOrigins: ["https://tool-owner.example"],
});
```

All three pieces must agree. Test:

- permission denied;
- owner not requested;
- tool not exposed;
- origin changed after navigation;
- iframe removed during execution;
- execution cancelled;
- tool removed and re-registered with a changed schema.

## Updating tool metadata

The current draft has registration and unregistration rather than a universal atomic “update” operation. To change name, description, schema, annotations, or handler meaning:

1. abort the old registration;
2. register the new definition;
3. account for the observation window and invocation races;
4. avoid reusing a name with incompatible input meaning without a migration plan.

For component re-renders, do not re-register only because a closure identity changed. Keep the latest handler in a ref/cell while stable metadata remains registered. Re-register when availability or contract changes.

## Error taxonomy for debugging

Classify failures before changing code:

| Layer | Typical symptoms |
|---|---|
| Surface | `document.modelContext` absent |
| Document | inactive document or origin isolation failure |
| Policy | `NotAllowedError`, cross-origin iframe missing `allow="tools"` |
| Registration | duplicate name, invalid schema, aborted lifecycle |
| Observation | tool not visible, stale registry, wrong frame/origin |
| Selection | agent chooses no tool or wrong overlapping tool |
| Arguments | missing/incorrect values, serialization mismatch |
| Callback | handler missing, precondition changed, runtime validation fails |
| Side effect | server rejects, rate limit, uncertain commit |
| UI reconciliation | result says success but page remains stale |
| Response | unserializable value, coarse browser error |
| Teardown | stale tool after route/component leaves |

Fix the layer that failed. Do not rewrite descriptions to compensate for a broken callback or origin policy.

## Implementation completion gate

Imperative integration is ready when:

- all real canonical-operation handlers exist before any wrapper or registration is created;
- tool metadata matches actual behavior;
- schema and runtime validation are both present;
- registration owner and teardown are tested;
- per-invocation cancellation reaches cancellable work;
- partial registration cleans up;
- return values serialize;
- normal UI state updates;
- route/selection/permission preconditions are re-checked;
- cross-origin configuration is explicit when used;
- browser/model layers are tested or marked `NOT RUN`.
