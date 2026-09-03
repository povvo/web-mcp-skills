# Service Worker WebMCP profile

Use this reference only for an explicit `webmcp-service-worker` research profile or a named implementation that independently supports such a surface.

## Maturity boundary

The canonical Service Worker material listed in `assets/sources/official-materials.json` is a supplemental proposal. It is part of WebMCP's design space, but it is not represented by the current document API:

- the current draft exposes `ModelContext` to `Window` documents;
- the current official type package describes the document surface;
- discovery, JIT installation, manifest linkage, session identity, routing, and multi-origin behavior remain unresolved or target-specific;
- `self.agent.provideContext(...)` is proposal vocabulary, not current standard IDL.

Do not remove this capability from a complete WebMCP skill. Route it as a first-class experimental branch and preserve its status.

## Proposed value

The proposal explores tools that remain available without an open page:

- background task or record updates;
- reservation or shopping preparation;
- notification and sync work;
- opening UI only when human review is needed;
- routing a conversation to a previously registered site capability.

This overlaps with use cases commonly served by MCP, but it remains a WebMCP proposal because it imagines browser-managed discovery and invocation of a site's Service Worker. Do not rename the proposal as MCP or claim that an MCP server proves it works.

## Architecture questions

Before prototyping, record answers or explicit unknowns for:

1. How is a provider discovered?
2. Is worker installation already present, manifest-declared, or JIT?
3. Which origin and registration owns the tool?
4. How does a call select one worker when multiple clients exist?
5. What identifies the agent conversation or session?
6. What happens when the worker is stopped and restarted?
7. How does the operation obtain authentication and durable state?
8. How is progress or cancellation represented?
9. When and how may the worker open a window for review?
10. How do pages reconcile changes made in the background?
11. What limits multi-origin data combination and external communication?

Unanswered questions are not implementation details to invent. Mark them `UNSUPPORTED` or `NOT RUN` for the chosen target.

## Proposal-safe operation model

Keep domain work independent of the proposed registration syntax:

```text
proposed worker adapter → canonical service operation → durable state
page UI adapter ────────→ canonical service operation → visible state
```

This lets a prototype test useful background behavior without encoding unverified proposal syntax into business logic.

If a current browser exposes a named experimental API, isolate it behind a target adapter and record:

- browser build and flag/origin trial;
- exact API object and callback signatures;
- discovery receipt;
- invocation receipt;
- lifecycle and restart behavior;
- differences from the official explainer.

## UI handoff

When an operation needs human input or review, specify:

- why background completion must stop;
- how the correct page/window is opened or focused;
- how request state is transferred;
- how the page resumes or rejects the operation;
- what the agent receives after completion;
- what happens if the user closes the window.

Do not silently perform a purchase, communication, permission change, or destructive effect merely because the proposal can open UI.

## Testing

For a real target implementation, test:

- discovery with no site tab open;
- worker cold start and restart;
- registration replacement and removal;
- session/conversation separation;
- two clients or windows;
- offline and sync recovery;
- cancellation before and after commit;
- UI handoff success, rejection, and abandonment;
- later page reconciliation;
- origin and data-flow boundaries.

For proposal-only work, test canonical operations and any local adapter harness, then report browser discovery and invocation as `UNSUPPORTED` or `NOT RUN`. Never convert a pseudocode harness into a conformance pass.

## Service Worker profile gate

- The output is labelled proposal/research or names an independent implementation.
- Current document WebMCP remains separately implemented and evaluated when requested.
- Proposal API names are not presented as standard APIs.
- Discovery, installation, session, routing, and multi-origin gaps are recorded.
- Background operations use a real durable domain path.
- UI handoff and page reconciliation are designed and tested where promised.
- Native background discovery and invocation have receipts or remain explicitly unrun/unsupported.
