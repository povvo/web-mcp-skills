const STORAGE_KEY = "webmcp.examples.shared-board.v1";

function copy(value) { return JSON.parse(JSON.stringify(value)); }
function abortReason(signal) { return signal?.reason ?? new DOMException("The operation was aborted.", "AbortError"); }
function assertActive(signal) { if (signal?.aborted) throw abortReason(signal); }
function memoryStorage() {
  const values = new Map();
  return {getItem: (key) => values.get(key) ?? null, setItem: (key, value) => values.set(key, value)};
}
function browserStorage() {
  try { if (typeof globalThis.window !== "undefined" && globalThis.window.localStorage) return globalThis.window.localStorage; } catch { /* The page can continue in memory. */ }
  return memoryStorage();
}

export function createBoardApplication({
  storage = browserStorage(),
  createId = () => globalThis.crypto?.randomUUID?.() ?? `item-${Date.now()}`,
} = {}) {
  const listeners = new Set();
  let state = {boardId: "shared-board", items: [], revision: 0, activity: "Board ready."};

  try {
    const stored = storage.getItem(STORAGE_KEY);
    const parsed = stored ? JSON.parse(stored) : null;
    if (parsed?.boardId === "shared-board" && Array.isArray(parsed.items) && Number.isInteger(parsed.revision)) {
      state = {...parsed, activity: "Saved board restored."};
    }
  } catch {
    state.activity = "Saved board unavailable. This page session remains usable.";
  }

  function publish() {
    const snapshot = copy(state);
    for (const listener of listeners) listener(snapshot);
  }

  function persist() {
    try { storage.setItem(STORAGE_KEY, JSON.stringify(state)); }
    catch { state = {...state, activity: `${state.activity} Storage did not accept the update.`}; }
  }

  async function inspectBoard(input = {}, {signal} = {}) {
    assertActive(signal);
    if (!input || typeof input !== "object" || Array.isArray(input) || Object.keys(input).length) {
      throw new TypeError("inspectBoard accepts an empty object");
    }
    return {boardId: state.boardId, items: copy(state.items), itemCount: state.items.length, revision: state.revision};
  }

  async function addBoardItem(input, {signal} = {}) {
    assertActive(signal);
    const title = typeof input?.title === "string" ? input.title.trim() : "";
    if (!title || title.length > 120) throw new TypeError("title must contain 1 to 120 non-whitespace characters");
    if (!Number.isInteger(input?.expectedRevision) || input.expectedRevision < 0) throw new TypeError("expectedRevision must be a non-negative integer");
    if (input.expectedRevision !== state.revision) {
      const conflict = new Error(`Board revision changed from ${input.expectedRevision} to ${state.revision}. Inspect the board before adding the item.`);
      conflict.name = "RevisionConflictError";
      throw conflict;
    }
    assertActive(signal);
    const item = {id: createId(), title};
    state = {...state, items: [...state.items, item], revision: state.revision + 1, activity: `Added “${title}” at revision ${state.revision + 1}.`};
    persist();
    publish();
    return {boardId: state.boardId, itemId: item.id, item: copy(item), itemCount: state.items.length, revision: state.revision};
  }

  return {
    inspectBoard,
    addBoardItem,
    getState: () => copy(state),
    subscribe(listener) { listeners.add(listener); listener(copy(state)); return () => listeners.delete(listener); },
  };
}

export const boardApplication = createBoardApplication();
export function inspectBoard(input, context) { return boardApplication.inspectBoard(input, context); }
export function addBoardItem(input, context) { return boardApplication.addBoardItem(input, context); }
