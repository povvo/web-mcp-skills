export class BoardOperationError extends Error {
  constructor(code, message) {
    super(message);
    this.name = "BoardOperationError";
    this.code = code;
  }
}

function throwIfAborted(signal) {
  if (signal?.aborted) {
    throw signal.reason ?? new DOMException("The operation was aborted.", "AbortError");
  }
}

function copyItem(item) {
  return { id: item.id, title: item.title };
}

export function createSharedBoard(boardId = "board-1") {
  let revision = 0;
  let nextItemId = 1;
  const items = [];
  const audit = [];
  const listeners = new Set();

  const snapshot = () => ({
    operationId: "board.inspect",
    boardId,
    revision,
    items: items.map(copyItem),
  });

  async function inspectBoard(_input, context = {}) {
    throwIfAborted(context.signal);
    return snapshot();
  }

  async function addBoardItem(input, context = {}) {
    throwIfAborted(context.signal);
    const title = typeof input?.title === "string" ? input.title.trim() : "";
    if (!title || title.length > 80) {
      throw new BoardOperationError("INVALID_TITLE", "title must contain 1-80 non-whitespace characters");
    }
    if (!Number.isInteger(input?.expectedRevision) || input.expectedRevision !== revision) {
      throw new BoardOperationError(
        "REVISION_CONFLICT",
        `expected revision ${input?.expectedRevision}; current revision is ${revision}`,
      );
    }
    throwIfAborted(context.signal);
    const item = { id: `item-${nextItemId++}`, title };
    items.push(item);
    revision += 1;
    const receipt = {
      operationId: "board.add_item",
      boardId,
      item: copyItem(item),
      revision,
      commitId: `${boardId}:r${revision}`,
      surface: context.surface ?? "unknown",
      actorId: context.actor?.id ?? "anonymous",
    };
    audit.push({ ...receipt });
    for (const listener of listeners) listener({ ...receipt });
    return receipt;
  }

  async function selectVisibleBoardItem(input, context = {}) {
    throwIfAborted(context.signal);
    const item = items.find((candidate) => candidate.id === input?.itemId);
    if (!item) {
      throw new BoardOperationError("ITEM_NOT_FOUND", `board item not found: ${input?.itemId}`);
    }
    if (typeof context.page?.setSelection !== "function") {
      throw new BoardOperationError("PAGE_CONTEXT_REQUIRED", "visible selection requires the open board page");
    }
    context.page.setSelection(item.id);
    return {
      operationId: "board.select_visible_item",
      boardId,
      selectedItemId: item.id,
      revision,
    };
  }

  async function readBoardAudit(input = {}, context = {}) {
    throwIfAborted(context.signal);
    const limit = input.limit ?? 20;
    if (!Number.isInteger(limit) || limit < 1 || limit > 100) {
      throw new BoardOperationError("INVALID_LIMIT", "limit must be an integer from 1 to 100");
    }
    return {
      operationId: "board.read_audit",
      boardId,
      revision,
      entries: audit.slice(-limit).map((entry) => ({ ...entry })),
    };
  }

  const operations = Object.freeze({
    inspectBoard,
    addBoardItem,
    selectVisibleBoardItem,
    readBoardAudit,
  });

  return Object.freeze({
    operations,
    snapshot,
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
  });
}
