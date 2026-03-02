const store = {
  get(key, fallback = "") {
    const value = localStorage.getItem(key);
    return value === null ? fallback : value;
  },
  set(key, value) {
    localStorage.setItem(key, value);
  },
};

const state = {
  ast: null,
  graph: null,
  graphUrl: null,
  guidance: null,
  execution: null,
  chatLog: [],
};

let codeEditor = null;

function logTo(el, message) {
  const time = new Date().toLocaleTimeString();
  if (el) {
    el.textContent = `[${time}] ${message}\n` + el.textContent;
    return;
  }
  const statusEl = document.getElementById("statusOutput");
  if (statusEl) {
    statusEl.textContent = `[${time}] ${message}`;
  } else {
    console.log(message);
  }
}

function setOutput(el, payload) {
  if (!el) return;
  if (payload === null || payload === undefined) {
    el.textContent = "No data.";
    return;
  }
  if (typeof payload === "string") {
    el.textContent = payload;
    return;
  }
  el.textContent = JSON.stringify(payload, null, 2);
}

function getApiBase() {
  const field = document.getElementById("apiBase");
  return field ? field.value.trim() : store.get("codexa_api_base", "http://localhost:8000");
}

function getToken() {
  const field = document.getElementById("accessToken");
  return field ? field.value.trim() : store.get("codexa_token", "");
}

function setToken(value) {
  store.set("codexa_token", value);
  const field = document.getElementById("accessToken");
  if (field) field.value = value;
}

function persistSettings() {
  const base = getApiBase();
  const token = getToken();
  store.set("codexa_api_base", base);
  store.set("codexa_token", token);
}

function hydrateSettings() {
  const base = store.get("codexa_api_base", "http://localhost:8000");
  const token = store.get("codexa_token", "");
  const baseField = document.getElementById("apiBase");
  const tokenField = document.getElementById("accessToken");
  if (baseField) baseField.value = base;
  if (tokenField) tokenField.value = token;
}

function authHeaders() {
  const token = getToken();
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}

function getCodeInput() {
  const language = document.getElementById("language")?.value || store.get("codexa_language", "python");
  const codeField = document.getElementById("code");
  const code = codeEditor ? codeEditor.getValue() : codeField?.value.trim() || store.get("codexa_code", "");
  return { language, code };
}

function saveLocalState() {
  const input = getCodeInput();
  store.set("codexa_code", input.code);
  store.set("codexa_language", input.language);
  store.set("codexa_ast", JSON.stringify(state.ast || {}));
  store.set("codexa_graph", JSON.stringify(state.graph || {}));
  store.set("codexa_graph_url", state.graphUrl || "");
  store.set("codexa_chat_log", JSON.stringify(state.chatLog || []));
  store.set("codexa_guidance", state.guidance || "");
  store.set("codexa_execution", JSON.stringify(state.execution || {}));
}

function loadLocalState() {
  const codeField = document.getElementById("code");
  const languageField = document.getElementById("language");
  const storedCode = store.get("codexa_code", "");
  if (codeField) codeField.value = storedCode;
  if (languageField) languageField.value = store.get("codexa_language", "python");
  const ast = store.get("codexa_ast", "{}");
  const graph = store.get("codexa_graph", "{}");
  state.ast = JSON.parse(ast || "{}");
  state.graph = JSON.parse(graph || "{}");
  state.graphUrl = store.get("codexa_graph_url", "");
  state.chatLog = JSON.parse(store.get("codexa_chat_log", "[]"));
  state.guidance = store.get("codexa_guidance", "");
  state.execution = JSON.parse(store.get("codexa_execution", "{}"));
}

function initCodeMirror() {
  const codeField = document.getElementById("code");
  if (!codeField || !window.CodeMirror) return;
  codeEditor = CodeMirror.fromTextArea(codeField, {
    lineNumbers: true,
    mode: document.getElementById("language")?.value || "python",
    theme: "default",
    viewportMargin: Infinity,
  });
  codeEditor.on("change", () => {
    saveLocalState();
  });
  const languageField = document.getElementById("language");
  if (languageField) {
    languageField.addEventListener("change", () => {
      const mode = languageField.value === "javascript" ? "javascript" : "python";
      codeEditor.setOption("mode", mode);
      saveLocalState();
    });
  }
}

async function apiFetch(path, options = {}, auth = false) {
  const apiBase = getApiBase();
  const headers = options.headers || {};
  const authHeader = auth ? authHeaders() : {};
  const response = await fetch(`${apiBase}${path}`, {
    ...options,
    headers: { ...headers, ...authHeader },
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Request failed");
  return data;
}

function renderGraph(graph) {
  const container = document.getElementById("graphPreview");
  if (!container) return;
  container.innerHTML = "";
  if (!graph || !graph.nodes || !graph.edges) {
    container.textContent = "No graph yet.";
    return;
  }
  if (!window.d3) {
    container.textContent = "D3 not loaded.";
    return;
  }

  const width = container.clientWidth || 500;
  const height = 260;
  const svg = d3.select(container).append("svg").attr("width", width).attr("height", height);
  const g = svg.append("g");

  svg.call(
    d3.zoom().scaleExtent([0.6, 2.5]).on("zoom", (event) => {
      g.attr("transform", event.transform);
    })
  );

  const link = g
    .append("g")
    .attr("stroke", "rgba(255,255,255,0.2)")
    .selectAll("line")
    .data(graph.edges)
    .enter()
    .append("line")
    .attr("stroke-width", 1.5);

  const node = g
    .append("g")
    .selectAll("circle")
    .data(graph.nodes)
    .enter()
    .append("circle")
    .attr("r", 8)
    .attr("fill", "#ff6b35");

  const labels = g
    .append("g")
    .selectAll("text")
    .data(graph.nodes)
    .enter()
    .append("text")
    .attr("fill", "#f4f1ea")
    .attr("font-size", 10)
    .attr("dx", 10)
    .attr("dy", 4)
    .text((d) => d.label || d.type);

  const simulation = d3
    .forceSimulation(graph.nodes)
    .force("link", d3.forceLink(graph.edges).id((d) => d.id).distance(60))
    .force("charge", d3.forceManyBody().strength(-120))
    .force("center", d3.forceCenter(width / 2, height / 2));

  node.call(
    d3.drag()
      .on("start", (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on("drag", (event, d) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on("end", (event, d) => {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      })
  );

  simulation.on("tick", () => {
    link
      .attr("x1", (d) => d.source.x)
      .attr("y1", (d) => d.source.y)
      .attr("x2", (d) => d.target.x)
      .attr("y2", (d) => d.target.y);
    node.attr("cx", (d) => d.x).attr("cy", (d) => d.y);
    labels.attr("x", (d) => d.x).attr("y", (d) => d.y);
  });
}

async function handleAnalyze() {
  const { language, code } = getCodeInput();
  if (!code) throw new Error("Provide code to analyze.");
  const data = await apiFetch("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, language }),
  });
  state.ast = data.ast;
  saveLocalState();
  return data;
}

async function handleVisualize() {
  if (!state.ast) throw new Error("Run analyze first.");
  const sessionId = store.get("codexa_session_id", "");
  const payload = { ast: state.ast };
  if (sessionId) payload.session_id = Number(sessionId);
  const data = await apiFetch("/api/visualize", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }, true);
  state.graph = data.graph;
  state.graphUrl = data.s3_url;
  saveLocalState();
  return data;
}

async function handleGuidance() {
  const question = document.getElementById("question")?.value.trim() || "";
  const { code } = getCodeInput();
  if (!question) throw new Error("Provide a question.");
  if (!state.ast) throw new Error("Run analyze first.");
  const sessionId = store.get("codexa_session_id", "");
  const data = await apiFetch("/api/guidance", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_question: question,
      code_context: code,
      ast_context: state.ast,
      session_id: sessionId ? Number(sessionId) : null,
    }),
  }, true);
  state.guidance = data.response;
  state.chatLog.push({ question, response: data.response });
  if (data.session_id) {
    store.set("codexa_session_id", String(data.session_id));
  }
  saveLocalState();
  return data;
}

async function handleExecute() {
  const { language, code } = getCodeInput();
  if (!code) throw new Error("Provide code to execute.");
  const data = await apiFetch("/api/execute", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, language }),
  });
  state.execution = data;
  saveLocalState();
  return data;
}

async function handleSaveSession() {
  const title = `Lesson ${new Date().toLocaleString()}`;
  const { language, code } = getCodeInput();
  if (!state.graph) throw new Error("Generate a visualization first.");
  const data = await apiFetch("/api/session/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title,
      language,
      code,
      visualization: state.graph,
      chat_log: state.chatLog,
    }),
  }, true);
  store.set("codexa_session_id", String(data.session_id));
  return data;
}

async function handleLoadSession(sessionId) {
  if (!sessionId) throw new Error("Session ID missing.");
  const data = await apiFetch(`/api/session/${sessionId}`, {}, true);
  state.graph = data.visualization;
  state.chatLog = data.chat_log || [];
  state.guidance = state.chatLog.length ? state.chatLog[state.chatLog.length - 1].response : state.guidance;
  store.set("codexa_session_id", String(sessionId));
  if (data.code) {
    store.set("codexa_code", data.code);
    if (codeEditor) {
      codeEditor.setValue(data.code);
    } else {
      const codeField = document.getElementById("code");
      if (codeField) codeField.value = data.code;
    }
  }
  if (data.language) {
    store.set("codexa_language", data.language);
    const languageField = document.getElementById("language");
    if (languageField) languageField.value = data.language;
  }
  saveLocalState();
  return data;
}

async function loadSessionList() {
  const list = await apiFetch("/api/session", {}, true);
  return list.sessions || [];
}

function renderSessionList(list, container, outputEl) {
  if (!container) return;
  if (!list.length) {
    container.textContent = "No sessions yet.";
    return;
  }
  container.innerHTML = "";
  list.forEach((item) => {
    const row = document.createElement("div");
    row.style.display = "flex";
    row.style.justifyContent = "space-between";
    row.style.alignItems = "center";
    row.style.marginBottom = "0.6rem";
    const label = document.createElement("div");
    label.textContent = `${item.title} · ${new Date(item.created_at).toLocaleString()}`;
    const btn = document.createElement("button");
    btn.className = "button ghost";
    btn.textContent = "Load";
    btn.addEventListener("click", async () => {
      try {
        const data = await handleLoadSession(item.session_id);
        setOutput(outputEl, data);
        renderGraph(data.visualization || state.graph);
      } catch (error) {
        logTo(outputEl, `Load error: ${error.message}`);
      }
    });
    row.appendChild(label);
    row.appendChild(btn);
    container.appendChild(row);
  });
}

function initHome() {
  const grid = document.getElementById("featureGrid");
  if (!grid) return;
  const items = [
    { title: "Analyze", body: "Understand code structure with AST summaries.", bullets: ["Python", "JavaScript"] },
    { title: "Visualize", body: "See control flow and dependencies in a graph.", bullets: ["D3 graphs", "S3 storage"] },
    { title: "Guidance", body: "Get Socratic hints instead of direct answers.", bullets: ["TinyLlama", "Socratic"] },
    { title: "Execute", body: "Run code safely with timeouts.", bullets: ["5s limit", "Resource caps"] },
  ];
  items.forEach((item, index) => {
    const card = document.createElement("div");
    card.className = "card";
    card.style.animationDelay = `${index * 0.1}s`;
    card.innerHTML = `
      <h3>${item.title}</h3>
      <p>${item.body}</p>
      <ul>${item.bullets.map((b) => `<li>${b}</li>`).join("")}</ul>
    `;
    grid.appendChild(card);
  });
}

function initDashboard() {
  const grid = document.getElementById("dashboardModules");
  if (!grid) return;
  const items = [
    { title: "1. Analyze", body: "Start by reading the AST summary.", bullets: ["/api/analyze"] },
    { title: "2. Visualize", body: "See the graph and note dependencies.", bullets: ["/api/visualize"] },
    { title: "3. Guidance", body: "Ask Codexa to guide your reasoning.", bullets: ["/api/guidance"] },
    { title: "4. Execute", body: "Test hypotheses with safe execution.", bullets: ["/api/execute"] },
    { title: "5. Save", body: "Store your session for review.", bullets: ["/api/session/save"] },
  ];
  items.forEach((item, index) => {
    const card = document.createElement("div");
    card.className = "card";
    card.style.animationDelay = `${index * 0.1}s`;
    card.innerHTML = `
      <h3>${item.title}</h3>
      <p>${item.body}</p>
      <ul>${item.bullets.map((b) => `<li>${b}</li>`).join("")}</ul>
    `;
    grid.appendChild(card);
  });
}

function initArchitecture() {
  const grid = document.getElementById("architectureGrid");
  if (!grid) return;
  const items = [
    { title: "FastAPI Monolith", body: "Single API surface for all routes.", bullets: ["/api/*"] },
    { title: "Lambda Parser", body: "Tree-sitter AST extraction.", bullets: ["Python", "JS"] },
    { title: "Socratic LLM", body: "TinyLlama on CPU.", bullets: ["GGUF", "Socratic"] },
    { title: "RDS + S3", body: "Persist sessions and graphs.", bullets: ["Postgres", "S3 JSON"] },
  ];
  items.forEach((item, index) => {
    const card = document.createElement("div");
    card.className = "card";
    card.style.animationDelay = `${index * 0.1}s`;
    card.innerHTML = `
      <h3>${item.title}</h3>
      <p>${item.body}</p>
      <ul>${item.bullets.map((b) => `<li>${b}</li>`).join("")}</ul>
    `;
    grid.appendChild(card);
  });
}

function initAuth() {
  const registerBtn = document.getElementById("registerBtn");
  const loginBtn = document.getElementById("loginBtn");
  const output = document.getElementById("authOutput");
  const meBtn = document.getElementById("meBtn");
  const clearBtn = document.getElementById("clearTokenBtn");

  if (registerBtn) {
    registerBtn.addEventListener("click", async () => {
      try {
        const email = document.getElementById("registerEmail").value.trim();
        const password = document.getElementById("registerPassword").value;
        const data = await apiFetch("/api/auth/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        });
        setOutput(output, data.message || "Registered");
      } catch (error) {
        setOutput(output, `Register error: ${error.message}`);
      }
    });
  }

  if (loginBtn) {
    loginBtn.addEventListener("click", async () => {
      try {
        const email = document.getElementById("loginEmail").value.trim();
        const password = document.getElementById("loginPassword").value;
        const data = await apiFetch("/api/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        });
        setToken(data.access_token);
        persistSettings();
        setOutput(output, "Login successful.");
      } catch (error) {
        setOutput(output, `Login error: ${error.message}`);
      }
    });
  }

  if (meBtn) {
    meBtn.addEventListener("click", async () => {
      try {
        const data = await apiFetch("/api/auth/me", {}, true);
        setOutput(output, data);
      } catch (error) {
        setOutput(output, `Auth error: ${error.message}`);
      }
    });
  }

  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      setToken("");
      persistSettings();
      setOutput(output, "Token cleared.");
    });
  }
}

function initPageActions() {
  const logEl = document.getElementById("log");
  const astOutput = document.getElementById("astOutput");
  const graphOutput = document.getElementById("graphOutput");
  const graphMeta = document.getElementById("graphMeta");
  const guidanceOutput = document.getElementById("guidanceOutput");
  const guidanceLog = document.getElementById("guidanceLog");
  const executionOutput = document.getElementById("executionOutput");
  const sessionOutput = document.getElementById("sessionOutput");
  const sessionListEl = document.getElementById("sessionList");

  const analyzeBtn = document.getElementById("analyzeBtn");
  const visualizeBtn = document.getElementById("visualizeBtn");
  const analyzeVisualizeBtn = document.getElementById("analyzeVisualizeBtn");
  const guidanceBtn = document.getElementById("guidanceBtn");
  const fullPipelineBtn = document.getElementById("fullPipelineBtn");
  const executeBtn = document.getElementById("executeBtn");
  const saveSessionBtn = document.getElementById("saveSessionBtn");
  const loadSessionBtn = document.getElementById("loadSessionBtn");
  const lessonSteps = document.getElementById("lessonSteps");
  const lessonStatus = document.getElementById("lessonStatus");
  const lessonAst = document.getElementById("lessonAst");
  const lessonGraph = document.getElementById("lessonGraph");
  const lessonGuidance = document.getElementById("lessonGuidance");
  const lessonNext = document.getElementById("lessonNextBtn");
  const lessonPrev = document.getElementById("lessonPrevBtn");
  const lessonAction = document.getElementById("lessonActionBtn");
  const lessonReset = document.getElementById("lessonResetBtn");

  if (analyzeBtn) {
    analyzeBtn.addEventListener("click", async () => {
      try {
        const data = await handleAnalyze();
        setOutput(astOutput, data.ast);
        logTo(logEl, "AST generated.");
      } catch (error) {
        logTo(logEl, `Analyze error: ${error.message}`);
      }
    });
  }

  if (visualizeBtn) {
    visualizeBtn.addEventListener("click", async () => {
      try {
        const data = await handleVisualize();
        setOutput(graphOutput, data.graph);
        setOutput(graphMeta, { s3_url: data.s3_url });
        renderGraph(data.graph);
        logTo(logEl, "Graph generated.");
      } catch (error) {
        logTo(logEl, `Visualize error: ${error.message}`);
      }
    });
  }

  if (analyzeVisualizeBtn) {
    analyzeVisualizeBtn.addEventListener("click", async () => {
      try {
        await handleAnalyze();
        const data = await handleVisualize();
        setOutput(graphOutput, data.graph);
        setOutput(graphMeta, { s3_url: data.s3_url });
        renderGraph(data.graph);
        logTo(logEl, "Analyze + Visualize complete.");
      } catch (error) {
        logTo(logEl, `Pipeline error: ${error.message}`);
      }
    });
  }

  if (guidanceBtn) {
    guidanceBtn.addEventListener("click", async () => {
      try {
        const data = await handleGuidance();
        setOutput(guidanceOutput, data.response);
        setOutput(guidanceLog, state.chatLog);
        logTo(logEl, "Guidance generated.");
      } catch (error) {
        logTo(logEl, `Guidance error: ${error.message}`);
      }
    });
  }

  if (fullPipelineBtn) {
    fullPipelineBtn.addEventListener("click", async () => {
      try {
        await handleAnalyze();
        await handleVisualize();
        const data = await handleGuidance();
        setOutput(guidanceOutput, data.response);
        setOutput(guidanceLog, state.chatLog);
        logTo(logEl, "Full pipeline complete.");
      } catch (error) {
        logTo(logEl, `Pipeline error: ${error.message}`);
      }
    });
  }

  if (executeBtn) {
    executeBtn.addEventListener("click", async () => {
      try {
        const data = await handleExecute();
        setOutput(executionOutput, data);
        logTo(logEl, "Execution complete.");
      } catch (error) {
        logTo(logEl, `Execute error: ${error.message}`);
      }
    });
  }

  if (saveSessionBtn) {
    saveSessionBtn.addEventListener("click", async () => {
      try {
        const data = await handleSaveSession();
        setOutput(sessionOutput, data);
        store.set("codexa_session_id", String(data.session_id));
        if (sessionListEl) {
          const list = await loadSessionList();
          renderSessionList(list, sessionListEl, sessionOutput);
        }
        logTo(logEl, `Session saved: ${data.session_id}`);
      } catch (error) {
        logTo(logEl, `Save error: ${error.message}`);
      }
    });
  }

  if (loadSessionBtn) {
    loadSessionBtn.addEventListener("click", async () => {
      try {
        const list = await loadSessionList();
        renderSessionList(list, sessionListEl, sessionOutput);
        logTo(logEl, "Session list refreshed.");
      } catch (error) {
        logTo(logEl, `Load error: ${error.message}`);
      }
    });
  }

  const lessonFlow = [
    { title: "Paste code", action: null, check: () => getCodeInput().code.length > 0 },
    { title: "Analyze the code", action: handleAnalyze, check: () => !!state.ast },
    { title: "Visualize the graph", action: handleVisualize, check: () => !!state.graph },
    { title: "Ask a Socratic question", action: handleGuidance, check: () => !!state.guidance },
    { title: "Execute and observe", action: handleExecute, check: () => !!state.execution },
    { title: "Save the session", action: handleSaveSession, check: () => true },
  ];
  let lessonIndex = Number(store.get("codexa_lesson_step", "0"));

  function renderLesson() {
    if (!lessonSteps) return;
    const list = lessonFlow
      .map((step, index) => {
        const active = index === lessonIndex ? " (current)" : "";
        const done = step.check() ? " ✓" : "";
        return `${index + 1}. ${step.title}${done}${active}`;
      })
      .join("\n");
    lessonSteps.textContent = list;
    setOutput(lessonAst, state.ast);
    setOutput(lessonGraph, state.graph);
    setOutput(lessonGuidance, state.guidance);
    renderGraph(state.graph);
  }

  if (lessonNext) {
    lessonNext.addEventListener("click", () => {
      lessonIndex = Math.min(lessonFlow.length - 1, lessonIndex + 1);
      store.set("codexa_lesson_step", String(lessonIndex));
      renderLesson();
    });
  }

  if (lessonPrev) {
    lessonPrev.addEventListener("click", () => {
      lessonIndex = Math.max(0, lessonIndex - 1);
      store.set("codexa_lesson_step", String(lessonIndex));
      renderLesson();
    });
  }

  if (lessonReset) {
    lessonReset.addEventListener("click", () => {
      lessonIndex = 0;
      store.set("codexa_lesson_step", "0");
      renderLesson();
      logTo(lessonStatus, "Lesson reset.");
    });
  }

  if (lessonAction) {
    lessonAction.addEventListener("click", async () => {
      const step = lessonFlow[lessonIndex];
      if (!step.action) {
        logTo(lessonStatus, "Add code to continue.");
        return;
      }
      try {
        await step.action();
        saveLocalState();
        renderLesson();
        logTo(lessonStatus, `Step complete: ${step.title}`);
      } catch (error) {
        logTo(lessonStatus, `Lesson error: ${error.message}`);
      }
    });
  }

  renderLesson();
}

function init() {
  if (!store.get("codexa_api_base")) {
    store.set("codexa_api_base", "http://localhost:8000");
  }
  hydrateSettings();
  loadLocalState();
  const codeField = document.getElementById("code");
  if (codeField && !codeField.value.trim()) {
    codeField.value = "def summarize(items):\n    total = 0\n    for item in items:\n        if item > 0:\n            total += item\n    return total\n";
    saveLocalState();
  }
  initHome();
  initDashboard();
  initArchitecture();
  initAuth();
  initPageActions();
  initCodeMirror();
  const baseField = document.getElementById("apiBase");
  const tokenField = document.getElementById("accessToken");
  if (baseField) baseField.addEventListener("change", persistSettings);
  if (tokenField) tokenField.addEventListener("change", persistSettings);

  const astOutput = document.getElementById("astOutput");
  const graphOutput = document.getElementById("graphOutput");
  const graphMeta = document.getElementById("graphMeta");
  const guidanceOutput = document.getElementById("guidanceOutput");
  const guidanceLog = document.getElementById("guidanceLog");
  const executionOutput = document.getElementById("executionOutput");
  const sessionOutput = document.getElementById("sessionOutput");

  if (astOutput && state.ast) setOutput(astOutput, state.ast);
  if (graphOutput && state.graph) setOutput(graphOutput, state.graph);
  if (graphMeta && state.graphUrl) setOutput(graphMeta, { s3_url: state.graphUrl });
  if (guidanceOutput && state.guidance) setOutput(guidanceOutput, state.guidance);
  if (guidanceLog && state.chatLog.length) setOutput(guidanceLog, state.chatLog);
  if (executionOutput && state.execution) setOutput(executionOutput, state.execution);
  if (sessionOutput && state.graphUrl) setOutput(sessionOutput, { graph_url: state.graphUrl });
  renderGraph(state.graph);

  const sessionListEl = document.getElementById("sessionList");
  if (sessionListEl) {
    loadSessionList()
      .then((list) => renderSessionList(list, sessionListEl, document.getElementById("sessionOutput")))
      .catch(() => {
        sessionListEl.textContent = "Sign in to view sessions.";
      });
  }
}

init();
