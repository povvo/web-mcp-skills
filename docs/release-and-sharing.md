# Release and sharing

There are two release units:

1. the portable `web-mcp` Agent Skill;
2. the repository containing that skill, the three examples, public documentation, brand assets, and CI.

They share a commit but have different boundaries. This is why `node_modules` does not need a commemorative place in either one.

## Portable skill candidate

The package source is exactly `skills/web-mcp/`. A release candidate must contain:

- `SKILL.md` with valid `name: web-mcp` frontmatter;
- every referenced script, schema, reference, agent, fixture, and asset;
- the skill icon at `assets/web-mcp-icon.svg`;
- no references to repository `/docs`, examples, build output, or absolute workspace paths;
- no dependency tree, virtual environment, cache, nested archive, secret, or unrelated repository file.

Build the archive, inspect its paths, extract it fresh, compare hashes, and run the full self-test from the extraction. Publish the resulting bytes as `web-mcp.skill` with byte count, archive SHA-256, tree SHA-256, source commit, toolkit version, and test summary.

## Repository candidate

The recommended public destination is `povvo/web-mcp`. Before the first external write, confirm:

- destination owner and repository name;
- public visibility;
- the exact source root;
- license;
- direct default-branch push or review branch/pull request.

Do not invent a license. The OpenAI WebMCP Challenge requires a public code repository with a license, so publication remains blocked until the owner selects one.

## Clean installation

After publication, verify current CLI discovery and installation from a clean temporary project:

```powershell
npx --yes skills@latest add povvo/web-mcp --skill web-mcp --agent codex --copy --yes
```

Record the `skills` CLI version and published commit SHA. Inspect the installed file tree, parse its `SKILL.md`, compare it with the published source, and run the bundled self-test there. Local registration is not a remote install receipt.

## CI

Repository CI should:

1. validate every skill under `skills/`;
2. run the `web-mcp` full self-test;
3. run all example domain and generated-adapter tests;
4. compile each product contract and reject warnings;
5. confirm generated adapters are deterministic;
6. exercise current `skills@latest` discovery/install against the repository when remote context exists;
7. report exact failures without converting network unavailability into a source defect.

## Challenge-capable output

The [OpenAI WebMCP Challenge](https://openai.com/webmcp-challenge/) identifies the practical bar: a useful, original application whose human-agent experience is meaningfully better through WebMCP, with a working live app, public repository, project description, and demo video required by the linked rules. Judges consider usefulness, originality, execution, thoughtful WebMCP use, and human-agent experience.

For a fully capable skill output, treat the challenge deliverable as more than a landing page:

- a real shared artifact and normal human workflow;
- discoverable tools bound to canonical operations;
- visible reconciliation after tool calls;
- explicit state, effects, trust, conflicts, and recovery;
- native browser and ChatGPT Site tools evidence;
- live model activation/behavior evaluation;
- live deployment and a source-linked demo;
- release/install receipts for the reusable skill.

The repository’s three examples are reusable reference applications, not a challenge submission by themselves. A submission still needs a specific product idea, deployed URL, narrative, and video.

## Publication sequence

1. Freeze source and run all local deterministic and browser checks.
2. Build and fresh-extract `web-mcp.skill`.
3. Inspect the repository diff and secret scan.
4. Confirm destination, visibility, license, and Git operation with the owner.
5. Create/push the repository.
6. Watch CI to completion.
7. Run clean remote skill discovery and install.
8. Deploy the examples or selected product and record the URL/artifact identity.
9. Run native Site tools and Chromium checks against that deployment.
10. Publish the final release receipt with unresolved gates still labelled.

Publication is complete when the remote user path works, not when the local archive has developed confidence.
