import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import test from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";


const generator = fileURLToPath(
  new URL("../../scripts/webmcp_proposals.py", import.meta.url),
);
const python = process.env.WEBMCP_TEST_PYTHON || "python";

async function generateServiceWorkerProposal() {
  const outputDir = await mkdtemp(path.join(tmpdir(), "webmcp-proposal-mock-"));
  const result = spawnSync(
    python,
    [
      "-B",
      generator,
      "generate",
      "service-worker",
      "--output-dir",
      outputDir,
      "--tool-name",
      "queue_background_item",
      "--description",
      "Queue one item through a proposal-only background adapter.",
    ],
    { encoding: "utf8" },
  );
  if (result.status !== 0) {
    await rm(outputDir, { recursive: true, force: true });
    throw new Error(`proposal generator failed: ${result.stderr || result.stdout}`);
  }
  return { outputDir, result: JSON.parse(result.stdout) };
}

test("Service Worker proposal mock executes a durable operation without a browser API claim", async () => {
  const generated = await generateServiceWorkerProposal();
  try {
    const moduleUrl = pathToFileURL(generated.result.artifact);
    moduleUrl.searchParams.set("test", String(Date.now()));
    const proposal = await import(moduleUrl.href);
    assert.equal(proposal.WEBMCP_SERVICE_WORKER_PROPOSAL_STATUS.maturity, "PROPOSAL");
    assert.equal(
      proposal.WEBMCP_SERVICE_WORKER_PROPOSAL_STATUS.documentApiConformance,
      "NOT_CLAIMED",
    );
    assert.equal(proposal.WEBMCP_SERVICE_WORKER_PROPOSAL_STATUS.testEvidence, "MOCK_ONLY");

    const runtime = proposal.createProposalMockRuntime();
    const observed = [];
    const registration = proposal.registerServiceWorkerProposal(
      runtime,
      async (input, context) => {
        observed.push({ input, sessionId: context.sessionId });
        return { queued: true, id: input.id, sessionId: context.sessionId };
      },
    );
    assert.deepEqual(runtime.listTools(), [
      {
        name: "queue_background_item",
        description: "Queue one item through a proposal-only background adapter.",
      },
    ]);
    assert.deepEqual(
      await runtime.invoke(
        "queue_background_item",
        { id: "item-1" },
        { sessionId: "conversation-7" },
      ),
      { queued: true, id: "item-1", sessionId: "conversation-7" },
    );
    assert.deepEqual(observed, [
      { input: { id: "item-1" }, sessionId: "conversation-7" },
    ]);

    registration.dispose();
    await assert.rejects(
      runtime.invoke("queue_background_item", { id: "item-2" }),
      /proposal mock tool is unavailable/,
    );

    const metadata = JSON.parse(
      await readFile(generated.result.statusMetadata, "utf8"),
    );
    assert.equal(metadata.verification.mockTests, "NOT_RUN");
    assert.equal(metadata.verification.nativeDiscovery, "NOT_RUN");
    assert.equal(metadata.verification.nativeInvocation, "NOT_RUN");
  } finally {
    await rm(generated.outputDir, { recursive: true, force: true });
  }
});

test("Service Worker proposal mock propagates cancellation without conformance claims", async () => {
  const generated = await generateServiceWorkerProposal();
  try {
    const proposal = await import(pathToFileURL(generated.result.artifact).href);
    const runtime = proposal.createProposalMockRuntime();
    proposal.registerServiceWorkerProposal(runtime, async () => ({ queued: true }));
    const controller = new AbortController();
    controller.abort(new DOMException("cancelled by mock test", "AbortError"));
    await assert.rejects(
      runtime.invoke("queue_background_item", {}, { signal: controller.signal }),
      { name: "AbortError" },
    );
  } finally {
    await rm(generated.outputDir, { recursive: true, force: true });
  }
});
