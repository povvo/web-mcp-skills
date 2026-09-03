import test from "node:test";
import assert from "node:assert/strict";
import {createEvidenceDeskApplication} from "../src/domain.mjs";
import {registerWebMCPTools, WEBMCP_TOOL_NAMES} from "../webmcp-tools.js";

test("generated tools register and invoke the canonical evidence operations", async (t) => {
  const tools = new Map();
  globalThis.document = {modelContext: {async registerTool(tool) { tools.set(tool.name, tool); }}};
  t.after(() => { delete globalThis.document; });
  const app = createEvidenceDeskApplication({createId: () => "tool-note"});
  const registration = await registerWebMCPTools({inspectEvidenceDesk: app.inspectEvidenceDesk, selectEvidenceRecord: app.selectEvidenceRecord, annotateEvidenceRecord: app.annotateEvidenceRecord});
  t.after(() => registration.dispose());
  assert.deepEqual([...WEBMCP_TOOL_NAMES], ["inspect_evidence_desk", "select_evidence_record", "annotate_evidence_record"]);
  const result = await tools.get("annotate_evidence_record").execute({recordId: "wpt", note: "Agent annotation", expectedRevision: 0}, {});
  assert.equal(result.annotationId, "tool-note");
  assert.equal((await tools.get("inspect_evidence_desk").execute({}, {})).selectedRecord.annotations.length, 1);
});
