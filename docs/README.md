# Web MCP field manual

This repository ships one portable Agent Skill and three working WebMCP applications. The skill builds the operation contract, tool schemas, adapters, tests, and release evidence. The examples show what that output looks like when the page is obliged to do something.

WebMCP is an experimental web standard. A page registers structured tools through `document.modelContext`; a supporting agent discovers and invokes them while the page is open. The user and agent then work against the same application state, provided the application was built that way. Registration cannot rescue imaginary product logic. It has tried nothing and is already blameless.

## Start here

1. Read [What WebMCP is](what-webmcp-is.md) for the browser/API boundary.
2. Read [Using the `web-mcp` skill](using-the-skill.md) to create or extend an application.
3. Run the [three examples](examples.md) and inspect their generated tool adapters.
4. Use [Architecture](architecture.md) when the page also needs a backend MCP server or external services.
5. Use [Testing and evidence](testing-and-evidence.md) before claiming browser, host, model, or deployment support.
6. Use [Release and sharing](release-and-sharing.md) to package the skill and publish the repository.

## What ships

| Surface | Location | Purpose |
| --- | --- | --- |
| Portable skill | `skills/web-mcp/` | Self-contained instructions, compiler, schemas, references, agents, validation, and icon |
| Shared Board | `examples/shared-board/` | Revision-protected inspect and add operations |
| Release Rail | `examples/release-rail/` | Finite inspect, advance, and reopen operations |
| Evidence Desk | `examples/evidence-desk/` | Evidence-preserving inspect, select, and annotate operations |
| Repository banner | `assets/web-mcp-repository-banner.svg` | Human and site-tool paths converging on shared application state |
| Official snapshots | `docs/official/snapshots/` | Supplied source material retained without editorial changes |

The repository documentation may point into the skill. The installed skill never points back into this repository or `/docs`; its required knowledge travels inside `skills/web-mcp/`.

## Run the examples

From `examples/`:

```powershell
npm start
```

Open `http://127.0.0.1:4173`. No dependency installation is required. Run all domain and generated-adapter tests with:

```powershell
npm test
```

The interface remains usable when WebMCP is absent. In a supporting host, each page reports how many tools registered.

## Evidence language

This manual uses the following states literally:

- **Observed** — the named check ran and produced inspectable evidence.
- **Prepared** — the code or artifact exists, but the external action has not run.
- **Blocked** — a required host, permission, credential, or response prevented the check.
- **Not run** — no execution is claimed.
- **Failed** — the check ran and did not meet its contract.

Structural validation proves structure. A browser test proves browser behavior. A deployment receipt proves deployment. They are colleagues, not aliases.

## Current sources

The living references are the [WebMCP repository](https://github.com/webmachinelearning/webmcp), [draft specification](https://webmachinelearning.github.io/webmcp/), [OpenAI Site tools help](https://help.openai.com/en/articles/20001423-using-site-tools-in-the-chatgpt-desktop-app), [`webmcp-types`](https://www.npmjs.com/package/webmcp-types), and [OpenAI WebMCP Challenge](https://openai.com/webmcp-challenge/). The preserved local source ledger is in [Official material](official/README.md).
