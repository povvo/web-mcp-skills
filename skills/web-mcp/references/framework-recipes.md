# Framework recipes

Read this reference after repository inspection, product operation design, and imperative/declarative selection. These patterns explain lifecycle placement and handler binding; the generated adapter supplies repetitive registration code.

Generate a target preview:

```bash
python scripts/webmcp_toolkit.py generate MANIFEST.json --target TARGET
```

Targets:

```text
vanilla-js
typescript
react
next
vue
svelte
angular
```

The generator accepts real canonical-operation handlers at runtime. Those handlers may be existing, extracted, or newly implemented through CREATE/EXTEND work. It does not import guessed application modules.

## Shared rules

Across frameworks:

1. registration begins only in a browser lifecycle;
2. the actual current handler collection is checked before proxy construction and registration;
3. the lifecycle controller aborts on teardown;
4. callbacks receive the latest handler implementation;
5. stable metadata is not re-registered on every render;
6. availability changes can dispose and re-register;
7. application state and permission are re-checked at invocation;
8. SSR/import evaluation never reads `document` unguarded;
9. registration errors remain observable;
10. the normal UI and tool call share the same application action.

## Vanilla JavaScript

### Document-lifetime toolset

Use after the module loads in a fully active document:

```js
import { registerWebMCPTools } from "./generated-webmcp.mjs";
import { inspectSeries, setDateRange } from "./dashboard-actions.js";

const session = await registerWebMCPTools({
  inspectSeries,
  setDateRange,
});

window.addEventListener("pagehide", (event) => {
  // A persisted page is entering BFCache. Its document registrations remain
  // owned by that document and become available again if the document restores.
  if (!event.persisted) session.dispose("document discarded");
});
```

Do not use an unconditional one-shot `pagehide` disposal for a document-lifetime
toolset: `pagehide` also fires on BFCache entry. If the selected host proves a
different lifecycle contract, isolate that behavior in its compatibility
profile and pair cleanup with a tested `pageshow` restoration path. An explicit
owner controller remains useful for hot reload and tests.

### Route or custom-element lifetime

Call registration from the router/controller mount and dispose from its unmount/disconnect callback:

```js
class DashboardPanel extends HTMLElement {
  #session;

  async connectedCallback() {
    this.#session = await registerWebMCPTools(this.#handlers());
  }

  disconnectedCallback() {
    this.#session?.dispose("dashboard disconnected");
  }
}
```

Guard against connection/disconnection racing with asynchronous registration.

## TypeScript

Prefer a typed handler map at the binding site:

```ts
type WebMCPHandlers = {
  inspectDashboardSeries(
    input: InspectInput,
    options: HandlerOptions,
  ): Promise<InspectResult>;
  setDashboardDateRange(
    input: RangeInput,
    options: HandlerOptions,
  ): Promise<RangeResult>;
};

const handlers: WebMCPHandlers = {
  inspectDashboardSeries,
  setDashboardDateRange,
};
```

The generated TypeScript target includes the manifest handler-name union and generic handler types. Refine input/result types from the application's source of truth; do not hand-maintain duplicate domain types if an existing schema/type generator exists.

For DOM typings, use the official `webmcp-types` package when the selected document profile matches it and record the resolved version. Treat it as development-time declarations, not a runtime or Service Worker implementation. Use a project-local narrow fallback only when necessary and never ship a competing global declaration that conflicts with browser-native types.

## React

Register in an effect owned by the component that makes the tools valid.

```tsx
const handlers = React.useMemo(() => ({
  inspectDashboardSeries: (input, { signal }) =>
    actions.inspect(input, { signal, dashboardId }),
  setDashboardDateRange: (input, { signal }) =>
    actions.setRange(input, { signal, dashboardId }),
}), [actions, dashboardId]);

const webmcp = useWebMCPTools(handlers, {
  enabled: canUseDashboard,
});
```

The generated hook:

- keeps handlers in a ref so ordinary renders do not re-register;
- starts registration in `useEffect`;
- aborts on cleanup;
- reports `supported`, `registered`, and `error`;
- accepts `enabled` for route/permission/state availability.

### Dependency decisions

If `dashboardId` changes the meaning of a tool, either:

- include it in the handler closure and ensure the hook's registration key/lifetime changes; or
- register one tool whose input explicitly selects among currently visible authorized dashboards.

Do not leave metadata saying “current dashboard” while the callback still closes over the previous dashboard.

### Strict Mode

Development Strict Mode can mount, clean up, and mount effects again. The adapter must make cleanup idempotent and registration failures visible. Tests should not assume exactly one registration call in development without accounting for Strict Mode.

### Experimental hook packages

A current browser guide may recommend an experimental React package. Evaluate it against:

- current `document.modelContext` surface;
- support for `title`, annotations, lifecycle signal, and execution signal;
- stale-closure behavior;
- SSR no-op behavior;
- error/result normalization;
- package maintenance and target React versions.

Reuse it when it fits; otherwise the generated dependency-free hook is a transparent baseline.

## Next.js

WebMCP registration is browser-only. The owner must be a Client Component:

```tsx
"use client";

export function DashboardWebMCPBoundary(props: Props) {
  const handlers = useDashboardHandlers(props.dashboardId);
  useWebMCPTools(handlers, { enabled: props.enabled });
  return null;
}
```

Render the boundary from the route/page that owns the state.

### Server Actions

Do not call a Server Action in a novel path that bypasses existing form/revalidation logic. Prefer a shared application action:

```text
human form → shared action → server mutation → revalidation
WebMCP handler → shared action → server mutation → revalidation
```

If the action requires a request-scoped token or server-only secret, pass through the existing client endpoint/action contract; never move secrets into browser code.

### Navigation

Dispose route-local tools when navigation replaces the owner. Test:

- client navigation;
- back/forward cache;
- loading and error boundaries;
- route segment reuse;
- fast refresh;
- permission/auth state changes.

## Vue

Use a composable inside `setup()`:

```ts
const handlers = {
  inspectDashboardSeries: (input, { signal }) =>
    dashboard.inspect(input, { signal }),
  setDashboardDateRange: (input, { signal }) =>
    dashboard.setRange(input, { signal }),
};

const state = useWebMCPTools(handlers, {
  enabled: computed(() => route.name === "dashboard" && canView.value),
});
```

The generated Vue adapter uses mount/unmount lifecycle and watches availability. Keep handler access current through refs/cells rather than rebuilding the entire registration for unrelated reactive changes.

When a reactive value changes tool semantics or schema, dispose and re-register deliberately.

For Nuxt/SSR, ensure registration is client-only.

## Svelte and SvelteKit

Register in `onMount` and return cleanup:

```svelte
<script lang="ts">
  import { onMount } from "svelte";
  import { mountWebMCPTools } from "./generated-webmcp";

  onMount(() => {
    const registration = mountWebMCPTools({
      inspectDashboardSeries,
      setDashboardDateRange,
    });

    return () => registration.dispose("component unmounted");
  });
</script>
```

If handlers use reactive state, pass getter functions or update the adapter's handler cell. Do not capture a stale value at mount when “current selection” changes.

For SvelteKit, browser registration belongs in a client lifecycle, not `load` on the server.

## Angular

Own registration with the component/service lifecycle. A direct pattern uses `DestroyRef`:

```ts
@Injectable()
export class DashboardWebMCP {
  private readonly destroyRef = inject(DestroyRef);

  async register(handlers: DashboardHandlers) {
    const session = await registerWebMCPTools(handlers);
    this.destroyRef.onDestroy(() =>
      session.dispose("Angular owner destroyed"),
    );
    return session;
  }
}
```

Register from a component or route-scoped provider when tool availability is local. A root provider implies document/application lifetime.

Use `NgZone` or signals according to the application's existing state architecture so tool-driven changes update the visible UI. Do not add a second state system.

Angular may expose experimental WebMCP helpers or Signal Forms integration. Verify current official Angular and browser documentation before depending on them. Direct imperative registration is the current document baseline, subject to the selected host profile.

## Declarative forms in frameworks

A framework does not change the semantic requirements of a native form.

- preserve lower-case tool attributes in rendered HTML;
- verify unknown-attribute passthrough;
- attach implementation-specific native events at the real form element;
- preserve labels, validation, focus, and fallback submission;
- keep the existing framework action as authoritative.

Type systems may need a narrow attribute/event augmentation. Scope it to the project and verified target.

## Metadata and handler updates

Distinguish three kinds of change:

### Handler implementation changes, same contract

Update the handler ref/cell. Do not re-register merely because a function identity changed.

### Availability changes

Dispose and register according to `enabled`, route, selection, mode, or permission.

### Contract changes

Name, description, schema, annotations, or meaning changed. Dispose old registration and create a new one. Test the observation gap and stale `RegisteredTool` behavior.

## Hot module replacement

Development HMR can leave duplicate tools if cleanup is skipped. Make development modules dispose previous sessions when the framework's HMR API supports it, or keep registration inside a lifecycle that HMR reliably tears down.

A duplicate-name error during HMR is a useful signal; do not suppress it globally.

## Page lifecycle and BFCache

Component unmount, route navigation, document inactivation, and back/forward cache are distinct lifecycle events. The current draft and host behavior may queue, reject, or defer work around a non-fully-active document; do not infer exact BFCache execution semantics from framework unmount alone.

For document-lifetime registrations, the default expectation is: retain the
registration while the document is stored in BFCache, allow it to be unavailable
while the document is not fully active, and avoid duplicate re-registration on
`pageshow`. Route/component owners may have narrower lifetimes, but their chosen
cleanup and restoration behavior must be explicit and tested.

Test the selected browser/profile for:

- navigation away and tool disappearance;
- back/forward restoration without duplicate registration;
- an invocation initiated before inactivation;
- late operation completion after the owner is stale;
- state refresh after restoration.

Report behavior that was not executed as `NOT RUN` rather than asserting that cleanup alone proves it.

## Error presentation

Framework adapters should expose state:

```ts
{
  supported: boolean;
  registered: readonly string[];
  error: Error | null;
}
```

Use it for development diagnostics. Do not show a generic user error merely because WebMCP is unavailable; the normal human interface remains the fallback.

Registration errors should be logged with:

- toolset name/hash;
- owner route/component;
- target browser;
- error name/message;
- lifecycle state;
- attempted tool names.

Do not log sensitive tool arguments by default.

## Testing recipes

### Unit

Stub `document.modelContext.registerTool`, capture tool definitions, invoke callbacks, and assert:

- descriptors;
- handler mapping;
- execution signal propagation;
- cleanup signal;
- unsupported-browser fallback;
- partial registration cleanup.

### Component

Mount owner, assert registration; change availability, assert abort; unmount, assert cleanup. Exercise state changes through the captured callback and assert visible UI.

### SSR

Import/render server output and confirm no `document` access occurs before client mount.

### Browser

Navigate into and out of the owner, inspect available tools, invoke one, cancel one, reload, use back/forward navigation, and repeat under permission/auth changes.

## Framework completion gate

The adapter is integrated—not merely generated—when:

- it is imported by a real owner;
- all manifest handlers are bound to real actions;
- the actual handler collection fails before registration when any operation is missing;
- availability matches route/component/state;
- SSR and HMR behavior are understood;
- navigation and BFCache behavior are tested for claimed targets or marked `NOT RUN`;
- teardown and async registration races are tested;
- tool-driven actions update visible state;
- normal human behavior remains unchanged;
- target-specific dependencies and compatibility are recorded.
