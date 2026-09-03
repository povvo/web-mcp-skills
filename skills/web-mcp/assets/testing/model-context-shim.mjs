/**
 * Deterministic test double for generated WebMCP publisher modules.
 *
 * This is not browser conformance evidence. It models registration ownership,
 * discovery, execution cancellation, JSON result transport, injected failures,
 * toolchange events, and fully-active/BFCache-style suspension so local tests can
 * prove publisher behavior before a native-host run.
 */

function abortError(reason) {
  return reason ?? new DOMException("The operation was aborted.", "AbortError");
}

function inactiveError() {
  return new DOMException("The document is not fully active.", "InvalidStateError");
}

function cloneForTransport(value) {
  let encoded;
  try {
    encoded = JSON.stringify(value);
  } catch (error) {
    throw new TypeError(`WebMCP result could not be JSON-serialized: ${error.message}`);
  }
  if (typeof encoded !== "string") {
    throw new TypeError("WebMCP result could not be JSON-serialized");
  }
  return JSON.parse(encoded);
}

export function installModelContextShim(target = globalThis, config = {}) {
  const registrations = new Map();
  const listeners = new Set();
  const pendingExecutions = new Set();
  const logs = {
    registrations: [],
    removals: [],
    toolChanges: [],
    invocations: [],
    results: [],
    aborts: [],
    lifecycle: [],
  };
  let registrationAttempt = 0;
  let fullyActive = config.fullyActive !== false;
  let ontoolchange = null;

  const dispatchToolChange = () => {
    const event = new Event("toolchange");
    logs.toolChanges.push({
      index: logs.toolChanges.length + 1,
      tools: [...registrations.keys()].sort(),
    });
    for (const listener of listeners) listener.call(modelContext, event);
    if (typeof ontoolchange === "function") ontoolchange.call(modelContext, event);
  };

  const shouldFailRegistration = (tool) => {
    if (typeof config.failRegistration === "function") {
      return config.failRegistration({ attempt: registrationAttempt, tool });
    }
    return Number.isInteger(config.failRegistrationAt) &&
      registrationAttempt === config.failRegistrationAt;
  };

  const executeNow = async (registeredTool, input, options, logEntry) => {
    const name = typeof registeredTool === "string" ? registeredTool : registeredTool?.name;
    const entry = registrations.get(name);
    if (!entry) throw new DOMException(`Tool not found: ${name}`, "NotFoundError");
    if (options.signal?.aborted) throw abortError(options.signal.reason);
    logEntry.status = "running";
    try {
      const raw = await entry.tool.execute(input, {
        signal: options.signal ?? new AbortController().signal,
      });
      const transported = cloneForTransport(raw);
      logEntry.status = "passed";
      logs.results.push({ name, result: transported });
      return transported;
    } catch (error) {
      logEntry.status = error?.name === "AbortError" ? "aborted" : "failed";
      logEntry.error = { name: error?.name ?? "Error", message: String(error?.message ?? error) };
      if (logEntry.status === "aborted") logs.aborts.push({ name, phase: "execution" });
      throw error;
    }
  };

  const modelContext = {
    async registerTool(tool, options = {}) {
      registrationAttempt += 1;
      if (!fullyActive) throw inactiveError();
      if (!tool || typeof tool.name !== "string" || !tool.name) {
        throw new TypeError("tool.name is required");
      }
      if (registrations.has(tool.name)) {
        throw new DOMException(`Tool already registered: ${tool.name}`, "InvalidStateError");
      }
      if (options.signal?.aborted) throw abortError(options.signal.reason);
      if (shouldFailRegistration(tool)) {
        throw new DOMException(
          `Injected registration failure at attempt ${registrationAttempt}`,
          "OperationError",
        );
      }

      const entry = { tool, options, attempt: registrationAttempt };
      registrations.set(tool.name, entry);
      logs.registrations.push({
        attempt: registrationAttempt,
        name: tool.name,
        descriptor: cloneForTransport({
          name: tool.name,
          title: tool.title,
          description: tool.description,
          inputSchema: tool.inputSchema,
          annotations: tool.annotations,
        }),
      });

      const remove = () => {
        if (registrations.delete(tool.name)) {
          logs.removals.push({ name: tool.name, reason: options.signal?.reason });
          dispatchToolChange();
        }
      };
      options.signal?.addEventListener("abort", remove, { once: true });
      dispatchToolChange();
    },

    async getTools() {
      if (!fullyActive) throw inactiveError();
      return [...registrations.values()]
        .map(({ tool }) => ({
          name: tool.name,
          title: tool.title ?? "",
          description: tool.description,
          inputSchema: structuredClone(tool.inputSchema),
          annotations: structuredClone(tool.annotations),
          origin: "https://shim.invalid",
          window: target,
        }))
        .sort((a, b) => a.name.localeCompare(b.name));
    },

    async executeTool(registeredTool, input = {}, options = {}) {
      const name = typeof registeredTool === "string" ? registeredTool : registeredTool?.name;
      if (!registrations.has(name)) {
        throw new DOMException(`Tool not found: ${name}`, "NotFoundError");
      }
      if (options.signal?.aborted) throw abortError(options.signal.reason);
      const logEntry = {
        index: logs.invocations.length + 1,
        name,
        input: cloneForTransport(input),
        status: fullyActive ? "running" : "queued",
      };
      logs.invocations.push(logEntry);
      if (fullyActive) return executeNow(registeredTool, input, options, logEntry);

      return new Promise((resolve, reject) => {
        const pending = {
          run: () => {
            cleanup();
            void executeNow(registeredTool, input, options, logEntry).then(resolve, reject);
          },
          abort: () => {
            cleanup();
            logEntry.status = "aborted";
            logs.aborts.push({ name, phase: "queued" });
            reject(abortError(options.signal?.reason));
          },
        };
        const cleanup = () => {
          pendingExecutions.delete(pending);
          options.signal?.removeEventListener("abort", pending.abort);
        };
        pendingExecutions.add(pending);
        options.signal?.addEventListener("abort", pending.abort, { once: true });
      });
    },

    addEventListener(type, listener) {
      if (type === "toolchange") listeners.add(listener);
    },

    removeEventListener(type, listener) {
      if (type === "toolchange") listeners.delete(listener);
    },

    get ontoolchange() {
      return ontoolchange;
    },

    set ontoolchange(listener) {
      ontoolchange = typeof listener === "function" ? listener : null;
    },
  };

  target.document = target.document ?? {};
  target.document.modelContext = modelContext;

  const setFullyActive = (active) => {
    const next = Boolean(active);
    if (next === fullyActive) return;
    fullyActive = next;
    logs.lifecycle.push({ state: fullyActive ? "fully-active" : "suspended" });
    if (fullyActive) {
      for (const pending of [...pendingExecutions]) pending.run();
    }
  };

  return Object.freeze({
    modelContext,
    registrations,
    logs,
    get fullyActive() {
      return fullyActive;
    },
    suspend() {
      setFullyActive(false);
    },
    resume() {
      setFullyActive(true);
    },
    setFullyActive,
    uninstall() {
      for (const pending of [...pendingExecutions]) pending.abort();
      if (target.document?.modelContext === modelContext) {
        delete target.document.modelContext;
      }
      registrations.clear();
      listeners.clear();
      ontoolchange = null;
    },
  });
}
