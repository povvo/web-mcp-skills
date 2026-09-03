# Official source map

Use this reference before making API, compatibility, package-version, browser-support, product-support, or challenge claims. The machine-readable ledger is `assets/sources/official-materials.json`.

## Authority order

For current document WebMCP:

1. current rendered draft and repository source;
2. Web Platform Tests for observed conformance expectations;
3. named browser implementation documentation and behavior;
4. ChatGPT Site tools documentation and native behavior for that product;
5. official explainers for design intent and proposals;
6. community libraries and examples.

For the OpenAI WebMCP Challenge, the current official Devpost rules govern inconsistencies with landing, resource, showcase, or promotional pages.

## Canonical official sources

The portable Skill resolves official evidence from the canonical URLs in `assets/sources/official-materials.json`. Its packaged `references/` explain how to apply that evidence; they are not copies of an external workspace corpus.

| Source class | Canonical authority | Correct use |
|---|---|---|
| draft specification | Web Machine Learning Community Group rendered draft and repository source | Document API algorithms, IDL, origins, cancellation, lifecycle |
| explainer | WebMCP repository README | Motivation, architecture, WebMCP/MCP distinction, open work |
| product documentation | OpenAI Help Center Site tools article | ChatGPT host behavior and limitations |
| implementation status | WebMCP repository status page | Starting point for live compatibility verification |
| declarative proposal | WebMCP repository declarative explainer | Experimental form branch only |
| Service Worker proposal | WebMCP repository Service Worker explainer | Experimental background branch only |
| security and privacy review | WebMCP repository questionnaire | Security/privacy intent and known gaps |

## Portability

- Keep all operational guidance needed by the Skill inside its packaged `SKILL.md`, `references/`, `assets/`, `scripts/`, and `validation/` source.
- Preserve canonical upstream URLs in the ledger.
- Never resolve evidence through a path outside the Skill package.
- Refresh mutable sources before a current claim.
- Record the checked date, version, commit, or browser build in the output.

## Maturity labels

Use exact labels:

- **current draft** — document WebMCP specification; not a W3C Recommendation;
- **browser implementation** — behavior observed or documented for a named build;
- **product subset** — ChatGPT Site tools behavior;
- **incomplete proposal** — declarative forms;
- **unstandardized proposal** — Service Worker WebMCP;
- **development types** — `webmcp-types`, not a runtime;
- **experimental tooling** — Chrome WebMCP eval package;
- **governing rules** — current challenge rules for a time-bounded submission.

Do not replace these with a single “official therefore production” label.

## Current API cautions carried from the official sources

- `ModelContext` is currently exposed to Window/document, not ServiceWorkerGlobalScope.
- The imperative callback may resolve to arbitrary JavaScript, but the platform JSON-serializes the result; application tests must catch non-serializable values early.
- The platform serializes `inputSchema`; application input validation remains the application's responsibility.
- The current annotations are `readOnlyHint` and `untrustedContentHint`; they are hints, not enforcement.
- The current draft contains in-page consumer and cross-origin APIs that a specific product host may not expose.
- ChatGPT's supplied product snapshot excludes declarative tools and all iframe-registered tools.
- Declarative proposal examples may not obey current normative name grammar; normalize to the draft grammar.
- Service Worker proposal examples use vocabulary not present in current document IDL/types.
- MCP-style `content[]` results are not required by WebMCP; return task-appropriate JSON evidence.

## Type package

`webmcp-types` is the official declaration package. At the 2026-08-31 verification, the npm registry `latest` was `0.1.5`.

For TypeScript work:

- resolve and record the package version actually installed;
- type-check generated integration code;
- do not ship a competing global declaration unless the project cannot use the package and the fallback is deliberately scoped;
- do not treat types as browser support, runtime validation, serializability proof, or Service Worker support.

Refresh the registry and repository before asserting the current latest version.

## WPT and browser evidence

Use the current `web-platform-tests/wpt` WebMCP corpus for browser/API conformance. Local shims exercise publisher contracts only.

For a browser claim, record:

- WPT revision or runner;
- browser name/build;
- flags/origin trial;
- passed, failed, unsupported, and skipped cases;
- discovered tool metadata;
- native invocation and visible result.

## Chrome eval evidence

Chrome's `webmcp-evals` tooling is supplemental. Record package version and exact command. Distinguish:

- local/model tool-selection evaluation;
- smoke execution that may force authored calls;
- browser/model multi-step evaluation.

Subset result matching, forced calls, or linearized ordering can hide defects. Retain strict contract and application assertions.

## Challenge evidence

Before a CHALLENGE release, refresh:

- OpenAI challenge landing page;
- governing Devpost rules;
- official resources;
- official WebMCP showcase.

Record dates, submission requirements, judging criteria, and any rule change. Do not infer a minimum tool count from showcase examples.

## Source refresh record

```yaml
claim: concise fact being used
source_id: ledger identifier
canonical_url: direct official URL
checked_at: ISO date/time
revision_or_version: commit, package version, browser build, or unknown
observed: exact supported fact
inference: any conclusion drawn from it
status: PASS | WARN | FAIL | UNSUPPORTED | NOT RUN
```

## Source gate

- Every changing claim has a current official source and checked date.
- Packaged guidance is distinguished from live upstream verification.
- Normative, product, implementation, proposal, and challenge evidence remain separate.
- Inferences are labelled.
- Source gaps become `WARN`, `UNSUPPORTED`, or `NOT RUN`, not fabricated certainty.
