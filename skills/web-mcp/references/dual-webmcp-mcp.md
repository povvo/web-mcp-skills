# Dual WebMCP and MCP architecture

Use this reference only when `surface: DUAL` is selected or when deciding whether both surfaces are independently valuable.

## The boundary

- **WebMCP** exposes capabilities of the currently open website to the browser's agent. It is appropriate for visible page state, a current selection, a route, a canvas, a map, an editor, a dashboard, or another shared human-agent artifact.
- **MCP** connects an AI application to a local or remote server. It is appropriate for page-independent data and operations that must remain usable without an open website.

An MCP server does not become WebMCP because it serves similarly named tools. WebMCP does not inherit or automatically call MCP tools connected to the host.

## Valid composition patterns

### Host-agent orchestration

```text
external MCP/context → host agent → WebMCP tool → visible page change
```

Example: an MCP connector reads source records; the agent calls a WebMCP tool to add selected records to the open planning canvas; the person reviews and edits them.

### Shared backend contract

```text
WebMCP adapter ─┐
                ├→ versioned application service/API → durable state
MCP adapter ────┘
```

Use this when browser and server processes cannot share an in-memory module.

### Shared package

```text
human UI ───────┐
WebMCP adapter ─┼→ shared domain package → repositories/services
MCP adapter ────┘
```

Use this when both runtimes can safely import the same operation layer.

### Explicit application bridge

A page may call its own backend or an explicitly implemented MCP client. Treat that as normal application architecture with authentication, transport, failure, and deployment requirements. Never imply that the WebMCP API provides the bridge.

## Surface allocation

Keep on WebMCP:

- current selection or editor mode;
- ephemeral canvas/map/view state;
- a visible preview or draft;
- actions that must update the open UI immediately;
- operations using the page's signed-in session where that is the intended product path.

Consider MCP for:

- cross-project or account-wide search;
- background or scheduled service work;
- durable record management independent of the page;
- operations used by clients that never open the website;
- external systems that already expose an MCP contract.

Do not expose every operation twice. Duplicate tools increase model ambiguity and can create competing state paths.

## Adapter contract

For each shared operation, define:

- canonical input and result types;
- actor and authentication context;
- authorization and validation owner;
- idempotency and revision behavior;
- commit boundary and cancellation semantics;
- transport-specific error mapping;
- visible WebMCP reconciliation;
- durable MCP evidence.

When binding the high-level official MCP TypeScript SDK, convert the portable
JSON input schemas to the SDK's pinned Zod version explicitly. Use
`createMCPTypeScriptSDKInputSchemaAdapter(z)` from the DUAL template for its
supported subset, or inject a project-owned synchronous adapter for richer
schemas. Conversion must complete and validate for every tool before any server
registration begins; never silently discard an unsupported constraint.

WebMCP may return page-oriented evidence such as selection, visible revision, and route state. MCP may return service-oriented evidence such as record version or job ID. Both must describe the same underlying outcome truthfully.

## Authentication and authority

Do not assume that a browser session and an MCP server identity are interchangeable. Record separately:

- page/session identity;
- MCP client/server identity;
- application user or tenant;
- operation authorization point;
- confirmation or review path;
- audit actor.

If identities cannot be reconciled, do not describe the adapters as one coherent authorized operation.

## Failure behavior

Test:

- WebMCP succeeds while MCP is unavailable;
- MCP succeeds while the page is closed;
- shared backend rejects stale revisions consistently;
- one adapter times out after the commit boundary;
- retries do not duplicate non-idempotent effects;
- external MCP content remains data rather than executable instruction;
- the page visibly reconciles changes originating through MCP when the product promises that behavior.

## DUAL verification

Evidence needs three independent layers:

1. **WebMCP:** native discovery/invocation and visible page effect.
2. **MCP:** server discovery/invocation and durable service effect.
3. **Composition:** a host agent uses the intended combination for a real user journey.

Passing either adapter alone is not composition evidence. A simulated MCP response inside the page is not an MCP server receipt.
For a live TypeScript SDK receipt, record the pinned SDK and Zod versions,
transport kind, negotiated server identity, discovered tool names, protocol
request methods, calls made after page teardown, and the shared durable
revision observed from both surfaces.

## Completion gate

- Both surfaces are independently useful.
- At least one genuine WebMCP tool exists.
- Shared behavior uses one operation or backend contract.
- Page-bound and page-independent responsibilities are explicit.
- Auth, revision, cancellation, error, and result mappings are tested.
- The host-agent composition is run or marked `NOT RUN`.
- No output claims that WebMCP automatically calls MCP or that MCP substitutes for WebMCP.
