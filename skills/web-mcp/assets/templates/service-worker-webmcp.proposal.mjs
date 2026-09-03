/**
 * SERVICE WORKER WEBMCP PROPOSAL MOCK
 *
 * Maturity: PROPOSAL
 * Current standard support: UNSUPPORTED
 * ChatGPT Site tools support: UNSUPPORTED
 * Document API conformance: NOT_CLAIMED
 * Test evidence: MOCK_ONLY
 *
 * This module deliberately accepts a dependency-injected mock runtime. It does
 * not access browser registration globals, a manifest installation hook, or
 * any other surface that could be mistaken for a current browser API.
 */

export const WEBMCP_SERVICE_WORKER_PROPOSAL_STATUS = Object.freeze({
  profile: "service-worker-webmcp",
  maturity: "PROPOSAL",
  specificationSupport: "UNSUPPORTED",
  chatgptSiteToolsSupport: "UNSUPPORTED",
  documentApiConformance: "NOT_CLAIMED",
  browserConformance: "NOT_RUN",
  testEvidence: "MOCK_ONLY",
  runtimeSurface: "DEPENDENCY_INJECTED_PROPOSAL_MOCK",
});

const toolDefinition = Object.freeze({
  name: __TOOL_NAME_JSON__,
  description: __DESCRIPTION_JSON__,
});

export function createProposalMockRuntime() {
  const tools = new Map();
  const log = [];

  return {
    profile: "WEBMCP_SERVICE_WORKER_PROPOSAL_MOCK",
    log,
    registerTool(tool) {
      if (!tool || typeof tool.name !== "string" || typeof tool.execute !== "function") {
        throw new TypeError("proposal mock requires a named executable tool");
      }
      if (tools.has(tool.name)) {
        throw new Error(`proposal mock already registered: ${tool.name}`);
      }
      tools.set(tool.name, tool);
      log.push({ type: "registered", name: tool.name });
      let disposed = false;
      return {
        dispose() {
          if (disposed) return;
          disposed = true;
          tools.delete(tool.name);
          log.push({ type: "disposed", name: tool.name });
        },
      };
    },
    async invoke(name, input = {}, context = {}) {
      const tool = tools.get(name);
      if (!tool) throw new Error(`proposal mock tool is unavailable: ${name}`);
      const signal = context.signal ?? new AbortController().signal;
      if (signal.aborted) throw signal.reason;
      log.push({ type: "invoked", name, sessionId: context.sessionId ?? null });
      return tool.execute(input, { ...context, signal });
    },
    listTools() {
      return [...tools.values()].map(({ name, description }) => ({ name, description }));
    },
  };
}

export function registerServiceWorkerProposal(runtime, operation) {
  if (runtime?.profile !== "WEBMCP_SERVICE_WORKER_PROPOSAL_MOCK") {
    throw new TypeError(
      "This scaffold accepts only the explicit Service Worker WebMCP proposal mock runtime.",
    );
  }
  if (typeof operation !== "function") {
    throw new TypeError("a durable domain operation is required");
  }

  return runtime.registerTool({
    ...toolDefinition,
    async execute(input, context) {
      if (context.signal.aborted) throw context.signal.reason;
      return operation(input, {
        signal: context.signal,
        sessionId: context.sessionId ?? null,
      });
    },
  });
}
