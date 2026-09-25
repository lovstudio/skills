"use strict";

const FILE_PREVIEW = window.location.protocol === "file:";

const PHASES = [
  ["feature-contract", "Feature contract"],
  ["core-sdk", "Core SDK"],
  ["distribution-surfaces", "Distribution"],
  ["profile-experience", "Profile experience"],
  ["operations", "Operations"],
  ["dashboard", "Dashboard"],
];

const TAB_TITLES = {
  overview: "Feature overview",
  contract: "Contract & schema",
  run: "Run surface",
  compare: "Compare results",
  evidence: "Evidence review",
};

const state = {
  data: null,
  activeTab: "overview",
  surface: "sdk",
  vector: null,
  preset: null,
  overrides: {},
  compareRuns: [],
  running: false,
};

const byId = (id) => document.getElementById(id);

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function pretty(value) {
  return JSON.stringify(value ?? {}, null, 2);
}

function statusClass(status) {
  const allowed = new Set(["planned", "implemented", "verified", "released", "not-applicable"]);
  const normalized = String(status || "planned").replaceAll("_", "-");
  return `status-${allowed.has(normalized) ? normalized : "planned"}`;
}

function badge(status) {
  const safe = escapeHtml(status || "planned");
  return `<span class="status-badge ${statusClass(status)}">${safe}</span>`;
}

function artifactLabel(record) {
  return record?.artifact ? escapeHtml(record.artifact) : "No artifact yet";
}

function initials(value) {
  return String(value || "AF")
    .split(/[\s-]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || `Request failed: ${response.status}`);
  return payload;
}

async function loadWorkspace({ announce = false } = {}) {
  try {
    const data = FILE_PREVIEW
      ? JSON.parse(JSON.stringify(window.ATOM_WORKBENCH_DEMO))
      : await api("/api/workspace");
    if (!data) throw new Error("直接预览数据未加载");
    state.data = data;
    const vectors = data.acceptance?.vectors || [];
    const presets = data.presets?.presets || [];
    const surfaces = data.manifest?.surfaces || {};
    if (!state.vector && vectors.length) state.vector = vectors[0].id;
    if (!state.preset) state.preset = data.presets?.active || presets[0]?.id || null;
    if (!surfaces[state.surface]) state.surface = Object.keys(surfaces)[0] || "sdk";
    hydrateShell();
    renderAll();
    byId("loading").hidden = true;
    byId("app").hidden = false;
    if (announce) toast("工作区已刷新");
  } catch (error) {
    byId("loading").innerHTML = `<p><strong>无法连接 Atom 工作区</strong><br>${escapeHtml(error.message)}</p>`;
  }
}

function hydrateShell() {
  const { workspace, manifest } = state.data;
  const feature = manifest.feature || {};
  byId("workspace-name").textContent = workspace.name;
  byId("workspace-monogram").textContent = initials(feature.title || workspace.name);
  byId("workspace-state").textContent = FILE_PREVIEW
    ? "File preview · demo data"
    : workspace.run_enabled
      ? "Execution enabled"
      : "Read-only workspace";
  byId("connection-label").textContent = FILE_PREVIEW ? "File preview" : "Local bridge";
  byId("crumb-workspace").textContent = workspace.name;
  byId("feature-title").textContent = feature.title || feature.id || "Atom feature";
  byId("feature-status").textContent = feature.status || "planned";
  byId("feature-status").className = `status-badge ${statusClass(feature.status)}`;
  byId("stage-title").textContent = TAB_TITLES[state.activeTab];
  renderPhases();
  renderSurfaceSwitcher();
  renderProfileInspector();
  renderAgentBrief();
  byId("run-primary").disabled = state.running;
}

function renderPhases() {
  const { manifest } = state.data;
  const surfaces = Object.values(manifest.surfaces || {});
  const operations = Object.values(manifest.operations || {});
  const surfaceState = deriveStatus(surfaces);
  const operationState = deriveStatus(operations);
  const phases = {
    "feature-contract": manifest.contracts?.feature ? "implemented" : "planned",
    "core-sdk": manifest.surfaces?.sdk?.status || "planned",
    "distribution-surfaces": surfaceState,
    "profile-experience": state.data.presets?.presets?.length ? "implemented" : "planned",
    operations: operationState,
    dashboard: manifest.dashboard?.status || "implemented",
  };
  byId("phase-list").innerHTML = PHASES.map(([id, label], index) => `
    <div class="phase-item ${id === "dashboard" ? "is-current" : ""}">
      <span class="phase-index">${String(index + 1).padStart(2, "0")}</span>
      <span class="phase-name">${escapeHtml(label)}</span>
      <span class="phase-state ${escapeHtml(phases[id])}" title="${escapeHtml(phases[id])}"></span>
    </div>
  `).join("");
}

function deriveStatus(records) {
  const statuses = records.map((item) => item?.status).filter((item) => item && item !== "not-applicable");
  if (!statuses.length) return "not-applicable";
  if (statuses.includes("planned")) return "planned";
  if (statuses.includes("implemented")) return "implemented";
  if (statuses.every((status) => status === "released")) return "released";
  return "verified";
}

function renderSurfaceSwitcher() {
  const surfaces = state.data.manifest?.surfaces || {};
  byId("surface-switcher").innerHTML = Object.entries(surfaces).map(([name, record]) => `
    <button
      class="surface-button ${name === state.surface ? "is-active" : ""}"
      type="button"
      data-surface="${escapeHtml(name)}"
      aria-pressed="${name === state.surface}"
      ${record.status === "not-applicable" ? "disabled" : ""}
      title="${escapeHtml(`${name}: ${record.status}`)}"
    >${escapeHtml(name)}</button>
  `).join("");
  document.querySelectorAll("[data-surface]").forEach((button) => {
    button.addEventListener("click", () => {
      state.surface = button.dataset.surface;
      hydrateShell();
      renderStage();
    });
  });
}

function renderProfileInspector() {
  const presets = state.data.presets?.presets || [];
  const select = byId("profile-select");
  select.innerHTML = [
    `<option value="">No preset</option>`,
    ...presets.map((preset) => `<option value="${escapeHtml(preset.id)}">${escapeHtml(preset.name)}</option>`),
  ].join("");
  select.value = state.preset || "";
  const preset = presets.find((item) => item.id === state.preset);
  const values = preset?.values || {};
  const entries = Object.entries(values);
  byId("profile-values").innerHTML = entries.length
    ? entries.map(([key, value]) => `
      <div class="profile-value">
        <span>${escapeHtml(key)}</span>
        <small>${escapeHtml(typeof value === "string" ? value : JSON.stringify(value))}</small>
      </div>
    `).join("")
    : `<div class="empty-state"><strong>无 Profile 覆盖</strong>本次运行只使用向量输入与显式参数。</div>`;
  byId("preset-source").textContent = preset ? "profile" : "fallback";
}

function renderAgentBrief() {
  const feature = state.data.manifest?.feature || {};
  const surface = state.data.manifest?.surfaces?.[state.surface] || {};
  const vector = findVector();
  const preset = findPreset();
  const brief = [
    `Feature: ${feature.title || feature.id}`,
    `Outcome: ${feature.summary || "Use the canonical atom contract."}`,
    `Surface: ${state.surface} (${surface.status || "planned"})`,
    `Test vector: ${vector?.name || vector?.id || "not selected"}`,
    `Profile preset: ${preset?.name || "none"}`,
    `Mode: ${FILE_PREVIEW ? "read-only file preview" : "local bridge"}`,
    "",
    "Work from .atom-feature/manifest.json and the shared SDK.",
    "Do not duplicate business rules in this adapter.",
    "Run the selected vector, read back side effects, and attach real evidence before changing status.",
  ].join("\n");
  byId("agent-brief").value = brief;
}

function renderAll() {
  renderTabs();
  renderStage();
}

function renderTabs() {
  document.querySelectorAll("[data-tab]").forEach((button) => {
    const active = button.dataset.tab === state.activeTab;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-selected", String(active));
  });
  byId("stage-title").textContent = TAB_TITLES[state.activeTab];
}

function renderStage() {
  const renderers = {
    overview: renderOverview,
    contract: renderContract,
    run: renderRun,
    compare: renderCompare,
    evidence: renderEvidence,
  };
  byId("stage-content").innerHTML = renderers[state.activeTab]();
  bindStageEvents();
}

function renderOverview() {
  const { manifest, acceptance } = state.data;
  const surfaces = Object.entries(manifest.surfaces || {});
  const operations = Object.entries(manifest.operations || {});
  const verified = surfaces.filter(([, value]) => ["verified", "released"].includes(value.status)).length;
  const evidenceCount = surfaces.reduce((sum, [, value]) => sum + (value.verification?.length || 0), 0);
  return `
    <div class="summary-grid">
      ${summaryCard("Surfaces", `${verified}/${surfaces.length}`, "已通过真实运行验证")}
      ${summaryCard("Test vectors", acceptance?.vectors?.length || 0, "共享输入与预期业务结果")}
      ${summaryCard("Evidence", evidenceCount, "制品、测试与渠道回读")}
    </div>
    <section class="section-block">
      <div class="section-row">
        <h2 class="section-title">One core, many surfaces</h2>
        <span class="section-note">当前 Profile：${escapeHtml(findPreset()?.name || "No preset")}</span>
      </div>
      <div class="surface-grid">
        ${surfaces.map(([name, record]) => surfaceCard(name, record)).join("")}
      </div>
    </section>
    <section class="section-block">
      <div class="section-row">
        <h2 class="section-title">Operations readiness</h2>
        <span class="section-note">不适用也是显式决定</span>
      </div>
      <div class="operation-grid">
        ${operations.map(([name, record]) => operationCard(name, record)).join("")}
      </div>
    </section>
    <section class="section-block panel">
      <div class="section-row">
        <div>
          <p class="eyebrow">Workspace why</p>
          <h2 class="section-title">${escapeHtml(manifest.feature?.title || "Atom feature")}</h2>
        </div>
        ${badge(manifest.feature?.status)}
      </div>
      <p>${escapeHtml(manifest.feature?.summary || "用同一业务核心服务程序、用户和 Agent，并让每个状态可回读。")}</p>
    </section>
  `;
}

function summaryCard(label, value, note) {
  return `<article class="summary-card"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong><p>${escapeHtml(note)}</p></article>`;
}

function surfaceCard(name, record) {
  return `
    <article class="surface-card ${name === state.surface ? "is-selected" : ""}">
      <div class="surface-card-head"><h3>${escapeHtml(name.toUpperCase())}</h3>${badge(record.status)}</div>
      <span class="artifact">${artifactLabel(record)}</span>
      <p>${record.command ? "Command contract ready" : "No executable command declared"}</p>
    </article>
  `;
}

function operationCard(name, record) {
  return `
    <article class="operation-card">
      <div class="operation-card-head"><h3>${escapeHtml(name)}</h3>${badge(record.status)}</div>
      <p>${escapeHtml(record.reason || record.artifact || "Awaiting applicability decision")}</p>
    </article>
  `;
}

function renderContract() {
  const contract = state.data.contract || {};
  const profileSchema = state.data.profiles_schema || {};
  const properties = contract.properties || {};
  return `
    <dl class="contract-grid">
      <div class="contract-row"><dt>schema</dt><dd>${escapeHtml(contract.$schema || "Not declared")}</dd></div>
      <div class="contract-row"><dt>contract id</dt><dd>${escapeHtml(contract.$id || "Not declared")}</dd></div>
      <div class="contract-row"><dt>required</dt><dd>${escapeHtml((contract.required || []).join(", ") || "None")}</dd></div>
      <div class="contract-row"><dt>input fields</dt><dd>${escapeHtml(Object.keys(properties.input?.properties || {}).join(", ") || "Open object")}</dd></div>
      <div class="contract-row"><dt>profile fields</dt><dd>${escapeHtml(Object.keys(profileSchema.properties?.values?.properties || {}).join(", ") || "Open object")}</dd></div>
    </dl>
    <section class="section-block panel">
      <div class="section-row"><h2 class="section-title">Canonical contract</h2><span class="section-note">read-only</span></div>
      <pre class="code-block">${escapeHtml(pretty(contract))}</pre>
    </section>
  `;
}

function renderRun() {
  const vectors = state.data.acceptance?.vectors || [];
  const presets = state.data.presets?.presets || [];
  const surface = state.data.manifest?.surfaces?.[state.surface] || {};
  return `
    <div class="run-layout">
      <section class="panel">
        <div class="run-form">
          <label>
            <span class="field-label">Surface</span>
            <select id="run-surface" class="select-control">
              ${Object.entries(state.data.manifest?.surfaces || {}).map(([name, record]) => `<option value="${escapeHtml(name)}" ${name === state.surface ? "selected" : ""} ${record.status === "not-applicable" ? "disabled" : ""}>${escapeHtml(name)} · ${escapeHtml(record.status)}</option>`).join("")}
            </select>
          </label>
          <label>
            <span class="field-label">Acceptance vector</span>
            <select id="run-vector" class="select-control">
              ${vectors.map((vector) => `<option value="${escapeHtml(vector.id)}" ${vector.id === state.vector ? "selected" : ""}>${escapeHtml(vector.name || vector.id)}</option>`).join("")}
            </select>
          </label>
          <label class="field-full">
            <span class="field-label">Profile preset</span>
            <select id="run-preset" class="select-control">
              <option value="">No preset</option>
              ${presets.map((preset) => `<option value="${escapeHtml(preset.id)}" ${preset.id === state.preset ? "selected" : ""}>${escapeHtml(preset.name)}</option>`).join("")}
            </select>
          </label>
          <label class="field-full">
            <span class="field-label">Explicit overrides · JSON</span>
            <textarea id="run-overrides" class="json-editor" spellcheck="false">${escapeHtml(pretty(state.overrides))}</textarea>
          </label>
        </div>
        <div class="run-toolbar">
          <span class="permission-note">${FILE_PREVIEW ? "当前是 file:// 只读 Demo；启动本地 bridge 后才能执行" : state.data.workspace.run_enabled ? "仅执行 manifest 声明的 command array" : "当前为只读模式；启动时加入 --allow-run 才能执行"}</span>
          <button id="execute-run" class="button button-primary" type="button" ${state.running ? "disabled" : ""}>${FILE_PREVIEW ? "查看启动方式" : state.running ? "运行中" : "运行当前向量"}</button>
        </div>
      </section>
      <aside class="panel">
        <p class="eyebrow">Resolved context</p>
        <h3>${escapeHtml(state.surface.toUpperCase())}</h3>
        <p>Artifact</p>
        <span class="artifact">${artifactLabel(surface)}</span>
        <p>Command</p>
        <pre class="code-block">${escapeHtml(surface.command ? surface.command.join(" ") : "No command declared")}</pre>
      </aside>
    </div>
  `;
}

function renderCompare() {
  if (!state.compareRuns.length) {
    return `<div class="empty-state"><strong>还没有可对比的结果</strong>用同一测试向量分别运行两个 surface，结果会保留在这里。</div>`;
  }
  return `
    <div class="compare-grid">
      ${state.compareRuns.slice(-2).map((run) => `
        <article class="compare-card">
          <div class="section-row"><h3>${escapeHtml(run.surface.toUpperCase())}</h3>${badge(run.exit_code === 0 ? "verified" : "implemented")}</div>
          <p>${escapeHtml(`${run.duration_ms} ms · ${run.vector || "ad hoc"}`)}</p>
          <pre class="code-block">${escapeHtml(run.stdout || run.stderr || "No output")}</pre>
        </article>
      `).join("")}
    </div>
    <section class="section-block panel">
      <div class="section-row"><h2 class="section-title">Normalization review</h2><span class="section-note">transport wrappers ignored</span></div>
      <p>${escapeHtml(compareVerdict())}</p>
    </section>
  `;
}

function compareVerdict() {
  const runs = state.compareRuns.slice(-2);
  if (runs.length < 2) return "再运行一个 surface 才能形成对比。";
  const left = normalizeOutput(runs[0].stdout);
  const right = normalizeOutput(runs[1].stdout);
  return JSON.stringify(left) === JSON.stringify(right)
    ? "两个 surface 的规范化业务结果一致。副作用仍需按 contract 单独回读。"
    : "规范化业务结果不同。请检查 adapter 是否复制了默认值、校验或状态迁移。";
}

function normalizeOutput(value) {
  try {
    const parsed = JSON.parse(value || "{}");
    delete parsed.request_id;
    delete parsed.timestamp;
    return parsed;
  } catch {
    return String(value || "").trim();
  }
}

function renderEvidence() {
  const manifest = state.data.manifest || {};
  const records = [
    ...Object.entries(manifest.surfaces || {}).map(([name, record]) => ["surface", name, record]),
    ...Object.entries(manifest.operations || {}).map(([name, record]) => ["operation", name, record]),
    ["dashboard", "dashboard", manifest.dashboard || {}],
  ];
  return `
    <section class="panel">
      <div class="section-row"><h2 class="section-title">Acceptance evidence</h2><span class="section-note">build ≠ verified ≠ released</span></div>
      <div class="evidence-list">
        ${records.map(([group, name, record]) => `
          <div class="evidence-row">
            <div><strong>${escapeHtml(`${group} / ${name}`)}</strong><small>${artifactLabel(record)}</small></div>
            <div>${badge(record.status)}</div>
          </div>
        `).join("")}
      </div>
    </section>
    <section class="section-block panel">
      <div class="section-row"><h2 class="section-title">Recent runs</h2><span class="section-note">${escapeHtml(state.data.status?.runs?.length || 0)} recorded</span></div>
      <div class="evidence-list">
        ${(state.data.status?.runs || []).slice(0, 8).map((run) => `
          <div class="evidence-row">
            <div><strong>${escapeHtml(`${run.surface} · ${run.vector || "ad hoc"}`)}</strong><small>${escapeHtml(run.created_at)}</small></div>
            <div>${badge(run.exit_code === 0 ? "verified" : "implemented")}</div>
          </div>
        `).join("") || `<div class="empty-state"><strong>暂无运行记录</strong>执行结果会写入本地 .atom-feature/status.json。</div>`}
      </div>
    </section>
  `;
}

function bindStageEvents() {
  byId("run-surface")?.addEventListener("change", (event) => {
    state.surface = event.target.value;
    hydrateShell();
    renderStage();
  });
  byId("run-vector")?.addEventListener("change", (event) => {
    state.vector = event.target.value;
    renderAgentBrief();
  });
  byId("run-preset")?.addEventListener("change", (event) => {
    state.preset = event.target.value || null;
    hydrateShell();
    renderStage();
  });
  byId("execute-run")?.addEventListener("click", executeRun);
}

function findVector() {
  return (state.data.acceptance?.vectors || []).find((item) => item.id === state.vector);
}

function findPreset() {
  return (state.data.presets?.presets || []).find((item) => item.id === state.preset);
}

async function executeRun() {
  if (state.running) return;
  const overridesNode = byId("run-overrides");
  if (overridesNode) {
    try {
      state.overrides = JSON.parse(overridesNode.value || "{}");
    } catch {
      toast("显式参数不是有效 JSON");
      overridesNode.focus();
      return;
    }
  }
  if (FILE_PREVIEW) {
    const command = "python3 scripts/atom_feature.py dashboard --root PROJECT --allow-run";
    setConsole(`当前是 file:// 只读 Demo，不能执行 surface。\n\n请在 Skill 根目录运行：\n${command}`, "error");
    byId("console-meta").textContent = "File preview · read-only";
    toast("启动本地 bridge 后才能执行");
    return;
  }
  state.running = true;
  hydrateShell();
  if (state.activeTab === "run") renderStage();
  setConsole(`$ run ${state.surface} --vector ${state.vector || "ad-hoc"}\n`, "command");
  try {
    const run = await api("/api/run", {
      method: "POST",
      body: JSON.stringify({
        surface: state.surface,
        vector: state.vector,
        preset: state.preset,
        overrides: state.overrides,
      }),
    });
    state.compareRuns.push(run);
    setConsole(`${run.stdout || ""}${run.stderr ? `\n${run.stderr}` : ""}\nexit ${run.exit_code} · ${run.duration_ms} ms`, run.exit_code === 0 ? "success" : "error");
    byId("console-meta").textContent = `${run.surface} · ${run.duration_ms} ms`;
    toast(run.exit_code === 0 ? "运行完成，结果已记录" : "运行失败，已保留诊断输出");
    await loadWorkspace();
  } catch (error) {
    setConsole(error.message, "error");
    toast(error.message);
  } finally {
    state.running = false;
    hydrateShell();
    if (state.activeTab === "run") renderStage();
  }
}

function setConsole(message, kind = "muted") {
  const output = byId("console-output");
  const className = {
    muted: "console-muted",
    command: "console-command",
    success: "console-success",
    error: "console-error",
  }[kind];
  const line = document.createElement("span");
  line.className = className;
  line.textContent = message;
  output.replaceChildren(line);
}

function toast(message) {
  const node = document.createElement("div");
  node.className = "toast";
  node.textContent = message;
  byId("toast-region").appendChild(node);
  window.setTimeout(() => node.remove(), 2800);
}

function bindGlobalEvents() {
  document.querySelectorAll("[data-tab]").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeTab = button.dataset.tab;
      renderAll();
      byId("stage-content").focus();
    });
  });
  byId("refresh-button").addEventListener("click", () => loadWorkspace({ announce: true }));
  byId("run-primary").addEventListener("click", () => {
    state.activeTab = "run";
    renderAll();
    executeRun();
  });
  byId("profile-select").addEventListener("change", (event) => {
    state.preset = event.target.value || null;
    hydrateShell();
    renderStage();
  });
  byId("copy-brief").addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(byId("agent-brief").value);
      toast("Agent brief 已复制");
    } catch {
      byId("agent-brief").select();
      toast("已选中 brief，请手动复制");
    }
  });
  byId("clear-console").addEventListener("click", () => {
    setConsole("控制台已清空。", "muted");
    byId("console-meta").textContent = "等待运行";
  });
  document.addEventListener("keydown", (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
      event.preventDefault();
      state.activeTab = "run";
      renderAll();
      executeRun();
    }
    if ((event.metaKey || event.ctrlKey) && /^[1-5]$/.test(event.key)) {
      event.preventDefault();
      state.activeTab = ["overview", "contract", "run", "compare", "evidence"][Number(event.key) - 1];
      renderAll();
    }
  });
}

bindGlobalEvents();
loadWorkspace();
