# Platform and compatibility

Read this reference when choosing WebMCP versus MCP, using document/in-page/cross-origin APIs, or reasoning about lifecycle and origins. Select the named target in `compatibility-profiles.md` and use `official-source-map.md` for source authority and refresh rules.

## Evidence hierarchy

Do not blend these layers:

1. **Current WebMCP draft** — the proposed web-platform contract; not a W3C Recommendation.
2. **Browser implementation** — behavior in a particular browser/version or origin trial.
3. **Product surface** — how ChatGPT or another agent discovers, reviews, confirms, and displays tools.
4. **Official proposal** — declarative forms or Service Worker WebMCP; not current document-API behavior.
5. **Library, eval tool, or demo** — useful implementation prior art, not platform law.

Record the source, date, and target for compatibility-sensitive decisions. A browser guide may lead or lag the draft. A demo may use an API that was renamed. A product may gate Site tools by model, workspace, app version, or rollout.

## Core model

A `Document` owns one stable `ModelContext`:

```js
document.modelContext
```

The current imperative surface is conceptually:

```ts
interface ModelContext extends EventTarget {
  registerTool(tool, options?): Promise<void>;
  getTools(options?): Promise<RegisteredTool[]>;
  executeTool(tool, input, options?): Promise<string>;
  ontoolchange: EventHandler;
}
```

A registered tool contains:

```ts
type ModelContextTool = {
  name: string;
  title?: string;
  description: string;
  inputSchema?: object;
  execute(input: object, options: { signal: AbortSignal }): Promise<unknown>;
  annotations?: {
    readOnlyHint?: boolean;
    untrustedContentHint?: boolean;
  };
};
```

Registration options contain:

```ts
{
  signal?: AbortSignal;      // abort unregisters the tool
  exposedTo?: string[];      // exact secure origins
}
```

In-page discovery options contain:

```ts
{
  fromOrigins?: string[];    // exact secure origins to query in addition to same-origin
}
```

Execution options contain:

```ts
{
  signal?: AbortSignal;      // abort cancels this invocation
}
```

### Tool-name grammar

Names are 1–128 characters and use only ASCII letters, digits, `_`, `-`, and `.`. Names are unique within the owning `ModelContext`. Duplicate registration rejects rather than silently overwriting.

Treat the name as a stable machine identifier, not the full explanation. Use `title` for a localized human label when supported and `description` for selection semantics.

### Registration preconditions

The draft gates WebMCP behind:

- a secure context;
- a fully active document;
- an origin-keyed agent cluster, except for the special `file` case described by the draft;
- the `tools` Permissions Policy;
- serializable input schema;
- a non-aborted registration signal.

A feature check proves only JavaScript surface presence:

```js
const supported =
  typeof document !== "undefined" &&
  typeof document.modelContext?.registerTool === "function";
```

Registration can still reject with `InvalidStateError`, `SecurityError`, `NotAllowedError`, schema serialization errors, duplicate-name errors, or an abort reason. Surface those errors during development instead of treating support as binary.

## Registration, discovery, execution, response

The lifecycle is:

1. the page registers tools;
2. the browser or in-page agent observes available tools;
3. an agent selects a tool and supplies structured input;
4. the browser queues execution on the owning document;
5. the callback runs in the page's application context;
6. the callback result is serialized and returned.

This is a live-document capability. Navigation, document destruction, permissions changes, or explicit registration abort can make tools unavailable.

### Registration is not invocation

The registration `AbortSignal` owns tool availability. The callback's `options.signal` owns one invocation. Do not substitute one for the other.

### Dynamic updates

`toolchange` notifies eligible documents when tools are added or removed:

```js
document.modelContext.addEventListener("toolchange", async () => {
  const tools = await document.modelContext.getTools();
  refreshLocalAgentRegistry(tools);
});
```

Task ordering across event-loop task sources is not a synchronous contract. Do not assume a timer queued after `registerTool()` observes `toolchange` in a particular interleaving. Await registration and query current tools when correctness depends on the result.

## In-page consumers

`getTools()` and `executeTool()` are for in-page or frame-hosted agents. A browser's built-in agent can use a separate internal observation mechanism.

`getTools()`:

- returns tools from the caller and eligible descendant documents;
- includes same-origin tools by default;
- includes requested cross-origin owners only when `fromOrigins` names them;
- still requires each cross-origin tool to expose itself to the caller;
- returns a sorted list in the current draft.

A returned `RegisteredTool` includes metadata, owner window, and origin. Do not persist it across navigation or registration churn and assume it remains executable.

### Consumer argument compatibility branch

The supplied/current draft and explainer show `executeTool(registeredTool, inputObject, options)`. A Chrome implementation guide dated August 2026 shows a JSON string argument. This is a real compatibility divergence, not a wording detail.

For publisher integrations, avoid coupling to it: `registerTool()` callbacks receive an object.

For in-page consumers:

1. target and document the exact browser/version;
2. run a feature/conformance test rather than guessing from method existence;
3. isolate argument serialization in one adapter;
4. test cancellation and return parsing;
5. remove the branch when the target converges.

Do not silently stringify everywhere; that would make code wrong for the object-taking contract.

## Cancellation and lifecycle races

The browser tracks pending executions outside a single document event loop. Cancellation can race with natural fulfillment or rejection. Once the caller's execution signal is aborted, its promise must not later be treated as a successful outcome.

Application code should:

- check `signal.aborted` before expensive work;
- pass `signal` to `fetch`, streams, workers, or cancellable services;
- avoid updating UI from a stale completion after cancellation or route change;
- distinguish “not started,” “cancelled before commit,” “commit may have happened,” and “completed”;
- return or log an operation identifier when outcome could be uncertain.

Unregistering a tool does not reverse a side effect. Browser behavior around in-flight executions may change; verify the target when teardown semantics matter.

## Frames, origins, and Permissions Policy

The policy-controlled feature is `tools`, with a default allowlist of `self` in the supplied draft.

For a cross-origin iframe, two independent gates are needed:

1. the embedding page delegates the feature:

```html
<iframe src="https://partner.example" allow="tools"></iframe>
```

2. the tool owner explicitly exposes the tool:

```js
await document.modelContext.registerTool(tool, {
  exposedTo: ["https://host.example"],
});
```

An in-page consumer also requests that owner:

```js
const tools = await document.modelContext.getTools({
  fromOrigins: ["https://partner.example"],
});
```

Use exact, potentially trustworthy origins. Do not use wildcard matching, URL paths, query strings, inherited trust, or a broad allowlist “for convenience.”

The browser's built-in agent is not modeled as an arbitrary iframe origin. Do not add `exposedTo` merely to make built-in Site tools discoverable.

## Imperative, declarative, or hybrid

Use imperative registration when the action:

- invokes application JavaScript;
- depends on route/component/selection state;
- manipulates a map, chart, canvas, editor, or store;
- performs inspection or navigation beyond a form;
- needs explicit lifecycle or callback control.

Use declarative registration only under the `webmcp-declarative` experimental profile when:

- an existing semantic HTML form already owns the workflow;
- fields and labels accurately describe the input;
- the target browser's declarative behavior is verified;
- normal submit validation and user-visible focus remain correct.

Use a hybrid when form filling and imperative state operations are both real parts of the journey.

The supplied draft leaves declarative algorithms unfinished. Browser-specific attributes and events therefore belong to a named experimental profile, not the document baseline. ChatGPT Site tools exclude declarative tools in the supplied product snapshot.

## WebMCP versus MCP

Use state and availability, not naming fashion.

| Question | WebMCP | MCP |
|---|---|---|
| Must the page be open? | Yes for current document WebMCP; a separate Service Worker proposal explores background use | No |
| Does current DOM/UI state matter? | Often | Usually not |
| Does the human inspect the same interface? | Yes | Not necessarily |
| Is availability tab/document-bound? | Yes | Usually service-bound |
| Are browser origins and Permissions Policy native concerns? | Yes | No |
| Is the capability primarily backend/background? | Usually no | Yes |

For **DUAL**, the page adapter and MCP server may expose different operations but should call one authoritative service/action layer or versioned backend contract. A host agent may orchestrate both; WebMCP does not automatically call MCP, and an MCP server cannot substitute for requested page-bound WebMCP. Avoid two tools with the same name and apparent effect when an agent could see both. Read `dual-webmcp-mcp.md`.

## ChatGPT Site tools product surface

Treat product availability as live information. At use time, verify official documentation for:

- supported ChatGPT surfaces and desktop/browser requirements;
- eligible models and workspaces;
- user permission settings;
- rollout or geographic limits;
- supported publisher/API subset;
- declarative-form support;
- top-level and iframe discovery behavior;
- current inspection and recent-activity UI;
- confirmation behavior for consequential actions.

Do not freeze model names or workspace eligibility into generated code. Product controls supplement the site's own permission and confirmation rules; they do not replace them.

## Compatibility record template

```text
Compatibility profile:
Draft/source:
Source date:
Target browser/version:
Product/agent surface:
Publisher API:
Consumer API:
Declarative branch:
Permissions policy:
Cross-origin topology:
Known divergence:
Conformance checks run:
Native host checks run:
Fallback:
```

A truthful record is more useful than a claim of “WebMCP compatible” without a target.
