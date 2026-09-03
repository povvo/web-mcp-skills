# DUAL adapter template

These modules keep WebMCP and MCP transport concerns outside the application's
operation layer:

```text
WebMCP adapter ─┐
                ├→ one operation map → one handler object → canonical state
MCP adapter ───┘
```

`contract.mjs` resolves both surfaces through the same top-level `handler`
mapping and rejects missing implementations before either surface is exposed.
The WebMCP adapter adds page evidence after normal UI reconciliation. The MCP
adapter adds service evidence and provides `bindServer(server, options)`. The
template intentionally does not vendor or emulate the MCP transport; the
application owning the server selects and pins its SDK.

The high-level official MCP TypeScript SDK accepts Zod input schemas at
`McpServer.registerTool`, while this bundle's portable contract stores JSON
Schema. Bind it explicitly so schema conversion is visible and testable:

```js
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import * as z from "zod/v4";

import {
  createMCPAdapter,
  createMCPTypeScriptSDKInputSchemaAdapter,
} from "./mcp-adapter.mjs";

const adapter = createMCPAdapter({ contract, operations });
const server = new McpServer({ name: "my-server", version: "1.0.0" });
adapter.bindServer(server, {
  inputSchemaAdapter: createMCPTypeScriptSDKInputSchemaAdapter(z),
});
```

The supplied converter preserves the JSON Schema subset used by the templates
and fails closed on references or constraints it cannot translate exactly. A
project using richer schemas should inject its own synchronous
`inputSchemaAdapter(schema, context)`. Hosts whose `registerTool` API natively
accepts JSON Schema may omit the option and receive an isolated JSON copy.

Use surface-distinct tool names. A page tool should state its visible/open-page
scope; an MCP tool should state that it works independently of the page. Do not
map every operation twice: keep ephemeral selection/view operations on WebMCP
and background/audit operations on MCP.

The executable `validation/fixtures/dual-shared-board` example demonstrates
shared mutation, cross-surface revision visibility, cancellation,
stale-revision error parity, WebMCP-only selection, MCP-only audit access, and
schema-adapter preflight before server registration.
