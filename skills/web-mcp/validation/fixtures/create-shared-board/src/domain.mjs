const STORAGE_KEY = "webmcp.shared-board.v1";

function abortReason(signal) {
  return signal?.reason ?? new DOMException("The operation was aborted.", "AbortError");
}

function assertActive(signal) {
  if (signal?.aborted) throw abortReason(signal);
}

function copy(value) {
  return JSON.parse(JSON.stringify(value));
}

function browserStorage() {
  try {
    if (typeof globalThis.window !== "undefined" && globalThis.localStorage) {
      return globalThis.localStorage;
    }
  } catch {
    // Storage can be unavailable under privacy/sandbox policies.
  }
  const memory = new Map();
  return {
    getItem(key) { return memory.has(key) ? memory.get(key) : null; },
    setItem(key, value) { memory.set(key, value); },
  };
}

export function createBoardApplication({
  storage = browserStorage(),
  createId = () => globalThis.crypto?.randomUUID?.() ?? `item-${Date.now()}`,
} = {}) {
  const listeners = new Set();
  let state = {boardId: "shared-board", items: [], revision: 0, activity: "Board ready."};
  try {
    const stored = storage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      if (parsed?.boardId === "shared-board" && Array.isArray(parsed.items) && Number.isInteger(parsed.revision)) {
        state = {...parsed, activity: "Restored saved board."};
      }
    }
  } catch {
    state.activity = "Storage unavailable; using this page session.";
  }

  const publish = () => {
    const snapshot = copy(state);
    for (const listener of listeners) listener(snapshot);
  };
  const persist = () => storage.setItem(STORAGE_KEY, JSON.stringify(state));

  async function inspect(input = {}, {signal} = {}) {
    assertActive(signal);
    if (!input || typeof input !== "object" || Array.isArray(input) || Object.keys(input).length > 0) {
      throw new TypeError("inspectBoard accepts an empty object");
    }
    return {
      boardId: state.boardId,
      items: copy(state.items),
      itemCount: state.items.length,
      revision: state.revision,
    };
  }

  async function add(input, {signal} = {}) {
    assertActive(signal);
    const title = typeof input?.title === "string" ? input.title.trim() : "";
    if (!title || title.length > 120) {
      throw new TypeError("title must contain 1 to 120 non-whitespace characters");
    }
    if (!Number.isInteger(input?.expectedRevision) || input.expectedRevision < 0) {
      throw new TypeError("expectedRevision must be a non-negative integer");
    }
    if (input.expectedRevision !== state.revision) {
      const conflict = new Error(`Board revision changed from ${input.expectedRevision} to ${state.revision}.`);
      conflict.name = "RevisionConflictError";
      throw conflict;
    }
    assertActive(signal);
    const item = {id: createId(), title};
    state = {
      ...state,
      items: [...state.items, item],
      revision: state.revision + 1,
      activity: `Added “${title}”.`,
    };
    persist();
    publish();
    return {
      boardId: state.boardId,
      itemId: item.id,
      item: copy(item),
      itemCount: state.items.length,
      revision: state.revision,
    };
  }

  return {
    inspectBoard: inspect,
    addBoardItem: add,
    getState: () => copy(state),
    subscribe(listener) {
      listeners.add(listener);
      listener(copy(state));
      return () => listeners.delete(listener);
    },
  };
}

export const boardApplication = createBoardApplication();

export function inspectBoard(input, context) {
  return boardApplication.inspectBoard(input, context);
}

export function addBoardItem(input, context) {
  return boardApplication.addBoardItem(input, context);
}
