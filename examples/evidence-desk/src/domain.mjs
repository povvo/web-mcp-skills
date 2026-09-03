const STORAGE_KEY = "webmcp.examples.evidence-desk.v1";
const RECORDS = Object.freeze([
  {id: "wpt", title: "Native Web Platform Tests", state: "observed", source: "Browser test run", summary: "Behavioral conformance was executed in a browser. Exact results belong in the attached receipt."},
  {id: "site-tools", title: "ChatGPT Site tools", state: "blocked", source: "Native host attempt", summary: "Discovery requires an eligible signed-in host and an open deployed page. A generated adapter is not that host."},
  {id: "deployment", title: "Deployment candidate", state: "prepared", source: "Release pipeline", summary: "Deployable bytes exist. Public availability requires a deployment receipt from the selected provider."},
]);

function copy(value) { return JSON.parse(JSON.stringify(value)); }
function abortReason(signal) { return signal?.reason ?? new DOMException("The operation was aborted.", "AbortError"); }
function assertActive(signal) { if (signal?.aborted) throw abortReason(signal); }
function memoryStorage() { const values = new Map(); return {getItem: (key) => values.get(key) ?? null, setItem: (key, value) => values.set(key, value)}; }
function browserStorage() { try { if (typeof globalThis.window !== "undefined" && globalThis.window.localStorage) return globalThis.window.localStorage; } catch { /* Continue in memory. */ } return memoryStorage(); }
function initialState() { return {deskId: "evidence-desk", selectedRecordId: "wpt", annotations: [], revision: 0, activity: "Evidence desk ready."}; }

export function createEvidenceDeskApplication({
  storage = browserStorage(),
  createId = () => globalThis.crypto?.randomUUID?.() ?? `note-${Date.now()}`,
} = {}) {
  const listeners = new Set();
  let state = initialState();
  try {
    const parsed = JSON.parse(storage.getItem(STORAGE_KEY) ?? "null");
    if (parsed?.deskId === "evidence-desk" && RECORDS.some((record) => record.id === parsed.selectedRecordId) && Array.isArray(parsed.annotations) && Number.isInteger(parsed.revision)) {
      state = {...parsed, activity: "Saved evidence desk restored."};
    }
  } catch { state.activity = "Saved desk unavailable. This page session remains usable."; }

  function recordById(recordId) { return RECORDS.find((record) => record.id === recordId) ?? null; }
  function snapshot() {
    const records = RECORDS.map((record) => ({...record, annotations: copy(state.annotations.filter((item) => item.recordId === record.id))}));
    return {...copy(state), records, selectedRecord: copy(records.find((record) => record.id === state.selectedRecordId))};
  }
  function publish() { const next = snapshot(); for (const listener of listeners) listener(next); }
  function persist() { try { storage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch { state = {...state, activity: `${state.activity} Storage did not accept the update.`}; } }
  function checkRevision(expectedRevision) {
    if (!Number.isInteger(expectedRevision) || expectedRevision < 0) throw new TypeError("expectedRevision must be a non-negative integer");
    if (expectedRevision !== state.revision) { const error = new Error(`Desk revision changed from ${expectedRevision} to ${state.revision}. Inspect the desk before changing it.`); error.name = "RevisionConflictError"; throw error; }
  }

  async function inspectEvidenceDesk(input = {}, {signal} = {}) {
    assertActive(signal);
    if (!input || typeof input !== "object" || Array.isArray(input) || Object.keys(input).length) throw new TypeError("inspectEvidenceDesk accepts an empty object");
    return snapshot();
  }

  async function selectEvidenceRecord(input, {signal} = {}) {
    assertActive(signal); checkRevision(input?.expectedRevision);
    const record = recordById(input?.recordId);
    if (!record) throw new TypeError("recordId must identify an evidence record");
    if (record.id !== state.selectedRecordId) {
      state = {...state, selectedRecordId: record.id, revision: state.revision + 1, activity: `Selected “${record.title}”. Evidence state remains ${record.state}.`};
      persist(); publish();
    }
    return {deskId: state.deskId, recordId: record.id, evidenceState: record.state, revision: state.revision};
  }

  async function annotateEvidenceRecord(input, {signal} = {}) {
    assertActive(signal); checkRevision(input?.expectedRevision);
    const record = recordById(input?.recordId);
    if (!record) throw new TypeError("recordId must identify an evidence record");
    const note = typeof input?.note === "string" ? input.note.trim() : "";
    if (!note || note.length > 280) throw new TypeError("note must contain 1 to 280 non-whitespace characters");
    const annotation = {id: createId(), recordId: record.id, note};
    state = {...state, selectedRecordId: record.id, annotations: [...state.annotations, annotation], revision: state.revision + 1, activity: `Annotation saved for “${record.title}”. Evidence state remains ${record.state}.`};
    persist(); publish();
    return {deskId: state.deskId, recordId: record.id, annotationId: annotation.id, annotation: copy(annotation), annotationCount: state.annotations.filter((item) => item.recordId === record.id).length, evidenceState: record.state, revision: state.revision};
  }

  return {inspectEvidenceDesk, selectEvidenceRecord, annotateEvidenceRecord, getState: snapshot, subscribe(listener) { listeners.add(listener); listener(snapshot()); return () => listeners.delete(listener); }};
}

export const evidenceDeskApplication = createEvidenceDeskApplication();
export function inspectEvidenceDesk(input, context) { return evidenceDeskApplication.inspectEvidenceDesk(input, context); }
export function selectEvidenceRecord(input, context) { return evidenceDeskApplication.selectEvidenceRecord(input, context); }
export function annotateEvidenceRecord(input, context) { return evidenceDeskApplication.annotateEvidenceRecord(input, context); }
