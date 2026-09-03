import assert from "node:assert/strict";
import test from "node:test";

import { generateModule, installShim, validHandlers } from "./helpers.mjs";

const invalidCases = [
  ["BigInt", () => ({ value: 1n }), /unsupported bigint/],
  ["undefined", () => ({ value: undefined }), /unsupported undefined/],
  ["function", () => ({ value: () => true }), /unsupported function/],
  ["symbol", () => ({ value: Symbol("x") }), /unsupported symbol/],
  ["NaN", () => ({ value: Number.NaN }), /number must be finite/],
  ["Infinity", () => ({ value: Infinity }), /number must be finite/],
  ["Date", () => ({ value: new Date("2026-01-01") }), /Date instances/],
  ["Map", () => ({ value: new Map([["a", 1]]) }), /Map instances/],
  ["Set", () => ({ value: new Set([1]) }), /Set instances/],
  ["custom instance", () => ({ value: new (class Fixture {})() }), /Fixture instances/],
  ["sparse array", () => ({ value: Array(2) }), /arrays must be dense/],
  ["symbol-keyed object", () => {
    const value = {};
    value[Symbol("hidden")] = true;
    return { value };
  }, /symbol-keyed object/],
  ["cyclic object", () => {
    const value = {};
    value.self = value;
    return { value };
  }, /cyclic reference/],
];

for (const [name, makeResult, pattern] of invalidCases) {
  test(`publisher rejects ${name} results before transport`, async () => {
    const generated = await generateModule();
    const shim = await installShim();
    try {
      await generated.registerWebMCPTools(validHandlers({
        inspectDashboardSeries: async () => makeResult(),
      }));
      const tool = (await shim.modelContext.getTools())[0];
      await assert.rejects(shim.modelContext.executeTool(tool, {}), pattern);
    } finally {
      shim.restore();
    }
  });
}

test("publisher accepts nested intentional JSON values", async () => {
  const generated = await generateModule();
  const shim = await installShim();
  const expected = {
    ok: true,
    count: 2,
    text: "ready",
    nullable: null,
    nested: [{ id: "a" }, { id: "b" }],
  };
  try {
    await generated.registerWebMCPTools(validHandlers({
      inspectDashboardSeries: async () => expected,
    }));
    const actual = await shim.modelContext.executeTool((await shim.modelContext.getTools())[0], {});
    assert.deepEqual(actual, expected);
  } finally {
    shim.restore();
  }
});

