import {
  abortReason,
  invokeBinding,
  surfaceBindings,
} from "./contract.mjs";

export function createWebMCPAdapter({
  contract,
  operations,
  getPageContext,
  reconcile = async () => {},
}) {
  if (typeof getPageContext !== "function") {
    throw new TypeError("getPageContext must be a function");
  }
  if (typeof reconcile !== "function") {
    throw new TypeError("reconcile must be a function");
  }
  const bindings = surfaceBindings(contract, operations, "webmcp");

  async function register(modelContext, options = {}) {
    const externalSignal = options.signal;
    if (externalSignal?.aborted) throw abortReason(externalSignal);
    if (typeof modelContext?.registerTool !== "function") {
      return Object.freeze({
        supported: false,
        registered: Object.freeze([]),
        dispose() {},
      });
    }

    const lifecycle = new AbortController();
    const forwardAbort = () => lifecycle.abort(abortReason(externalSignal));
    externalSignal?.addEventListener("abort", forwardAbort, { once: true });
    const registered = [];

    try {
      for (const binding of bindings) {
        const descriptor = binding.descriptor;
        await modelContext.registerTool({
          ...descriptor,
          execute: async (input, executionOptions = {}) => {
            const pageBefore = getPageContext();
            const outcome = await invokeBinding(binding, input, {
              surface: "webmcp",
              actor: pageBefore.actor,
              page: pageBefore,
              signal: executionOptions.signal,
            });
            await reconcile(outcome, {
              binding,
              pageBefore,
              signal: executionOptions.signal,
            });
            const pageAfter = getPageContext();
            return {
              outcome,
              evidence: {
                surface: "webmcp",
                route: pageAfter.route ?? null,
                visibleRevision: pageAfter.visibleRevision ?? null,
                selectedItemId: pageAfter.selectedItemId ?? null,
              },
            };
          },
        }, { signal: lifecycle.signal });
        registered.push(descriptor.name);
      }
    } catch (error) {
      lifecycle.abort(error);
      externalSignal?.removeEventListener("abort", forwardAbort);
      throw error;
    }

    let disposed = false;
    return Object.freeze({
      supported: true,
      registered: Object.freeze([...registered]),
      signal: lifecycle.signal,
      dispose(reason) {
        if (disposed) return;
        disposed = true;
        lifecycle.abort(reason);
        externalSignal?.removeEventListener("abort", forwardAbort);
      },
    });
  }

  return Object.freeze({
    surface: "webmcp",
    bindings,
    register,
  });
}
