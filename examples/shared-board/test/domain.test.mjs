import test from "node:test";
import assert from "node:assert/strict";
import {createBoardApplication} from "../src/domain.mjs";

function storage() {
  const values = new Map();
  return {getItem: (key) => values.get(key) ?? null, setItem: (key, value) => values.set(key, value)};
}

test("human and WebMCP entrypoints can share the revisioned board operation", async () => {
  const app = createBoardApplication({storage: storage(), createId: () => "item-1"});
  const added = await app.addBoardItem({title: " Verify release receipt ", expectedRevision: 0});
  const inspected = await app.inspectBoard({});
  assert.deepEqual(added, {boardId: "shared-board", itemId: "item-1", item: {id: "item-1", title: "Verify release receipt"}, itemCount: 1, revision: 1});
  assert.equal(inspected.items[0].title, "Verify release receipt");
  assert.equal(inspected.revision, 1);
});

test("a stale write is rejected without changing the board", async () => {
  const app = createBoardApplication({storage: storage(), createId: () => "item-1"});
  await app.addBoardItem({title: "First", expectedRevision: 0});
  await assert.rejects(() => app.addBoardItem({title: "Stale", expectedRevision: 0}), {name: "RevisionConflictError"});
  assert.equal((await app.inspectBoard({})).itemCount, 1);
});

test("invalid input is preserved as a failed operation, not a partial write", async () => {
  const app = createBoardApplication({storage: storage()});
  await assert.rejects(() => app.addBoardItem({title: "   ", expectedRevision: 0}), TypeError);
  assert.equal((await app.inspectBoard({})).revision, 0);
});
