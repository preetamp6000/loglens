const filterForm = document.querySelector("#filter-form");
const keywordFilter = document.querySelector("#keyword-filter");
const severityFilter = document.querySelector("#severity-filter");
const dateFilter = document.querySelector("#date-filter");
const logsBody = document.querySelector("#logs-body");
const errorsContent = document.querySelector("#errors-content");
const resultCount = document.querySelector("#result-count");

let activeRequest;

function currentQuery() {
  const params = new URLSearchParams();
  if (severityFilter.value) params.set("severity", severityFilter.value);
  if (keywordFilter.value.trim()) params.set("keyword", keywordFilter.value.trim());
  if (dateFilter.value) params.set("date", dateFilter.value);
  return params.toString();
}

function setLoading() {
  logsBody.replaceChildren();
  const row = document.createElement("tr");
  const cell = document.createElement("td");
  cell.colSpan = 3;
  const state = document.createElement("div");
  state.className = "table-state";
  const spinner = document.createElement("span");
  spinner.className = "spinner";
  const text = document.createElement("span");
  text.textContent = "Loading log records…";
  state.append(spinner, text);
  cell.append(state);
  row.append(cell);
  logsBody.append(row);
  errorsContent.replaceChildren();
  const errorLoading = document.createElement("div");
  errorLoading.className = "inline-loading";
  const errorSpinner = document.createElement("span");
  errorSpinner.className = "spinner";
  errorLoading.append(errorSpinner, document.createTextNode("Loading error analysis…"));
  errorsContent.append(errorLoading);
  resultCount.textContent = "Loading…";
}

function setTableState(message, kind) {
  logsBody.replaceChildren();
  const row = document.createElement("tr");
  const cell = document.createElement("td");
  cell.colSpan = 3;
  const state = document.createElement("div");
  state.className = `table-state ${kind}-state`;
  state.textContent = message;
  cell.append(state);
  row.append(cell);
  logsBody.append(row);
}

function renderRecords(records) {
  logsBody.replaceChildren();
  if (records.length === 0) {
    setTableState("No log entries match these filters.", "empty");
    return;
  }

  const fragment = document.createDocumentFragment();
  for (const record of records) {
    const row = document.createElement("tr");
    const timestamp = document.createElement("td");
    timestamp.className = "timestamp-cell";
    timestamp.textContent = record.timestamp;

    const severity = document.createElement("td");
    const badge = document.createElement("span");
    badge.className = `severity-badge severity-${record.severity.toLowerCase()}`;
    badge.textContent = record.severity;
    severity.append(badge);

    const message = document.createElement("td");
    message.className = "message-cell";
    message.textContent = record.message;
    row.append(timestamp, severity, message);
    fragment.append(row);
  }
  logsBody.append(fragment);
}

function renderFrequentErrors(errors) {
  errorsContent.replaceChildren();
  if (errors.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty-errors";
    empty.textContent = "No errors found for the current filters.";
    errorsContent.append(empty);
    return;
  }

  const fragment = document.createDocumentFragment();
  errors.forEach((error, index) => {
    const row = document.createElement("div");
    row.className = "error-row";
    const rank = document.createElement("span");
    rank.className = "error-rank";
    rank.textContent = String(index + 1).padStart(2, "0");
    const message = document.createElement("span");
    message.className = "error-message";
    message.title = error.message;
    message.textContent = error.message;
    const count = document.createElement("span");
    count.className = "error-count";
    const dot = document.createElement("span");
    dot.className = "error-count-dot";
    const countText = document.createElement("span");
    countText.textContent = `${error.count} ${error.count === 1 ? "event" : "events"}`;
    count.append(dot, countText);
    row.append(rank, message, count);
    fragment.append(row);
  });
  errorsContent.append(fragment);
}

async function loadDashboard() {
  if (activeRequest) activeRequest.abort();
  activeRequest = new AbortController();
  setLoading();

  const query = currentQuery();
  try {
    const response = await fetch(`/api/dashboard${query ? `?${query}` : ""}`, {
      headers: { Accept: "application/json" },
      signal: activeRequest.signal,
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Could not load dashboard data.");

    document.querySelector("#total-count").textContent = data.summary.total_logs.toLocaleString();
    document.querySelector("#info-count").textContent = data.summary.info.toLocaleString();
    document.querySelector("#warning-count").textContent = data.summary.warning.toLocaleString();
    document.querySelector("#error-count").textContent = data.summary.error.toLocaleString();
    resultCount.textContent = `${data.records.length.toLocaleString()} ${data.records.length === 1 ? "entry" : "entries"}`;
    document.querySelector("#table-footer-text").textContent =
      `${data.invalid_lines} invalid ${data.invalid_lines === 1 ? "line" : "lines"} skipped in source`;
    document.querySelector("#connection-status").classList.remove("is-error");
    document.querySelector("#connection-status").lastChild.textContent = " LIVE DATA";
    document.querySelector("#source-dot").classList.remove("is-error");
    document.querySelector("#source-dot").setAttribute("aria-label", "Connected");
    renderRecords(data.records);
    renderFrequentErrors(data.frequent_errors);
  } catch (error) {
    if (error.name === "AbortError") return;
    document.querySelector("#total-count").textContent = "—";
    document.querySelector("#info-count").textContent = "—";
    document.querySelector("#warning-count").textContent = "—";
    document.querySelector("#error-count").textContent = "—";
    document.querySelector("#connection-status").classList.add("is-error");
    document.querySelector("#connection-status").lastChild.textContent = " SOURCE ERROR";
    document.querySelector("#source-dot").classList.add("is-error");
    document.querySelector("#source-dot").setAttribute("aria-label", "Disconnected");
    resultCount.textContent = "Unavailable";
    setTableState(error.message || "Unable to reach the dashboard. Check your connection and try again.", "error");
    errorsContent.replaceChildren();
    const errorMessage = document.createElement("div");
    errorMessage.className = "empty-errors";
    errorMessage.textContent = error.message || "Error analysis is unavailable.";
    errorsContent.append(errorMessage);
  }
}

filterForm.addEventListener("submit", (event) => {
  event.preventDefault();
  loadDashboard();
});

severityFilter.addEventListener("change", loadDashboard);
dateFilter.addEventListener("change", loadDashboard);

document.querySelector("#clear-filters").addEventListener("click", () => {
  filterForm.reset();
  loadDashboard();
});

document.querySelector("#export-button").addEventListener("click", () => {
  const query = currentQuery();
  window.location.assign(`/api/export.csv${query ? `?${query}` : ""}`);
});

loadDashboard();
