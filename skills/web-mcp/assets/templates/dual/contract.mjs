export class DualAdapterError extends Error {
  constructor(code, message) {
    super(message);
    this.name = "DualAdapterError";
    this.code = code;
  }
}

export function abortReason(signal) {
  return signal?.reason ?? new DOMException("The operation was aborted.", "AbortError");
}

function assertJsonValue(value, path, ancestors) {
  if (value === null || typeof value === "string" || typeof value === "boolean") return;
  if (typeof value === "number") {
    if (!Number.isFinite(value)) {
      throw new DualAdapterError("RESULT_NOT_JSON", `${path} must be a finite number.`);
    }
    return;
  }
  if (typeof value !== "object") {
    throw new DualAdapterError(
      "RESULT_NOT_JSON",
      `${path} contains unsupported ${typeof value}.`,
    );
  }
  if (ancestors.has(value)) {
    throw new DualAdapterError("RESULT_NOT_JSON", `${path} contains a cyclic reference.`);
  }
  ancestors.add(value);
  try {
    if (Array.isArray(value)) {
      for (let index = 0; index < value.length; index += 1) {
        if (!Object.hasOwn(value, index)) {
          throw new DualAdapterError("RESULT_NOT_JSON", `${path} must not contain sparse arrays.`);
        }
        assertJsonValue(value[index], `${path}[${index}]`, ancestors);
      }
      return;
    }
    const prototype = Object.getPrototypeOf(value);
    if (prototype !== Object.prototype && prototype !== null) {
      throw new DualAdapterError(
        "RESULT_NOT_JSON",
        `${path} contains unsupported ${value.constructor?.name ?? "object"} instance.`,
      );
    }
    if (Object.getOwnPropertySymbols(value).length > 0) {
      throw new DualAdapterError("RESULT_NOT_JSON", `${path} contains symbol-keyed data.`);
    }
    for (const [key, child] of Object.entries(value)) {
      assertJsonValue(child, `${path}.${key}`, ancestors);
    }
  } finally {
    ancestors.delete(value);
  }
}

export function cloneJson(value, label = "operation result") {
  assertJsonValue(value, label, new Set());
  let encoded;
  try {
    encoded = JSON.stringify(value);
  } catch (error) {
    throw new DualAdapterError(
      "RESULT_NOT_JSON",
      `${label} is not JSON-serializable: ${error.message}`,
    );
  }
  if (typeof encoded !== "string") {
    throw new DualAdapterError("RESULT_NOT_JSON", `${label} is not a JSON value.`);
  }
  return JSON.parse(encoded);
}

export function surfaceBindings(contract, operations, surface) {
  if (contract?.schemaVersion !== "webmcp-dual.v1") {
    throw new DualAdapterError("CONTRACT_VERSION", "Unsupported or missing dual contract version.");
  }
  if (!operations || typeof operations !== "object") {
    throw new DualAdapterError("OPERATIONS_TYPE", "operations must be an object keyed by handler name.");
  }
  if (surface !== "webmcp" && surface !== "mcp") {
    throw new DualAdapterError("SURFACE", `Unsupported surface: ${surface}`);
  }

  const names = new Set();
  const bindings = [];
  for (const operation of contract.operations ?? []) {
    const surfaceSpec = operation?.surfaces?.[surface];
    if (!surfaceSpec) continue;
    const handler = operation.handler;
    const implementation = operations[handler];
    if (typeof implementation !== "function") {
      throw new DualAdapterError(
        "HANDLER_MISSING",
        `Missing canonical operation handler: ${handler} for ${operation.operationId}`,
      );
    }
    if (names.has(surfaceSpec.toolName)) {
      throw new DualAdapterError(
        "TOOL_NAME_DUPLICATE",
        `Duplicate ${surface} tool name: ${surfaceSpec.toolName}`,
      );
    }
    names.add(surfaceSpec.toolName);
    bindings.push(Object.freeze({
      operationId: operation.operationId,
      handler,
      operation: implementation,
      effect: operation.effect,
      descriptor: Object.freeze({
        name: surfaceSpec.toolName,
        title: surfaceSpec.title,
        description: surfaceSpec.description,
        inputSchema: operation.inputSchema,
        annotations: operation.annotations,
      }),
    }));
  }
  if (bindings.length === 0) {
    throw new DualAdapterError("SURFACE_EMPTY", `No operations are mapped to ${surface}.`);
  }
  return Object.freeze(bindings);
}

export function findBinding(bindings, toolName) {
  const binding = bindings.find((candidate) => candidate.descriptor.name === toolName);
  if (!binding) {
    throw new DualAdapterError("TOOL_NOT_FOUND", `Unknown tool: ${toolName}`);
  }
  return binding;
}

export async function invokeBinding(binding, input, context) {
  if (context?.signal?.aborted) throw abortReason(context.signal);
  const result = await binding.operation(input ?? {}, Object.freeze({
    ...context,
    operationId: binding.operationId,
    handler: binding.handler,
  }));
  // The canonical operation owns its commit boundary. Once it resolves with a
  // receipt, an adapter must not reinterpret that committed outcome as a
  // cancellation merely because the signal changed during promise settlement.
  return cloneJson(result, `${binding.operationId} result`);
}
