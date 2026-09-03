import {annotateEvidenceRecord, evidenceDeskApplication, inspectEvidenceDesk, selectEvidenceRecord} from "./domain.mjs";
import {registerWebMCPTools} from "../webmcp-tools.js";

const elements = {
  activity: document.querySelector("#activity"), annotationCount: document.querySelector("#annotation-count"), detail: document.querySelector("#selected-detail"), form: document.querySelector("#annotation-form"), list: document.querySelector("#evidence-records"), note: document.querySelector("#annotation-note"), revision: document.querySelector("#revision"), runtime: document.querySelector("#runtime-state"), selectedId: document.querySelector("#selected-id"),
};

function render(state) {
  elements.list.replaceChildren(...state.records.map((record) => {
    const row = document.createElement("li"); row.className = "record"; row.dataset.state = record.id === state.selectedRecordId ? "current" : record.state === "blocked" ? "error" : record.state === "observed" ? "complete" : "pending";
    const button = document.createElement("button"); button.type = "button"; button.dataset.recordId = record.id; button.setAttribute("aria-pressed", String(record.id === state.selectedRecordId));
    const title = document.createElement("h3"); title.textContent = record.title;
    const meta = document.createElement("p"); meta.textContent = `${record.state.toUpperCase()} · ${record.annotations.length} annotation${record.annotations.length === 1 ? "" : "s"}`;
    button.append(title, meta); row.append(button); return row;
  }));
  const selected = state.selectedRecord;
  elements.detail.replaceChildren();
  const dl = document.createElement("dl");
  for (const [term, value] of [["Record", selected.title], ["State", selected.state], ["Source", selected.source], ["Finding", selected.summary]]) {
    const dt = document.createElement("dt"); dt.textContent = term; const dd = document.createElement("dd"); dd.textContent = value; dl.append(dt, dd);
  }
  elements.detail.append(dl);
  const notesTitle = document.createElement("h3"); notesTitle.className = "subhead"; notesTitle.textContent = "Annotations"; elements.detail.append(notesTitle);
  const notes = document.createElement("ul"); notes.className = "records";
  if (selected.annotations.length) selected.annotations.forEach((annotation) => { const item = document.createElement("li"); item.className = "record"; item.textContent = annotation.note; notes.append(item); });
  else { const item = document.createElement("li"); item.className = "empty"; item.textContent = "No annotations exist for this record."; notes.append(item); }
  elements.detail.append(notes);
  elements.selectedId.textContent = selected.id; elements.annotationCount.textContent = String(selected.annotations.length); elements.revision.textContent = String(state.revision); elements.activity.textContent = state.activity; elements.activity.dataset.tone = "default";
}

evidenceDeskApplication.subscribe(render);
async function run(action) { try { await action(); } catch (error) { elements.activity.dataset.tone = "error"; elements.activity.textContent = error instanceof Error ? error.message : String(error); } }

elements.list.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-record-id]"); if (!button) return;
  run(() => selectEvidenceRecord({recordId: button.dataset.recordId, expectedRevision: evidenceDeskApplication.getState().revision}, {}));
});
elements.form.addEventListener("submit", async (event) => {
  event.preventDefault(); elements.note.removeAttribute("aria-invalid");
  const selected = evidenceDeskApplication.getState();
  try { await annotateEvidenceRecord({recordId: selected.selectedRecordId, note: elements.note.value, expectedRevision: selected.revision}, {}); elements.note.value = ""; elements.note.focus(); }
  catch (error) { elements.note.setAttribute("aria-invalid", "true"); elements.activity.dataset.tone = "error"; elements.activity.textContent = error instanceof Error ? error.message : String(error); }
});

try {
  const registration = await registerWebMCPTools({inspectEvidenceDesk, selectEvidenceRecord, annotateEvidenceRecord});
  elements.runtime.textContent = registration.supported ? `${registration.registered.length} tools registered` : "WebMCP unavailable · human controls remain active";
} catch (error) { elements.runtime.textContent = `Tool registration failed · ${error instanceof Error ? error.message : String(error)}`; }
