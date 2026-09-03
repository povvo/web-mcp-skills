# Architecture

The core design decision is ownership. State and business effects belong to an application operation. The human interface, WebMCP, and optional MCP server are adapters around that operation.

```text
                       current document lifetime

person ─> semantic UI ───────┐
                             │
agent  ─> WebMCP adapter ────┼─> canonical operation ─> state/service
                             │                              │
MCP client ─> MCP adapter ───┘                              ├─> visible render
                                                            └─> result evidence
```

This relationship matters because WebMCP and MCP are separate protocols with different discovery, lifecycle, authority, and transport. Shared vocabulary is not shared execution.

## Layers

### 1. Product journey

Name the shared artifact, user goal, normal UI, state machine, effects, consequences, and evidence. Product nouns come from the product. The string “Web MCP” contributes no inventory system, dashboard, browser tabs, or tasteful little robots.

### 2. Canonical operations

Operations validate inputs, apply authorization and concurrency rules, commit persistence, publish state, and return JSON-safe results. They accept cancellation when the underlying work can be cancelled. An operation should be callable without pretending to click its own interface.

### 3. Human interface

Use native controls and platform semantics. The interface renders canonical state, preserves failed input, labels loading/errors/results, and gives keyboard alternatives for every action. Tool calls and human actions reconcile through the same subscriptions or query invalidation path.

### 4. WebMCP adapter

The adapter exposes names, titles, descriptions, input schemas, annotations, lifetime, and execute callbacks. It binds handlers and returns operation evidence. Document and route teardown dispose registration. Dynamic availability may use narrower lifetimes when the operation genuinely depends on selection, mode, or permission.

### 5. Optional MCP adapter

The MCP adapter exposes the same operation to an MCP client through stdio, Streamable HTTP, or the project’s existing transport. It owns MCP protocol framing and host composition, not separate product rules.

### 6. External composition

A canonical operation may call databases, remote APIs, queues, model endpoints, or an MCP client. WebMCP can therefore initiate work that reaches those systems, but only because the application implements the bridge. Test the actual provider and transport. A diagram arrow is prepared infrastructure.

## State and concurrency

The examples use monotonic integer revisions. A mutating call supplies `expectedRevision`; the operation compares it immediately before commit. On mismatch, it returns a scoped conflict and preserves current state.

Other products may use protected fields, semantic anchors, partial acceptance, idempotency keys, transactions, or service-native version tokens. The tool schema must expose the concurrency input the operation actually uses.

## Tool result contract

Return the smallest result that lets the caller and person inspect the effect:

- stable artifact and record identifiers;
- committed revision or version;
- affected object or scope;
- measured count when useful;
- explicit partial, blocked, or failed state;
- recovery information when another action is required.

Do not return “success” alone. It is a mood, not a receipt.

## Trust and effects

Every tool declares a real effect such as read, local write, remote write, external communication, purchase, permission change, or destructive action. It also declares output trust and whether user-generated or external content can appear in results. Those fields inform host behavior and evaluation; they do not replace application authorization.

## Proposal boundaries

The skill models declarative forms and service-worker WebMCP as explicit proposal profiles. Generated production document adapters do not silently include unresolved service-worker discovery, installation, sessions, or cross-document form behavior. Official work remains available in the package references and [preserved source snapshots](official/README.md), with maturity attached.
