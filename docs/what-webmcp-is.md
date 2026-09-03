# What WebMCP is

WebMCP lets a website expose named, described, schema-bound tools to an agent through the browser. The current imperative surface lives at `document.modelContext`. A declarative form proposal also exists. The standard remains experimental, so the release process must pin what was tested rather than treating “web platform” as a version number.

## The useful distinction

**MCP** connects an AI application to a local or remote server. Its tools can work without an open webpage. They are suited to service APIs, records, long-lived integrations, and workflows whose state belongs to the backend.

**WebMCP** lets the current webpage register tools. Those tools share the page’s application code, signed-in browser session, visible state, and lifecycle. They are suited to work where a person and an agent need to see and change the same artifact.

A product can support both. Neither protocol summons the other automatically.

| Need | WebMCP | MCP server | Both |
| --- | --- | --- | --- |
| Agent works with the open page and visible selection | Yes | Usually indirect | Yes |
| Tool remains available after the page closes | No | Yes | Yes |
| Use the page’s browser session and client state | Yes | No, unless separately bridged | Yes |
| Call a service independently of browser UI | Not by itself | Yes | Yes |
| Keep one product operation behind multiple tool surfaces | Yes | Yes | Recommended |

## Browser lifecycle

1. The page loads its application and canonical operations.
2. It calls `document.modelContext.registerTool()` for each available action.
3. A supporting host discovers the current tools and their input schemas.
4. The host requests a tool invocation with structured arguments.
5. The browser mediates the request and calls the registered `execute` function.
6. The execute function calls the same domain operation used by the human interface.
7. The operation updates canonical state, the page renders that state, and the tool returns JSON-safe evidence.
8. When the document or owning route leaves scope, registration is disposed.

The adapter is intentionally thin. If its `execute` function starts recreating validation, persistence, or business rules, the product has acquired two truths and will eventually schedule a meeting between them.

## Minimal imperative registration

```js
const controller = new AbortController();

await document.modelContext.registerTool(
  {
    name: "add_board_item",
    title: "Add board item",
    description: "Add one item when the supplied board revision is current.",
    inputSchema: {
      type: "object",
      properties: {
        title: {type: "string", minLength: 1, maxLength: 120},
        expectedRevision: {type: "integer", minimum: 0}
      },
      required: ["title", "expectedRevision"],
      additionalProperties: false
    },
    annotations: {readOnlyHint: false, untrustedContentHint: false},
    execute(input, {signal} = {}) {
      return boardApplication.addBoardItem(input, {signal});
    }
  },
  {signal: controller.signal}
);

// End the registration lifetime.
controller.abort();
```

The `web-mcp` skill generates this adapter from a validated tool manifest and verifies that `addBoardItem` is a real exported handler. The application still owns the operation.

## Current host picture

As checked on 3 September 2026:

- ChatGPT Site tools use WebMCP in the ChatGPT desktop app’s built-in browser when the account, selected model, page, and tool are supported. They are not a Chrome feature supplied by ChatGPT. See [OpenAI’s current help article](https://help.openai.com/en/articles/20001423-using-site-tools-in-the-chatgpt-desktop-app).
- The WebMCP project reports a Chrome 149 origin trial and an Edge 150 origin trial, with other browser work tracked separately. Treat those as versioned implementation status, not universal availability. See the [upstream status file](https://github.com/webmachinelearning/webmcp/blob/main/implementation-status.md).
- The OpenAI challenge describes testing in ChatGPT’s in-app browser or Chrome with the experimental feature/origin trial enabled. See the [challenge page](https://openai.com/webmcp-challenge/).
- The published TypeScript declarations are supplied by [`webmcp-types`](https://www.npmjs.com/package/webmcp-types). The registry reported `0.1.6` during this check.

## Imperative, declarative, and service-worker work

The production examples in this repository use imperative document registration because it has the complete operation boundary needed for shared state and explicit results.

The official repository also contains:

- a declarative form proposal that synthesizes tools from annotated forms;
- a service-worker explainer for background discovery and execution;
- cross-document and cross-origin work involving `getTools()`, `executeTool()`, permissions policy, and `exposedTo`.

These are official materials. Official provenance does not make every proposal a deployed production API. The skill preserves them as explicit profiles and labels unresolved behavior rather than deleting it from history or promoting it by enthusiasm.

## What WebMCP does not do

WebMCP does not create the website’s business operations, persistence, authorization, rollback, or evidence model. It does not make an MCP server appear, deploy a site, enable a browser flag, grant ChatGPT availability, or prove that a model will choose the right tool. Those are separate implementation and verification layers described in [Testing and evidence](testing-and-evidence.md).
