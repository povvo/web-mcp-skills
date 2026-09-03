# Repository integration

Read this reference before choosing operations, registration locations, framework adapters, or repository changes in CREATE or EXTEND mode. Read `product-compiler.md` first.

## Goal

A good WebMCP integration exposes real product behavior through one canonical operation path. In EXTEND mode, reuse behavior that already works for people. In CREATE mode, implement the behavior and its normal UI before registering it. The repository—not a generic example—must answer:

- what action exists or must be implemented for the agreed journey;
- where its state lives;
- who may perform it;
- which validations and confirmations apply;
- how the interface shows progress, success, and failure;
- when the action is available;
- how human and tool invocation are tested.

The scanner accelerates inventory. It does not prove semantics.

```bash
python scripts/webmcp_toolkit.py scan-repo PATH --format json
```

## CREATE and EXTEND classification

Classify every capability before editing:

- **existing** — a callable operation already used by the normal UI;
- **extract** — behavior exists inside a UI handler and should move behind a shared boundary;
- **create** — the requested product journey needs new state, operation, UI, or persistence;
- **reject** — decorative, navigation-only, unowned, or outside the agreed product.

An absent handler is a blocker to registration, not automatically a blocker to the build. In CREATE mode, and for an agreed missing capability in EXTEND mode, implement the operation with a named state/UI owner and tests before binding it.

## Repository inspection order

### 1. Establish the application boundary

Inspect:

- root and workspace package manifests;
- lockfiles and package manager;
- framework/build configuration;
- language and module format;
- source roots and aliases;
- server/client boundaries;
- test framework;
- generated, vendor, dependency, cache, and build directories.

Do not patch compiled output or dependencies when source exists.

### 2. Find current WebMCP surfaces

Search for:

```text
document.modelContext
navigator.modelContext
registerTool
provideContext
getTools
executeTool
toolchange
toolname
tooldescription
toolparamdescription
toolautosubmit
agentInvoked
respondWith
toolactivated
toolcanceled
toolcancel (legacy or implementation-specific occurrence)
useWebMCP
webmcp
```

Classify each occurrence as:

- current imperative publisher;
- current in-page consumer;
- browser-specific declarative form;
- experimental library;
- legacy/renamed surface;
- test/shim/demo;
- generated or vendored code;
- unrelated text.

Do not globally replace a symbol until its role is known.

### 3. Trace user-visible workflows

Start from a critical user journey and trace inward:

```text
route/page
→ control or form
→ event/submit handler
→ action/service/store mutation
→ API or persistence boundary
→ state reconciliation
→ visible completion
```

Useful evidence includes:

- `onClick`, `onSubmit`, commands, actions, reducers, effects;
- exported service functions;
- form actions/loaders;
- state-store methods;
- API client methods;
- route guards and permission hooks;
- dialogs and confirmation components;
- toast/status/error state;
- tests that assert final UI or backend state.

A function named `handleSubmit` is not automatically a reusable handler. It may close over component state, depend on a synthetic event, or bundle UI-only work.

### 4. Identify the authoritative action

Prefer, in order:

1. an application/domain action already called by both UI and tests;
2. a service/store method with authorization and validation preserved;
3. a small extraction from a UI handler into a shared action, with the UI kept on that action;
4. a newly implemented canonical operation required by the agreed product journey, with its normal UI and tests;
5. the existing UI handler only when its callback shape and lifetime are genuinely reusable.

Do not create a second API request path merely because it is easier to call from a tool.

### 5. Locate lifecycle ownership

Ask when the tool is valid:

- entire document;
- one route;
- one mounted component;
- one selected object;
- one editor mode;
- one authenticated/authorized state;
- one open dialog or visible form.

Place registration at the narrowest stable owner that has access to the required dependencies.

Examples:

- a global read-only help tool → app shell/document;
- `set_dashboard_range` → dashboard route/component;
- `comment_on_selection` → editor component while a selection exists;
- `submit_return_request` → returns form or route;
- `inspect_map_results` → map/search page while result state exists.

Static registration is simpler, but static registration of an invalid action is worse than dynamic registration.

## Scanner interpretation

The bundled scanner reports:

- framework and language indicators;
- package manifests and source roots;
- current WebMCP occurrences;
- forms and declarative attributes;
- candidate exported functions and event handlers;
- likely routes/components/stores/services;
- test and configuration files;
- skipped directories and limits;
- heuristic integration anchors.

Use these confidence levels:

- **direct** — explicit current WebMCP code or exact manifest handler symbol;
- **strong candidate** — exported action/service referenced by UI;
- **candidate** — naming or location suggests relevance;
- **weak** — generic event handler or text match.

Open source context around every candidate before using it. Scanner output is evidence for where to look, not permission to patch.

## Integration map

Create one row per tool:

| Field | Evidence |
|---|---|
| User job | What the person is trying to accomplish |
| Visible entry point | Button, form, route, command, canvas, map, dashboard |
| Owner | Route/component/form that makes the action valid |
| Handler | Existing callable action and source path |
| Dependencies | Store, service, router, API client, selection, locale |
| Permission path | Client and server checks already used |
| Validation | Schema and runtime/domain validation |
| Confirmation | Existing dialog or review step |
| Side effect | Local state, remote state, communication, purchase, deletion |
| UI completion | What visibly changes |
| Result evidence | IDs, revision, applied filters, status, counts |
| Cancellation | Cancellable before/after which boundary |
| Tests | Existing and new tests |
| Registration lifetime | Document/route/component/selection/mode/permission |

Missing cells are blockers or explicit assumptions.

## Handler adaptation patterns

### Pure or service action

Best case:

```ts
export async function setDateRange(
  input: { startDate: string; endDate: string },
  options: { signal?: AbortSignal } = {},
) {
  // Existing validation, store update, fetch, and UI reconciliation.
}
```

Bind directly:

```ts
const handlers = { setDateRange };
```

### UI handler that receives an event

Do not pass a synthetic event from WebMCP. Extract the action:

```ts
async function saveDraft(input: DraftInput, options?: SaveOptions) {
  // authoritative work
}

function onSubmit(event: SubmitEvent) {
  event.preventDefault();
  return saveDraft(readDraftFromForm());
}
```

The tool calls `saveDraft`; the human form continues to call the same function.

### Handler with component dependencies

Bind at the owner:

```tsx
const handlers = useMemo(
  () => ({
    setDashboardDateRange: (input, { signal }) =>
      dashboardActions.setRange(input, { signal, dashboardId }),
  }),
  [dashboardActions, dashboardId],
);
```

The generated adapter should use the latest handler without needlessly re-registering metadata. If a dependency changes the tool's meaning or availability, tear down and re-register.

### Navigation-only action

Describe it as initiation, not completion:

```text
start_return_request
Open the return-request page for the selected eligible order and preselect it.
Does not submit a return.
```

Return the destination and selection state. Do not call it `return_order`.

## Framework and rendering boundaries

### Server rendering

`document` does not exist during SSR. Registration belongs in a client-only lifecycle.

- Next.js: client component or client hook, not a server component.
- React SSR: effect after hydration.
- Vue/Nuxt: client lifecycle; guard server execution.
- SvelteKit: `onMount`.
- Angular SSR: browser platform check or a client-only owner.

Feature detection inside a server-rendered module is not enough if importing that module executes browser code at module scope.

### Code splitting and routes

A route-local tool module should load with the route and abort on unmount. Do not import every tool into the global shell solely to make registration convenient.

### State managers

Call existing store actions rather than mutating store internals. Preserve middleware, optimistic-update reconciliation, logging, and authorization hooks.

## Patch-plan workflow

Use:

```bash
python scripts/webmcp_toolkit.py patch-plan REPO MANIFEST \
  --target next --format json
```

For existing and extracted operations, the plan should report:

- detected target/framework confidence;
- every manifest handler and matching source candidates;
- proposed generated adapter path;
- likely owner files;
- test locations;
- blockers such as zero/multiple handler matches;
- commands to generate and validate;
- no repository mutation.

Resolve ambiguous handler matches manually. `HANDLER_NOT_FOUND` blocks registration. It becomes an implementation task only when the CREATE/EXTEND capability map explicitly calls for a new operation; otherwise it remains a scope blocker. A plan is ready only when each tool maps to one authoritative operation and one owner.

## Patch discipline

Before editing:

1. capture the relevant file list and tests;
2. decide generated versus hand-maintained code;
3. choose import/binding boundaries;
4. preserve formatting and project conventions;
5. make the smallest cohesive change;
6. avoid unrelated upgrades or dependency changes;
7. add tests beside existing test architecture.

After editing:

1. inspect the diff;
2. run focused tests;
3. run broader project checks when affordable;
4. run toolkit validation/compatibility checks;
5. test route/component teardown;
6. verify normal human UI behavior still uses the same path.

## Failure patterns

### “One tool per endpoint”

Endpoints are not user jobs. This creates overlapping tools, exposes implementation detail, and forces the model to orchestrate what the app already knows.

### “Register all tools at app startup”

This leaks invalid actions into routes where state or permissions do not exist.

### “Call the backend directly from execute”

This often bypasses UI reconciliation, client validation, confirmation, analytics, and existing error handling.

### “Use DOM clicks inside execute”

A WebMCP tool should call application logic. Triggering arbitrary clicks recreates brittle actuation behind a function-call facade.

A narrowly justified form submit or navigation through normal browser primitives may be appropriate, but it must remain the application's canonical path.

### “Infer permission from visible controls”

A hidden or disabled control is UI evidence, not authorization. Preserve server-side checks.

### “Generate a framework hook without an owner”

A hook is not integration until a real component binds handlers, availability, and teardown.

## Repository completion gate

Repository integration is complete when:

- the source framework and browser boundary are known;
- each tool has an authoritative existing, extracted, or newly implemented canonical operation;
- newly implemented operations have a normal UI/state owner and focused tests;
- registration owner and teardown are explicit;
- permissions, validation, confirmation, and UI reconciliation remain on the normal path;
- generated code is bound in application code;
- focused tests cover human and tool invocation;
- no scanner heuristic is presented as verified behavior.
