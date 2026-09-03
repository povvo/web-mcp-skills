import assert from "node:assert/strict";
import test from "node:test";

import { generateModule, installShim, validHandlers } from "./helpers.mjs";

test("missing actual handler prevents every registration", async () => {
  const generated = await generateModule();
  const shim = await installShim();
  try {
    await assert.rejects(
      generated.registerWebMCPTools({ inspectDashboardSeries: async () => ({}) }),
      /Missing WebMCP application handler: setDashboardDateRange/,
    );
    assert.equal(shim.registrations.size, 0);
    assert.equal(shim.logs.registrations.length, 0);
  } finally {
    shim.restore();
  }
});

test("registration, discovery, invocation, and disposal share one real handler map", async () => {
  const generated = await generateModule();
  const shim = await installShim();
  try {
    const handlers = validHandlers();
    const registration = await generated.registerWebMCPTools(handlers);
    assert.deepEqual(registration.registered, [
      "inspect_dashboard_series",
      "set_dashboard_date_range",
    ]);
    const tools = await shim.modelContext.getTools();
    assert.deepEqual(tools.map((tool) => tool.name), registration.registered);
    const result = await shim.modelContext.executeTool(tools[0], { seriesId: "revenue" });
    assert.equal(result.seriesId, "revenue");
    assert.equal(shim.logs.invocations[0].status, "passed");
    registration.dispose();
    registration.dispose();
    assert.equal(shim.registrations.size, 0);
  } finally {
    shim.restore();
  }
});

test("Nth registration failure rolls back earlier registrations", async () => {
  const generated = await generateModule();
  const shim = await installShim({ failRegistrationAt: 2 });
  try {
    await assert.rejects(
      generated.registerWebMCPTools(validHandlers()),
      /Injected registration failure at attempt 2/,
    );
    assert.equal(shim.registrations.size, 0);
    assert.deepEqual(shim.logs.removals.map((entry) => entry.name), [
      "inspect_dashboard_series",
    ]);
  } finally {
    shim.restore();
  }
});

test("handler removal after ready fails explicitly without invoking stale logic", async () => {
  const generated = await generateModule();
  const shim = await installShim();
  try {
    const handlers = validHandlers();
    await generated.registerWebMCPTools(handlers);
    delete handlers.setDashboardDateRange;
    const tool = (await shim.modelContext.getTools()).find(
      (candidate) => candidate.name === "set_dashboard_date_range",
    );
    await assert.rejects(
      shim.modelContext.executeTool(tool, { startDate: "2026-01-01", endDate: "2026-01-31" }),
      /Missing WebMCP application handler: setDashboardDateRange/,
    );
  } finally {
    shim.restore();
  }
});

test("execution AbortSignal reaches the real handler", async () => {
  const generated = await generateModule();
  const shim = await installShim();
  try {
    let observedSignal;
    const handlers = validHandlers({
      inspectDashboardSeries: async (_input, context) => {
        observedSignal = context.signal;
        await new Promise((resolve, reject) => {
          context.signal.addEventListener("abort", () => reject(context.signal.reason), { once: true });
          setTimeout(resolve, 1000);
        });
        return {};
      },
    });
    await generated.registerWebMCPTools(handlers);
    const tool = (await shim.modelContext.getTools())[0];
    const execution = new AbortController();
    const promise = shim.modelContext.executeTool(tool, {}, { signal: execution.signal });
    execution.abort(new DOMException("cancelled by test", "AbortError"));
    await assert.rejects(promise, { name: "AbortError" });
    assert.equal(observedSignal, execution.signal);
  } finally {
    shim.restore();
  }
});

test("unsupported host returns fallback only after validating handlers", async () => {
  const generated = await generateModule();
  const previousDocument = globalThis.document;
  delete globalThis.document;
  try {
    await assert.rejects(
      generated.registerWebMCPTools({ inspectDashboardSeries: async () => ({}) }),
      /Missing WebMCP application handler/,
    );
    const fallback = await generated.registerWebMCPTools(validHandlers());
    assert.equal(fallback.supported, false);
    assert.deepEqual(fallback.registered, []);
  } finally {
    if (previousDocument !== undefined) globalThis.document = previousDocument;
  }
});

