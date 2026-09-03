# Release profiles

Use this reference for DEVELOPMENT, PRODUCTION, and OpenAI WebMCP CHALLENGE delivery. Release status describes evidence, not intent.

## DEVELOPMENT

Required:

- build profile and compatibility profile;
- capability and tool inventory;
- real canonical operations;
- normal UI path;
- manifest/contract validation;
- direct operation and generated-adapter tests;
- lifecycle, cancellation, and serializability checks;
- exact changed files;
- live layers marked `NOT RUN` when absent.

Development may use local URLs, test data, and a model-context shim, but those limitations must be visible.

## PRODUCTION

Add:

- production build and clean-install instructions;
- supported-browser and host matrix with checked dates;
- deployment configuration and production URL where deployment was authorized;
- authentication/testing instructions;
- accessibility and unsupported-browser behavior;
- browser-native discovery/invocation receipts;
- monitoring and recoverable error behavior appropriate to the app;
- exact source revision and clean-room reproduction;
- public-facing explanation of Site tools where useful.

An application is not production-complete if its ordinary human interface breaks when WebMCP is absent.

## CHALLENGE

The CHALLENGE profile is the highest product-and-evidence bar. Refresh the official rules immediately before packaging. The Devpost rules govern inconsistencies with landing or resource pages.

The rules verified on 2026-08-31 require:

- a working WebMCP-powered web app;
- genuine `document.modelContext.registerTool(...)` integration;
- consistent installation/running and behavior matching the description/demo;
- a live URL accessible through the specified ChatGPT or Chrome environment;
- a public GitHub, GitLab, or Bitbucket repository containing source, assets, run instructions, and a visible open-source license;
- a written explanation of WebMCP fit, UX improvement, new human-agent capability, and implementation;
- a public demonstration video under three minutes, with audio, showing the functioning app and WebMCP;
- authentication credentials or testing instructions when needed;
- clear before/after WebMCP provenance for an existing app.

An MCP server may complement this output but cannot replace the required page-bound WebMCP integration.

## Judging-oriented acceptance

The verified rules apply an initial theme/reasonable-use screen and then four equally weighted criteria:

| Criterion | Required product evidence |
|---|---|
| WebMCP leverage | Non-trivial tools that expose genuine application operations and improve reliability or capability |
| Execution | Runnable, complete, coherent product; normal UI and WebMCP behavior match the claims |
| Potential impact | Specific audience/problem and demonstrated improvement |
| Creativity and ambition | Distinctive shared human-agent workflow or technically ambitious capability |

Do not inflate tool count to target leverage. Official showcases range from small to large toolsets; completeness, shared state, and useful operations matter more.

## Challenge evidence package

Prepare:

```text
README
├─ product and audience
├─ why WebMCP
├─ human-agent workflow
├─ setup/run/test
├─ compatibility and limitations
├─ WebMCP implementation map
└─ license

evidence
├─ capability/tool inventory
├─ architecture diagram
├─ claim-to-test matrix
├─ compatibility receipts
├─ screenshots/captures
├─ deterministic test report
├─ browser/host report
└─ before-after provenance for EXTEND

submission
├─ concise description
├─ four-criterion narrative
├─ live URL
├─ public repository URL
└─ demo script and shot list under three minutes
```

The app, text, screenshots, and video must agree. Remove or qualify any claim not demonstrated by the tested build.

## Demo sequence

A compact demo should show:

1. the normal human product and shared artifact;
2. Available Site tools or browser tool inventory;
3. a meaningful request rather than a contrived direct call;
4. genuine tool execution;
5. the visible application effect;
6. the person reviewing, editing, or continuing the result;
7. one concise architecture/evidence explanation.

Do not spend most of the video on setup, registration logs, or slides.

## Release status matrix

Report at least:

| Layer | Examples |
|---|---|
| Static | schemas, tool names, profile rules, source dates |
| Operation | canonical handlers, validation, persistence, UI parity |
| Adapter | handler preflight, registration rollback, cancellation, JSON results |
| Lifecycle | route/remount/navigation/BFCache |
| Browser | WPT/API, discovery, invocation, observed schema |
| Model | selection, arguments, distractors, state dependency, repeated runs |
| Host | native Chrome and native ChatGPT receipts, separately |
| Deployment | live URL, auth path, production build |
| Package | public source, license, clean extraction, exact revision |
| Submission | narrative, video, URLs, claim parity |

Use only `PASS`, `WARN`, `FAIL`, `UNSUPPORTED`, or `NOT RUN` for checks. A required `FAIL` blocks release. A required `NOT RUN` is a visible gap, not a pass.

## External actions

Preparing deployment files does not prove deployment. Preparing repository metadata does not make the repository public. Preparing a demo script does not upload a video. Report these states separately:

- prepared;
- executed;
- verified by receipt.

Perform external publication only when it is within the user's requested release action.

## Release gate

- The exact candidate tree is identified.
- The product works through normal UI and genuine WebMCP.
- Claims match executable behavior and evidence.
- Compatibility facts were refreshed.
- Native host checks are separate and truthful.
- Clean-install/build/test instructions work from a fresh extraction.
- CHALLENGE artifacts satisfy the current governing rules.
- Deployment, public repository, license, and video states are explicit.
