import assert from "node:assert/strict";
import {spawnSync} from "node:child_process";
import {readFileSync} from "node:fs";
import {fileURLToPath} from "node:url";
import test from "node:test";

import {installShim} from "./helpers.mjs";

const toolkit = fileURLToPath(new URL("../../scripts/webmcp_toolkit.py", import.meta.url));
const fixture = new URL("../fixtures/create-shared-board/", import.meta.url);
const manifest = fileURLToPath(new URL("toolset.json", fixture));
const domain = await import(new URL("src/domain.mjs", fixture));

function generateFixtureAdapterSource() {
  const python = process.env.WEBMCP_TEST_PYTHON || "python";
  const result = spawnSync(
    python,
    ["-B", toolkit, "generate", manifest, "--target", "vanilla-js"],
    {encoding: "utf8"},
  );
  if (result.status !== 0) {
    throw new Error(`fixture generator failed (${result.status}): ${result.stderr || result.stdout}`);
  }
  return result.stdout.replace(/\r\n/g, "\n");
}

async function generateFixtureAdapter() {
  const source = generateFixtureAdapterSource();
  return import(`data:text/javascript;base64,${Buffer.from(source).toString("base64")}`);
}

test("CREATE fixture ships the exact generated adapter consumed by its browser entrypoint", () => {
  const generated = generateFixtureAdapterSource();
  const packaged = readFileSync(new URL("src/webmcp-tools.js", fixture), "utf8").replace(/\r\n/g, "\n");
  assert.equal(packaged, generated);

  const html = readFileSync(new URL("index.html", fixture), "utf8");
  assert.match(html, /<script\s+type="module"\s+src="\.\/src\/ui\.mjs"><\/script>/);
});

test("CREATE fixture packaged browser entrypoint registers tools and reconciles visible state", async () => {
  const previousDocument = globalThis.document;
  const registered = new Map();
  const elements = new Map([
    ["#board-items", {children: [], replaceChildren(...children) { this.children = children; }}],
    ["#item-count", {textContent: ""}],
    ["#revision", {textContent: ""}],
    ["#activity", {textContent: ""}],
    ["#add-item-form", {
      listeners: new Map(),
      attributes: new Map(),
      addEventListener(type, listener) { this.listeners.set(type, listener); },
      setAttribute(name, value) { this.attributes.set(name, value); },
      removeAttribute(name) { this.attributes.delete(name); },
    }],
    ["#item-title", {value: ""}],
  ]);
  const documentElement = {dataset: {}};
  globalThis.document = {
    documentElement,
    querySelector(selector) { return elements.get(selector) ?? null; },
    createElement(tagName) { return {tagName, dataset: {}, textContent: ""}; },
    modelContext: {
      async registerTool(tool) { registered.set(tool.name, tool); },
    },
  };

  try {
    const nonce = `${Date.now()}-${Math.random()}`;
    await import(new URL(`src/ui.mjs?entrypoint=${nonce}`, fixture));
    for (let turn = 0; turn < 10 && documentElement.dataset.webmcp !== "ready"; turn += 1) {
      await new Promise((resolve) => setImmediate(resolve));
    }

    assert.deepEqual([...registered.keys()], ["inspect_board", "add_board_item"]);
    assert.equal(documentElement.dataset.webmcp, "ready");

    const initialRevision = Number(elements.get("#revision").textContent);
    const result = await registered.get("add_board_item").execute(
      {title: "Packaged entrypoint item", expectedRevision: initialRevision},
      {signal: new AbortController().signal},
    );
    assert.equal(result.revision, initialRevision + 1);
    assert.equal(elements.get("#revision").textContent, String(result.revision));
    assert.equal(elements.get("#item-count").textContent, "1");
    assert.equal(elements.get("#board-items").children.at(-1).textContent, "Packaged entrypoint item");
  } finally {
    if (previousDocument === undefined) delete globalThis.document;
    else globalThis.document = previousDocument;
  }
});

test("CREATE fixture human and WebMCP paths share one revisioned operation store", async () => {
  const generated = await generateFixtureAdapter();
  const shim = await installShim();
  const saved = new Map();
  let nextId = 0;
  const application = domain.createBoardApplication({
    storage: {
      getItem: (key) => saved.get(key) ?? null,
      setItem: (key, value) => saved.set(key, value),
    },
    createId: () => `item-${++nextId}`,
  });
  const visibleStates = [];
  application.subscribe((state) => visibleStates.push(state));
  try {
    const registration = await generated.registerWebMCPTools({
      inspectBoard: application.inspectBoard,
      addBoardItem: application.addBoardItem,
    });
    assert.deepEqual(registration.registered, ["inspect_board", "add_board_item"]);

    const initial = await shim.modelContext.executeTool("inspect_board", {});
    assert.equal(initial.revision, 0);

    const agentCommit = await shim.modelContext.executeTool("add_board_item", {
      title: "Agent-created item",
      expectedRevision: 0,
    });
    assert.equal(agentCommit.revision, 1);
    assert.equal(visibleStates.at(-1).items.at(-1).title, "Agent-created item");

    const humanCommit = await application.addBoardItem({
      title: "Human-created item",
      expectedRevision: 1,
    });
    assert.equal(humanCommit.revision, 2);
    const afterHuman = await shim.modelContext.executeTool("inspect_board", {});
    assert.deepEqual(afterHuman.items.map((item) => item.title), [
      "Agent-created item",
      "Human-created item",
    ]);
    assert.equal(afterHuman.revision, visibleStates.at(-1).revision);

    await assert.rejects(
      shim.modelContext.executeTool("add_board_item", {
        title: "Stale item",
        expectedRevision: 0,
      }),
      {name: "RevisionConflictError"},
    );
    registration.dispose();
  } finally {
    shim.restore();
  }
});

test("CREATE fixture canonical operation propagates cancellation before commit", async () => {
  const application = domain.createBoardApplication({
    storage: {getItem: () => null, setItem() {}},
    createId: () => "never-committed",
  });
  const controller = new AbortController();
  controller.abort(new DOMException("cancel fixture operation", "AbortError"));
  await assert.rejects(
    application.addBoardItem(
      {title: "Cancelled", expectedRevision: 0},
      {signal: controller.signal},
    ),
    {name: "AbortError"},
  );
  assert.equal(application.getState().revision, 0);
});
