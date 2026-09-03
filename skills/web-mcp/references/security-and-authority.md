# Security and authority

Read this reference when the user explicitly requests security/privacy/governance review or when a tool handles external or user-generated content, sensitive inputs, cross-origin access, durable writes, communication, purchases, permissions, deletion, or other consequential effects.

For ordinary page-local reads and reversible UI state, apply the baseline controls and return to implementation. Do not expand every build into a full governance exercise.


## Proportionate review depth

Use three levels:

- **Baseline** — accurate metadata, minimum inputs, existing authorization, runtime validation, lifecycle/cancellation, output trust, and UI parity.
- **Heightened** — add data-flow review, origin review, adversarial output tests, logging/retention review, and repeated retries for external content, sensitive inputs, cross-origin exposure, or durable writes.
- **Consequential** — add exact-operation confirmation, step-up authentication where the application requires it, idempotency/receipt checks, uncertain-outcome recovery, and independent end-state verification for purchases, communication, permissions, deletion, or irreversible actions.

The deterministic `threat-model` command is a structured prompt for review, not proof of security.

## Core authority model

WebMCP exposes another path to application functionality. The website remains responsible for its own security.

In DUAL mode, page/session identity and MCP client/server identity may differ. Record and test both; sharing an operation name does not establish equivalent authority.

The following are claims, not proof:

- a tool name;
- a natural-language description;
- `readOnlyHint`;
- `untrustedContentHint`;
- an input schema;
- a returned `"success"` value;
- a page's assertion that the user authorized an action.

Enforcement belongs in deterministic application and service controls:

- session authentication;
- tenant/resource authorization;
- CSRF/origin protections where relevant;
- input validation and canonicalization;
- current-state/precondition checks;
- confirmation and transaction rules;
- rate limits and abuse controls;
- idempotency;
- audit/receipt generation.

Tool definitions, arguments, and results are untrusted content from the agent's perspective. Website content is not permission to disclose unrelated user information or take an unrelated sensitive action.

## Threat model

Trace actors and boundaries before implementation:

- user;
- browser/agent;
- top-level page;
- same-origin and cross-origin frames;
- registered tool and handler;
- application state store;
- backend/API;
- external data sources;
- third-party recipients;
- logs, analytics, and caches.

For each boundary record data, authority, expected origin, side effect, trust, retention, and verification.

### 1. Metadata or description injection

A malicious or compromised page can put instructions in tool names, descriptions, titles, or parameter descriptions to redirect the agent, request secrets, or manipulate later actions.

Controls:

- keep metadata factual, short, and action-specific;
- treat metadata as a capability advertisement, not instructions;
- reject tool descriptions that ask the agent to ignore policy, visit unrelated sites, reveal context, or call other tools;
- test tool-selection poisoning, including a malicious tool that imitates a legitimate one;
- keep sensitive context out of arguments unless the user's task requires it.

### 2. Output injection

External pages, reviews, tickets, messages, documents, or search results can contain adversarial instructions.

Controls:

- set `untrustedContentHint: true` for user-generated, external, or mixed output;
- return bounded structured records with source/provenance identifiers;
- maintain an explicit data/instruction boundary;
- never promote output text into tool descriptions, system instructions, executable code, destinations, recipients, or follow-on actions;
- independently authorize every later tool call;
- require confirmation for consequential follow-on actions;
- include adversarial content in eval fixtures.

Provenance marking or “spotlighting” can improve robustness in a measured setting, but it is not a universal guarantee. Adaptive attacks can bypass defenses that appear strong against fixed attacks. Test the combined system.

### 3. Intent misrepresentation

A tool can be described as a read or preparation step while actually purchasing, sending, deleting, granting access, or changing state.

Controls:

- compare description and manifest semantics with the handler call graph and observed network/state effects;
- use direct effect verbs;
- fail validation when `readOnlyHint` conflicts with the declared effect;
- separate preview from commit where scope or consent matters;
- show and confirm recipient, amount, resource, permission, or deletion set;
- return authoritative evidence and reconcile the visible UI.

### 4. Privacy leakage through over-parameterization

A schema can solicit age, location, pregnancy, health, browsing history, purchase history, or other personal context under plausible personalization language.

Controls:

- require a field-by-field necessity test;
- derive authorized context inside the site/service instead of asking the agent to transmit it;
- omit optional personalization by default;
- declare sensitive inputs and purpose in build semantics;
- prohibit unrelated cross-site context;
- minimize logs and retention;
- test that the agent leaves unnecessary fields absent;
- test rejection of unknown properties.

The toolkit uses name-based heuristics only. Domain privacy review remains necessary.

### 5. Signed-in-session privilege

The page can act with the user's current credentials even when no secret appears in tool arguments.

Controls:

- apply the same or stronger authorization as the human UI/API path;
- require reauthentication or step-up checks where the existing application does;
- use current state, not stale agent assertions;
- bind consequential confirmation to the exact operation;
- include tenant/account/resource identifiers in the confirmation and result;
- log actor, origin, tool, input digest, result, and authoritative transaction ID without storing unnecessary content.

### 6. Cross-origin exposure

`exposedTo` broadens who can discover and invoke a tool in the document tree.

Controls:

- default to same origin;
- list exact secure origins;
- avoid wildcard and unnecessary partners;
- apply Permissions Policy deliberately;
- authorize inside the handler regardless of exposure;
- test embedding direction, caller origin, frame navigation, and revoked partnerships;
- review data returned to cross-origin callers separately from same-origin UI needs.

### 7. Cancellation, navigation, and race conditions

An aborted call can race with a server commit. A registration can become stale after route, tenant, permission, or selection changes.

Controls:

- propagate execution signals;
- use idempotency and authoritative status checks for uncertain commits;
- abort state-dependent registrations promptly;
- re-check preconditions immediately before mutation;
- distinguish cancellation requested, cancellation completed, commit completed, and outcome unknown;
- test navigation, back-forward cache, component unmount, rapid re-registration, and late promise resolution.

### 8. UI/tool path divergence

The WebMCP handler may call a different code path than the visible interface and omit validation or confirmation.

Controls:

- invoke shared application/service functions;
- keep one permission model;
- write integration tests comparing UI and tool paths;
- update the same state store;
- verify the visible result;
- preserve the human interface as a fallback and review surface.

Do not invent a consequential-action annotation, `requestUserInput`, or native confirmation API that is only an open proposal. Use the application's actual review/confirmation path and describe host confirmation behavior separately.

## Consequential action gate

Before committing a purchase, destructive change, external communication, permission change, or equivalent high-impact effect, verify all of:

1. the user asked for the effect or approved the exact current preview;
2. the current account, tenant, resource, recipient, amount, and scope are visible or otherwise inspectable;
3. authorization is fresh;
4. the handler uses the authoritative service;
5. retries cannot silently duplicate the action;
6. the output contains authoritative evidence;
7. cancellation/unknown-outcome behavior is defined;
8. the UI reflects or can inspect the result.

A host safety review reduces risk but does not make a page or output trustworthy.

## Security evaluation set

At minimum include:

- poisoned description that requests unrelated secrets;
- malicious output that asks for another tool call;
- lookalike tool with overlapping name/schema;
- read-only claim with hidden mutation;
- schema requesting unrelated sensitive attributes;
- cross-origin caller not on the allowlist;
- tenant switch during execution;
- confirmation decline;
- duplicate/retry after timeout;
- execution cancellation before and during commit;
- stale selection/route;
- UI and API result mismatch;
- partial backend failure;
- compromised external content in a tool chain.

Measure both task utility and attack success. A defense that blocks attacks by making the tool unusable is not a production success.

## Research basis

The build architecture incorporates:

- Greshake et al., *Not What You've Signed Up For* (2023), DOI `10.1145/3605764.3623985`, establishing indirect prompt injection against LLM-integrated applications and tool/API manipulation.
- Debenedetti et al., *AgentDojo* (2024), DOI `10.52202/079017-2636`, supporting realistic utility and security evaluation of agents operating over untrusted tool data.
- Hines et al., *Defending Against Indirect Prompt Injection Attacks With Spotlighting* (2024), arXiv `2403.14720`, supporting provenance-oriented transformations as one measured defense.
- Zhan et al., *Adaptive Attacks Break Defenses Against Indirect Prompt Injection Attacks on LLM Agents* (2025), DOI `10.18653/v1/2025.findings-naacl.395`, motivating adaptive rather than fixed-only testing.
- *Prompt Injection Attack to Tool Selection in LLM Agents* (NDSS 2026), motivating tool-selection and metadata-poisoning cases.

These works inform the test model. They do not prove a particular site is secure.
