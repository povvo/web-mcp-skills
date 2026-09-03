import {advanceReleaseStep, inspectReleaseRail, releaseRailApplication, reopenReleaseStep} from "./domain.mjs";
import {registerWebMCPTools} from "../webmcp-tools.js";

const elements = {
  activity: document.querySelector("#activity"),
  advance: document.querySelector("#advance-step"),
  complete: document.querySelector("#complete-count"),
  current: document.querySelector("#current-step"),
  path: document.querySelector("#release-path"),
  revision: document.querySelector("#revision"),
  runtime: document.querySelector("#runtime-state"),
};

function render(state) {
  elements.complete.textContent = `${state.completeCount}/${state.stepCount}`;
  elements.current.textContent = state.currentStep?.title ?? "Rail complete";
  elements.revision.textContent = String(state.revision);
  elements.advance.disabled = !state.currentStep;
  elements.advance.textContent = state.currentStep ? `Complete ${state.currentStep.title}` : "Every step complete";
  elements.activity.textContent = state.activity;
  elements.activity.dataset.tone = "default";
  elements.path.replaceChildren(...state.steps.map((step) => {
    const row = document.createElement("li");
    row.className = "record";
    row.dataset.state = step.state;
    const title = document.createElement("h3");
    title.textContent = step.title;
    const detail = document.createElement("p");
    detail.textContent = `${step.state.toUpperCase()} · ${step.detail}`;
    row.append(title, detail);
    if (step.state === "complete") {
      const actions = document.createElement("div");
      actions.className = "actions";
      const reopen = document.createElement("button");
      reopen.className = "button";
      reopen.type = "button";
      reopen.dataset.reopenStep = step.id;
      reopen.textContent = `Reopen ${step.title}`;
      actions.append(reopen);
      row.append(actions);
    }
    return row;
  }));
}

releaseRailApplication.subscribe(render);

async function run(action) {
  elements.activity.dataset.tone = "default";
  try { await action(); }
  catch (error) { elements.activity.dataset.tone = "error"; elements.activity.textContent = error instanceof Error ? error.message : String(error); }
}

elements.advance.addEventListener("click", () => run(() => advanceReleaseStep({expectedRevision: releaseRailApplication.getState().revision}, {})));
elements.path.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-reopen-step]");
  if (!button) return;
  run(() => reopenReleaseStep({stepId: button.dataset.reopenStep, expectedRevision: releaseRailApplication.getState().revision}, {}));
});

try {
  const registration = await registerWebMCPTools({inspectReleaseRail, advanceReleaseStep, reopenReleaseStep});
  elements.runtime.textContent = registration.supported ? `${registration.registered.length} tools registered` : "WebMCP unavailable · human controls remain active";
} catch (error) { elements.runtime.textContent = `Tool registration failed · ${error instanceof Error ? error.message : String(error)}`; }
