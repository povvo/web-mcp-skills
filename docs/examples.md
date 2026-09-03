# Three working examples

The examples are small enough to inspect and complete enough to fail honestly. Each has a normal interface, a canonical state owner, versioned persistence, WebMCP tool contracts, a generated adapter, operation tests, and generated-adapter invocation tests.

Run them from `examples/`:

```powershell
npm start
npm test
```

Then open `http://127.0.0.1:4173`.

All three use the Web MCP Design system: JetBrains Mono, a neutral high-contrast palette, one bounded signal region, one geometric rupture, native controls, visible focus, 44px targets, stable labels, explicit states, responsive reflow, dark mode, forced-colour support, and reduced-motion end states. There are no decorative network clouds. The packets have been informed.

## Shared Board

**Journey:** inspect a board, then add one item without overwriting a newer human or agent change.

**Canonical owner:** `boardApplication` in `examples/shared-board/src/domain.mjs`.

**Tools:**

| Tool | Effect | Input | Returned evidence |
| --- | --- | --- | --- |
| `inspect_board` | Read | Empty object | Board ID, all items, count, revision |
| `add_board_item` | Local write | `title`, `expectedRevision` | Item ID, committed item, count, new revision |

Both the labelled form and `add_board_item` call `addBoardItem`. A stale `expectedRevision` raises `RevisionConflictError` and leaves the board unchanged. The page preserves invalid input and reports the repair.

Inspect [Shared Board source](../examples/shared-board/) or open `/shared-board/` from the local server.

## Release Rail

**Journey:** inspect a four-step release path, complete the current step, or reopen a completed step.

**Canonical owner:** `releaseRailApplication` in `examples/release-rail/src/domain.mjs`.

**Tools:**

| Tool | Effect | Input | Returned evidence |
| --- | --- | --- | --- |
| `inspect_release_rail` | Read | Empty object | Ordered steps, current step, complete count, revision |
| `advance_release_step` | Local write | `expectedRevision` | Completed step, next current step, count, revision |
| `reopen_release_step` | Local write | `stepId`, `expectedRevision` | Reopened step, affected later steps, count, revision |

The rail uses sample state and labels it. Advancing changes one current node to complete and promotes the next pending node. Reopening a step makes it current and returns every later non-pending state to pending. The result names that affected scope.

Inspect [Release Rail source](../examples/release-rail/) or open `/release-rail/`.

## Evidence Desk

**Journey:** inspect sample evidence, select a record, and add a factual annotation without changing the record’s evidence state.

**Canonical owner:** `evidenceDeskApplication` in `examples/evidence-desk/src/domain.mjs`.

**Tools:**

| Tool | Effect | Input | Returned evidence |
| --- | --- | --- | --- |
| `inspect_evidence_desk` | Read | Empty object | All records, explicit states, selection, annotations, revision |
| `select_evidence_record` | Local write | `recordId`, `expectedRevision` | Selected record, unchanged evidence state, revision |
| `annotate_evidence_record` | Local write | `recordId`, `note`, `expectedRevision` | Saved annotation, count, unchanged evidence state, revision |

The sample records use `observed`, `prepared`, and `blocked` literally. Selection changes the shared detail region. Annotation adds user-generated content. Neither action promotes evidence state.

Inspect [Evidence Desk source](../examples/evidence-desk/) or open `/evidence-desk/`.

## Read the generated boundary

Each application’s `webmcp-tools.js` is generated from `product.json` and `toolset.json`. The corresponding `src/ui.mjs` imports that adapter and passes exported domain handlers into `registerWebMCPTools()`.

That is the recurring shape:

1. The UI calls an operation.
2. The tool adapter calls the same operation.
3. The operation commits state.
4. Subscribers render the committed state.
5. The caller receives structured evidence including identifiers and revision.

The tests invoke both the domain operations and the registered tool callbacks. A generated file existing on disk is useful, but not yet behavior.
