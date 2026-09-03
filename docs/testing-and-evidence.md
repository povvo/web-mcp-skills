# Testing and evidence

A complete WebMCP release has several proof layers. Each layer answers a different question. Passing the first six does not cause the seventh to become embarrassed and pass by association.

## Release evidence ladder

| Layer | Question | Minimum evidence |
| --- | --- | --- |
| Contract | Are product and tool manifests valid and internally consistent? | Schema and semantic reports with zero errors or warnings |
| Operation | Do real handlers produce the required state and results? | Domain tests covering read, write, conflict, invalid input, and cancellation where applicable |
| Adapter | Do generated tools register and invoke those handlers? | Runtime tests against a controlled `document.modelContext` |
| Shared UI | Do human and tool actions reconcile in the visible page? | Browser automation plus screenshots or DOM receipts |
| Web Platform Tests | Does a target browser implement the native API contract? | Native WPT report, browser version, test revision, pass/fail counts |
| Chromium discovery | Can headed Chromium discover and invoke the deployed tools? | Host-native tool inventory and invocation receipt |
| ChatGPT Site tools | Can the built-in browser discover and invoke the deployed tools? | Native Site tools inventory, permission step, invocation result, visible page evidence |
| MCP composition | Does the optional MCP adapter work through a real SDK transport and host? | Protocol initialize/list/call exchange and shared-operation evidence |
| Model behavior | Does the selected model choose and use tools for representative prompts? | Versioned trigger/behavior suite, model identity, raw outputs, scoring contract |
| Deployment | Are the verified bytes reachable at a stable URL? | Provider receipt, URL, commit/artifact hash, HTTP/browser check |
| Distribution | Can a clean user discover and install the exact skill? | Current `skills` CLI version, clean install tree, fresh self-test, published commit |

## Deterministic checks

From the repository root:

```powershell
npm --prefix examples test
python -B skills/web-mcp/scripts/webmcp_toolkit.py self-test --profile full
```

For each example, rerun `product-plan` and `compile-product`, then compare the generated adapter with a clean regeneration. A release package should be inspected before extraction, extracted into a fresh directory, compared to source by file path and SHA-256, and tested from that extraction.

Deterministic checks can prove:

- required files exist;
- schemas and semantic relationships pass;
- declared handlers resolve;
- adapters register, delegate, cancel, and serialize correctly;
- source and packaged bytes match;
- the package contains no dependency trees, caches, nested archives, or repository-only paths.

They cannot prove native host discovery, model choice, or deployment.

## Browser checks

Serve the examples over HTTP. For each page:

1. Confirm there are no console or module-loading errors.
2. Exercise every visible control with pointer and keyboard.
3. Exercise invalid input and revision-conflict recovery.
4. Invoke every registered tool through a controlled WebMCP host or native browser surface.
5. Confirm returned identifiers/revisions match the visible state.
6. Reload and confirm documented persistence.
7. Inspect narrow viewport, 200–400% reflow, dark mode, reduced motion, and forced colours.
8. Record browser version, feature flag/origin-trial state, URL, tool inventory, calls, results, and screenshots.

A polyfill or test shim is useful adapter evidence. Label it as such. It is not native Chromium or ChatGPT evidence.

## Web Platform Tests

Run the native WebMCP tests from [Web Platform Tests](https://github.com/web-platform-tests/wpt/tree/master/webmcp) in a supported browser. Pin both the WPT revision and browser build. Report behavioral and strict conformance separately when a single Web IDL mismatch exists; a near-perfect count still contains a failure, which remains capable of arithmetic.

## ChatGPT Site tools

Open the deployed page in the ChatGPT desktop app’s built-in browser. Confirm the Site tools surface appears, inspect Available site tools, approve the website-access prompt when requested, invoke a read and write tool, then inspect the page and Recently used/Sources evidence. Availability depends on the account, selected model, app version, page, and tool. If authentication or rollout prevents discovery, record **blocked**, not **failed implementation** and not **passed after local simulation**.

## Live model evaluation

Separate activation from behavior:

- **Activation suite:** prompts where the model should choose one tool, no tool, or request missing information.
- **Behavior suite:** multi-step tasks requiring inspection, revision use, mutation, result checking, and recovery.

Pin the model and host configuration. Preserve raw tool selections, arguments, results, visible final state, and scoring rules. A suite that truncates before the model can respond is an invalid run, not a philosophical statement about intelligence.

## Current repository evidence

Machine-produced evidence belongs under `build/` and is excluded from the portable skill and published source unless deliberately selected as a compact release receipt. The public release summary should name what ran, what remains blocked, and which hashes identify the candidate. See [Release and sharing](release-and-sharing.md).
