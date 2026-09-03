import {addBoardItem, boardApplication, inspectBoard} from "./domain.mjs";
import {registerWebMCPTools} from "../webmcp-tools.js";

const elements = {
  activity: document.querySelector("#activity"),
  count: document.querySelector("#item-count"),
  form: document.querySelector("#add-item-form"),
  input: document.querySelector("#item-title"),
  list: document.querySelector("#board-items"),
  revision: document.querySelector("#revision"),
  runtime: document.querySelector("#runtime-state"),
};

function render(state) {
  elements.list.replaceChildren(...state.items.map((item) => {
    const row = document.createElement("li");
    row.className = "record";
    row.dataset.itemId = item.id;
    row.dataset.state = "complete";
    const title = document.createElement("h3");
    title.textContent = item.title;
    const id = document.createElement("p");
    id.textContent = item.id;
    row.append(title, id);
    return row;
  }));
  if (!state.items.length) {
    const empty = document.createElement("li");
    empty.className = "empty";
    empty.textContent = "Nothing exists on this board. Add the first item.";
    elements.list.replaceChildren(empty);
  }
  elements.count.textContent = String(state.items.length);
  elements.revision.textContent = String(state.revision);
  elements.activity.textContent = state.activity;
  elements.activity.dataset.tone = "default";
}

boardApplication.subscribe(render);

elements.form.addEventListener("submit", async (event) => {
  event.preventDefault();
  elements.form.setAttribute("aria-busy", "true");
  elements.input.removeAttribute("aria-invalid");
  try {
    const {revision} = boardApplication.getState();
    await addBoardItem({title: elements.input.value, expectedRevision: revision}, {});
    elements.input.value = "";
    elements.input.focus();
  } catch (error) {
    elements.input.setAttribute("aria-invalid", "true");
    elements.activity.dataset.tone = "error";
    elements.activity.textContent = error instanceof Error ? error.message : String(error);
  } finally {
    elements.form.removeAttribute("aria-busy");
  }
});

try {
  const registration = await registerWebMCPTools({inspectBoard, addBoardItem});
  document.documentElement.dataset.webmcp = registration.supported ? "ready" : "unsupported";
  elements.runtime.textContent = registration.supported ? `${registration.registered.length} tools registered` : "WebMCP unavailable · human controls remain active";
} catch (error) {
  document.documentElement.dataset.webmcp = "error";
  elements.runtime.textContent = `Tool registration failed · ${error instanceof Error ? error.message : String(error)}`;
}
