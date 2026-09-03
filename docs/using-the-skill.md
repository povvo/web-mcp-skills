# Using the `web-mcp` skill

The portable skill lives at `skills/web-mcp/`. It can create a WebMCP-enabled application or extend an existing one. It can also generate a dual WebMCP and MCP surface when both adapters share the same application operation or backend contract.

## Install

After this repository is published, install only the skill with:

```powershell
npx skills add povvo/web-mcp --skill web-mcp
```

For local inspection before publication:

```powershell
npx skills add . --skill web-mcp --list
```

The installable unit is `skills/web-mcp/`. Repository docs, examples, build evidence, and CI remain outside it. The package contains no `node_modules`, Python environment, external docs path, or generated cache.

## Ask for a product, not a registration snippet

A useful request names the product journey and its state owner:

> Add WebMCP to this issue board. People and agents must inspect the same current issue, assign it through the existing assignment service, and see the resulting assignee and revision in the page. Add a page-independent MCP adapter over the same service as well.

The skill then identifies:

- the human entrypoint;
- canonical operations and their owner;
- state reads, writes, persistence, and revisions;
- tool names, descriptions, schemas, effects, and result evidence;
- registration lifetime and disposal;
- UI reconciliation after human and tool actions;
- deterministic, browser, host, model, and release gates.

“Add AI tools” omits most of this. It is admirably compact.

## CREATE mode

Use CREATE when the application does not exist. The skill builds a vertical slice:

1. Define the shared artifact and finite user journey.
2. Implement canonical domain operations and persistence.
3. Build the normal human interface over those operations.
4. Describe the same operations in `toolset.json`.
5. Bind product, state, UI, and tools in `product.json`.
6. Compile the WebMCP adapter.
7. Test the operations, adapter, browser state reconciliation, and requested hosts.

The [three examples](examples.md) use CREATE mode.

## EXTEND mode

Use EXTEND for an existing application. The skill inspects repository structure, routes, current UI handlers, state ownership, APIs, tests, and build commands before changing anything. It reuses existing operations. If a required operation is missing, it adds that operation to the application owner first, then binds both the visible interface and WebMCP adapter to it.

DOM-click proxy tools are not integration. They are browser automation wearing a name badge.

## Product compiler

Each product uses two contracts:

- `product.json` binds the user journey, application state, normal UI, canonical operations, target hosts, optional proposal profiles, and evidence gates.
- `toolset.json` defines discoverable tool metadata, JSON Schema inputs, annotations, lifetime, effects, preconditions, failure modes, trust, and success evidence.

Inspect a build plan:

```powershell
python -B skills/web-mcp/scripts/webmcp_toolkit.py product-plan examples/shared-board/product.json --target vanilla-js
```

Compile and write generated artifacts:

```powershell
python -B skills/web-mcp/scripts/webmcp_toolkit.py compile-product examples/shared-board/product.json --target vanilla-js --output-dir examples/shared-board --write --force
```

The compiler emits:

- `webmcp-tools.js` — the runtime registration adapter;
- `webmcp-capabilities.json` — the resolved capability map;
- `webmcp-build-plan.json` — product and evidence plan;
- `webmcp-compile-receipt.json` — hashes and written artifacts.

Generated adapters validate handler presence, propagate cancellation, reject non-JSON-safe results, register against `document.modelContext`, and dispose through an abort signal. They do not invent domain behavior.

## Frameworks and types

The compiler supports vanilla JavaScript, TypeScript, React, Next.js, Vue, Svelte, and Angular targets. Framework recipes keep registration aligned with document, route, component, selection, mode, or permission lifetime. The skill’s pinned type-validation workspace is internal validation material; application projects may use the current [`webmcp-types`](https://www.npmjs.com/package/webmcp-types) release.

## Dual WebMCP and MCP output

Choose a dual surface when the open page needs WebMCP and a page-independent client needs an MCP server. Both surfaces should call the same backend/domain contract:

```text
human UI ───────┐
WebMCP adapter ─┼─> canonical operation ─> state/service ─> result evidence
MCP adapter ────┘
```

The WebMCP tool may call a canonical operation that itself uses remote APIs or an MCP-backed service. The browser does not automatically discover an arbitrary MCP server and compose it on the page’s behalf. That composition belongs to the application architecture and must be tested through the real transport.

## Portable by construction

The skill’s required instructions, scripts, schemas, references, agents, validation fixtures, and brand icon live inside `skills/web-mcp/`. Run its self-test from that directory or through the toolkit. Packaging copies only that tree into the `.skill` archive, then compares source and fresh extraction by path and SHA-256.

Repository documentation may help a human understand the package. The package must not require it to function.
