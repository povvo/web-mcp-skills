import test from "node:test";
import assert from "node:assert/strict";
import {createReleaseRailApplication} from "../src/domain.mjs";
import {registerWebMCPTools, WEBMCP_TOOL_NAMES} from "../webmcp-tools.js";

test("generated tools register and invoke the canonical release operations", async (t) => {
  const tools = new Map();
  globalThis.document = {modelContext: {async registerTool(tool) { tools.set(tool.name, tool); }}};
  t.after(() => { delete globalThis.document; });
  const app = createReleaseRailApplication();
  const registration = await registerWebMCPTools({inspectReleaseRail: app.inspectReleaseRail, advanceReleaseStep: app.advanceReleaseStep, reopenReleaseStep: app.reopenReleaseStep});
  t.after(() => registration.dispose());
  assert.deepEqual([...WEBMCP_TOOL_NAMES], ["inspect_release_rail", "advance_release_step", "reopen_release_step"]);
  const result = await tools.get("advance_release_step").execute({expectedRevision: 0}, {});
  assert.equal(result.completedStepId, "contract");
  assert.equal((await tools.get("inspect_release_rail").execute({}, {})).currentStep.id, "tests");
});
