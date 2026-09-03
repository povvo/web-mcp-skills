# WebMCP product compiler

Use this reference for CREATE and EXTEND work. The output is a working web product with a genuine WebMCP surface, not merely a registration module.

## Build profile

Record:

```text
mode: CREATE | EXTEND
surface: WEBMCP | DUAL
targets: one or more compatibility profiles
experimental: declarative and/or service-worker only when selected
release: DEVELOPMENT | PRODUCTION | CHALLENGE
framework: detected or explicitly chosen
```

If the user supplies enough product direction, proceed. Ask only when the missing choice would materially change the product, state model, deployment, or external effect.

## Completion model

A capability is complete only when this chain is real:

```text
human goal
→ shared artifact or page state
→ normal UI entry point
→ canonical operation
→ validation/auth/persistence/effects
→ WebMCP adapter
→ optional MCP adapter
→ visible and structured evidence
→ tests
```

Registration without the shared artifact, operation, or visible effect is scaffolding, not a finished capability.

## CREATE mode

CREATE applies to a new app or a repository that lacks the product foundations needed for the requested journey.

Implement, as required:

- domain types and canonical state;
- persistence or backend access;
- typed operations;
- ordinary human controls;
- loading, success, conflict, partial, and error behavior;
- agent activity or authorship where useful;
- WebMCP adapters;
- optional MCP adapters;
- tests and release configuration.

Choose the smallest coherent product boundary. Do not create a tool dashboard whose only purpose is to demonstrate registration. The application must remain useful when `document.modelContext` is absent.

## EXTEND mode

EXTEND starts from the existing user journey. Trace current UI, route, state, services, validation, authorization, persistence, tests, and visible feedback.

Classify each proposed operation:

- **existing** — callable application operation already used by the UI;
- **extract** — logic exists inside a UI event handler and should be moved behind a typed boundary;
- **create** — the agreed product journey requires a capability the app does not yet have;
- **reject** — decorative, navigation-only, unowned, or outside the requested product.

A created operation in EXTEND mode needs a named UI/state owner and tests. Do not bypass existing protections or add a shadow state model.

## Canonical operation design

Prefer an application boundary such as:

```ts
type OperationContext = {
  signal?: AbortSignal;
  actor: "human" | "agent" | "system";
};

async function updateArtifact(
  input: UpdateArtifactInput,
  context: OperationContext,
): Promise<UpdateArtifactResult> {
  // validate, authorize, commit, reconcile visible state, return evidence
}
```

Human UI and adapters call this operation. They may format inputs or render results, but must not reimplement its business rules.

When browser and server processes cannot import the same function, share a versioned backend/domain contract instead:

```text
human UI ───────┐
WebMCP adapter ─┼→ application service/API → canonical durable state
MCP adapter ────┘
```

## Shared visible state

The page must expose the result a person needs to inspect or continue:

- changed content or entity;
- updated selection, map, canvas, schedule, grid, cart, or dashboard;
- comment or revision attached to its subject;
- generated artifact or download;
- operation status and recoverable error;
- authorship or activity when collaboration would otherwise be ambiguous.

Do not update a hidden demonstration object while leaving the normal product unchanged.

## Concurrency and recovery

Evaluate shared mutable work for:

- stable entity IDs;
- revision, ETag, or expected-version preconditions;
- protected human-edited fields;
- partial batch acceptance;
- conflict results containing current state;
- undo, history, or another recoverable correction path;
- cancellation before work, during work, and after commit.

Use these mechanisms only where the product needs them. Document why a simple operation does not require them.

## Tool topology

Prefer:

```text
inspect/list/get → create/update/run → inspect/validate/export
```

The number of tools is not a quality target. A three-tool surface can be complete; a twenty-tool surface can be unusable. Add a tool only when it exposes a coherent user job and can be reliably distinguished from its neighbors.

Reject:

- `open_tab`, `click_button`, or other browser-driving wrappers;
- tools that only return a prepared URL when the requested operation should execute;
- a success result without state evidence;
- generated proxies over missing handlers;
- agent-only state that the person cannot review;
- one tool per endpoint without a user-journey reason.

## Activity and provenance

Add only the product-appropriate amount of visibility:

- WebMCP supported or unavailable;
- current/recent agent operation;
- success, conflict, partial, or failure state;
- actor identity;
- changed entity/revision;
- inspectable generated content or query.

The browser or ChatGPT may provide its own call history. Application-level visibility remains necessary when the human needs to understand or continue the changed artifact.

## Capability map

Maintain a compact table during implementation:

| Capability | UI owner | Canonical operation | WebMCP tool | MCP tool | Visible effect | Result evidence | Tests |
|---|---|---|---|---|---|---|---|

For WEBMCP, the MCP column is absent. For DUAL, adapters may expose different subsets; record why.

## Product completion gate

- Mode, surface, targets, experimental branches, framework, and release are explicit.
- The normal human product works without WebMCP.
- Every tool reaches a real canonical operation.
- Human UI and tools reconcile through the same state path.
- Tool effects are visible or durably inspectable.
- Results contain JSON-safe evidence rather than a bare success flag.
- Shared mutable state has proportionate conflict/recovery behavior.
- Unsupported-browser behavior is usable.
- Deterministic and live evidence are reported separately.

