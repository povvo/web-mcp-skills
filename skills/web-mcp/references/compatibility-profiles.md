# Compatibility profiles

Select a profile before implementing or claiming support. The machine-readable registry is `assets/profiles/compatibility-profiles.json`; source provenance is in `assets/sources/official-materials.json`.

## Why profiles are required

“WebMCP support” can refer to different evidence layers:

1. the current document-scoped draft specification;
2. a browser implementation;
3. ChatGPT Site tools product behavior;
4. the declarative-form proposal;
5. the Service Worker proposal.

These layers overlap but are not interchangeable. Record exact target, checked date, implementation version, and observed API subset.

## `webmcp-document`

Use for the current document-scoped draft and for an in-page consumer that explicitly uses the draft API.

Baseline:

- `document.modelContext` on a `Window` document;
- Promise-returning imperative registration;
- registration cancellation through `AbortSignal`;
- execution callback receives `{signal}`;
- result is JSON-serialized by the platform;
- `getTools()`, `executeTool()`, `toolchange`, origins, and Permissions Policy belong to the broader draft, not necessarily every host product.

Claim it as a draft, not a W3C Recommendation or universal browser feature. A shim validates publisher logic only.

## `chatgpt-site-tools`

Use for ChatGPT Work or Codex in the built-in browser.

The supplied official product snapshot supports top-level imperative Site tools and states that declarative forms and iframe-registered tools are not discovered. Models, workspace eligibility, app version, rollout, and the supported API subset are volatile.

Before a current claim, verify:

- supported model and workspace;
- desktop app/browser version;
- Site tools availability;
- imperative/declarative subset;
- iframe discovery behavior;
- user-control and confirmation behavior.

Required native evidence includes Available Site tools, an actual invocation, the resulting page change, and Recently used/Sources when available. A document-draft or Chrome pass is not a ChatGPT pass.

## `chromium-webmcp`

Use for current Chromium/Chrome implementation work.

Record:

- exact browser build;
- origin-trial or testing-flag state;
- discovered tool inventory and browser-observed schemas;
- DevTools/inspector output;
- manual invocation and visible effect;
- Chrome WebMCP eval command, version, and result.

Chrome tooling is experimental and drift-prone. Smoke evals may force expected calls and use subset result matching; they do not replace strict schema, handler, state, or agent-selection tests.

## `webmcp-declarative`

Use only for a selected target that independently implements the declarative proposal.

The proposal discusses form attributes, synthesized schemas, automatic or human-reviewed submission, response integration, events, and pseudo-classes. Several algorithms and integration points remain incomplete. ChatGPT Site tools exclude this surface in the supplied product snapshot.

Requirements:

- label the branch experimental and target-specific;
- preserve the ordinary semantic form;
- use valid WebMCP machine-name grammar even if an explainer example does not;
- inspect the synthesized schema rather than assume it;
- verify exact event, focus, reset, submit, cancellation, and response behavior;
- never claim portable production conformance from one browser demo.

## `webmcp-service-worker`

Use only for explicit research or a named target implementation.

The official supplemental explainer proposes background discovery, JIT installation, Service Worker tool routing, session identity, and optional UI handoff. The current document draft exposes `ModelContext` to `Window`, and the current official type package does not establish a Service Worker API.

Treat `self.agent`, `provideContext`, discovery, manifest linkage, and session examples as proposal vocabulary or pseudocode unless a target independently implements them. Record unresolved discovery and multi-origin issues. Read `service-worker-profile.md`.

## Profile combinations

Valid combinations include:

- `webmcp-document` + `chatgpt-site-tools`;
- `webmcp-document` + `chromium-webmcp`;
- one document/browser profile + `webmcp-declarative` for an explicit experiment;
- `webmcp-service-worker` as a separate experimental branch beside document WebMCP;
- any genuine WebMCP profile + DUAL MCP architecture.

Do not combine statuses into one claim. Report each profile separately.

## Compatibility record

```yaml
profile: chatgpt-site-tools
checked_at: 2026-08-28
source: official product documentation URL
host_version: exact version or unknown
api_subset:
  imperative: observed | documented | unsupported | not_run
  declarative: observed | documented | unsupported | not_run
  iframe_discovery: observed | documented | unsupported | not_run
native_discovery: PASS | WARN | FAIL | UNSUPPORTED | NOT RUN
native_invocation: PASS | WARN | FAIL | UNSUPPORTED | NOT RUN
visible_effect: PASS | WARN | FAIL | UNSUPPORTED | NOT RUN
notes: implementation-specific assumptions and gaps
```

## Claim gate

- The profile and checked date are explicit.
- Draft, implementation, product, and proposal evidence are not conflated.
- Volatile facts were refreshed from official sources.
- Unsupported features are `UNSUPPORTED`, not silently omitted.
- Unexecuted native checks remain `NOT RUN`.
- Service Worker and declarative code is not called production-portable without independent implementation evidence.

