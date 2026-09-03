

# Skills for Web MCP

Two agent skills, one for actual work on Web MCP, and the other is an optional extra, mainly so that you can make nice looking outputs with minimal friction. Three running WebMCP applications. The `web-mcp` skill builds web applications where the human interface and WebMCP agent tools share one canonical domain operation, no parallel business logic inside tool callbacks, no DOM-click automation dressed up as integration. The `web-mcp-design` skill ships a source-independent visual system that works alongside the first. WebMCP is an experimental browser standard; the skills track what was tested rather than what the specification diagram implies is already stable.

[![Validate skills](https://github.com/povvo/web-mcp-skills/actions/workflows/validate-skills.yml/badge.svg)](https://github.com/povvo/web-mcp-skills/actions/workflows/validate-skills.yml) ![Node.js ≥ 20](https://img.shields.io/badge/node-%E2%89%A520-3c3c3c?logo=nodedotjs&logoColor=white) ![WebMCP experimental](https://img.shields.io/badge/WebMCP-experimental-525252)

## Install

List available skills:

```bash
npx skills add povvo/web-mcp-skills --list
```

Install `web-mcp` into the current project:

```bash
npx skills add povvo/web-mcp-skills --skill web-mcp
```

Install the visual-system companion:

```bash
npx skills add povvo/web-mcp-skills --skill web-mcp-design
```

Install both globally for Codex:

```bash
npx skills add povvo/web-mcp-skills --skill '*' --agent codex --global --yes
```

The installable trees are [`skills/web-mcp`](skills/web-mcp) and [`skills/web-mcp-design`](skills/web-mcp-design). Each is self-contained and carries no `node_modules`, virtual environment, repository `/docs` dependency, or build cache.

## Why this exists

Backend MCP servers work without an open page. Browser automation tools work with whatever the DOM currently renders. Neither produces an application where a person and an agent work on the same shared artifact through the same state and business rules at the same time.

WebMCP is a browser API — `document.modelContext` — that lets the current page register structured tools. Those tools share the page's application code, signed-in browser session, visible state, and lifecycle. The `web-mcp` skill builds the adapter that binds those tools to real application operations. The application still owns the operation. The adapter remains thin. When that boundary collapses, the application acquires a second source of truth and a permanent appointment with itself.

The `web-mcp-design` skill is optional. It supplies the visual system used in the repository and examples and is independent of the implementation skill.

## What ships

| Surface | Location | Purpose |
| --- | --- | --- |
| WebMCP implementation skill | `skills/web-mcp/` | Instructions, compiler, schemas, validation, references, agents, and icon |
| Web MCP design skill | `skills/web-mcp-design/` | Visual manual, foundations, tokens, components, patterns, accessibility, and generation guidance |
| Shared Board | `examples/shared-board/` | Revision-protected `inspect_board` and `add_board_item` tools |
| Release Rail | `examples/release-rail/` | Finite `inspect_release_rail`, `advance_release_step`, and `reopen_release_step` tools |
| Evidence Desk | `examples/evidence-desk/` | Evidence-preserving `inspect_evidence_desk`, `select_evidence_record`, and `annotate_evidence_record` tools |
| Repository banner | `assets/` | Visual identity for the repository surface |
| Official snapshots | `docs/official/snapshots/` | Upstream source material, retained without editorial changes |

Each example is dependency-free, uses local browser storage, labels sample data, and keeps the human interface fully usable when WebMCP is absent. Each generated adapter was compiled from a validated product contract and tool manifest.

## Run the examples

```bash
cd examples
npm start
```

Open `http://127.0.0.1:4173`. Run all domain and generated-adapter tests:

```bash
npm test
```

## Verify

```bash
npm test
python -B skills/web-mcp/scripts/webmcp_toolkit.py self-test --profile full --format text
```

The checks validate the portable skill, run 12 application and adapter tests, validate every product contract, and compare each checked-in generated adapter against a clean regeneration. CI validates skill structure, compiler output, examples, and install discovery on every push.

Native browser, ChatGPT Site tools, live model, MCP transport, and deployment evidence are separate gates. See [Testing and evidence](docs/testing-and-evidence.md) for the exact boundary.

## Documentation

Start with the [field manual](docs/README.md):

- [What WebMCP is](docs/what-webmcp-is.md)
- [Using the skill](docs/using-the-skill.md)
- [How the examples work](docs/examples.md)
- [WebMCP, MCP, and operation ownership](docs/architecture.md)
- [Testing and evidence](docs/testing-and-evidence.md)
- [Release and sharing](docs/release-and-sharing.md)
- [Official material snapshots and provenance](docs/official/README.md)

## Repository layout

```text
skills/web-mcp/          portable WebMCP implementation skill
skills/web-mcp-design/   portable visual-system skill
examples/                three runnable WebMCP applications
docs/                    field manual and official snapshots
assets/                  repository banner
.github/                 structural, compiler, example, and install validation
```

## Known limitations

WebMCP is an experimental browser standard. A Chrome 149 origin trial and an Edge 150 origin trial are in progress; other browsers are not currently supported. ChatGPT Site tools use WebMCP in the ChatGPT desktop app's built-in browser under specific account, model, and page conditions — this is not a Chrome feature and is not universally available. Treat both as versioned implementation status, not stable platform APIs.

The `npm start` development server is a preview. Examples use local browser storage with no backend, network dependency, or build step required.

No project license has been selected for original content in this repository. The [OpenAI WebMCP Challenge](https://openai.com/webmcp-challenge/) requires a public repository with a license; challenge readiness remains blocked until one is chosen. Three third-party content areas have independent licenses: JetBrains Mono font files under `examples/_shared/fonts/` remain under OFL-1.1; WebMCP specification material under `docs/official/snapshots/` remains under the W3C Software and Document License; the OpenAI Site tools snapshot is not covered by the project license. See [Third-party notices](docs/third-party-notices.md) for the exact boundary.

## License

No project license has been selected. See [Known limitations](#known-limitations) and [Third-party notices](docs/third-party-notices.md).
