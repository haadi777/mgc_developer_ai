"use strict";

const API_URL = "https://78b3c3d3-8000.inc1.devtunnels.ms/chat";
const PREDICT_URL = "https://78b3c3d3-8000.inc1.devtunnels.ms/predict_lead";

const chatEl = document.getElementById("chat");
const welcomeEl = document.getElementById("welcome");
const messagesEl = document.getElementById("messages");
const formEl = document.getElementById("composer");
const inputEl = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const newChatBtn = document.getElementById("newChatBtn");
const threadEl = document.getElementById("threadId");
const suggestionButtons = Array.from(document.querySelectorAll(".suggestion"));

const messages = [];
let currentThreadId = "";
let isSending = false;
let abortController = null;
let typingNode = null;

function createThreadId() {
  const random = Math.random().toString(36).substring(2, 8);
  return `ollama-session-${Date.now()}-${random}`;
}

function updateThreadLabel() {
  threadEl.textContent = `Thread: ${currentThreadId}`;
  threadEl.title = currentThreadId;
}

function syncAppHeight() {
  const viewport = window.visualViewport;
  const height = viewport ? viewport.height : window.innerHeight;
  document.documentElement.style.setProperty("--app-height", `${height}px`);
}

function resizeInput() {
  inputEl.style.height = "auto";
  const nextHeight = Math.min(inputEl.scrollHeight, 160);
  inputEl.style.height = `${nextHeight}px`;
  inputEl.style.overflowY = inputEl.scrollHeight > 160 ? "auto" : "hidden";
}

function updateSendState() {
  const hasText = inputEl.value.trim().length > 0;
  sendBtn.disabled = isSending || !hasText;
  suggestionButtons.forEach((button) => {
    button.disabled = isSending;
  });
}

function scrollToBottom() {
  requestAnimationFrame(() => {
    chatEl.scrollTop = chatEl.scrollHeight;
  });
}

function syncView() {
  const hasConversation = messages.length > 0 || typingNode !== null;
  welcomeEl.hidden = hasConversation;
  messagesEl.hidden = !hasConversation;
}

function createMessage(role, text) {
  const item = document.createElement("article");
  item.className = `message message-${role}`;

  const label = document.createElement("span");
  label.className = "sr-only";
  label.textContent = role === "user" ? "You" : "AI Assistant";

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  const body = document.createElement("p");
  body.className = "message-text";
  body.textContent = text;
  bubble.append(body);

  if (role === "assistant") {
    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.setAttribute("aria-hidden", "true");
    avatar.textContent = "AI";
    item.append(avatar, label, bubble);
  } else {
    item.append(label, bubble);
  }

  return item;
}

function createTypingIndicator() {
  const item = document.createElement("div");
  item.className = "message message-assistant typing";

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.setAttribute("aria-hidden", "true");
  avatar.textContent = "AI";

  const bubble = document.createElement("div");
  bubble.className = "bubble typing-bubble";

  const text = document.createElement("span");
  text.textContent = "AI is thinking";

  const dots = document.createElement("span");
  dots.className = "dots";
  dots.setAttribute("aria-hidden", "true");
  for (let index = 0; index < 3; index += 1) {
    dots.append(document.createElement("span"));
  }

  bubble.append(text, dots);
  item.append(avatar, bubble);
  return item;
}

function showTyping() {
  hideTyping();
  typingNode = createTypingIndicator();
  messagesEl.append(typingNode);
  syncView();
  scrollToBottom();
}

function hideTyping() {
  if (!typingNode) return;
  typingNode.remove();
  typingNode = null;
}

function appendMessage(role, text) {
  messages.push({ role, text });
  messagesEl.append(createMessage(role, text));
  syncView();
  scrollToBottom();
}

function clearConversation() {
  messages.length = 0;
  hideTyping();
  messagesEl.replaceChildren();
  syncView();
}

function friendlyError(error) {
  const base = "Sorry, I couldn't get a response right now. Please try again.";
  if (error && error.code === "cors") {
    return `${base}\n\nCORS must be enabled on the API server for this frontend origin.`;
  }
  return base;
}

async function requestReply(threadId, message, signal) {
  let response;

  try {
    response = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        thread_id: threadId,
        message
      }),
      signal
    });
  } catch (error) {
    if (error.name === "AbortError") throw error;
    console.error("Chat request failed before a response was received.", error);
    console.error("CORS must be enabled on the API server for this frontend origin.");
    const corsError = new Error("Network request failed");
    corsError.code = "cors";
    throw corsError;
  }

  if (!response.ok) {
    let body = "";
    try {
      body = await response.text();
    } catch (readError) {
      console.error("Could not read the API error body.", readError);
    }
    console.error("Chat API HTTP error", {
      status: response.status,
      statusText: response.statusText,
      body
    });
    const httpError = new Error("HTTP error");
    httpError.code = "http";
    throw httpError;
  }

  let data;
  try {
    data = await response.json();
  } catch (error) {
    console.error("Chat API returned invalid JSON.", error);
    const jsonError = new Error("Invalid JSON");
    jsonError.code = "json";
    throw jsonError;
  }

  if (!data || typeof data.response !== "string" || data.response.trim() === "") {
    console.error("Chat API returned an empty response.", data);
    const emptyError = new Error("Empty response");
    emptyError.code = "empty";
    throw emptyError;
  }

  return data.response.trim();
}

async function sendMessage(rawText) {
  const message = rawText.trim();
  if (!message || isSending) return;

  const restoreFocus = document.activeElement === inputEl || window.matchMedia("(min-width: 800px)").matches;

  isSending = true;
  updateSendState();
  appendMessage("user", message);
  inputEl.value = "";
  resizeInput();
  updateSendState();
  showTyping();

  const threadId = currentThreadId;
  const controller = new AbortController();
  abortController = controller;

  try {
    const reply = await requestReply(threadId, message, controller.signal);
    if (controller.signal.aborted || threadId !== currentThreadId) return;
    hideTyping();
    appendMessage("assistant", reply);
  } catch (error) {
    if (error.name === "AbortError" || controller.signal.aborted || threadId !== currentThreadId) return;
    hideTyping();
    appendMessage("assistant", friendlyError(error));
  } finally {
    if (abortController === controller) abortController = null;
    if (!controller.signal.aborted && threadId === currentThreadId) {
      isSending = false;
      updateSendState();
      if (restoreFocus) inputEl.focus();
    }
  }
}

function startNewChat() {
  if (abortController) {
    abortController.abort();
    abortController = null;
  }

  isSending = false;
  currentThreadId = createThreadId();
  updateThreadLabel();
  clearConversation();
  inputEl.value = "";
  resizeInput();
  updateSendState();
  inputEl.focus();
}

formEl.addEventListener("submit", (event) => {
  event.preventDefault();
  sendMessage(inputEl.value);
});

inputEl.addEventListener("keydown", (event) => {
  if (event.isComposing || event.keyCode === 229) return;
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendMessage(inputEl.value);
  }
});

inputEl.addEventListener("input", () => {
  resizeInput();
  updateSendState();
});

newChatBtn.addEventListener("click", startNewChat);

suggestionButtons.forEach((button) => {
  button.addEventListener("click", () => {
    sendMessage(button.dataset.question || "");
  });
});

syncAppHeight();
window.addEventListener("resize", syncAppHeight);
if (window.visualViewport) {
  window.visualViewport.addEventListener("resize", syncAppHeight);
}

currentThreadId = createThreadId();
updateThreadLabel();
resizeInput();
updateSendState();

if (window.matchMedia("(min-width: 800px)").matches) {
  inputEl.focus();
}

const leadForm = document.getElementById("leadForm");
const citySelect = document.getElementById("citySelect");
const sourceSelect = document.getElementById("sourceSelect");
const predictBtn = document.getElementById("predictBtn");
const leadStatus = document.getElementById("leadStatus");
const leadResult = document.getElementById("leadResult");
const leadPercent = document.getElementById("leadPercent");
const leadPriority = document.getElementById("leadPriority");

const LEAD_TIMEOUT_MS = 20000;

let isPredicting = false;
let leadAbortController = null;
let leadRequestId = 0;

function markPlaceholder(select) {
  select.classList.toggle("is-placeholder", select.value === "");
}

function updatePredictState() {
  const ready = citySelect.value !== "" && sourceSelect.value !== "";
  predictBtn.disabled = !ready;
  predictBtn.textContent = isPredicting ? "Predicting..." : "Predict";
}

function showLeadStatus(message) {
  leadResult.hidden = true;
  leadStatus.hidden = false;
  leadStatus.textContent = message;
}

async function requestLead(city, source, signal) {
  const payload = {
    source_clean: source,
    city_clean: city
  };

  console.log("Lead API request", {
    url: PREDICT_URL,
    method: "POST",
    body: payload
  });

  let response;

  try {
    response = await fetch(PREDICT_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload),
      signal,
      cache: "no-store"
    });
  } catch (error) {
    if (error.name === "AbortError") throw error;
    console.error("Lead API response", {
      url: PREDICT_URL,
      error
    });
    console.error("CORS must be enabled on the API server for this frontend origin.");
    const corsError = new Error("Network request failed");
    corsError.code = "cors";
    throw corsError;
  }

  if (!response.ok) {
    let body = "";
    try {
      body = await response.text();
    } catch (readError) {
      console.error("Could not read the lead API error body.", readError);
    }
    console.error("Lead API response", {
      url: PREDICT_URL,
      status: response.status,
      statusText: response.statusText,
      body
    });
    const httpError = new Error("HTTP error");
    httpError.code = "http";
    throw httpError;
  }

  let data;
  try {
    data = await response.json();
  } catch (error) {
    console.error("Lead API response", {
      url: PREDICT_URL,
      status: response.status,
      error: "Invalid JSON"
    });
    const jsonError = new Error("Invalid JSON");
    jsonError.code = "json";
    throw jsonError;
  }

  console.log("Lead API response", {
    url: PREDICT_URL,
    status: response.status,
    body: data
  });

  const percentage = data && typeof data.conversion_percentage === "string"
    ? data.conversion_percentage.trim()
    : "";
  const priority = data && typeof data.priority_level === "string"
    ? data.priority_level.trim()
    : "";
  const probability = data && typeof data.conversion_probability === "number"
    ? data.conversion_probability
    : null;

  if (!percentage && probability === null && !priority) {
    console.error("Lead API returned an empty prediction.", data);
    const emptyError = new Error("Empty response");
    emptyError.code = "empty";
    throw emptyError;
  }

  return {
    percentage: percentage || (probability === null ? "—" : `${(probability * 100).toFixed(1)}%`),
    priority: priority || "Unknown"
  };
}

async function predictLead(event) {
  event.preventDefault();
  const city = citySelect.value;
  const source = sourceSelect.value;
  if (!city || !source) return;

  if (leadAbortController) {
    console.log("Lead API request cancelled so a new one can be sent.");
    leadAbortController.abort();
  }

  const controller = new AbortController();
  const requestId = ++leadRequestId;
  leadAbortController = controller;
  const timeoutId = setTimeout(() => controller.abort(), LEAD_TIMEOUT_MS);

  isPredicting = true;
  updatePredictState();
  showLeadStatus("Predicting...");

  try {
    const result = await requestLead(city, source, controller.signal);
    if (requestId !== leadRequestId) return;
    leadStatus.hidden = true;
    leadPercent.textContent = result.percentage;
    leadPriority.textContent = result.priority;
    leadPriority.className = `lead-priority priority-${result.priority.toLowerCase()}`;
    leadResult.hidden = false;
  } catch (error) {
    if (requestId !== leadRequestId) return;
    if (error.name === "AbortError") {
      console.error("Lead API response", {
        url: PREDICT_URL,
        error: "Timed out before a response was received."
      });
      showLeadStatus("The prediction took too long. Please try again.");
      return;
    }
    const corsNote = error && error.code === "cors"
      ? "\n\nCORS must be enabled on the API server for this frontend origin."
      : "";
    showLeadStatus(`Sorry, I couldn't predict this lead right now. Please try again.${corsNote}`);
  } finally {
    clearTimeout(timeoutId);
    if (requestId === leadRequestId) {
      leadAbortController = null;
      isPredicting = false;
      updatePredictState();
    }
  }
}

citySelect.addEventListener("change", () => {
  markPlaceholder(citySelect);
  updatePredictState();
});

sourceSelect.addEventListener("change", () => {
  markPlaceholder(sourceSelect);
  updatePredictState();
});

leadForm.addEventListener("submit", predictLead);

markPlaceholder(citySelect);
markPlaceholder(sourceSelect);
updatePredictState();
