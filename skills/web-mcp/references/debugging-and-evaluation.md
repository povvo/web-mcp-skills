# Debugging and evaluation

Read this reference when tools are missing, stale, duplicated, failing, selected incorrectly, or when producing executable release evidence. Read `release-profiles.md` for production or challenge packaging.

## Separate evaluation layers

A WebMCP system spans several independent layers:

1. **Static contract** — names, schemas, manifest, origins, metadata.
2. **Registration mechanics** — API support, document state, policy, lifecycle.
3. **Callback mechanics** — handler binding, validation, cancellation, serialization.
4. **Application behavior** — state, network effects, UI reconciliation, authorization.
5. **Browser discovery** — tool appears to the intended browser/in-page agent.
6. **Agent behavior** — selection, arguments, chaining, refusal/no-tool.
7. **End-to-end outcome** — visible and durable state matches the user goal.
8. **Adversarial behavior** — untrusted metadata/content and cross-tool interactions do not redirect authority.
9. **Native host behavior** — Chrome and ChatGPT discovery/invocation receipts, evaluated separately.
10. **Deployment/package behavior** — live build, authentication path, fresh extraction, and exact candidate identity.

A pass at one layer is not a pass at the next.

## Deterministic first

Run inexpensive deterministic checks before probabilistic evals.

### Manifest

```bash
python scripts/webmcp_toolkit.py validate MANIFEST.json --format json
```

Check:

- unique valid names;
- object-root schemas;
- required fields exist in properties;
- bounded inputs;
- annotations match declared effects/output trust;
- exact secure origins;
- registration owner/lifetime;
- success evidence and failure modes;
- minimum necessary sensitive inputs.

### Repository compatibility

```bash
python scripts/webmcp_toolkit.py scan-repo REPO --format json
python scripts/webmcp_toolkit.py compatibility REPO --format json
```

Check:

- current versus legacy/experimental symbols;
- duplicate registration paths;
- declarative branch usage;
- consumer API usage;
- iframe permission configuration;
- manifest handler resolution;
- SSR/client placement.

### Generated code

For JavaScript:

```bash
node --check generated-webmcp.mjs
```

Then execute against a stub/shim. The bundled `assets/testing/model-context-shim.mjs` provides a minimal test double.

Do not claim the shim implements browser conformance. It verifies your generated publisher contract.

## Model-context unit test

A useful stub records registrations:

```js
const registrations = [];

globalThis.document = {
  modelContext: {
    async registerTool(tool, options) {
      registrations.push({ tool, options });
    },
  },
};
```

Assert:

- exact names/descriptions/schemas/annotations;
- every registration has the lifecycle signal;
- `exposedTo` is absent when empty;
- callbacks map to the correct application handler;
- execution signal is forwarded;
- missing handlers fail before registration;
- failure on the Nth registration aborts earlier registrations;
- `dispose()` is idempotent;
- unsupported browsers return a no-op state;
- callback results serialize;
- aborted execution does not update stale UI.

## Application tests

Use the repository's normal test architecture.

### Read tool

- correct current state;
- bounded/truncated output;
- external/user content is marked and returned as data;
- authorization filters records;
- page state changes before execution;
- cancellation;
- empty result;
- rate limit or unavailable source.

### Local state tool

- visible controls/store update;
- URL/query state updates when canonical;
- repeat call is stable;
- browser back/forward behavior;
- route teardown;
- concurrent human change;
- cancellation before and after state update.

### Remote write

- validation;
- server authorization;
- idempotency;
- normal confirmation/review;
- optimistic update success and rollback;
- duplicate/retry;
- uncertain outcome after cancellation;
- durable state and visible UI agree.

## Browser discovery and invocation

Use the selected compatibility profile and target browser's current inspector or developer utility when available. Validate:

- API feature and policy status;
- list of registered tools;
- schema as observed by the browser;
- registration/unregistration across navigation;
- manual invocation;
- callback output and errors;
- execution cancellation;
- frame origin and Permissions Policy;
- declarative form activation, fill, focus, submit, reset, and cancel only for the explicit declarative profile;
- reload and back/forward cache;
- HMR only as a development concern.

Use the current Web Platform Tests for browser/API conformance where available. Chrome's current `webmcp-evals` package can add local, smoke, and browser/model evidence, but its smoke path may force expected calls and its result matcher may accept subsets. Treat those as external experimental utilities, record exact versions/commands, and retain strict schema and application assertions.

## Debugging decision tree

### `document.modelContext` is absent

Check:

1. target browser/version or origin trial/flag;
2. secure context;
3. origin isolation / `document.domain` configuration;
4. product/browser feature availability;
5. whether code runs in a browser rather than SSR;
6. iframe Permissions Policy.

Do not patch application logic until surface availability is established.

### `registerTool()` rejects

Capture `error.name` and message. Check:

- duplicate name;
- invalid/empty name or description;
- unserializable schema;
- already-aborted signal;
- inactive document;
- `NotAllowedError`;
- origin-keyed requirement;
- invalid `exposedTo` origin.

### Tool registers but is not visible

Check:

- browser agent observation timing;
- expected page/frame is active;
- registration was not immediately aborted;
- cross-origin `allow="tools"`;
- `exposedTo` and `fromOrigins` agreement for in-page consumers;
- target product actually supports Site tools in the current surface;
- stale inspector/agent registry; trigger/re-query after `toolchange`.

### Wrong tool is selected

Do not immediately add “never use” language. Examine:

- overlapping names/descriptions;
- too many simultaneously registered tools;
- action versus preparation ambiguity;
- schema or parameter descriptions carrying hidden selection semantics;
- dynamic tools registered outside valid state;
- related distractor cases;
- user prompt variation;
- whether no tool was the correct answer.

Reduce or restructure the toolset before model-specific patches.

### Correct tool, wrong arguments

Check:

- schema types and required fields;
- opaque IDs;
- transformation burden pushed to the model;
- date/time/locale ambiguity;
- dynamic choices missing from visible state;
- cross-field rules not represented or explained;
- insufficient-information behavior;
- canonicalization in application code.

### Callback runs but UI is stale

Check:

- direct API call bypasses store/action;
- asynchronous reconciliation not awaited;
- optimistic update rolled back;
- stale closure;
- route/selection changed;
- callback executed in another frame/document;
- cancellation suppressed a final update.

### Tool remains after leaving the page state

Check:

- owner cleanup ran;
- one controller per correct lifetime;
- async registration raced with unmount;
- HMR left an old session;
- multiple registration call sites;
- attributes remained on a declarative form;
- route reuse kept the owner mounted.

### Cancellation appears to succeed but effect happened

Identify the commit boundary. Aborting the browser promise or fetch does not guarantee the server did not commit. Query by idempotency/operation ID and report an uncertain outcome until reconciled.

## Agent evaluation suite

Generate a deterministic plan:

```bash
python scripts/webmcp_toolkit.py eval-plan MANIFEST.json --format json
```

Then execute with the target agent/model when available.

### Selection

For each tool:

- direct positive;
- paraphrase;
- terse request;
- noisy natural request;
- related distractor tool;
- no-tool request;
- tool unavailable in current state;
- preparation versus execution distinction.

Research on function-calling robustness motivates naturalistic query variation and semantically related toolset expansion, not just exact benchmark prompts.

### Arguments

Test:

- exact extraction;
- optional fields omitted;
- defaults;
- enums and semantic values;
- out-of-range values;
- format variation;
- extra fields;
- insufficient information;
- changed user answer;
- dynamic IDs;
- raw input versus unnecessary model transformation.

Score tool selection separately from argument correctness.

### Multi-tool and state

Test:

- correct chain/order;
- state dependency;
- invalid order;
- intermediate milestone;
- final visible/durable state;
- user goal revision mid-conversation;
- repeated operation;
- stale result/identifier;
- cancellation;
- tool disappears during the journey.

ToolSandbox emphasizes stateful execution, implicit dependencies, insufficient information, and intermediate/final milestones. τ-bench emphasizes interaction, policy adherence, end-state comparison, and repeated-run reliability. Transfer those principles rather than copying benchmark domains.

### No-tool and refusal

A robust agent should not call a tool when:

- the user only asks for explanation;
- the required page state is absent;
- information is insufficient and the correct next step is a question;
- the action is outside the site's capabilities;
- the requested effect needs a human review step not yet completed.

### Repeated-run reliability

One successful run is weak evidence for stochastic agents. Run multiple seeds/trials when the environment permits and report:

- pass@1 or success rate;
- all-trials reliability such as pass^k when appropriate;
- selection and argument breakdown;
- failure clusters;
- confidence intervals or at least sample count;
- exact model/version/date/configuration.

Do not compare systems with different tool lists or hidden prompts without recording the difference.

## Evaluation records

Each case should define:

```json
{
  "id": "set_range.related-distractor",
  "layer": "agent",
  "initialState": {},
  "availableTools": [],
  "prompt": "...",
  "expectedSelection": "set_dashboard_date_range",
  "expectedArguments": {},
  "expectedVisibleState": {},
  "expectedDurableState": {},
  "deterministicAssertions": [],
  "judgeCriteria": [],
  "status": "NOT RUN"
}
```

Keep model judging separate from candidate execution. Prefer deterministic state assertions when outcomes are structured.

## Research-to-test transfer

### API-Bank and decomposed tool evaluation

Separate:

- tool retrieval/selection;
- planning;
- argument construction;
- execution;
- response/review.

An aggregate score can hide the failing stage.

### ToolSandbox

Add:

- state dependencies;
- canonicalization;
- insufficient information;
- dynamic intermediate/final milestones;
- on-policy dialogue where feasible.

### τ-bench and τ²-bench

Add:

- domain/policy adherence;
- end-state comparison;
- multi-turn user interaction;
- reliability across repetitions;
- tasks requiring coordination with the user rather than autonomous execution.

### Function-calling robustness

Add:

- natural prompt perturbations;
- semantically related tools;
- larger toolsets with controlled distractors;
- selection stability across variations.

### Structured-output caveat

A format-compliant call does not prove procedural or application correctness. Score interface compliance, tool decision, and environment outcome separately.

## Adversarial and trust-boundary tests

When warranted, test:

- metadata containing instruction-like text;
- external/user-generated output containing instruction-like text;
- read tool followed by mutating tool;
- over-parameterized input requests;
- description/effect mismatch;
- cross-origin owner substitution;
- stale tool re-registration with changed schema;
- external content causing the agent to skip confirmation.

Use the security reference for design details. Keep adversarial tests proportionate to the toolset.

## Release matrix

Use a matrix, not one overall claim:

| Layer | Status | Evidence |
|---|---|---|
| Skill structure | PASS/WARN/FAIL/UNSUPPORTED/NOT RUN | validator report |
| Toolkit tests | PASS/WARN/FAIL/UNSUPPORTED/NOT RUN | test output |
| Manifest | PASS/WARN/FAIL/UNSUPPORTED/NOT RUN | validation JSON |
| Generated syntax/types | PASS/WARN/FAIL/UNSUPPORTED/NOT RUN | Node/compiler output |
| Application and normal UI | PASS/WARN/FAIL/UNSUPPORTED/NOT RUN | project test output |
| Browser/WPT conformance | PASS/WARN/FAIL/UNSUPPORTED/NOT RUN | target/browser evidence |
| Chrome native discovery/invocation | PASS/WARN/FAIL/UNSUPPORTED/NOT RUN | browser receipt |
| ChatGPT native discovery/invocation | PASS/WARN/FAIL/UNSUPPORTED/NOT RUN | Site tools/Sources receipt |
| Agent selection | PASS/WARN/FAIL/UNSUPPORTED/NOT RUN | eval records |
| End-to-end visible/durable state | PASS/WARN/FAIL/UNSUPPORTED/NOT RUN | UI/database assertions |
| DUAL MCP and composition | PASS/WARN/FAIL/UNSUPPORTED/NOT RUN | MCP and host-agent receipts |
| Adversarial/failure recovery | PASS/WARN/FAIL/UNSUPPORTED/NOT RUN | scoped cases |
| Deployment/auth | PASS/WARN/FAIL/UNSUPPORTED/NOT RUN | live URL/build receipt |
| Fresh package | PASS/WARN/FAIL/UNSUPPORTED/NOT RUN | extracted validation |

Only the exact candidate in the package inherits these statuses.

## Completion gate

Evaluation is sufficient for release when:

- deterministic failures are repaired;
- lifecycle and cancellation have executed tests;
- application effect and visible UI agree;
- browser discovery is tested on every claimed target or marked `NOT RUN`/`UNSUPPORTED`;
- native Chrome and native ChatGPT checks are separate;
- agent selection includes positives, related negatives, no-tool, and state cases;
- consequential paths include confirmation and uncertain-outcome tests;
- repeated-run evidence includes model/config/sample counts;
- package extraction matches the tested candidate.
