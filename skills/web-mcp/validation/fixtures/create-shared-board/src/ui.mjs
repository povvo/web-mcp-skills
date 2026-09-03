import {addBoardItem, boardApplication, inspectBoard} from "./domain.mjs";
import {registerWebMCPTools} from "./webmcp-tools.js";

const list = document.querySelector("#board-items");
const count = document.querySelector("#item-count");
const revision = document.querySelector("#revision");
const activity = document.querySelector("#activity");
const form = document.querySelector("#add-item-form");
const input = document.querySelector("#item-title");

boardApplication.subscribe((state) => {
  list.replaceChildren(...state.items.map((item) => {
    const row = document.createElement("li");
    row.dataset.itemId = item.id;
    row.textContent = item.title;
    return row;
  }));
  count.textContent = String(state.items.length);
  revision.textContent = String(state.revision);
  activity.textContent = state.activity;
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const state = boardApplication.getState();
  form.setAttribute("aria-busy", "true");
  try {
    await addBoardItem({title: input.value, expectedRevision: state.revision}, {});
    input.value = "";
  } catch (error) {
    activity.textContent = error instanceof Error ? error.message : String(error);
  } finally {
    form.removeAttribute("aria-busy");
  }
});

registerWebMCPTools({inspectBoard, addBoardItem}).then((registration) => {
  document.documentElement.dataset.webmcp = registration.supported ? "ready" : "unsupported";
});
