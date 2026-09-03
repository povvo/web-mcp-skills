import assert from "node:assert/strict";
import test from "node:test";

import { generateModule, installShim, validHandlers } from "./helpers.mjs";

test("suspension preserves registrations and resumes one queued invocation", async () => {
  const generated = await generateModule();
  const shim = await installShim();
  try {
    let calls = 0;
    await generated.registerWebMCPTools(validHandlers({
      inspectDashboardSeries: async () => ({ calls: ++calls }),
    }));
    const tool = (await shim.modelContext.getTools())[0];
    shim.suspend();
    assert.equal(shim.registrations.size, 2);
    await assert.rejects(shim.modelContext.getTools(), { name: "InvalidStateError" });
    const queued = shim.modelContext.executeTool(tool, {});
    await Promise.resolve();
    assert.equal(calls, 0);
    assert.equal(shim.logs.invocations.at(-1).status, "queued");
    shim.resume();
    assert.deepEqual(await queued, { calls: 1 });
    assert.equal(calls, 1);
  } finally {
    shim.restore();
  }
});

test("queued invocation can be cancelled before resume", async () => {
  const generated = await generateModule();
  const shim = await installShim();
  try {
    let calls = 0;
    await generated.registerWebMCPTools(validHandlers({
      inspectDashboardSeries: async () => ({ calls: ++calls }),
    }));
    const tool = (await shim.modelContext.getTools())[0];
    shim.suspend();
    const controller = new AbortController();
    const queued = shim.modelContext.executeTool(tool, {}, { signal: controller.signal });
    controller.abort(new DOMException("cancel queued", "AbortError"));
    await assert.rejects(queued, { name: "AbortError" });
    shim.resume();
    assert.equal(calls, 0);
    assert.equal(shim.logs.aborts.at(-1).phase, "queued");
  } finally {
    shim.restore();
  }
});

test("registration is rejected while the document is suspended", async () => {
  const generated = await generateModule();
  const shim = await installShim({ fullyActive: false });
  try {
    await assert.rejects(
      generated.registerWebMCPTools(validHandlers()),
      { name: "InvalidStateError" },
    );
    assert.equal(shim.registrations.size, 0);
  } finally {
    shim.restore();
  }
});

