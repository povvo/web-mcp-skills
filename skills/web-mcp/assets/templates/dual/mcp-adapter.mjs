import {
  cloneJson,
  DualAdapterError,
  findBinding,
  invokeBinding,
  surfaceBindings,
} from "./contract.mjs";

function schemaError(code, path, message) {
  throw new DualAdapterError(code, `${path}: ${message}`);
}

function assertZodNamespace(z) {
  const required = ["array", "boolean", "literal", "null", "number", "object", "string", "union"];
  for (const name of required) {
    if (typeof z?.[name] !== "function") {
      throw new TypeError(`z.${name} must be a function`);
    }
  }
}

function applyDescription(schema, source) {
  return typeof source.description === "string" && typeof schema.describe === "function"
    ? schema.describe(source.description)
    : schema;
}

const ANNOTATION_KEYWORDS = new Set([
  "$comment",
  "$id",
  "$schema",
  "default",
  "deprecated",
  "description",
  "examples",
  "readOnly",
  "title",
  "writeOnly",
]);

function assertSupportedKeywords(schema, path, validationKeywords) {
  const supported = new Set(validationKeywords);
  for (const keyword of Object.keys(schema)) {
    if (!ANNOTATION_KEYWORDS.has(keyword) && !supported.has(keyword)) {
      schemaError(
        "MCP_SDK_SCHEMA_UNSUPPORTED",
        `${path}.${keyword}`,
        "requires a project-owned Zod mapping",
      );
    }
  }
}

function scalarMatchesType(value, type) {
  switch (type) {
    case "string": return typeof value === "string";
    case "integer": return typeof value === "number" && Number.isInteger(value);
    case "number": return typeof value === "number" && Number.isFinite(value);
    case "boolean": return typeof value === "boolean";
    case "null": return value === null;
    default: return false;
  }
}

function assertScalarMatchesDeclaredType(value, declaredType, path) {
  if (declaredType === undefined) return;
  const types = Array.isArray(declaredType) ? declaredType : [declaredType];
  if (!types.some((type) => scalarMatchesType(value, type))) {
    schemaError(
      "MCP_SDK_SCHEMA_INVALID",
      path,
      `value does not match declared type ${JSON.stringify(declaredType)}`,
    );
  }
}

function convertEnum(schema, z, path) {
  if (!Array.isArray(schema.enum) || schema.enum.length === 0) {
    schemaError("MCP_SDK_SCHEMA_INVALID", path, "enum must be a non-empty array");
  }
  const encoded = new Set(schema.enum.map((value) => JSON.stringify(value)));
  if (encoded.size !== schema.enum.length) {
    schemaError("MCP_SDK_SCHEMA_INVALID", path, "enum values must be unique JSON values");
  }
  const choices = schema.enum.map((value, index) => {
    if (
      value !== null
      && typeof value !== "string"
      && typeof value !== "number"
      && typeof value !== "boolean"
    ) {
      schemaError("MCP_SDK_SCHEMA_UNSUPPORTED", `${path}.enum[${index}]`, "only scalar JSON enum values are supported");
    }
    assertScalarMatchesDeclaredType(value, schema.type, `${path}.enum[${index}]`);
    return z.literal(value);
  });
  return choices.length === 1 ? choices[0] : z.union(choices);
}

function convertJsonSchema(schema, z, path = "inputSchema") {
  if (!schema || typeof schema !== "object" || Array.isArray(schema)) {
    schemaError("MCP_SDK_SCHEMA_INVALID", path, "must be a JSON Schema object");
  }
  if (schema.$ref !== undefined || schema.$defs !== undefined || schema.definitions !== undefined) {
    schemaError(
      "MCP_SDK_SCHEMA_UNSUPPORTED",
      path,
      "$ref/$defs/definitions require a project-owned resolver before SDK registration",
    );
  }
  if (schema.oneOf !== undefined || schema.allOf !== undefined || schema.not !== undefined) {
    schemaError(
      "MCP_SDK_SCHEMA_UNSUPPORTED",
      path,
      "oneOf/allOf/not cannot be converted without changing JSON Schema semantics",
    );
  }
  if (schema.anyOf !== undefined) {
    assertSupportedKeywords(schema, path, ["anyOf"]);
    if (!Array.isArray(schema.anyOf) || schema.anyOf.length < 2) {
      schemaError("MCP_SDK_SCHEMA_INVALID", `${path}.anyOf`, "must contain at least two schemas");
    }
    return applyDescription(
      z.union(schema.anyOf.map((choice, index) => convertJsonSchema(choice, z, `${path}.anyOf[${index}]`))),
      schema,
    );
  }
  if (schema.const !== undefined) {
    assertSupportedKeywords(schema, path, ["const", "type"]);
    if (
      schema.const !== null
      && typeof schema.const !== "string"
      && typeof schema.const !== "number"
      && typeof schema.const !== "boolean"
    ) {
      schemaError("MCP_SDK_SCHEMA_UNSUPPORTED", `${path}.const`, "only scalar JSON const values are supported");
    }
    assertScalarMatchesDeclaredType(schema.const, schema.type, `${path}.const`);
    return applyDescription(z.literal(schema.const), schema);
  }
  if (schema.enum !== undefined) {
    assertSupportedKeywords(schema, path, ["enum", "type"]);
    return applyDescription(convertEnum(schema, z, path), schema);
  }
  if (Array.isArray(schema.type)) {
    if (schema.type.length < 2) {
      schemaError("MCP_SDK_SCHEMA_INVALID", `${path}.type`, "must contain at least two types");
    }
    return applyDescription(
      z.union(schema.type.map((type, index) => convertJsonSchema({ ...schema, type }, z, `${path}.type[${index}]`))),
      schema,
    );
  }

  let converted;
  switch (schema.type) {
    case "object": {
      assertSupportedKeywords(schema, path, ["additionalProperties", "properties", "required", "type"]);
      const properties = schema.properties ?? {};
      if (!properties || typeof properties !== "object" || Array.isArray(properties)) {
        schemaError("MCP_SDK_SCHEMA_INVALID", `${path}.properties`, "must be an object");
      }
      if (
        schema.additionalProperties !== undefined
        && schema.additionalProperties !== true
        && schema.additionalProperties !== false
      ) {
        schemaError(
          "MCP_SDK_SCHEMA_UNSUPPORTED",
          `${path}.additionalProperties`,
          "schema-valued additionalProperties requires a project-owned adapter",
        );
      }
      if (schema.required !== undefined && !Array.isArray(schema.required)) {
        schemaError("MCP_SDK_SCHEMA_INVALID", `${path}.required`, "must be an array");
      }
      const required = new Set(schema.required ?? []);
      for (const name of required) {
        if (typeof name !== "string" || !Object.hasOwn(properties, name)) {
          schemaError("MCP_SDK_SCHEMA_INVALID", `${path}.required`, `unknown property ${String(name)}`);
        }
      }
      const shape = {};
      for (const [name, propertySchema] of Object.entries(properties)) {
        let property = convertJsonSchema(propertySchema, z, `${path}.properties.${name}`);
        if (!required.has(name)) property = property.optional();
        shape[name] = property;
      }
      converted = z.object(shape);
      if (schema.additionalProperties === false && typeof converted.strict === "function") {
        converted = converted.strict();
      } else if (schema.additionalProperties !== false && typeof converted.passthrough === "function") {
        converted = converted.passthrough();
      }
      break;
    }
    case "array": {
      assertSupportedKeywords(schema, path, ["items", "maxItems", "minItems", "type", "uniqueItems"]);
      if (!schema.items || Array.isArray(schema.items)) {
        schemaError("MCP_SDK_SCHEMA_UNSUPPORTED", `${path}.items`, "must be one JSON Schema object");
      }
      converted = z.array(convertJsonSchema(schema.items, z, `${path}.items`));
      if (Number.isInteger(schema.minItems)) converted = converted.min(schema.minItems);
      if (Number.isInteger(schema.maxItems)) converted = converted.max(schema.maxItems);
      if (schema.uniqueItems === true) {
        schemaError("MCP_SDK_SCHEMA_UNSUPPORTED", `${path}.uniqueItems`, "requires a project-owned uniqueness refinement");
      }
      break;
    }
    case "string":
      assertSupportedKeywords(schema, path, ["format", "maxLength", "minLength", "pattern", "type"]);
      converted = z.string();
      if (Number.isInteger(schema.minLength)) converted = converted.min(schema.minLength);
      if (Number.isInteger(schema.maxLength)) converted = converted.max(schema.maxLength);
      if (schema.pattern !== undefined) {
        if (typeof schema.pattern !== "string") {
          schemaError("MCP_SDK_SCHEMA_INVALID", `${path}.pattern`, "must be a string");
        }
        converted = converted.regex(new RegExp(schema.pattern));
      }
      if (schema.format !== undefined) {
        schemaError(
          "MCP_SDK_SCHEMA_UNSUPPORTED",
          `${path}.format`,
          "format requires an explicit project-owned Zod mapping",
        );
      }
      break;
    case "integer":
    case "number":
      assertSupportedKeywords(schema, path, [
        "exclusiveMaximum",
        "exclusiveMinimum",
        "maximum",
        "minimum",
        "multipleOf",
        "type",
      ]);
      converted = z.number();
      if (schema.type === "integer") converted = converted.int();
      if (typeof schema.minimum === "number") converted = converted.min(schema.minimum);
      if (typeof schema.maximum === "number") converted = converted.max(schema.maximum);
      if (typeof schema.exclusiveMinimum === "number") converted = converted.gt(schema.exclusiveMinimum);
      if (typeof schema.exclusiveMaximum === "number") converted = converted.lt(schema.exclusiveMaximum);
      if (typeof schema.multipleOf === "number") converted = converted.multipleOf(schema.multipleOf);
      break;
    case "boolean":
      assertSupportedKeywords(schema, path, ["type"]);
      converted = z.boolean();
      break;
    case "null":
      assertSupportedKeywords(schema, path, ["type"]);
      converted = z.null();
      break;
    default:
      schemaError(
        "MCP_SDK_SCHEMA_UNSUPPORTED",
        `${path}.type`,
        `unsupported or missing JSON Schema type ${String(schema.type)}`,
      );
  }
  return applyDescription(converted, schema);
}

/**
 * Build the synchronous input-schema hook required by the high-level official
 * MCP TypeScript SDK. The caller owns and pins Zod; this template has no hidden
 * SDK/runtime dependency and refuses constructs it cannot preserve exactly.
 */
export function createMCPTypeScriptSDKInputSchemaAdapter(z) {
  assertZodNamespace(z);
  return (inputSchema, context = {}) => convertJsonSchema(
    cloneJson(inputSchema, `${context.toolName ?? "MCP tool"} JSON input schema`),
    z,
    `${context.toolName ?? "MCP tool"}.inputSchema`,
  );
}

export function createMCPAdapter({
  contract,
  operations,
  getRequestContext = () => ({}),
}) {
  if (typeof getRequestContext !== "function") {
    throw new TypeError("getRequestContext must be a function");
  }
  const bindings = surfaceBindings(contract, operations, "mcp");

  function listTools() {
    return cloneJson(bindings.map((binding) => binding.descriptor), "MCP tool list");
  }

  async function callTool(toolName, input = {}, options = {}) {
    const binding = findBinding(bindings, toolName);
    const request = getRequestContext(options) ?? {};
    const outcome = await invokeBinding(binding, input, {
      surface: "mcp",
      actor: request.actor,
      request,
      signal: options.signal,
    });
    const structuredContent = {
      outcome,
      evidence: {
        surface: "mcp",
        revision: outcome.revision ?? null,
        commitId: outcome.commitId ?? null,
      },
    };
    return {
      content: [{ type: "text", text: JSON.stringify(structuredContent) }],
      structuredContent,
    };
  }

  function bindServer(server, options = {}) {
    if (typeof server?.registerTool !== "function") {
      throw new TypeError("server.registerTool must be a function");
    }
    const inputSchemaAdapter = options.inputSchemaAdapter ?? ((schema) => schema);
    if (typeof inputSchemaAdapter !== "function") {
      throw new TypeError("options.inputSchemaAdapter must be a function");
    }
    const prepared = bindings.map((binding) => {
      const descriptor = binding.descriptor;
      const inputSchema = inputSchemaAdapter(
        cloneJson(descriptor.inputSchema, `${descriptor.name} input schema`),
        Object.freeze({
          operationId: binding.operationId,
          surface: "mcp",
          toolName: descriptor.name,
        }),
      );
      if (
        !inputSchema
        || (typeof inputSchema !== "object" && typeof inputSchema !== "function")
        || typeof inputSchema.then === "function"
      ) {
        throw new DualAdapterError(
          "SERVER_INPUT_SCHEMA",
          `inputSchemaAdapter must synchronously return a schema object for ${descriptor.name}`,
        );
      }
      return { binding, descriptor, inputSchema };
    });

    const registrations = [];
    try {
      for (const { binding, descriptor, inputSchema } of prepared) {
        const registration = server.registerTool(
          descriptor.name,
          {
            title: descriptor.title,
            description: descriptor.description,
            inputSchema,
            annotations: descriptor.annotations,
          },
          (input, extra = {}) => callTool(descriptor.name, input, {
            signal: extra.signal,
            requestContext: extra,
          }),
        );
        registrations.push(registration);
      }
    } catch (error) {
      for (const registration of registrations.reverse()) {
        if (typeof registration?.remove === "function") registration.remove();
      }
      throw error;
    }
    return Object.freeze(bindings.map((binding) => binding.descriptor.name));
  }

  return Object.freeze({
    surface: "mcp",
    bindings,
    listTools,
    callTool,
    bindServer,
  });
}
