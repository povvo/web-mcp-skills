import test from "node:test";
import assert from "node:assert/strict";
import {createBoardApplication} from "../src/domain.mjs";
import {registerWebMCPTools, WEBMCP_TOOL_NAMES} from "../webmcp-tools.js";

test("generated tools register and invoke the canonical board operations", async (t) => {
  const tools = new Map();
  globalThis.document = {modelContext: {async registerTool(tool) { tools.set(tool.name, tool); }}};
  t.after(() => { delete globalThis.document; });
  const app = createBoardApplication({createId: () => "tool-item"});
  const registration = await registerWebMCPTools({inspectBoard: app.inspectBoard, addBoardItem: app.addBoardItem});
  t.after(() => registration.dispose());
  assert.deepEqual([...WEBMCP_TOOL_NAMES], ["inspect_board", "add_board_item"]);
  assert.deepEqual([...tools.keys()], [...WEBMCP_TOOL_NAMES]);
  const result = await tools.get("add_board_item").execute({title: "Agent item", expectedRevision: 0}, {});
  assert.equal(result.itemId, "tool-item");
  assert.equal((await tools.get("inspect_board").execute({}, {})).itemCount, 1);
});
