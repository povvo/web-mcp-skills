const STORAGE_KEY = "webmcp.examples.release-rail.v1";
const STEP_DEFINITIONS = Object.freeze([
  {id: "contract", title: "Freeze tool contract", detail: "Validate names, schemas, effects, and shared operation bindings."},
  {id: "tests", title: "Run behavioral tests", detail: "Exercise read, write, conflict, failure, and cancellation paths."},
  {id: "evidence", title: "Read release evidence", detail: "Separate executed proof from prepared or blocked external gates."},
  {id: "publish", title: "Publish verified bytes", detail: "Share the exact candidate that passed the release gates."},
]);

function copy(value) { return JSON.parse(JSON.stringify(value)); }
function abortReason(signal) { return signal?.reason ?? new DOMException("The operation was aborted.", "AbortError"); }
function assertActive(signal) { if (signal?.aborted) throw abortReason(signal); }
function memoryStorage() { const values = new Map(); return {getItem: (key) => values.get(key) ?? null, setItem: (key, value) => values.set(key, value)}; }
function browserStorage() { try { if (typeof globalThis.window !== "undefined" && globalThis.window.localStorage) return globalThis.window.localStorage; } catch { /* Continue in memory. */ } return memoryStorage(); }
function initialState() {
  return {railId: "release-rail", revision: 0, activity: "Release rail ready.", steps: STEP_DEFINITIONS.map((step, index) => ({...step, state: index === 0 ? "current" : "pending"}))};
}

export function createReleaseRailApplication({storage = browserStorage()} = {}) {
  const listeners = new Set();
  let state = initialState();
  try {
    const parsed = JSON.parse(storage.getItem(STORAGE_KEY) ?? "null");
    const ids = parsed?.steps?.map((step) => step.id);
    if (parsed?.railId === "release-rail" && Number.isInteger(parsed.revision) && JSON.stringify(ids) === JSON.stringify(STEP_DEFINITIONS.map((step) => step.id))) {
      state = {...parsed, activity: "Saved release rail restored."};
    }
  } catch { state.activity = "Saved rail unavailable. This page session remains usable."; }

  function snapshot() {
    const completeCount = state.steps.filter((step) => step.state === "complete").length;
    return {...copy(state), completeCount, stepCount: state.steps.length, currentStep: copy(state.steps.find((step) => step.state === "current") ?? null)};
  }
  function publish() { const next = snapshot(); for (const listener of listeners) listener(next); }
  function persist() { try { storage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch { state = {...state, activity: `${state.activity} Storage did not accept the update.`}; } }
  function checkRevision(expectedRevision) {
    if (!Number.isInteger(expectedRevision) || expectedRevision < 0) throw new TypeError("expectedRevision must be a non-negative integer");
    if (expectedRevision !== state.revision) { const error = new Error(`Rail revision changed from ${expectedRevision} to ${state.revision}. Inspect the rail before changing it.`); error.name = "RevisionConflictError"; throw error; }
  }

  async function inspectReleaseRail(input = {}, {signal} = {}) {
    assertActive(signal);
    if (!input || typeof input !== "object" || Array.isArray(input) || Object.keys(input).length) throw new TypeError("inspectReleaseRail accepts an empty object");
    return snapshot();
  }

  async function advanceReleaseStep(input, {signal} = {}) {
    assertActive(signal);
    checkRevision(input?.expectedRevision);
    const index = state.steps.findIndex((step) => step.state === "current");
    if (index < 0) { const error = new Error("Every release step is already complete."); error.name = "SequenceCompleteError"; throw error; }
    const completed = state.steps[index];
    const steps = state.steps.map((step, stepIndex) => stepIndex === index ? {...step, state: "complete"} : stepIndex === index + 1 ? {...step, state: "current"} : step);
    const next = steps[index + 1] ?? null;
    state = {...state, steps, revision: state.revision + 1, activity: next ? `Completed “${completed.title}”. “${next.title}” is current.` : `Completed “${completed.title}”. Release rail complete.`};
    persist(); publish();
    return {railId: state.railId, completedStepId: completed.id, nextCurrentStepId: next?.id ?? null, completeCount: steps.filter((step) => step.state === "complete").length, revision: state.revision};
  }

  async function reopenReleaseStep(input, {signal} = {}) {
    assertActive(signal);
    checkRevision(input?.expectedRevision);
    const index = state.steps.findIndex((step) => step.id === input?.stepId);
    if (index < 0) throw new TypeError("stepId must identify a release rail step");
    if (state.steps[index].state !== "complete") { const error = new Error(`Step “${input.stepId}” is not complete and cannot be reopened.`); error.name = "InvalidStepStateError"; throw error; }
    const affectedStepIds = state.steps.slice(index + 1).filter((step) => step.state !== "pending").map((step) => step.id);
    const steps = state.steps.map((step, stepIndex) => stepIndex < index ? {...step, state: "complete"} : stepIndex === index ? {...step, state: "current"} : {...step, state: "pending"});
    state = {...state, steps, revision: state.revision + 1, activity: `Reopened “${steps[index].title}”. ${affectedStepIds.length} later state${affectedStepIds.length === 1 ? "" : "s"} returned to pending.`};
    persist(); publish();
    return {railId: state.railId, reopenedStepId: steps[index].id, affectedStepIds, completeCount: index, revision: state.revision};
  }

  return {inspectReleaseRail, advanceReleaseStep, reopenReleaseStep, getState: snapshot, subscribe(listener) { listeners.add(listener); listener(snapshot()); return () => listeners.delete(listener); }};
}

export const releaseRailApplication = createReleaseRailApplication();
export function inspectReleaseRail(input, context) { return releaseRailApplication.inspectReleaseRail(input, context); }
export function advanceReleaseStep(input, context) { return releaseRailApplication.advanceReleaseStep(input, context); }
export function reopenReleaseStep(input, context) { return releaseRailApplication.reopenReleaseStep(input, context); }
