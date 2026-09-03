import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

import { installModelContextShim } from "../../../assets/testing/model-context-shim.mjs";
import {
  createMCPAdapter,
  createMCPTypeScriptSDKInputSchemaAdapter,
} from "../../../assets/templates/dual/mcp-adapter.mjs";
import { createWebMCPAdapter } from "../../../assets/templates/dual/webmcp-adapter.mjs";
import { createSharedBoard } from "./operations.mjs";


const contract = JSON.parse(await readFile(new URL("./dual-contract.json", import.meta.url), "utf8"));
const board = createSharedBoard();
const page = {
  route: "/boards/board-1",
  visibleRevision: 0,
  selectedItemId: null,
  actor: { id: "page-user" },
  setSelection(itemId) {
    this.selectedItemId = itemId;
  },
};
const unsubscribe = board.subscribe((receipt) => {
  page.visibleRevision = receipt.revision;
});

const webmcp = createWebMCPAdapter({
  contract,
  operations: board.operations,
  getPageContext: () => page,
});
const mcp = createMCPAdapter({
  contract,
  operations: board.operations,
  getRequestContext: () => ({ actor: { id: "mcp-client" } }),
});

const sharedOperationIds = contract.operations
  .filter((operation) => operation.surfaces.webmcp && operation.surfaces.mcp)
  .map((operation) => operation.operationId);
for (const operationId of sharedOperationIds) {
  const webBinding = webmcp.bindings.find((binding) => binding.operationId === operationId);
  const mcpBinding = mcp.bindings.find((binding) => binding.operationId === operationId);
  assert.ok(webBinding);
  assert.ok(mcpBinding);
  assert.equal(webBinding.handler, mcpBinding.handler);
  assert.equal(webBinding.operation, mcpBinding.operation);
}

assert.deepEqual(
  webmcp.bindings.map((binding) => binding.descriptor.name),
  contract.operations.flatMap((operation) => operation.surfaces.webmcp?.toolName ?? []),
);
assert.deepEqual(
  mcp.bindings.map((binding) => binding.descriptor.name),
  contract.operations.flatMap((operation) => operation.surfaces.mcp?.toolName ?? []),
);

const host = {};
const shim = installModelContextShim(host);
const registration = await webmcp.register(host.document.modelContext);
assert.equal(registration.supported, true);
assert.equal(shim.registrations.size, 3);

const webAdd = await shim.modelContext.executeTool("add_visible_board_item", {
  title: "First card",
  expectedRevision: 0,
});
assert.equal(webAdd.outcome.revision, 1);
assert.equal(webAdd.outcome.surface, "webmcp");
assert.equal(webAdd.evidence.visibleRevision, 1);

const mcpInspect = await mcp.callTool("inspect_board_record");
assert.equal(mcpInspect.structuredContent.outcome.revision, 1);
assert.deepEqual(mcpInspect.structuredContent.outcome.items.map((item) => item.title), ["First card"]);

const mcpAdd = await mcp.callTool("add_board_item", {
  title: "Second card",
  expectedRevision: 1,
});
assert.equal(mcpAdd.structuredContent.outcome.revision, 2);
assert.equal(mcpAdd.structuredContent.outcome.surface, "mcp");
assert.equal(page.visibleRevision, 2);

const webInspect = await shim.modelContext.executeTool("inspect_visible_board");
assert.equal(webInspect.outcome.revision, 2);
assert.deepEqual(webInspect.outcome.items.map((item) => item.title), ["First card", "Second card"]);

const webSelect = await shim.modelContext.executeTool("select_visible_board_item", { itemId: "item-2" });
assert.equal(webSelect.outcome.selectedItemId, "item-2");
assert.equal(webSelect.evidence.selectedItemId, "item-2");
assert.equal(page.selectedItemId, "item-2");

const audit = await mcp.callTool("read_board_audit", { limit: 10 });
assert.deepEqual(audit.structuredContent.outcome.entries.map((entry) => entry.surface), ["webmcp", "mcp"]);

const serverRegistrations = [];
const schemaAdapterContexts = [];
const boundNames = mcp.bindServer({
  registerTool(name, config, callback) {
    serverRegistrations.push({ name, config, callback });
  },
}, {
  inputSchemaAdapter(schema, context) {
    schemaAdapterContexts.push(context);
    return { sdkLikeSchema: true, source: schema };
  },
});
assert.deepEqual(boundNames, mcp.listTools().map((tool) => tool.name));
assert.deepEqual(serverRegistrations.map((entry) => entry.name), boundNames);
assert.deepEqual(schemaAdapterContexts.map((entry) => entry.toolName), boundNames);
assert.ok(serverRegistrations.every((entry) => entry.config.inputSchema.sdkLikeSchema === true));
const boundInspect = await serverRegistrations
  .find((entry) => entry.name === "inspect_board_record")
  .callback({}, {});
assert.equal(boundInspect.structuredContent.outcome.revision, 2);

let invalidSchemaRegistrationAttempted = false;
assert.throws(
  () => mcp.bindServer({
    registerTool() {
      invalidSchemaRegistrationAttempted = true;
    },
  }, {
    inputSchemaAdapter: async (schema) => schema,
  }),
  (error) => error?.code === "SERVER_INPUT_SCHEMA",
);
assert.equal(invalidSchemaRegistrationAttempted, false);
assert.throws(
  () => createMCPTypeScriptSDKInputSchemaAdapter({}),
  /z\.array must be a function/,
);

const invalidResultAdapter = createMCPAdapter({
  contract,
  operations: {
    ...board.operations,
    inspectBoard: async () => ({ erasedWithoutStrictValidation: undefined }),
  },
});
await assert.rejects(
  invalidResultAdapter.callTool("inspect_board_record"),
  (error) => error?.code === "RESULT_NOT_JSON",
);

let webConflict;
try {
  await shim.modelContext.executeTool("add_visible_board_item", {
    title: "Stale web card",
    expectedRevision: 0,
  });
} catch (error) {
  webConflict = error;
}
let mcpConflict;
try {
  await mcp.callTool("add_board_item", {
    title: "Stale MCP card",
    expectedRevision: 0,
  });
} catch (error) {
  mcpConflict = error;
}
assert.equal(webConflict?.code, "REVISION_CONFLICT");
assert.equal(mcpConflict?.code, "REVISION_CONFLICT");

const cancelled = new AbortController();
cancelled.abort(new DOMException("cancel fixture", "AbortError"));
await assert.rejects(
  mcp.callTool("inspect_board_record", {}, { signal: cancelled.signal }),
  { name: "AbortError" },
);
assert.equal(board.snapshot().revision, 2);

registration.dispose();
assert.equal(shim.registrations.size, 0);
const closedPageInspect = await mcp.callTool("inspect_board_record");
assert.equal(closedPageInspect.structuredContent.outcome.revision, 2);

unsubscribe();
shim.uninstall();
console.log(JSON.stringify({
  status: "PASS",
  sharedOperations: sharedOperationIds,
  webmcpTools: webmcp.bindings.map((binding) => binding.descriptor.name),
  mcpTools: mcp.bindings.map((binding) => binding.descriptor.name),
  sdkSchemaAdapterPreflight: "PASS",
  finalRevision: board.snapshot().revision,
  auditSurfaces: audit.structuredContent.outcome.entries.map((entry) => entry.surface),
  pageClosedMcpInvocation: "PASS",
}));
