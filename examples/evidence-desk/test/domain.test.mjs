import test from "node:test";
import assert from "node:assert/strict";
import {createEvidenceDeskApplication} from "../src/domain.mjs";

function storage() { const values = new Map(); return {getItem: (key) => values.get(key) ?? null, setItem: (key, value) => values.set(key, value)}; }

test("selection changes the shared record without changing evidence state", async () => {
  const app = createEvidenceDeskApplication({storage: storage()});
  const result = await app.selectEvidenceRecord({recordId: "site-tools", expectedRevision: 0});
  assert.deepEqual(result, {deskId: "evidence-desk", recordId: "site-tools", evidenceState: "blocked", revision: 1});
  assert.equal(app.getState().selectedRecord.state, "blocked");
});

test("annotations preserve the named record state", async () => {
  const app = createEvidenceDeskApplication({storage: storage(), createId: () => "note-1"});
  const result = await app.annotateEvidenceRecord({recordId: "deployment", note: " Provider receipt still required. ", expectedRevision: 0});
  assert.equal(result.annotation.note, "Provider receipt still required.");
  assert.equal(result.evidenceState, "prepared");
  assert.equal((await app.inspectEvidenceDesk({})).selectedRecord.state, "prepared");
});

test("stale and invalid annotations do not write partial state", async () => {
  const app = createEvidenceDeskApplication({storage: storage()});
  await assert.rejects(() => app.annotateEvidenceRecord({recordId: "wpt", note: "Stale", expectedRevision: 4}), {name: "RevisionConflictError"});
  await assert.rejects(() => app.annotateEvidenceRecord({recordId: "wpt", note: " ", expectedRevision: 0}), TypeError);
  assert.equal(app.getState().annotations.length, 0);
});
