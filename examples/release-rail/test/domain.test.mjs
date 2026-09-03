import test from "node:test";
import assert from "node:assert/strict";
import {createReleaseRailApplication} from "../src/domain.mjs";

function storage() { const values = new Map(); return {getItem: (key) => values.get(key) ?? null, setItem: (key, value) => values.set(key, value)}; }

test("the rail advances one durable step at a time", async () => {
  const app = createReleaseRailApplication({storage: storage()});
  const first = await app.advanceReleaseStep({expectedRevision: 0});
  assert.deepEqual(first, {railId: "release-rail", completedStepId: "contract", nextCurrentStepId: "tests", completeCount: 1, revision: 1});
  assert.equal((await app.inspectReleaseRail({})).currentStep.id, "tests");
});

test("reopening a completed step returns later states to pending", async () => {
  const app = createReleaseRailApplication({storage: storage()});
  await app.advanceReleaseStep({expectedRevision: 0});
  await app.advanceReleaseStep({expectedRevision: 1});
  const result = await app.reopenReleaseStep({stepId: "contract", expectedRevision: 2});
  assert.deepEqual(result.affectedStepIds, ["tests", "evidence"]);
  assert.deepEqual(app.getState().steps.map((step) => step.state), ["current", "pending", "pending", "pending"]);
});

test("stale revisions and invalid step states do not mutate the rail", async () => {
  const app = createReleaseRailApplication({storage: storage()});
  await assert.rejects(() => app.advanceReleaseStep({expectedRevision: 3}), {name: "RevisionConflictError"});
  await assert.rejects(() => app.reopenReleaseStep({stepId: "contract", expectedRevision: 0}), {name: "InvalidStepStateError"});
  assert.equal(app.getState().revision, 0);
});
