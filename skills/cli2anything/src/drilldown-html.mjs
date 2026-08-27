export function createDrilldownHtml({ manifest, openapi, apiGraph, extensionDir }) {
  const listLogsExample = openapi.paths["/api/api_key/activity"].post.requestBody.content["application/json"].example;
  const endpointOperationSpecs = createEndpointOperationSpecs(openapi);
  const extensionHelp = `Load or reload ${extensionDir} in chrome://extensions, then open ${manifest.target}.`;
  const graphTitle = apiGraph.scope === "all" ? "Endpoint Map" : "Dependency Graph";
  const graphSubtitle = apiGraph.scope === "all" ? "API inventory" : "API dependency map";
  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>${escapeHtml(manifest.target)} ${escapeHtml(manifest.filterKeyword)} Drilldown</title>
    <style>
      :root {
        color-scheme: light;
        --bg: #f7f8fa;
        --panel: #ffffff;
        --line: #d8dde5;
        --line-strong: #aeb8c7;
        --text: #1d2430;
        --muted: #627084;
        --accent: #1f7a5b;
        --accent-soft: #e5f5ef;
        --warn: #8a5a00;
        --warn-soft: #fff4d6;
        --danger: #a12a2a;
        --danger-soft: #fde8e8;
        --code: #101828;
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        min-height: 100vh;
        background: var(--bg);
        color: var(--text);
        font: 13px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      }
      button, input, select { font: inherit; }
      button {
        border: 1px solid var(--line-strong);
        background: #fff;
        color: var(--text);
        border-radius: 6px;
        padding: 7px 10px;
        cursor: pointer;
      }
      button:hover { border-color: #7f8da3; }
      button.primary {
        border-color: #17684c;
        background: var(--accent);
        color: #fff;
      }
      button:disabled {
        opacity: 0.55;
        cursor: not-allowed;
      }
      input, select {
        width: 100%;
        border: 1px solid var(--line);
        border-radius: 6px;
        padding: 7px 8px;
        background: #fff;
        color: var(--text);
      }
      a { color: #155fca; text-decoration: none; }
      a:hover { text-decoration: underline; }
      .banner {
        display: flex;
        align-items: center;
        gap: 12px;
        min-height: 46px;
        padding: 10px 18px;
        border-bottom: 1px solid var(--line);
        background: #fff;
      }
      .banner strong { font-weight: 650; }
      .banner .spacer { flex: 1; }
      .nav-link {
        border: 1px solid var(--line);
        border-radius: 999px;
        padding: 4px 9px;
        color: var(--text);
      }
      .status {
        display: inline-flex;
        align-items: center;
        min-height: 22px;
        padding: 2px 8px;
        border-radius: 999px;
        background: var(--warn-soft);
        color: var(--warn);
        white-space: nowrap;
      }
      .status.connected {
        background: var(--accent-soft);
        color: #106b35;
      }
      .layout-switch {
        display: inline-flex;
        align-items: center;
        border: 1px solid var(--line);
        border-radius: 999px;
        padding: 2px;
        background: #f7f8fa;
      }
      .layout-switch button {
        min-height: 24px;
        border: 0;
        border-radius: 999px;
        padding: 3px 9px;
        background: transparent;
        color: var(--muted);
      }
      .layout-switch button.active {
        background: #fff;
        color: var(--text);
        box-shadow: 0 1px 2px rgba(20, 30, 45, 0.09);
        font-weight: 650;
      }
      .app {
        display: flex;
        flex-direction: column;
        gap: 0;
        height: calc(100vh - 46px);
        padding: 12px;
        overflow: hidden;
      }
      body[data-layout="columns"] .app {
        flex-direction: row;
        align-items: stretch;
        gap: 12px;
        overflow-x: auto;
        overflow-y: hidden;
      }
      .workspace-tabs {
        display: flex;
        flex: 0 0 auto;
        align-items: flex-end;
        gap: 4px;
        min-height: 36px;
        overflow-x: auto;
        border-bottom: 1px solid var(--line);
        padding: 0 2px;
      }
      body[data-layout="columns"] .workspace-tabs {
        display: none;
      }
      .workspace-tab-item {
        display: inline-flex;
        align-items: stretch;
        min-width: 0;
        border: 1px solid transparent;
        border-bottom: 0;
        border-radius: 8px 8px 0 0;
        background: transparent;
      }
      .workspace-tab-item.active {
        border-color: var(--line);
        background: #fff;
        transform: translateY(1px);
      }
      .workspace-tab-item.is-hidden {
        display: none;
      }
      .workspace-tab {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        min-height: 34px;
        max-width: 280px;
        border: 0;
        background: transparent;
        color: var(--muted);
        padding: 7px 10px;
        border-radius: 8px 0 0 0;
      }
      .workspace-tab-item.active .workspace-tab {
        color: var(--text);
        font-weight: 650;
      }
      .tab-meta {
        color: var(--muted);
        font-size: 12px;
        font-weight: 500;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .tab-close {
        display: inline-grid;
        place-items: center;
        width: 30px;
        min-height: 34px;
        padding: 0;
        border: 0;
        border-left: 1px solid transparent;
        border-radius: 0 8px 0 0;
        background: transparent;
        color: var(--muted);
      }
      .workspace-tab-item.active .tab-close {
        border-left-color: var(--line);
      }
      .tab-close:hover {
        background: #f3f5f8;
        color: var(--text);
      }
      .pane {
        min-width: 0;
        min-height: 0;
        display: flex;
        flex-direction: column;
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 8px;
        overflow: hidden;
      }
      .pane-head {
        display: flex;
        align-items: center;
        gap: 8px;
        min-height: 43px;
        padding: 10px 12px;
        border-bottom: 1px solid var(--line);
        background: #fff;
      }
      .pane-head h2 {
        margin: 0;
        font-size: 13px;
        line-height: 1.2;
        font-weight: 700;
      }
      .pane-head .muted { margin-left: auto; }
      .panel-close {
        display: none;
        place-items: center;
        flex: 0 0 auto;
        width: 28px;
        height: 28px;
        padding: 0;
        border-radius: 6px;
        color: var(--muted);
      }
      .panel-close:hover {
        color: var(--text);
        background: #f3f5f8;
      }
      body[data-layout="columns"] .panel-close {
        display: inline-grid;
      }
      .page-panel {
        flex: 1 1 auto;
        border-top: 0;
        border-radius: 0 0 8px 8px;
      }
      .page-panel.is-hidden {
        display: none;
      }
      .graph-pane {
        width: 100%;
      }
      body[data-layout="columns"] .page-panel {
        flex: 1 1 0;
        min-width: 360px;
        border-top: 1px solid var(--line);
        border-radius: 8px;
      }
      body[data-layout="columns"] .graph-pane {
        flex-grow: 1.08;
        width: auto;
      }
      body[data-layout="columns"] .logs-pane {
        flex-grow: 1.24;
        min-width: 420px;
      }
      body[data-layout="columns"] .detail-pane {
        flex-grow: 1.08;
        min-width: 380px;
      }
      body[data-layout="columns"] .ai-pane {
        flex: 0 0 380px;
        min-width: 340px;
      }
      .graph-pane .pane-body {
        display: flex;
        flex-direction: column;
        overflow: hidden;
      }
      .pane-body {
        flex: 1 1 auto;
        min-height: 0;
        overflow: auto;
        padding: 12px;
      }
      .muted { color: var(--muted); }
      .small { font-size: 12px; }
      .controls {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 10px;
        margin-bottom: 12px;
      }
      .control label {
        display: block;
        margin-bottom: 4px;
        color: var(--muted);
        font-size: 12px;
      }
      .actions {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 12px;
      }
      .graph-workbench {
        display: flex;
        flex: 1 1 auto;
        gap: 10px;
        min-height: 0;
        min-width: 0;
      }
      .graph-main {
        display: flex;
        flex: 1 1 auto;
        flex-direction: column;
        min-width: 0;
        min-height: 0;
      }
      .graph-toolbar {
        display: flex;
        flex: 0 0 auto;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 10px;
      }
      .graph-toolbar[hidden] {
        display: none;
      }
      .graph-breadcrumbs {
        display: flex;
        flex: 0 0 auto;
        align-items: center;
        gap: 6px;
        min-height: 26px;
        margin: -2px 0 10px;
        color: var(--muted);
        font-size: 12px;
      }
      .graph-breadcrumbs[hidden] {
        display: none;
      }
      .graph-breadcrumbs button {
        min-height: 24px;
        border: 1px solid transparent;
        border-radius: 999px;
        background: transparent;
        color: #445368;
        padding: 3px 8px;
        font-size: 12px;
        font-weight: 650;
      }
      .graph-breadcrumbs button:hover {
        border-color: #d3dbe6;
        background: #f7f9fb;
        color: var(--text);
      }
      .graph-breadcrumbs .crumb-current {
        overflow: hidden;
        max-width: min(460px, 48vw);
        color: var(--text);
        font-weight: 750;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .graph-breadcrumbs .crumb-separator {
        color: #a0a9b7;
      }
      .graph-search {
        flex: 1 1 260px;
        min-width: 200px;
      }
      .graph-toolbar select {
        flex: 0 1 220px;
        width: auto;
        min-width: 170px;
      }
      .method-filters {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        border: 1px solid var(--line);
        border-radius: 999px;
        background: #f7f8fa;
        padding: 2px;
      }
      .method-filters button {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        min-height: 26px;
        border: 0;
        border-radius: 999px;
        background: transparent;
        color: var(--muted);
        padding: 4px 8px;
        font-size: 12px;
      }
      .method-filters button.active {
        background: #fff;
        color: var(--text);
        box-shadow: 0 1px 2px rgba(20, 30, 45, 0.08);
        font-weight: 650;
      }
      .legend-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 999px;
        background: #2470a0;
      }
      .legend-dot.post { background: #2a9d8f; }
      .legend-dot.mutation { background: #b67816; }
      .legend-dot.danger { background: #c54a4a; }
      .graph-reset {
        flex: 0 0 auto;
      }
      .graph-board {
        position: relative;
        flex: 1 1 auto;
        height: auto;
        min-height: 0;
        min-width: 0;
        border: 1px solid var(--line);
        border-radius: 8px;
        background:
          radial-gradient(circle at 1px 1px, #edf2f7 0.9px, transparent 0),
          linear-gradient(#fbfcfd, #fff);
        background-size: 28px 28px, 100% 100%;
        overflow: hidden;
      }
      .graph-board svg {
        width: 100%;
        height: 100%;
        display: block;
      }
      .graph-board.dense-graph {
        cursor: grab;
      }
      .graph-board.dense-graph:active {
        cursor: grabbing;
      }
      .dense-link.is-filtered {
        stroke-opacity: 0.025;
      }
      .dense-link {
        stroke: #7d8ba0;
        stroke-width: 1;
        stroke-opacity: 0.16;
      }
      .dense-link.namespace {
        stroke-opacity: 0.14;
      }
      .dense-link.target-namespace {
        stroke: #8d9aac;
        stroke-width: 1;
        stroke-opacity: 0.2;
      }
      .dense-link.namespace-endpoint {
        stroke: #9aa6b7;
        stroke-width: 0.9;
        stroke-opacity: 0.14;
      }
      .dense-link.dependency-link {
        fill: none;
        stroke: #496274;
        stroke-width: 1.25;
        stroke-opacity: 0.42;
      }
      .dense-link.fanout-payload,
      .dense-link.fanout-detail,
      .dense-link.fanout-metadata {
        stroke: #1f7a5b;
        stroke-width: 1.7;
        stroke-opacity: 0.7;
      }
      .dense-link.filter-dependency {
        stroke: #8b6f34;
        stroke-dasharray: 5 4;
        stroke-opacity: 0.46;
      }
      .dense-link.resource-action {
        stroke: #9b5d2d;
        stroke-opacity: 0.34;
      }
      .dense-link.semantic-dependency {
        stroke: #6b7d90;
        stroke-dasharray: 2 4;
        stroke-opacity: 0.34;
      }
      .dense-link.cross-group {
        stroke: #6d858c;
        stroke-width: 1.05;
        stroke-dasharray: 5 5;
        stroke-opacity: 0.28;
      }
      .dense-link.is-neighbor {
        stroke: #315f79;
        stroke-width: 2.1;
        stroke-opacity: 0.86;
      }
      .dense-link.cross-group.is-neighbor {
        stroke: #53756f;
        stroke-width: 1.55;
        stroke-dasharray: 5 4;
        stroke-opacity: 0.58;
      }
      .dense-link.is-dim {
        stroke-opacity: 0.025;
      }
      .dense-cell {
        cursor: pointer;
      }
      .dense-cell rect {
        fill: rgba(255, 255, 255, 0.72);
        stroke: #d6dde7;
        stroke-width: 1;
      }
      .dense-cell text {
        fill: #4f5d70;
        font-size: 11px;
        font-weight: 800;
        pointer-events: none;
      }
      .dense-cell.is-active rect,
      .dense-cell:hover rect {
        fill: rgba(229, 245, 239, 0.74);
        stroke: #7e9f92;
      }
      .dense-cell.is-dim rect {
        opacity: 0.26;
      }
      .dense-cell.is-filtered rect,
      .dense-cell.is-filtered text {
        opacity: 0.12;
      }
      .dense-root-label {
        cursor: pointer;
      }
      .dense-root-label text {
        fill: #273241;
        font-size: 11px;
        font-weight: 850;
        pointer-events: none;
      }
      .dense-root-label.is-active text,
      .dense-root-label:hover text {
        fill: #101820;
      }
      .dense-root-label.is-filtered text {
        opacity: 0.18;
      }
      .dense-node {
        cursor: pointer;
      }
      .dense-node.namespace-root {
        cursor: pointer;
      }
      .dense-node.target-root {
        cursor: pointer;
      }
      .dense-node circle {
        stroke: rgba(255, 255, 255, 0.94);
        stroke-width: 1.2;
        filter: drop-shadow(0 1px 1px rgba(20, 30, 45, 0.07));
      }
      .dense-node.namespace-root circle {
        fill: #ffffff;
        stroke: #506074;
        stroke-width: 1.8;
      }
      .dense-node.target-root circle {
        fill: #101820;
        stroke: #101820;
        stroke-width: 2;
      }
      .dense-node.namespace-root circle.root-halo {
        fill: rgba(80, 96, 116, 0.08);
        stroke: rgba(80, 96, 116, 0.14);
        stroke-width: 1;
        filter: none;
      }
      .dense-node.target-root circle.root-halo {
        fill: rgba(16, 24, 32, 0.1);
        stroke: rgba(16, 24, 32, 0.18);
        filter: none;
      }
      .dense-node.mutation circle {
        stroke: #8f650d;
      }
      .dense-node.mutation-danger circle {
        stroke: #9d2727;
      }
      .dense-node.is-active circle {
        stroke: #101820;
        stroke-width: 3;
      }
      .dense-node.is-neighbor circle {
        stroke: #1f7a5b;
        stroke-width: 2.2;
      }
      .dense-node.is-dim circle {
        opacity: 0.22;
      }
      .dense-node.is-filtered circle {
        opacity: 0.1;
      }
      .dense-node text {
        fill: #202936;
        paint-order: stroke;
        stroke: rgba(255, 255, 255, 0.94);
        stroke-width: 4px;
        stroke-linejoin: round;
        font-size: 11px;
        font-weight: 700;
        opacity: 0;
        pointer-events: none;
      }
      .dense-node.label-visible text {
        opacity: 1;
      }
      .dense-node:hover text {
        opacity: 1;
      }
      .dense-node.namespace-root text {
        opacity: 0.76;
        fill: #566274;
        font-size: 8.8px;
        font-weight: 800;
      }
      .dense-node.namespace-root.is-active text,
      .dense-node.namespace-root:hover text {
        opacity: 1;
        fill: #1d2430;
      }
      .dense-node.target-root text {
        opacity: 0.9;
        fill: #101820;
        font-size: 10px;
        font-weight: 900;
      }
      .dense-group-label {
        fill: #5a687a;
        paint-order: stroke;
        stroke: rgba(255, 255, 255, 0.9);
        stroke-width: 4px;
        stroke-linejoin: round;
        font-size: 11px;
        font-weight: 750;
        pointer-events: none;
      }
      .graph-tooltip {
        position: absolute;
        z-index: 3;
        max-width: min(360px, calc(100% - 24px));
        border: 1px solid #aeb8c7;
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.96);
        box-shadow: 0 8px 20px rgba(20, 30, 45, 0.14);
        padding: 10px;
        color: #202936;
        pointer-events: none;
      }
      .graph-tooltip .tip-head {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 7px;
      }
      .graph-tooltip .tip-method {
        flex: 0 0 auto;
        border-radius: 6px;
        background: #eef2f7;
        color: #405066;
        padding: 4px 6px;
        font-size: 11px;
        font-weight: 850;
      }
      .graph-tooltip .tip-title {
        min-width: 0;
        font-weight: 800;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .graph-tooltip .tip-path {
        color: #556276;
        font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        font-size: 11px;
        overflow-wrap: anywhere;
      }
      .graph-tooltip .tip-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 5px;
        margin-top: 8px;
      }
      .graph-tooltip .tip-pill {
        border-radius: 999px;
        background: #eef2f7;
        color: #405066;
        padding: 2px 6px;
        font-size: 11px;
      }
      .endpoint-inspector {
        flex: 0 0 320px;
        min-width: 280px;
        min-height: 0;
        overflow: auto;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: #fff;
      }
      .endpoint-inspector[hidden] {
        display: none;
      }
      .inspector-head {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 11px 12px;
        border-bottom: 1px solid var(--line);
        background: #fbfcfd;
      }
      .inspector-head strong {
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .inspector-body {
        display: grid;
        gap: 12px;
        padding: 12px;
      }
      .inspector-section {
        display: grid;
        gap: 7px;
      }
      .inspector-label {
        color: var(--muted);
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
      }
      .inspector-path {
        margin: 0;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: #f7f8fa;
        color: #283345;
        padding: 9px;
        font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        font-size: 12px;
        overflow-wrap: anywhere;
      }
      .inspector-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 7px;
      }
      .stat-box {
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 8px;
        background: #fbfcfd;
      }
      .stat-box span {
        display: block;
        color: var(--muted);
        font-size: 11px;
      }
      .stat-box strong {
        display: block;
        margin-top: 2px;
        font-size: 15px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .namespace-list,
      .linked-list {
        display: grid;
        gap: 6px;
      }
      .namespace-button,
      .linked-button {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        gap: 8px;
        width: 100%;
        min-height: 34px;
        padding: 7px 9px;
        text-align: left;
      }
      .namespace-button.active,
      .linked-button.active {
        border-color: #17684c;
        background: var(--accent-soft);
      }
      .namespace-button span,
      .linked-button span {
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .linked-button code {
        grid-column: 1 / -1;
        color: var(--muted);
        font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        font-size: 11px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .method-badge {
        justify-self: start;
        border-radius: 6px;
        background: #eef2f7;
        color: #405066;
        padding: 3px 6px;
        font-size: 11px;
        font-weight: 800;
      }
      .method-badge.get { background: #e8f2fb; color: #15577d; }
      .method-badge.post { background: #e5f5ef; color: #17684c; }
      .method-badge.mutation { background: #fff0c2; color: #8a5a00; }
      .method-badge.danger { background: #fde8e8; color: #9d2727; }
      .endpoint-runner {
        display: grid;
        gap: 8px;
      }
      .endpoint-runner textarea {
        width: 100%;
        min-height: 132px;
        resize: vertical;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: #fbfcfd;
        color: #243044;
        padding: 9px;
        font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        font-size: 11px;
        line-height: 1.45;
      }
      .endpoint-param-grid {
        display: grid;
        gap: 7px;
      }
      .endpoint-param-grid label {
        display: grid;
        gap: 4px;
        color: var(--muted);
        font-size: 11px;
        font-weight: 700;
      }
      .endpoint-run-actions {
        display: flex;
        align-items: center;
        gap: 8px;
      }
      .endpoint-run-result {
        display: grid;
        gap: 8px;
      }
      .request-preview {
        margin: 0;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: #f7f8fa;
        color: #344154;
        padding: 8px;
        font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        font-size: 11px;
        overflow-wrap: anywhere;
      }
      .ai-open {
        flex: 0 0 auto;
        min-height: 28px;
        padding: 5px 9px;
      }
      .ai-open.active {
        border-color: #17684c;
        background: var(--accent-soft);
        color: #105f42;
        font-weight: 650;
      }
      .ai-body {
        display: flex;
        flex: 1 1 auto;
        min-height: 0;
        flex-direction: column;
        gap: 10px;
        padding: 12px;
        overflow: auto;
      }
      .ai-prompt {
        width: 100%;
        min-height: 106px;
        resize: vertical;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: #fbfcfd;
        color: #243044;
        padding: 10px;
        line-height: 1.45;
      }
      .ai-actions {
        display: flex;
        align-items: center;
        gap: 8px;
      }
      .ai-actions .muted {
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .ai-result {
        display: grid;
        gap: 10px;
        min-height: 0;
      }
      .ai-status {
        border: 1px solid var(--line);
        border-radius: 8px;
        background: #fbfcfd;
        padding: 10px;
        color: #3f4b5d;
      }
      .ai-status strong {
        display: block;
        margin-bottom: 4px;
        color: var(--text);
      }
      .ai-steps {
        display: grid;
        gap: 6px;
        max-height: min(360px, 42vh);
        overflow: auto;
        overscroll-behavior: contain;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: #fbfcfd;
        padding: 8px;
      }
      .ai-steps-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        color: var(--muted);
        font-size: 11px;
        font-weight: 750;
        text-transform: uppercase;
      }
      .ai-step {
        display: grid;
        grid-template-columns: auto minmax(0, 1fr);
        gap: 7px;
        align-items: start;
        color: var(--muted);
        font-size: 12px;
      }
      .ai-step::before {
        content: "";
        width: 7px;
        height: 7px;
        margin-top: 5px;
        border-radius: 999px;
        background: #9aa6b7;
      }
      .ai-step.ok::before { background: #1f7a5b; }
      .ai-step.err::before { background: #a12a2a; }
      .ai-card {
        display: grid;
        gap: 9px;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: #fff;
        padding: 10px;
      }
      .ai-card-head {
        display: flex;
        align-items: center;
        gap: 8px;
      }
      .ai-card-head strong {
        flex: 1 1 auto;
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .ai-meta {
        display: grid;
        grid-template-columns: 82px minmax(0, 1fr);
        gap: 5px 8px;
        color: var(--muted);
        font-size: 12px;
      }
      .ai-meta div:nth-child(even) {
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        color: #344154;
      }
      .ai-result .image-grid {
        grid-template-columns: repeat(auto-fill, minmax(118px, 1fr));
        margin-bottom: 0;
      }
      .ai-result pre {
        max-height: 260px;
      }
      .graph-card { cursor: pointer; }
      .graph-card rect.node-box {
        fill: #fff;
        stroke: #aeb8c7;
        stroke-width: 1.4;
        filter: drop-shadow(0 2px 3px rgba(20, 30, 45, 0.08));
      }
      .graph-card.root-list rect.node-box { fill: #f2fbf7; stroke: #207b5d; }
      .graph-card.payload rect.node-box { fill: #faf8ff; stroke: #7a669e; }
      .graph-card.filter rect.node-box { fill: #fcfcfd; stroke-dasharray: 5 4; }
      .graph-card.selected rect.node-box { stroke: #1f7a5b; stroke-width: 2.4; }
      .graph-card text { pointer-events: none; }
      .graph-method-bg { fill: #eef2f7; }
      .graph-method { fill: #405066; font-size: 11px; font-weight: 800; letter-spacing: 0; }
      .graph-label { fill: #1d2430; font-size: 14px; font-weight: 750; }
      .graph-path { fill: #627084; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 11px; }
      .graph-link { fill: none; stroke: #65758a; stroke-width: 1.7; opacity: 0.86; }
      .graph-link.fanout-payload { stroke: #547a6b; stroke-width: 2; }
      .graph-link.filter-dependency { stroke: #8b97a8; stroke-dasharray: 5 4; }
      .graph-edge-label {
        fill: #526176;
        paint-order: stroke;
        stroke: #fff;
        stroke-width: 4px;
        stroke-linejoin: round;
        font-size: 11px;
        font-weight: 650;
        pointer-events: none;
      }
      .summary-bar {
        display: flex;
        flex: 0 0 auto;
        flex-wrap: wrap;
        gap: 6px;
        margin-top: 10px;
        max-height: 136px;
        overflow: auto;
      }
      .pill {
        display: inline-flex;
        align-items: center;
        min-height: 22px;
        padding: 2px 7px;
        border-radius: 999px;
        background: #eef2f7;
        color: #405066;
        font-size: 12px;
      }
      .pill.ok { background: var(--accent-soft); color: #106b35; }
      .pill.err { background: var(--danger-soft); color: var(--danger); }
      .table-wrap {
        min-height: 0;
        overflow: auto;
        border: 1px solid var(--line);
        border-radius: 8px;
      }
      table {
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
        background: #fff;
      }
      th, td {
        border-bottom: 1px solid var(--line);
        padding: 8px;
        text-align: left;
        vertical-align: middle;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      th {
        position: sticky;
        top: 0;
        z-index: 1;
        background: #f9fafb;
        color: #3f4b5d;
        font-size: 12px;
      }
      tr.selected td { background: #edf8f3; }
      tr.loading td { background: #fffaf0; }
      tr.error td { background: #fff3f3; }
      td code, .code {
        font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        font-size: 12px;
      }
      .row-actions {
        display: flex;
        gap: 6px;
      }
      .row-actions button {
        padding: 4px 7px;
        border-radius: 5px;
        font-size: 12px;
      }
      .detail-tabs {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        padding: 10px 12px 0;
      }
      .detail-tabs button {
        padding: 6px 9px;
      }
      .detail-tabs button.active {
        border-color: #17684c;
        background: var(--accent-soft);
        color: #105f42;
      }
      .detail-content {
        flex: 1 1 auto;
        min-height: 0;
        overflow: auto;
        padding: 12px;
      }
      .empty {
        padding: 18px;
        border: 1px dashed var(--line-strong);
        border-radius: 8px;
        color: var(--muted);
        background: #fbfcfd;
      }
      .kv {
        display: grid;
        grid-template-columns: 128px minmax(0, 1fr);
        gap: 6px 10px;
        margin-bottom: 12px;
      }
      .kv div:nth-child(odd) { color: var(--muted); }
      pre {
        margin: 0;
        padding: 12px;
        overflow: auto;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: #0f1720;
        color: #e8eef7;
        line-height: 1.45;
        font-size: 12px;
      }
      .text-fragments {
        display: grid;
        gap: 8px;
      }
      .text-fragment {
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 10px;
        background: #fbfcfd;
        white-space: pre-wrap;
        overflow-wrap: anywhere;
      }
      .image-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
        gap: 10px;
        margin-bottom: 12px;
      }
      .image-card {
        border: 1px solid var(--line);
        border-radius: 8px;
        overflow: hidden;
        background: #fff;
      }
      .image-card img {
        display: block;
        width: 100%;
        aspect-ratio: 1 / 1;
        object-fit: contain;
        background: #f3f5f8;
      }
      .image-card div {
        padding: 6px 8px;
        color: var(--muted);
        font-size: 11px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .log-line {
        padding: 7px 0;
        border-bottom: 1px solid var(--line);
        color: var(--muted);
      }
      .log-line:last-child { border-bottom: 0; }
      @media (max-width: 1180px) {
        .app {
          height: calc(100vh - 46px);
          padding: 10px;
        }
        .pane { min-height: 0; }
      }
      @media (max-width: 760px) {
        .banner {
          align-items: flex-start;
          flex-wrap: wrap;
        }
        .banner .spacer {
          display: none;
        }
        .controls {
          grid-template-columns: 1fr;
        }
        .graph-workbench {
          flex-direction: column;
        }
        .endpoint-inspector {
          flex-basis: auto;
          max-height: 260px;
        }
      }
    </style>
  </head>
  <body data-layout="tabs">
    <div class="banner">
      <strong>cli2anything++</strong>
      <span>${escapeHtml(manifest.target)} / ${escapeHtml(manifest.filterKeyword)} drilldown</span>
      <a class="nav-link" href="/">Swagger</a>
      <div class="layout-switch" role="group" aria-label="Workspace layout">
        <button class="active" id="layout-tabs" data-layout-mode="tabs" aria-pressed="true">Tabs</button>
        <button id="layout-columns" data-layout-mode="columns" aria-pressed="false">Columns</button>
      </div>
      <span class="spacer"></span>
      <span id="bridge-status" class="status">Checking bridge...</span>
      <span id="bridge-help" class="muted small"></span>
    </div>
    <main class="app">
      <nav class="workspace-tabs" role="tablist" aria-label="Drilldown pages">
        <div class="workspace-tab-item active" id="tab-item-graph">
          <button class="workspace-tab" id="tab-graph" data-page-tab="graph" role="tab" aria-controls="graph-panel" aria-selected="true">Graph</button>
        </div>
        <div class="workspace-tab-item" id="tab-item-ai">
          <button class="workspace-tab" id="tab-ai" data-page-tab="ai" role="tab" aria-controls="ai-panel" aria-selected="false">AI <span class="tab-meta" id="tab-ai-meta">Ready</span></button>
          <button class="tab-close" id="close-ai" data-close-page="ai" title="Close AI tab" aria-label="Close AI tab">x</button>
        </div>
        <div class="workspace-tab-item is-hidden" id="tab-item-logs">
          <button class="workspace-tab" id="tab-logs" data-page-tab="logs" role="tab" aria-controls="logs-panel" aria-selected="false">Logs <span class="tab-meta" id="tab-logs-meta">No list</span></button>
          <button class="tab-close" id="close-logs" data-close-page="logs" title="Close logs tab" aria-label="Close logs tab">x</button>
        </div>
        <div class="workspace-tab-item is-hidden" id="tab-item-detail">
          <button class="workspace-tab" id="tab-detail" data-page-tab="detail" role="tab" aria-controls="detail-panel" aria-selected="false">Detail <span class="tab-meta" id="tab-detail-meta">No row</span></button>
          <button class="tab-close" id="close-detail" data-close-page="detail" title="Close detail tab" aria-label="Close detail tab">x</button>
        </div>
      </nav>
      <section class="pane page-panel graph-pane active" id="graph-panel" role="tabpanel" aria-labelledby="tab-graph">
        <div class="pane-head">
          <h2>${escapeHtml(graphTitle)}</h2>
          <span class="muted small">${escapeHtml(graphSubtitle)}</span>
          <button id="ai-sidebar-toggle" class="ai-open active" title="Open AI sidebar" aria-pressed="true">AI</button>
        </div>
        <div class="pane-body">
          <div class="graph-toolbar" id="graph-toolbar" hidden>
            <input class="graph-search" id="graph-search" placeholder="Search endpoints" />
            <select id="graph-namespace" aria-label="Namespace"></select>
            <div class="method-filters" id="graph-methods" role="group" aria-label="Endpoint kind">
              <button class="active" data-graph-kind="get" aria-pressed="true"><span class="legend-dot get"></span>GET</button>
              <button class="active" data-graph-kind="post" aria-pressed="true"><span class="legend-dot post"></span>POST</button>
              <button class="active" data-graph-kind="mutation" aria-pressed="true"><span class="legend-dot mutation"></span>Write</button>
              <button class="active" data-graph-kind="danger" aria-pressed="true"><span class="legend-dot danger"></span>Risk</button>
            </div>
            <button class="graph-reset" id="graph-reset" title="Reset graph filters">Reset</button>
          </div>
          <nav class="graph-breadcrumbs" id="graph-breadcrumbs" aria-label="Graph breadcrumbs" hidden></nav>
          <div class="graph-workbench">
            <div class="graph-main">
              <div id="graph" class="graph-board"></div>
            </div>
            <aside id="endpoint-inspector" class="endpoint-inspector" hidden></aside>
          </div>
          <div class="summary-bar" id="graph-summary"></div>
        </div>
      </section>
      <section class="pane page-panel ai-pane is-hidden" id="ai-panel" role="tabpanel" aria-labelledby="tab-ai" aria-hidden="true">
        <div class="pane-head">
          <h2>AI Sidebar</h2>
          <span class="muted small">browser-session planner</span>
          <span class="pill" id="ai-engine">planner</span>
          <button class="panel-close" data-close-page="ai" title="Close AI panel" aria-label="Close AI panel">x</button>
        </div>
        <div class="pane-body ai-body">
          <textarea id="ai-prompt" class="ai-prompt" spellcheck="false" placeholder="Show and render the latest two image generation results"></textarea>
          <div class="ai-actions">
            <button class="primary" id="ai-run">Run</button>
            <button id="ai-clear">Clear</button>
            <span class="muted small" id="ai-summary">Ready</span>
          </div>
          <div id="ai-result" class="ai-result">
            <div class="empty">Ask for a browser-session task, then the sidebar will plan API calls and render the result.</div>
          </div>
        </div>
      </section>
      <section class="pane page-panel logs-pane is-hidden" id="logs-panel" role="tabpanel" aria-labelledby="tab-logs" aria-hidden="true">
        <div class="pane-head">
          <h2>Logs</h2>
          <span class="muted small" id="list-summary">No list loaded</span>
          <button class="panel-close" data-close-page="logs" title="Close logs panel" aria-label="Close logs panel">x</button>
        </div>
        <div class="pane-body">
          <div class="controls">
            <div class="control"><label for="days">Days</label><input id="days" type="number" min="1" max="90" value="7" /></div>
            <div class="control"><label for="page-size">Page size</label><input id="page-size" type="number" min="5" max="200" value="${Number(listLogsExample.pageSize || 20)}" /></div>
            <div class="control"><label for="page-no">Page</label><input id="page-no" type="number" min="1" value="1" /></div>
            <div class="control"><label for="request-id-filter">Request id filter</label><input id="request-id-filter" placeholder="optional" /></div>
            <div class="control"><label for="max-drill">Max drill items</label><input id="max-drill" type="number" min="1" max="200" value="20" /></div>
            <div class="control"><label for="concurrency">Concurrency</label><input id="concurrency" type="number" min="1" max="8" value="3" /></div>
          </div>
          <div class="actions">
            <button class="primary" id="run-list" title="Run listLogs with the current form values">Run listLogs</button>
            <button id="drill-selected" title="Fetch all dependent APIs for the selected row" disabled>Drill selected</button>
            <button id="drill-first" title="Fetch all dependent APIs for the first N rows" disabled>Drill first N</button>
            <button id="stop-drill" title="Stop queued drilldown calls" disabled>Stop</button>
          </div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th style="width: 220px;">requestId</th>
                  <th style="width: 120px;">model</th>
                  <th style="width: 130px;">provider</th>
                  <th style="width: 90px;">finish</th>
                  <th style="width: 80px;">latency</th>
                  <th style="width: 80px;">cost</th>
                  <th style="width: 150px;">created</th>
                  <th style="width: 126px;">actions</th>
                </tr>
              </thead>
              <tbody id="logs-body">
                <tr><td colspan="8" class="muted">Run listLogs to populate request ids.</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>
      <section class="pane page-panel detail-pane is-hidden" id="detail-panel" role="tabpanel" aria-labelledby="tab-detail" aria-hidden="true">
        <div class="pane-head">
          <h2>Detail</h2>
          <span class="muted small" id="detail-title">No row selected</span>
          <button class="panel-close" data-close-page="detail" title="Close detail panel" aria-label="Close detail panel">x</button>
        </div>
        <div class="detail-tabs" id="detail-tabs"></div>
        <div class="detail-content" id="detail-content">
          <div class="empty">Select a log row, then drill into request/response payloads.</div>
        </div>
      </section>
    </main>
    <script src="https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js"></script>
    <script>
      const targetHost = ${JSON.stringify(manifest.target)};
      const extensionHelp = ${JSON.stringify(extensionHelp)};
      const apiGraph = ${JSON.stringify(apiGraph)};
      const initialExample = ${JSON.stringify(listLogsExample)};
      const endpointOperationSpecs = ${JSON.stringify(endpointOperationSpecs)};
      const state = {
        logs: [],
        selectedId: null,
        details: {},
        activeTab: "responsePayload",
        abortDrill: false,
        running: false,
        endpointRuns: {},
        ai: {
          prompt: "Show and render the latest two image generation results",
          running: false,
          engine: "",
          plan: null,
          result: null,
          error: "",
          steps: []
        },
        events: [],
        activePage: "graph",
        layout: "tabs",
        graph: {
          query: "",
          namespace: "",
          selectedNodeId: null,
          selectedNamespace: "",
          selectedRoot: false,
          kinds: {
            get: true,
            post: true,
            mutation: true,
            danger: true
          }
        },
        pages: {
          ai: true,
          logs: false,
          detail: false
        }
      };

      window.addEventListener("load", () => {
        bindControls();
        setLayout(readLayoutPreference(), { persist: false });
        syncPages();
        renderAiSidebar();
        renderGraph();
        monitorBridge();
      });

      function bindControls() {
        bindGraphControls();
        bindAiSidebar();
        document.getElementById("run-list").addEventListener("click", runListLogs);
        document.getElementById("drill-selected").addEventListener("click", () => {
          if (state.selectedId) drillMany([state.selectedId]);
        });
        document.getElementById("drill-first").addEventListener("click", () => {
          const limit = Number(document.getElementById("max-drill").value || "20");
          const ids = state.logs.map(getRequestId).filter(Boolean).slice(0, limit);
          drillMany(ids);
        });
        document.getElementById("stop-drill").addEventListener("click", () => {
          state.abortDrill = true;
          setEvent("Stop requested. In-flight requests will finish.");
        });
        document.querySelectorAll("[data-layout-mode]").forEach((button) => {
          button.addEventListener("click", () => setLayout(button.dataset.layoutMode));
        });
        document.querySelectorAll("[data-page-tab]").forEach((button) => {
          button.addEventListener("click", () => openPage(button.dataset.pageTab));
        });
        document.querySelectorAll("[data-close-page]").forEach((button) => {
          button.addEventListener("click", (event) => {
            event.stopPropagation();
            closePage(button.dataset.closePage);
          });
        });
      }

      function bindGraphControls() {
        const search = document.getElementById("graph-search");
        const namespace = document.getElementById("graph-namespace");
        const reset = document.getElementById("graph-reset");
        const inspector = document.getElementById("endpoint-inspector");
        const breadcrumbs = document.getElementById("graph-breadcrumbs");

        search.addEventListener("input", () => {
          state.graph.query = search.value.trim();
          state.graph.selectedNodeId = null;
          state.graph.selectedNamespace = state.graph.namespace;
          state.graph.selectedRoot = false;
          renderGraph();
        });
        namespace.addEventListener("change", () => {
          enterGraphNamespace(namespace.value);
        });
        document.querySelectorAll("[data-graph-kind]").forEach((button) => {
          button.addEventListener("click", () => {
            const kind = button.dataset.graphKind;
            state.graph.kinds[kind] = !state.graph.kinds[kind];
            state.graph.selectedNodeId = null;
            state.graph.selectedRoot = false;
            renderGraph();
          });
        });
        reset.addEventListener("click", () => {
          state.graph.query = "";
          state.graph.namespace = "";
          state.graph.selectedNodeId = null;
          state.graph.selectedNamespace = "";
          state.graph.selectedRoot = false;
          state.graph.kinds = { get: true, post: true, mutation: true, danger: true };
          renderGraph();
        });
        breadcrumbs.addEventListener("click", (event) => {
          const rootCrumb = event.target.closest("[data-graph-crumb-root]");
          if (rootCrumb) {
            enterGraphRoot();
            return;
          }
          const namespaceCrumb = event.target.closest("[data-graph-crumb-namespace]");
          if (namespaceCrumb) enterGraphNamespace(namespaceCrumb.dataset.graphCrumbNamespace);
        });
        inspector.addEventListener("click", (event) => {
          const runButton = event.target.closest("[data-run-endpoint]");
          if (runButton) {
            runEndpointFromButton(runButton);
            return;
          }
          const namespaceButton = event.target.closest("[data-graph-namespace]");
          if (namespaceButton) {
            enterGraphNamespace(namespaceButton.dataset.graphNamespace);
            return;
          }
          const rootButton = event.target.closest("[data-graph-root]");
          if (rootButton) {
            enterGraphRoot({ selected: true });
            return;
          }
          const nodeButton = event.target.closest("[data-graph-node]");
          if (nodeButton) {
            state.graph.selectedNodeId = nodeButton.dataset.graphNode;
            state.graph.selectedNamespace = "";
            state.graph.selectedRoot = false;
            renderGraph();
            focusGraphNode(state.graph.selectedNodeId);
          }
        });
      }

      function bindAiSidebar() {
        const prompt = document.getElementById("ai-prompt");
        const run = document.getElementById("ai-run");
        const clear = document.getElementById("ai-clear");
        const pane = document.getElementById("ai-panel");
        const toggle = document.getElementById("ai-sidebar-toggle");

        prompt.value = state.ai.prompt;
        run.addEventListener("click", runAiSidebar);
        clear.addEventListener("click", () => {
          state.ai.result = null;
          state.ai.error = "";
          state.ai.steps = [];
          renderAiSidebar();
        });
        prompt.addEventListener("keydown", (event) => {
          if ((event.metaKey || event.ctrlKey) && event.key === "Enter") runAiSidebar();
        });
        toggle.addEventListener("click", () => {
          if (state.pages.ai) closePage("ai");
          else openPage("ai");
          requestAnimationFrame(renderGraph);
        });
        pane.addEventListener("click", (event) => {
          const detailButton = event.target.closest("[data-ai-detail]");
          if (!detailButton) return;
          const requestId = detailButton.dataset.aiDetail;
          if (!requestId) return;
          state.selectedId = requestId;
          openPage("detail");
          renderLogs({ total: undefined });
          renderDetail();
        });
      }

      function readLayoutPreference() {
        try {
          const value = window.localStorage.getItem("cli2anything-plus-plus-drilldown-layout");
          return value === "columns" ? "columns" : "tabs";
        } catch {
          return "tabs";
        }
      }

      function setLayout(name, options = {}) {
        state.layout = name === "columns" ? "columns" : "tabs";
        document.body.dataset.layout = state.layout;
        document.querySelectorAll("[data-layout-mode]").forEach((button) => {
          const active = button.dataset.layoutMode === state.layout;
          button.classList.toggle("active", active);
          button.setAttribute("aria-pressed", active ? "true" : "false");
        });
        if (options.persist !== false) {
          try {
            window.localStorage.setItem("cli2anything-plus-plus-drilldown-layout", state.layout);
          } catch {
            // Ignore storage failures in locked-down browser contexts.
          }
        }
        syncPages();
        requestAnimationFrame(renderGraph);
      }

      function openPage(name) {
        if (name !== "graph") state.pages[name] = true;
        state.activePage = name || "graph";
        syncPages();
        renderAiSidebar();
        if (state.activePage === "graph" || state.layout === "columns") requestAnimationFrame(renderGraph);
      }

      function closePage(name) {
        if (name === "graph") return;
        state.pages[name] = false;
        if (state.activePage === name) {
          state.activePage = state.pages.detail ? "detail" : state.pages.logs ? "logs" : state.pages.ai ? "ai" : "graph";
        }
        syncPages();
        renderAiSidebar();
        if (state.activePage === "graph" || state.layout === "columns") requestAnimationFrame(renderGraph);
      }

      function syncPages() {
        const columns = state.layout === "columns";
        if (state.activePage !== "graph" && !state.pages[state.activePage]) {
          state.activePage = state.pages.detail ? "detail" : state.pages.logs ? "logs" : "graph";
        }
        for (const name of ["graph", "ai", "logs", "detail"]) {
          const tabItem = document.getElementById("tab-item-" + name);
          const tab = document.getElementById("tab-" + name);
          const panel = document.getElementById(name + "-panel");
          const open = name === "graph" || state.pages[name];
          const selected = open && state.activePage === name;
          const visible = open && (columns || selected);
          tabItem.classList.toggle("is-hidden", !open);
          tabItem.classList.toggle("active", !columns && selected);
          tab.setAttribute("aria-selected", !columns && selected ? "true" : "false");
          tab.tabIndex = !columns && selected ? 0 : -1;
          panel.classList.toggle("is-hidden", !visible);
          panel.classList.toggle("active", visible);
          panel.setAttribute("aria-hidden", visible ? "false" : "true");
        }
        const aiMeta = document.getElementById("tab-ai-meta");
        if (aiMeta) aiMeta.textContent = state.ai.running ? "Running" : state.ai.result ? summarizeAiResult(state.ai.result) : "Ready";
        document.getElementById("tab-logs-meta").textContent = state.logs.length ? state.logs.length + " rows" : "No list";
        document.getElementById("tab-detail-meta").textContent = state.selectedId ? truncateMiddle(state.selectedId, 13) : "No row";
      }

      async function monitorBridge() {
        const status = document.getElementById("bridge-status");
        const help = document.getElementById("bridge-help");
        while (true) {
          try {
            const response = await fetch("/__cap/health", { cache: "no-store" });
            const health = await response.json();
            if (health.bridge === "extension" && health.extensionConnected && health.extensionCurrent !== false) {
              status.textContent = "Extension connected";
              status.className = "status connected";
              help.textContent = "";
            } else if (health.bridge === "extension" && health.extensionConnected) {
              status.textContent = "Extension reconnecting";
              status.className = "status";
              help.textContent = extensionHelp;
            } else if (health.bridge === "extension") {
              status.textContent = "Extension not connected";
              status.className = "status";
              help.textContent = extensionHelp;
            } else {
              status.textContent = "CDP bridge";
              status.className = health.ok ? "status connected" : "status";
              help.textContent = "";
            }
          } catch {
            status.textContent = "Proxy offline";
            status.className = "status";
            help.textContent = "Restart cli2anything --output swagger.";
          }
          await sleep(2000);
        }
      }

      function renderGraph() {
        const board = document.getElementById("graph");
        syncGraphWorkbench();
        if (!window.d3) {
          renderGraphFallback(board);
        } else if (isDenseGraph()) {
          renderDenseGraph(board);
        } else {
          renderForceGraph(board);
        }
        renderGraphSummary();
      }

      function isDenseGraph() {
        return apiGraph.scope === "all" || apiGraph.nodes.length > 32;
      }

      function syncGraphWorkbench() {
        const dense = isDenseGraph();
        const toolbar = document.getElementById("graph-toolbar");
        const inspector = document.getElementById("endpoint-inspector");
        const breadcrumbs = document.getElementById("graph-breadcrumbs");
        toolbar.hidden = !dense;
        inspector.hidden = !dense;
        breadcrumbs.hidden = !dense;
        if (!dense) return;

        const namespace = document.getElementById("graph-namespace");
        const groups = [...groupBy(apiGraph.nodes, (node) => node.group || "/").entries()]
          .sort((left, right) => right[1].length - left[1].length || left[0].localeCompare(right[0]));
        const options = ['<option value="">All namespaces</option>'].concat(groups.map(([group, nodes]) =>
          '<option value="' + escapeAttr(group) + '">' + escapeHtml(group) + ' (' + nodes.length + ')</option>'
        )).join("");
        if (namespace.innerHTML !== options) namespace.innerHTML = options;
        namespace.value = state.graph.namespace;

        document.getElementById("graph-search").value = state.graph.query;
        document.querySelectorAll("[data-graph-kind]").forEach((button) => {
          const active = Boolean(state.graph.kinds[button.dataset.graphKind]);
          button.classList.toggle("active", active);
          button.setAttribute("aria-pressed", active ? "true" : "false");
        });
        const selected = apiGraph.nodes.find((node) => node.id === state.graph.selectedNodeId);
        if (selected && !graphNodeMatches(selected)) state.graph.selectedNodeId = null;
        if (state.graph.selectedNamespace && !apiGraph.nodes.some((node) => (node.group || "/") === state.graph.selectedNamespace && graphNodeMatches(node))) {
          state.graph.selectedNamespace = "";
        }
        renderGraphBreadcrumbs();
        renderEndpointInspector();
      }

      function renderGraphBreadcrumbs() {
        const breadcrumbs = document.getElementById("graph-breadcrumbs");
        if (!isDenseGraph()) {
          breadcrumbs.hidden = true;
          return;
        }
        breadcrumbs.hidden = false;
        const namespace = state.graph.namespace;
        const rootButton = '<button type="button" data-graph-crumb-root="true" title="' + escapeAttr(targetHost) + ' API root">' + escapeHtml(targetHost) + ' API root</button>';
        if (!namespace) {
          breadcrumbs.innerHTML = rootButton + '<span class="crumb-separator">/</span><span class="crumb-current">all groups</span>';
          return;
        }
        breadcrumbs.innerHTML = rootButton +
          '<span class="crumb-separator">/</span>' +
          '<button type="button" class="crumb-current" data-graph-crumb-namespace="' + escapeAttr(namespace) + '" title="' + escapeAttr(namespace) + '">' + escapeHtml(namespace) + '</button>';
      }

      function enterGraphNamespace(namespace) {
        state.graph.namespace = namespace || "";
        state.graph.selectedNodeId = null;
        state.graph.selectedNamespace = namespace || "";
        state.graph.selectedRoot = false;
        renderGraph();
      }

      function enterGraphRoot(options = {}) {
        state.graph.namespace = "";
        state.graph.selectedNodeId = null;
        state.graph.selectedNamespace = "";
        state.graph.selectedRoot = Boolean(options.selected);
        renderGraph();
      }

      function renderGraphSummary() {
        document.getElementById("graph-summary").innerHTML = graphSummaryPills().join("");
      }

      function graphSummaryPills() {
        const groups = new Set(apiGraph.nodes.map((node) => node.group).filter(Boolean));
        const shown = isDenseGraph() ? apiGraph.nodes.filter(graphNodeMatches).length : null;
        const inferredEdges = apiGraph.edges.filter((edge) => edge.relation !== "namespace");
        if (apiGraph.scope === "all") {
          const counts = countBy(apiGraph.nodes, graphNodeKind);
          return [
            '<span class="pill">' + apiGraph.nodes.length + ' endpoints</span>',
            '<span class="pill ok">' + inferredEdges.length + ' inferred links</span>',
            shown !== null && shown !== apiGraph.nodes.length ? '<span class="pill">' + shown + ' shown</span>' : '',
            groups.size ? '<span class="pill">' + groups.size + ' namespaces</span>' : '',
            '<span class="pill">GET ' + (counts.get || 0) + '</span>',
            '<span class="pill">POST ' + (counts.post || 0) + '</span>',
            '<span class="pill">Write ' + (counts.mutation || 0) + '</span>',
            '<span class="pill">Risk ' + (counts.danger || 0) + '</span>',
            '<span class="pill">' + apiGraph.defaultWorkflowId + '</span>'
          ].filter(Boolean);
        }
        return [
          '<span class="pill ok">' + apiGraph.edges.filter((edge) => edge.safe).length + ' safe edges</span>',
          '<span class="pill">' + apiGraph.nodes.length + ' operations</span>',
          shown !== null && shown !== apiGraph.nodes.length ? '<span class="pill">' + shown + ' shown</span>' : '',
          groups.size ? '<span class="pill">' + groups.size + ' namespaces</span>' : '',
          '<span class="pill">' + apiGraph.defaultWorkflowId + '</span>'
        ].filter(Boolean);
      }

      function groupBy(values, keyFn) {
        const groups = new Map();
        for (const value of values) {
          const key = keyFn(value);
          if (!groups.has(key)) groups.set(key, []);
          groups.get(key).push(value);
        }
        return groups;
      }

      function graphNodeKind(node) {
        if (node._type === "target-root" || node._type === "namespace") return "namespace";
        if (node.role === "mutation-danger") return "danger";
        if (node.role === "mutation") return "mutation";
        if (node.method === "GET") return "get";
        return "post";
      }

      function graphNodeMatches(node) {
        const kind = graphNodeKind(node);
        if (!state.graph.kinds[kind]) return false;
        if (state.graph.namespace && (node.group || "/") !== state.graph.namespace) return false;
        const query = state.graph.query.toLowerCase();
        if (!query) return true;
        return [node.method, node.label, node.path, node.group, node.operationId]
          .filter(Boolean)
          .some((value) => String(value).toLowerCase().includes(query));
      }

      function visualNodeMatches(node) {
        if (!node) return false;
        if (node._type === "target-root") return apiGraph.nodes.some(graphNodeMatches);
        if (node._type === "namespace") {
          return apiGraph.nodes.some((item) => (item.group || "/") === node.group && graphNodeMatches(item));
        }
        return graphNodeMatches(node);
      }

      function renderEndpointInspector() {
        const inspector = document.getElementById("endpoint-inspector");
        if (!isDenseGraph() || inspector.hidden) return;
        const selected = apiGraph.nodes.find((node) => node.id === state.graph.selectedNodeId);
        if (selected) {
          inspector.innerHTML = renderSelectedEndpointInspector(selected);
        } else if (state.graph.selectedNamespace || state.graph.namespace) {
          inspector.innerHTML = renderNamespaceInspector(state.graph.selectedNamespace || state.graph.namespace);
        } else if (state.graph.selectedRoot) {
          inspector.innerHTML = renderTargetRootInspector();
        } else {
          inspector.innerHTML = renderInventoryInspector();
        }
      }

      function renderInventoryInspector() {
        const groups = [...groupBy(apiGraph.nodes, (node) => node.group || "/").entries()]
          .sort((left, right) => right[1].length - left[1].length || left[0].localeCompare(right[0]));
        const counts = countBy(apiGraph.nodes, graphNodeKind);
        return '<div class="inspector-head"><strong>Endpoint Inventory</strong><span class="pill">' + apiGraph.nodes.length + '</span></div>' +
          '<div class="inspector-body">' +
            '<div class="inspector-section">' +
              '<button class="namespace-button ' + (state.graph.selectedRoot ? "active" : "") + '" data-graph-root="true">' +
                '<span>' + escapeHtml(targetHost) + '</span><strong>root</strong>' +
              '</button>' +
            '</div>' +
            '<div class="inspector-grid">' +
              statBox("GET", counts.get || 0) +
              statBox("POST", counts.post || 0) +
              statBox("Write", counts.mutation || 0) +
              statBox("Risk", counts.danger || 0) +
            '</div>' +
            '<div class="inspector-section">' +
              '<div class="inspector-label">Namespaces</div>' +
              '<div class="namespace-list">' +
                groups.map(([group, nodes]) =>
                  '<button class="namespace-button ' + (state.graph.namespace === group ? "active" : "") + '" data-graph-namespace="' + escapeAttr(group) + '">' +
                    '<span>' + escapeHtml(group) + '</span><strong>' + nodes.length + '</strong>' +
                  '</button>'
                ).join("") +
              '</div>' +
            '</div>' +
          '</div>';
      }

      function renderTargetRootInspector() {
        const groups = [...groupBy(apiGraph.nodes, (node) => node.group || "/").entries()]
          .sort((left, right) => right[1].length - left[1].length || left[0].localeCompare(right[0]));
        const shown = apiGraph.nodes.filter(graphNodeMatches).length;
        return '<div class="inspector-head"><strong>' + escapeHtml(targetHost) + '</strong><span class="pill">root</span></div>' +
          '<div class="inspector-body">' +
            '<div class="inspector-grid">' +
              statBox("Endpoints", apiGraph.nodes.length) +
              statBox("Shown", shown) +
              statBox("Namespaces", groups.length) +
              statBox("Workflow", apiGraph.defaultWorkflowId) +
            '</div>' +
            '<div class="inspector-section">' +
              '<div class="inspector-label">Namespaces</div>' +
              '<div class="namespace-list">' +
                groups.map(([group, nodes]) =>
                  '<button class="namespace-button" data-graph-namespace="' + escapeAttr(group) + '">' +
                    '<span>' + escapeHtml(group) + '</span><strong>' + nodes.length + '</strong>' +
                  '</button>'
                ).join("") +
              '</div>' +
            '</div>' +
          '</div>';
      }

      function renderNamespaceInspector(group) {
        const nodes = apiGraph.nodes
          .filter((node) => (node.group || "/") === group)
          .sort((left, right) => left.path.localeCompare(right.path));
        const counts = countBy(nodes, graphNodeKind);
        return '<div class="inspector-head"><strong title="' + escapeAttr(group) + '">' + escapeHtml(group) + '</strong><span class="pill">namespace</span></div>' +
          '<div class="inspector-body">' +
            '<div class="inspector-grid">' +
              statBox("Endpoints", nodes.length) +
              statBox("GET", counts.get || 0) +
              statBox("POST", counts.post || 0) +
              statBox("Risk", counts.danger || 0) +
            '</div>' +
            '<div class="inspector-section">' +
              '<div class="inspector-label">Endpoints</div>' +
              '<div class="linked-list">' +
                nodes.map((item) =>
                  '<button class="linked-button" data-graph-node="' + escapeAttr(item.id) + '">' +
                    '<span>' + escapeHtml(item.label) + '</span><span class="method-badge ' + escapeAttr(graphNodeKind(item)) + '">' + escapeHtml(item.method) + '</span>' +
                    '<code>' + escapeHtml(item.path) + '</code>' +
                  '</button>'
                ).join("") +
              '</div>' +
            '</div>' +
          '</div>';
      }

      function renderSelectedEndpointInspector(node) {
        const related = relatedEndpointNodes(node);
        const kind = graphNodeKind(node);
        return '<div class="inspector-head">' +
            '<span class="method-badge ' + escapeAttr(kind) + '">' + escapeHtml(node.method) + '</span>' +
            '<strong title="' + escapeAttr(node.label) + '">' + escapeHtml(node.label) + '</strong>' +
          '</div>' +
          '<div class="inspector-body">' +
            '<div class="inspector-section">' +
              '<div class="inspector-label">Path</div>' +
              '<pre class="inspector-path">' + escapeHtml(node.path) + '</pre>' +
            '</div>' +
            '<div class="inspector-grid">' +
              statBox("Namespace", node.group || "/") +
              statBox("Linked", related.length) +
              statBox("Kind", endpointKindLabel(kind)) +
              statBox("Auto run", node.safeAutoRun ? "yes" : "manual") +
            '</div>' +
            renderEndpointRunner(node) +
            (node.reason ? '<div class="inspector-section"><div class="inspector-label">Reason</div><div class="small muted">' + escapeHtml(node.reason) + '</div></div>' : '') +
            '<div class="inspector-section">' +
              '<div class="inspector-label">Linked endpoints</div>' +
              '<div class="linked-list">' +
                (related.length ? related.map((item) =>
                  '<button class="linked-button ' + (item.id === state.graph.selectedNodeId ? "active" : "") + '" data-graph-node="' + escapeAttr(item.id) + '">' +
                    '<span>' + escapeHtml(item.label) + '</span><span class="method-badge ' + escapeAttr(graphNodeKind(item)) + '">' + escapeHtml(item.method) + '</span>' +
                    '<code>' + escapeHtml(item.path) + '</code>' +
                  '</button>'
                ).join("") : '<div class="small muted">No inferred links</div>') +
              '</div>' +
            '</div>' +
          '</div>';
      }

      function renderEndpointRunner(node) {
        const spec = operationSpecForNode(node);
        const params = (spec?.parameters || []).filter((param) => param.in === "path" || param.in === "query");
        const body = defaultEndpointBody(node, spec);
        const paramHtml = params.length ? '<div class="endpoint-param-grid">' + params.map((param) =>
          '<label>' + escapeHtml(param.in + "." + param.name) +
            '<input data-endpoint-param="true" data-param-in="' + escapeAttr(param.in) + '" data-param-name="' + escapeAttr(param.name) + '" value="' + escapeAttr(defaultEndpointParamValue(param, node)) + '" />' +
          '</label>'
        ).join("") + '</div>' : "";
        const bodyHtml = body === undefined ? "" :
          '<label class="inspector-label">JSON body</label>' +
          '<textarea data-endpoint-body="true" spellcheck="false">' + escapeHtml(JSON.stringify(body, null, 2)) + '</textarea>';
        const run = state.endpointRuns[node.id];
        return '<div class="inspector-section endpoint-runner" data-endpoint-runner="' + escapeAttr(node.id) + '">' +
          '<div class="inspector-label">Execute</div>' +
          paramHtml +
          bodyHtml +
          '<div class="endpoint-run-actions">' +
            '<button class="primary" data-run-endpoint="' + escapeAttr(node.id) + '">' + (isEndpointSafeToRun(node) ? "Run endpoint" : "Run manually") + '</button>' +
            '<span class="small muted">' + escapeHtml(node.method + " " + node.path) + '</span>' +
          '</div>' +
          renderEndpointRunResult(run) +
        '</div>';
      }

      function renderEndpointRunResult(run) {
        if (!run) return '<div class="empty">Run this endpoint to inspect the live browser-session response.</div>';
        const requestHtml = run.request ? '<pre class="request-preview">' + escapeHtml(run.request.method + " " + run.request.path + (run.request.body !== undefined ? "\\n" + JSON.stringify(run.request.body, null, 2) : "")) + '</pre>' : "";
        if (run.loading) return requestHtml + '<div class="empty">Running endpoint...</div>';
        if (run.error) return requestHtml + '<div class="empty">' + escapeHtml(run.error) + '</div>';
        return '<div class="endpoint-run-result">' + requestHtml + renderValuePanel(run.response, "endpoint response") + '</div>';
      }

      function operationSpecForNode(node) {
        const normalizedPath = normalizeOperationPath(node.path);
        return endpointOperationSpecs.find((spec) =>
          spec.method === node.method &&
          (spec.path === node.path || normalizeOperationPath(spec.path) === normalizedPath)
        ) || null;
      }

      function normalizeOperationPath(path) {
        return String(path || "").replace(/\\{[^}]+\\}/g, "{}");
      }

      function defaultEndpointParamValue(param, node) {
        const name = String(param.name || "").toLowerCase();
        if (name === "type") return param.example || param.default || "";
        if (name.includes("id") || name.includes("request")) {
          return state.selectedId || getRequestId(state.logs[0]) || cleanDefaultValue(param.example || param.default);
        }
        return cleanDefaultValue(param.example || param.default);
      }

      function cleanDefaultValue(value) {
        const text = value === undefined || value === null ? "" : String(value);
        return text.startsWith("paste-") ? "" : text;
      }

      function defaultEndpointBody(node, spec) {
        if (node.method === "GET" || node.method === "HEAD") return undefined;
        if (node.method === "POST" && node.path === "/api/api_key/activity") return buildListLogsBody();
        if (spec && spec.requestBodyExample !== undefined) return spec.requestBodyExample;
        return {};
      }

      function isEndpointSafeToRun(node) {
        return Boolean(node.safeAutoRun || (node.method === "POST" && node.path === "/api/api_key/activity"));
      }

      function relatedEndpointNodes(node) {
        const ids = new Set();
        for (const edge of apiGraph.edges) {
          if (edge.relation === "namespace") continue;
          if (edge.from === node.id) ids.add(edge.to);
          if (edge.to === node.id) ids.add(edge.from);
        }
        if (apiGraph.scope === "all" && !ids.size) {
          return apiGraph.nodes
            .filter((item) => item.id !== node.id && (item.group || "/") === (node.group || "/"))
            .sort((left, right) => left.path.localeCompare(right.path));
        }
        return apiGraph.nodes
          .filter((item) => ids.has(item.id))
          .sort((left, right) => (left.group || "").localeCompare(right.group || "") || left.path.localeCompare(right.path));
      }

      function countBy(values, keyFn) {
        const counts = {};
        for (const value of values) {
          const key = keyFn(value);
          counts[key] = (counts[key] || 0) + 1;
        }
        return counts;
      }

      function statBox(label, value) {
        return '<div class="stat-box"><span>' + escapeHtml(label) + '</span><strong title="' + escapeAttr(value) + '">' + escapeHtml(value) + '</strong></div>';
      }

      function endpointKindLabel(kind) {
        return { get: "GET", post: "POST", mutation: "Write", danger: "Risk" }[kind] || kind;
      }

      function renderDenseGraph(board) {
        board.classList.add("dense-graph");
        const width = Math.max(900, board.clientWidth || 1100);
        const height = Math.max(460, board.clientHeight || 520);
        const scopedNodes = apiGraph.nodes.filter((node) => !state.graph.namespace || (node.group || "/") === state.graph.namespace);
        const groupedNodes = [...groupBy(scopedNodes, (node) => node.group || "/").entries()]
          .sort((left, right) => right[1].length - left[1].length || left[0].localeCompare(right[0]));
        const groupNames = groupedNodes.map(([group]) => group);
        const groupLayouts = denseGroupLayouts(groupedNodes, width, height);
        const targetRoot = {
          id: "target:" + targetHost,
          label: targetHost,
          method: "ROOT",
          group: targetHost,
          role: "target-root",
          _type: "target-root",
          count: apiGraph.nodes.length,
          x: 18,
          y: 15,
          anchorX: 18,
          anchorY: 15,
          fx: 18,
          fy: 15
        };
        const namespaceRoots = [];
        const endpointNodes = [];

        for (const [group, groupNodes] of groupedNodes) {
          const layout = groupLayouts.get(group) || { x: width / 2, y: height / 2, radius: 54 };
          const rootId = "namespace:" + group;
          namespaceRoots.push({
            id: rootId,
            label: group,
            method: "GROUP",
            group,
            role: "namespace-root",
            _type: "namespace",
            count: groupNodes.length,
            x: (layout.x0 + layout.x1) / 2,
            y: (layout.y0 + layout.y1) / 2,
            anchorX: (layout.x0 + layout.x1) / 2,
            anchorY: (layout.y0 + layout.y1) / 2,
            labelAngle: layout.angle,
            radius: layout.radius,
            x0: layout.x0,
            y0: layout.y0,
            x1: layout.x1,
            y1: layout.y1
          });
          const sortedGroupNodes = [...groupNodes].sort((left, right) => left.path.localeCompare(right.path));
          sortedGroupNodes.forEach((node, index) => {
            const position = denseEndpointPosition(index, sortedGroupNodes.length, layout);
            endpointNodes.push({
              ...node,
              _type: "endpoint",
              x: position.x,
              y: position.y,
              anchorX: layout.x,
              anchorY: layout.y,
              rootId,
              groupSize: groupNodes.length
            });
          });
        }

        const nodes = [targetRoot, ...namespaceRoots, ...endpointNodes];
        const renderNodes = endpointNodes;
        const nodeIds = new Set(nodes.map((node) => node.id));
        const nodeById = new Map(nodes.map((node) => [node.id, node]));
        const topologyLinks = namespaceRoots.map((node) => ({
          id: targetRoot.id + "-to-" + node.id,
          source: targetRoot.id,
          target: node.id,
          relation: "target-namespace",
          _type: "topology"
        }));
        const membershipLinks = endpointNodes.map((node) => ({
          id: node.rootId + "-to-" + node.id,
          source: node.rootId,
          target: node.id,
          relation: "namespace-endpoint",
          _type: "membership"
        }));
        const dependencyLinks = apiGraph.edges
          .map((edge) => ({
            ...edge,
            source: edge.from,
            target: edge.to,
            relation: edge.relation || "dependency",
            _type: "dependency"
          }))
          .filter((edge) => edge.relation !== "namespace");
        const links = [
          ...topologyLinks,
          ...membershipLinks,
          ...dependencyLinks
        ]
          .filter((edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target))
          .map((edge) => ({ ...edge, source: nodeById.get(edge.source), target: nodeById.get(edge.target) }));
        const neighbors = new Map(nodes.map((node) => [node.id, new Set([node.id])]));
        const dependencyNeighbors = new Map(nodes.map((node) => [node.id, new Set([node.id])]));
        for (const edge of links) {
          neighbors.get(edge.source.id)?.add(edge.target.id);
          neighbors.get(edge.target.id)?.add(edge.source.id);
          if (edge._type === "dependency") {
            dependencyNeighbors.get(edge.source.id)?.add(edge.target.id);
            dependencyNeighbors.get(edge.target.id)?.add(edge.source.id);
          }
        }
        const visibleLinks = links.filter((edge) => edge._type === "dependency");
        targetRoot.fx = null;
        targetRoot.fy = null;

        board.innerHTML = '<svg aria-label="API dependency graph"></svg><div class="graph-tooltip" hidden></div>';
        const svg = d3.select(board).select("svg").attr("viewBox", [0, 0, width, height]);
        svg.append("defs").append("marker")
          .attr("id", "dense-arrow")
          .attr("viewBox", "0 -5 10 10")
          .attr("refX", 9)
          .attr("refY", 0)
          .attr("markerWidth", 6)
          .attr("markerHeight", 6)
          .attr("orient", "auto")
          .append("path")
          .attr("d", "M0,-4L9,0L0,4")
          .attr("fill", "#496274");
        svg.select("defs").append("marker")
          .attr("id", "dense-arrow-muted")
          .attr("viewBox", "0 -5 10 10")
          .attr("refX", 8)
          .attr("refY", 0)
          .attr("markerWidth", 4)
          .attr("markerHeight", 4)
          .attr("orient", "auto")
          .append("path")
          .attr("d", "M0,-3.5L8,0L0,3.5")
          .attr("fill", "#6d858c")
          .attr("opacity", "0.56");
        const root = svg.append("g");
        svg.call(
          d3.zoom()
            .scaleExtent([0.35, 3.2])
            .on("zoom", (event) => root.attr("transform", event.transform))
        );
        const rootLabel = root.append("g")
          .datum(targetRoot)
          .attr("class", "dense-root-label")
          .attr("transform", "translate(16,16)")
          .on("mouseenter", (event, item) => {
            applyFocus(item);
            showTooltip(item, event, pinnedNode?.id === item.id);
          })
          .on("mousemove", (event, item) => showTooltip(item, event, pinnedNode?.id === item.id))
          .on("mouseleave", () => {
            applyFocus(pinnedNode);
            if (pinnedNode) showTooltip(pinnedNode, null, true);
            else hideTooltip();
          })
          .on("click", handleItemClick);
        rootLabel.append("text").text(targetHost + " API root");
        let pinnedNode = nodes.find((item) =>
          item.id === state.graph.selectedNodeId ||
          (state.graph.selectedNamespace && item._type === "namespace" && item.group === state.graph.selectedNamespace) ||
          (state.graph.selectedRoot && item._type === "target-root")
        ) || null;

        const cell = root.append("g")
          .selectAll("g")
          .data(namespaceRoots)
          .join("g")
          .attr("class", "dense-cell")
          .on("mouseenter", (event, item) => {
            applyFocus(item);
            showTooltip(item, event, pinnedNode?.id === item.id);
          })
          .on("mousemove", (event, item) => showTooltip(item, event, pinnedNode?.id === item.id))
          .on("mouseleave", () => {
            applyFocus(pinnedNode);
            if (pinnedNode) showTooltip(pinnedNode, null, true);
            else hideTooltip();
          })
          .on("click", handleItemClick);

        cell.append("title")
          .text((item) => item.group + " (" + item.count + " endpoints)");

        cell.append("rect")
          .attr("x", (item) => item.x0)
          .attr("y", (item) => item.y0)
          .attr("width", (item) => Math.max(0, item.x1 - item.x0))
          .attr("height", (item) => Math.max(0, item.y1 - item.y0))
          .attr("rx", 8)
          .attr("ry", 8);

        cell.append("text")
          .attr("x", (item) => item.x0 + 10)
          .attr("y", (item) => item.y0 + 18)
          .text(denseGroupLabel);

        const link = root.append("g")
          .selectAll("path")
          .data(visibleLinks)
          .join("path")
          .attr("class", (edge) => "dense-link " + cssToken(edge.relation) + " " + (edge._type === "dependency" ? "dependency-link" : "tree-link") + " " + (denseLinkCrossesGroup(edge) ? "cross-group" : "same-group"))
          .attr("marker-end", (edge) => edge._type === "dependency" ? (denseLinkCrossesGroup(edge) ? "url(#dense-arrow-muted)" : "url(#dense-arrow)") : null);

        const node = root.append("g")
          .selectAll("g")
          .data(renderNodes)
          .join("g")
          .attr("class", (item) => "dense-node " + cssToken(item.role) + " " + graphNodeKind(item))
          .on("mouseenter", (event, item) => {
            applyFocus(item);
            showTooltip(item, event, pinnedNode?.id === item.id);
          })
          .on("mousemove", (event, item) => showTooltip(item, event, pinnedNode?.id === item.id))
          .on("mouseleave", () => {
            applyFocus(pinnedNode);
            if (pinnedNode) {
              showTooltip(pinnedNode, null, true);
            } else {
              hideTooltip();
            }
          })
          .on("click", handleItemClick)
          .call(
            d3.drag()
              .on("drag", (event, item) => {
                if (item._type === "namespace") {
                  const members = nodes.filter((candidate) => candidate.group === item.group && candidate._type !== "target-root");
                  for (const member of members) {
                    member.x = clamp(member.x + event.dx, 18, width - 18);
                    member.y = clamp(member.y + event.dy, 18, height - 18);
                  }
                } else {
                  item.x = clamp(event.x, 18, width - 18);
                  item.y = clamp(event.y, 18, height - 18);
                }
                ticked();
                applyFocus(item);
                showTooltip(item, event, pinnedNode?.id === item.id);
              })
          );

        node.filter((item) => item._type === "namespace" || item._type === "target-root")
          .append("circle")
          .attr("class", "root-halo")
          .attr("r", (item) => item._type === "target-root" ? 11 : Math.max(14, Math.min(30, String(item.group || "").length * 2.2)));

        node.append("circle")
          .attr("r", denseNodeRadius)
          .attr("fill", denseNodeColor);

        node.append("text")
          .attr("text-anchor", denseTextAnchor)
          .attr("x", denseTextX)
          .attr("y", denseTextY)
          .text((item) => item._type === "target-root"
            ? item.label
            : item._type === "namespace"
              ? item.group + " (" + item.count + ")"
              : truncateMiddle(item.label, 28));

        svg.on("click", () => {
          pinnedNode = null;
          state.graph.selectedNodeId = null;
          state.graph.selectedNamespace = state.graph.namespace;
          state.graph.selectedRoot = false;
          applyFocus(null);
          renderEndpointInspector();
          hideTooltip();
        });
        ticked();
        applyFocus(pinnedNode);

        function ticked() {
          nodes.forEach((item) => {
            item.x = clamp(item.x, 18, width - 18);
            item.y = clamp(item.y, item._type === "target-root" ? 24 : 18, height - 18);
          });
          link.attr("d", denseLinkPath);
          node.attr("transform", (item) => "translate(" + item.x + "," + item.y + ")");
        }

        function handleItemClick(event, item) {
          event.stopPropagation();
          if (item._type === "namespace") {
            enterGraphNamespace(item.group);
            return;
          }
          if (item._type === "target-root") {
            enterGraphRoot({ selected: true });
            return;
          }
          pinnedNode = pinnedNode?.id === item.id ? null : item;
          state.graph.selectedNodeId = pinnedNode?._type === "endpoint" ? pinnedNode.id : null;
          state.graph.selectedNamespace = pinnedNode?._type === "namespace" ? pinnedNode.group : "";
          state.graph.selectedRoot = pinnedNode?._type === "target-root";
          renderEndpointInspector();
          if (pinnedNode) {
            applyFocus(pinnedNode);
            showTooltip(pinnedNode, event, true);
            if (item._type === "endpoint") {
              focusGraphNode(item.id);
            } else if (item._type === "namespace") {
              setEvent("Namespace " + item.group + " contains " + item.count + " endpoints.");
            } else {
              setEvent(targetHost + " contains " + apiGraph.nodes.length + " endpoints across " + groupNames.length + " namespaces.");
            }
          } else {
            applyFocus(null);
            hideTooltip();
          }
        }

        function applyFocus(activeNode) {
          const related = activeNode ? denseFocusSet(activeNode, nodes, neighbors, dependencyNeighbors, targetRoot.id) : null;
          const relatedCount = related ? related.size - 1 : 0;
          link
            .classed("is-neighbor", (edge) => Boolean(activeNode && denseLinkIsFocused(edge, activeNode, related)))
            .classed("is-dim", (edge) => Boolean(activeNode && !denseLinkIsFocused(edge, activeNode, related)))
            .classed("is-filtered", (edge) => !visualNodeMatches(edge.source) || !visualNodeMatches(edge.target));
          node
            .classed("is-active", (item) => Boolean(activeNode && item.id === activeNode.id))
            .classed("is-neighbor", (item) => Boolean(activeNode && item.id !== activeNode.id && related.has(item.id)))
            .classed("is-dim", (item) => Boolean(activeNode && !related.has(item.id)))
            .classed("is-filtered", (item) => !visualNodeMatches(item))
            .classed("label-visible", (item) => Boolean(activeNode && item._type === "endpoint" && (item.id === activeNode.id || (relatedCount <= 16 && related.has(item.id)))));
          cell
            .classed("is-active", (item) => Boolean(activeNode && item.id === activeNode.id))
            .classed("is-neighbor", (item) => Boolean(activeNode && item.id !== activeNode.id && related.has(item.id)))
            .classed("is-dim", (item) => Boolean(activeNode && !related.has(item.id) && activeNode._type !== "target-root"))
            .classed("is-filtered", (item) => !visualNodeMatches(item));
          rootLabel
            .classed("is-active", () => Boolean(activeNode && activeNode._type === "target-root"))
            .classed("is-filtered", () => !visualNodeMatches(targetRoot));
        }

        function showTooltip(item, event, pinned) {
          const tooltip = board.querySelector(".graph-tooltip");
          tooltip.hidden = false;
          tooltip.innerHTML = denseTooltipHtml(item, (neighbors.get(item.id)?.size || 1) - 1, pinned);
          const rect = board.getBoundingClientRect();
          const rawX = event ? event.clientX - rect.left + 14 : item.x + 14;
          const rawY = event ? event.clientY - rect.top + 14 : item.y + 14;
          const maxX = Math.max(8, board.clientWidth - tooltip.offsetWidth - 8);
          const maxY = Math.max(8, board.clientHeight - tooltip.offsetHeight - 8);
          tooltip.style.left = clamp(rawX, 8, maxX) + "px";
          tooltip.style.top = clamp(rawY, 8, maxY) + "px";
        }

        function hideTooltip() {
          const tooltip = board.querySelector(".graph-tooltip");
          if (tooltip) tooltip.hidden = true;
        }
      }

      function renderForceGraph(board) {
        board.classList.remove("dense-graph");
        const width = Math.max(960, board.clientWidth || 960);
        const height = Math.max(300, board.clientHeight || 312);
        const nodeWidth = 190;
        const nodeHeight = 76;
        const nodes = apiGraph.nodes.map((node) => {
          const anchor = graphAnchor(node, width, height);
          return {
            ...node,
            x: anchor.x,
            y: anchor.y,
            fx: node.id === "listLogs" ? anchor.x : undefined,
            fy: node.id === "listLogs" ? anchor.y : undefined,
            anchorX: anchor.x,
            anchorY: anchor.y,
            w: nodeWidth,
            h: nodeHeight
          };
        });
        const links = apiGraph.edges
          .filter((edge) => nodes.some((node) => node.id === edge.from) && nodes.some((node) => node.id === edge.to))
          .map((edge) => ({ ...edge, source: edge.from, target: edge.to }));

        board.innerHTML = '<svg aria-label="API dependency graph"></svg>';
        const svg = d3.select(board).select("svg").attr("viewBox", [0, 0, width, height]);
        const root = svg.append("g");
        svg.call(
          d3.zoom()
            .scaleExtent([0.65, 2.4])
            .on("zoom", (event) => root.attr("transform", event.transform))
        );
        svg.append("defs").append("marker")
          .attr("id", "force-arrow")
          .attr("viewBox", "0 -5 10 10")
          .attr("refX", 8)
          .attr("refY", 0)
          .attr("markerWidth", 8)
          .attr("markerHeight", 8)
          .attr("orient", "auto")
          .append("path")
          .attr("d", "M0,-5L10,0L0,5")
          .attr("fill", "#547a6b");

        const link = root.append("g")
          .selectAll("path")
          .data(links)
          .join("path")
          .attr("class", (edge) => "graph-link " + edge.relation)
          .attr("marker-end", "url(#force-arrow)");

        const edgeLabel = root.append("g")
          .selectAll("text")
          .data(links)
          .join("text")
          .attr("class", "graph-edge-label")
          .attr("text-anchor", "middle")
          .text((edge) => compactEdgeLabel(edge));

        const card = root.append("g")
          .selectAll("g")
          .data(nodes)
          .join("g")
          .attr("class", (node) => "graph-card " + node.role)
          .on("click", (_, node) => focusGraphNode(node.id))
          .call(
            d3.drag()
              .on("start", dragStarted)
              .on("drag", dragged)
              .on("end", dragEnded)
          );

        card.append("rect")
          .attr("class", "node-box")
          .attr("x", -nodeWidth / 2)
          .attr("y", -nodeHeight / 2)
          .attr("width", nodeWidth)
          .attr("height", nodeHeight)
          .attr("rx", 8)
          .attr("ry", 8);

        card.append("rect")
          .attr("class", "graph-method-bg")
          .attr("x", -nodeWidth / 2 + 12)
          .attr("y", -nodeHeight / 2 + 11)
          .attr("width", 48)
          .attr("height", 21)
          .attr("rx", 5);

        card.append("text")
          .attr("class", "graph-method")
          .attr("x", -nodeWidth / 2 + 20)
          .attr("y", -nodeHeight / 2 + 26)
          .text((node) => node.method);

        card.append("text")
          .attr("class", "graph-label")
          .attr("x", -nodeWidth / 2 + 12)
          .attr("y", -nodeHeight / 2 + 51)
          .text((node) => node.label);

        card.append("text")
          .attr("class", "graph-path")
          .attr("x", -nodeWidth / 2 + 12)
          .attr("y", -nodeHeight / 2 + 68)
          .text((node) => truncateMiddle(node.path, 26));

        const simulation = d3.forceSimulation(nodes)
          .force("link", d3.forceLink(links).id((node) => node.id).distance((edge) => edge.relation.includes("filter") ? 250 : 310).strength(0.56))
          .force("charge", d3.forceManyBody().strength(-620))
          .force("collide", d3.forceCollide().radius(118).strength(0.9).iterations(3))
          .force("x", d3.forceX((node) => node.anchorX).strength(0.42))
          .force("y", d3.forceY((node) => node.anchorY).strength(0.3))
          .on("tick", ticked);

        for (let i = 0; i < 140; i += 1) simulation.tick();
        ticked();
        simulation.alpha(0.18).restart();

        function ticked() {
          nodes.forEach((node) => {
            node.x = clamp(node.x, nodeWidth / 2 + 18, width - nodeWidth / 2 - 18);
            node.y = clamp(node.y, nodeHeight / 2 + 16, height - nodeHeight / 2 - 16);
          });
          link.attr("d", (edge) => curvedEdgePath(edge, nodeWidth, nodeHeight));
          edgeLabel
            .attr("x", (edge) => (edge.source.x + edge.target.x) / 2)
            .attr("y", (edge) => (edge.source.y + edge.target.y) / 2 - 10);
          card
            .classed("selected", (node) => node.id === "listLogs" && !state.selectedId)
            .attr("transform", (node) => "translate(" + node.x + "," + node.y + ")");
        }

        function dragStarted(event, node) {
          if (!event.active) simulation.alphaTarget(0.22).restart();
          node.fx = node.x;
          node.fy = node.y;
        }

        function dragged(event, node) {
          node.fx = clamp(event.x, nodeWidth / 2 + 18, width - nodeWidth / 2 - 18);
          node.fy = clamp(event.y, nodeHeight / 2 + 16, height - nodeHeight / 2 - 16);
        }

        function dragEnded(event, node) {
          if (!event.active) simulation.alphaTarget(0);
          if (node.id !== "listLogs") {
            node.fx = null;
            node.fy = null;
          }
        }
      }

      function renderGraphFallback(board) {
        if (isDenseGraph()) {
          renderDenseGraphFallback(board);
          return;
        }
        board.classList.remove("dense-graph");
        const width = 960;
        const height = 312;
        const nodesById = Object.fromEntries(apiGraph.nodes.map((node) => [node.id, node]));
        const edgeSvg = apiGraph.edges.map((edge) => {
          const from = nodesById[edge.from];
          const to = nodesById[edge.to];
          if (!from || !to) return "";
          const fromAnchor = graphAnchor(from, width, height);
          const toAnchor = graphAnchor(to, width, height);
          const x1 = fromAnchor.x + 94;
          const y1 = fromAnchor.y;
          const x2 = toAnchor.x - 94;
          const y2 = toAnchor.y;
          return '<path class="graph-link ' + escapeAttr(edge.relation) + '" d="M ' + x1 + ' ' + y1 + ' C ' + (x1 + 68) + ' ' + y1 + ', ' + (x2 - 68) + ' ' + y2 + ', ' + x2 + ' ' + y2 + '" marker-end="url(#force-arrow)" />';
        }).join("");
        board.innerHTML =
          '<svg viewBox="0 0 ' + width + ' ' + height + '" aria-hidden="true">' +
          '<defs><marker id="force-arrow" viewBox="0 -5 10 10" refX="8" refY="0" markerWidth="8" markerHeight="8" orient="auto"><path d="M0,-5L10,0L0,5" fill="#547a6b" /></marker></defs>' +
          edgeSvg +
          '</svg>';
      }

      function renderDenseGraphFallback(board) {
        board.classList.add("dense-graph");
        const width = 1100;
        const height = 560;
        const groupedNodes = [...groupBy(apiGraph.nodes, (node) => node.group || "/").entries()]
          .sort((left, right) => right[1].length - left[1].length || left[0].localeCompare(right[0]));
        const groupNames = groupedNodes.map(([group]) => group);
        const groupIndex = new Map(groupNames.map((group, index) => [group, index]));
        const groupAnchors = denseGroupAnchors(groupNames, width, height);
        const palette = ["#2470a0", "#2a9d8f", "#8f6ab7", "#d58512", "#607d3b", "#b55452", "#4d7c8a", "#936639", "#5865a8", "#b0648f", "#697b30", "#5f6f7d", "#356a8a"];
        const nodes = [];
        for (const [group, groupNodes] of groupedNodes) {
          const anchor = groupAnchors.get(group) || { x: width / 2, y: height / 2 };
          const spread = Math.min(74, 20 + Math.sqrt(groupNodes.length) * 10);
          groupNodes.forEach((node, index) => {
            const angle = (Math.PI * 2 * index) / Math.max(1, groupNodes.length);
            nodes.push({
              ...node,
              x: anchor.x + Math.cos(angle) * spread,
              y: anchor.y + Math.sin(angle) * spread
            });
          });
        }
        const nodeById = new Map(nodes.map((node) => [node.id, node]));
        const edgeSvg = apiGraph.edges.map((edge) => {
          const from = nodeById.get(edge.from);
          const to = nodeById.get(edge.to);
          if (!from || !to) return "";
          return '<line class="dense-link ' + escapeAttr(cssToken(edge.relation)) + '" x1="' + from.x + '" y1="' + from.y + '" x2="' + to.x + '" y2="' + to.y + '" />';
        }).join("");
        const labelSvg = groupedNodes.map(([group, groupNodes]) => {
          const position = denseGroupLabelPosition(group, nodes, width, height);
          return '<text class="dense-group-label" text-anchor="middle" x="' + position.x + '" y="' + position.y + '">' + escapeHtml(group) + ' (' + groupNodes.length + ')</text>';
        }).join("");
        const nodeSvg = nodes.map((node) =>
          '<g class="dense-node ' + escapeAttr(cssToken(node.role)) + ' ' + escapeAttr(graphNodeKind(node)) + '" transform="translate(' + node.x + ',' + node.y + ')">' +
            '<title>' + escapeHtml(node.method + " " + node.path) + '</title>' +
            '<circle r="' + denseNodeRadius(node) + '" fill="' + escapeAttr(denseNodeColor(node, groupIndex, palette)) + '" />' +
            '<text x="' + (denseNodeRadius(node) + 7) + '" y="4">' + escapeHtml(truncateMiddle(node.label, 28)) + '</text>' +
          '</g>'
        ).join("");
        board.innerHTML =
          '<svg viewBox="0 0 ' + width + ' ' + height + '" aria-label="API dependency graph">' +
            edgeSvg +
            labelSvg +
            nodeSvg +
          '</svg>';
      }

      function runDenseSimulation(nodes, links, width, height) {
        const simulation = d3.forceSimulation(nodes)
          .force("link", d3.forceLink(links)
            .distance((edge) => denseLinkDistance(edge, width, height))
            .strength(denseLinkStrength)
            .iterations(2))
          .force("charge", d3.forceManyBody().strength((node) => {
            if (node._type === "target-root") return 0;
            if (node._type === "namespace") return -260;
            return -24;
          }))
          .force("collide", d3.forceCollide().radius((node) => {
            if (node._type === "target-root") return 10;
            if (node._type === "namespace") return Math.max(30, 16 + String(node.group || "").length * 1.8);
            return denseNodeRadius(node) + 10;
          }).strength(0.94).iterations(4))
          .force("x", d3.forceX((node) => node.anchorX || width / 2).strength((node) => {
            if (node._type === "target-root") return 1;
            if (node._type === "namespace") return 0.18;
            return 0.05;
          }))
          .force("y", d3.forceY((node) => node.anchorY || height / 2).strength((node) => {
            if (node._type === "target-root") return 1;
            if (node._type === "namespace") return 0.18;
            return 0.05;
          }))
          .force("center", d3.forceCenter(width / 2, height / 2))
          .stop();

        for (let index = 0; index < 620; index += 1) simulation.tick();
      }

      function denseLinkDistance(edge, width, height) {
        if (edge.relation === "target-namespace") return Math.max(190, Math.min(width, height) * 0.3);
        if (edge.relation === "namespace-endpoint") return 52 + Math.min(42, (edge.target.groupSize || 1) * 0.65);
        if (edge.relation === "fanout-payload") return 150;
        if (edge.relation === "fanout-detail" || edge.relation === "fanout-metadata") return 154;
        if (edge.relation === "filter-dependency") return 176;
        if (edge.relation === "resource-action") return 112;
        if (edge.relation === "semantic-dependency") return 196;
        return 136;
      }

      function denseLinkStrength(edge) {
        if (edge.relation === "target-namespace") return 0.025;
        if (edge.relation === "namespace-endpoint") return 0.11;
        if (edge.relation === "fanout-payload" || edge.relation === "fanout-detail") return 0.72;
        if (edge.relation === "fanout-metadata") return 0.62;
        if (edge.relation === "filter-dependency") return 0.5;
        if (edge.relation === "resource-action") return 0.36;
        if (edge.relation === "semantic-dependency") return 0.25;
        return 0.5;
      }

      function fitDenseNodes(nodes, width, height) {
        const measuredNodes = nodes.filter((node) => node._type !== "target-root");
        if (!measuredNodes.length) return;
        const padding = 64;
        const xs = measuredNodes.map((node) => node.x);
        const ys = measuredNodes.map((node) => node.y);
        const minX = Math.min(...xs);
        const maxX = Math.max(...xs);
        const minY = Math.min(...ys);
        const maxY = Math.max(...ys);
        const graphWidth = Math.max(1, maxX - minX);
        const graphHeight = Math.max(1, maxY - minY);
        const scale = Math.min(
          1.16,
          (width - padding * 2) / graphWidth,
          (height - padding * 2) / graphHeight
        );
        const sourceCenterX = (minX + maxX) / 2;
        const sourceCenterY = (minY + maxY) / 2;
        const targetCenterX = width / 2;
        const targetCenterY = height / 2;
        for (const node of nodes) {
          node.x = targetCenterX + (node.x - sourceCenterX) * scale;
          node.y = targetCenterY + (node.y - sourceCenterY) * scale;
        }
      }

      function denseGroupLayouts(groupedNodes, width, height) {
        const layouts = new Map();
        const root = d3.hierarchy({
          name: targetHost,
          children: groupedNodes.map(([group, nodes]) => ({
            name: group,
            value: Math.max(1, nodes.length),
            count: nodes.length
          }))
        })
          .sum((node) => node.value || 0)
          .sort((left, right) => right.value - left.value || left.data.name.localeCompare(right.data.name));

        d3.treemap()
          .tile(d3.treemapSquarify.ratio(1.25))
          .size([width, height])
          .paddingOuter(14)
          .paddingTop(24)
          .paddingInner(10)
          .round(true)(root);

        for (const leaf of root.leaves()) {
          const group = leaf.data.name;
          const nodes = groupedNodes.find(([name]) => name === group)?.[1] || [];
          const centerX = (leaf.x0 + leaf.x1) / 2;
          const centerY = (leaf.y0 + leaf.y1) / 2;
          const angle = Math.atan2(centerY - height / 2, centerX - width / 2);
          layouts.set(group, {
            x: centerX,
            y: centerY,
            x0: leaf.x0,
            y0: leaf.y0,
            x1: leaf.x1,
            y1: leaf.y1,
            angle,
            radius: Math.max(20, Math.min(48, Math.sqrt((leaf.x1 - leaf.x0) * (leaf.y1 - leaf.y0)) * 0.08)),
            count: nodes.length
          });
        }
        return layouts;
      }

      function denseGroupSlots(count, width, height) {
        const columns = Math.max(3, Math.ceil(Math.sqrt(count * width / Math.max(1, height))));
        const rows = Math.max(1, Math.ceil(count / columns));
        const left = Math.max(92, width * 0.1);
        const right = width - left;
        const top = Math.max(78, height * 0.15);
        const bottom = height - Math.max(82, height * 0.12);
        const slots = [];
        for (let row = 0; row < rows; row += 1) {
          const rowCount = Math.min(columns, count - row * columns);
          const rowInset = rowCount < columns ? (columns - rowCount) * 0.5 : 0;
          for (let column = 0; column < rowCount; column += 1) {
            const xRatio = (column + rowInset + 0.5) / columns;
            const yRatio = rows === 1 ? 0.5 : row / (rows - 1);
            slots.push({
              x: left + (right - left) * xRatio,
              y: top + (bottom - top) * yRatio
            });
          }
        }
        return slots;
      }

      function fitDenseGroupNodes(nodes, width, height) {
        if (!nodes.length) return;
        const padding = 90;
        const minX = Math.min(...nodes.map((node) => node.x - node.radius));
        const maxX = Math.max(...nodes.map((node) => node.x + node.radius));
        const minY = Math.min(...nodes.map((node) => node.y - node.radius));
        const maxY = Math.max(...nodes.map((node) => node.y + node.radius));
        const graphWidth = Math.max(1, maxX - minX);
        const graphHeight = Math.max(1, maxY - minY);
        const scale = Math.min(
          1.18,
          (width - padding * 2) / graphWidth,
          (height - padding * 2) / graphHeight
        );
        const sourceCenterX = (minX + maxX) / 2;
        const sourceCenterY = (minY + maxY) / 2;
        for (const node of nodes) {
          node.x = width / 2 + (node.x - sourceCenterX) * scale;
          node.y = height / 2 + (node.y - sourceCenterY) * scale;
        }
      }

      function denseRelationWeight(relation) {
        return {
          "fanout-payload": 3.2,
          "fanout-detail": 2.4,
          "fanout-metadata": 2.2,
          "filter-dependency": 1.8,
          "detail-dependency": 1.2,
          "resource-action": 0.9,
          "semantic-dependency": 0.7
        }[relation] || 1;
      }

      function denseEndpointPosition(index, count, layout) {
        const pad = 13;
        const header = 26;
        const x0 = layout.x0 + pad;
        const y0 = layout.y0 + header;
        const x1 = layout.x1 - pad;
        const y1 = layout.y1 - pad;
        const innerWidth = Math.max(1, x1 - x0);
        const innerHeight = Math.max(1, y1 - y0);
        const columns = Math.max(1, Math.ceil(Math.sqrt(count * innerWidth / Math.max(1, innerHeight))));
        const rows = Math.max(1, Math.ceil(count / columns));
        const column = index % columns;
        const row = Math.floor(index / columns);
        return {
          x: x0 + ((column + 0.5) / columns) * innerWidth,
          y: y0 + ((row + 0.5) / rows) * innerHeight
        };
      }

      function denseGroupAnchors(groupNames, width, height) {
        const anchors = new Map();
        const columns = Math.max(1, Math.ceil(Math.sqrt(groupNames.length * width / Math.max(1, height))));
        const rows = Math.max(1, Math.ceil(groupNames.length / columns));
        const xMargin = Math.min(170, Math.max(96, width * 0.08));
        const yMargin = Math.min(118, Math.max(74, height * 0.12));
        groupNames.forEach((group, index) => {
          const column = index % columns;
          const row = Math.floor(index / columns);
          const cellWidth = (width - xMargin * 2) / Math.max(1, columns - 1);
          const cellHeight = (height - yMargin * 2) / Math.max(1, rows - 1);
          anchors.set(group, {
            x: columns === 1 ? width / 2 : xMargin + cellWidth * column,
            y: rows === 1 ? height / 2 : yMargin + cellHeight * row
          });
        });
        return anchors;
      }

      function denseGroupLabelPosition(group, nodes, width, height) {
        const groupNodes = nodes.filter((node) => (node.group || "/") === group);
        if (!groupNodes.length) return { x: width / 2, y: 24 };
        const xs = groupNodes.map((node) => node.x);
        const ys = groupNodes.map((node) => node.y);
        const minX = Math.min(...xs);
        const maxX = Math.max(...xs);
        const minY = Math.min(...ys);
        const maxY = Math.max(...ys);
        const x = clamp((minX + maxX) / 2, 76, width - 76);
        const aboveY = minY - 18;
        const belowY = maxY + 24;
        const y = aboveY >= 22 ? aboveY : belowY;
        return {
          x,
          y: clamp(y, 22, height - 22)
        };
      }

      function denseNodeRadius(node) {
        if (node._type === "target-root") return 5.8;
        if (node._type === "namespace") return 6.2;
        if (node.role === "mutation-danger") return 5.8;
        if (node.role === "mutation") return 5.4;
        if (node.method === "GET") return 4.4;
        return 4.8;
      }

      function denseNodeColor(node) {
        if (node._type === "target-root") return "#101820";
        if (node._type === "namespace") return "#ffffff";
        return {
          get: "#2470a0",
          post: "#2a9d8f",
          mutation: "#b67816",
          danger: "#c54a4a"
        }[graphNodeKind(node)] || "#5f6f7d";
      }

      function denseTextAnchor(node) {
        if (node._type === "endpoint") return "start";
        if (node._type === "target-root") return "middle";
        const x = Math.cos(node.labelAngle || 0);
        if (x > 0.35) return "start";
        if (x < -0.35) return "end";
        return "middle";
      }

      function denseTextX(node) {
        if (node._type === "endpoint") return denseNodeRadius(node) + 7;
        if (node._type === "target-root") return 0;
        const distance = (node.radius || 34) + 22;
        return Math.cos(node.labelAngle || 0) * distance;
      }

      function denseTextY(node) {
        if (node._type === "endpoint") return 4;
        if (node._type === "target-root") return 21;
        const distance = (node.radius || 34) + 22;
        return Math.sin(node.labelAngle || 0) * distance + 3;
      }

      function denseTooltipHtml(node, neighborCount, pinned) {
        if (node._type === "target-root") {
          return '<div class="tip-head">' +
            '<span class="tip-method">ROOT</span>' +
            '<span class="tip-title">' + escapeHtml(node.label) + '</span>' +
          '</div>' +
          '<div class="tip-path">' + apiGraph.nodes.length + ' endpoints across ' + new Set(apiGraph.nodes.map((item) => item.group).filter(Boolean)).size + ' namespaces</div>' +
          '<div class="tip-meta">' +
            '<span class="tip-pill">target</span>' +
            '<span class="tip-pill">' + neighborCount + ' namespaces</span>' +
            (pinned ? '<span class="tip-pill">pinned</span>' : '') +
          '</div>';
        }
        if (node._type === "namespace") {
          return '<div class="tip-head">' +
            '<span class="tip-method">GROUP</span>' +
            '<span class="tip-title">' + escapeHtml(node.group) + '</span>' +
          '</div>' +
          '<div class="tip-path">' + node.count + ' endpoints under ' + escapeHtml(node.group) + '</div>' +
          '<div class="tip-meta">' +
            '<span class="tip-pill">namespace</span>' +
            '<span class="tip-pill">' + neighborCount + ' linked</span>' +
            (pinned ? '<span class="tip-pill">pinned</span>' : '') +
          '</div>';
        }
        return '<div class="tip-head">' +
          '<span class="tip-method">' + escapeHtml(node.method) + '</span>' +
          '<span class="tip-title" title="' + escapeAttr(node.label) + '">' + escapeHtml(node.label) + '</span>' +
        '</div>' +
        '<div class="tip-path">' + escapeHtml(node.path) + '</div>' +
        '<div class="tip-meta">' +
          '<span class="tip-pill">' + escapeHtml(node.group || "/") + '</span>' +
          '<span class="tip-pill">' + escapeHtml(node.role || "endpoint") + '</span>' +
          '<span class="tip-pill">' + neighborCount + ' linked</span>' +
          (pinned ? '<span class="tip-pill">pinned</span>' : '') +
        '</div>';
      }

      function denseFocusSet(activeNode, nodes, neighbors, dependencyNeighbors, targetRootId) {
        const related = new Set([activeNode.id]);
        if (activeNode._type === "target-root") {
          for (const node of nodes) {
            if (node._type === "namespace" || node.id === targetRootId) related.add(node.id);
          }
          return related;
        }
        if (activeNode._type === "namespace") {
          for (const node of nodes) {
            if ((node.group || "/") === activeNode.group || node.id === targetRootId) related.add(node.id);
          }
          for (const node of nodes) {
            if ((node.group || "/") !== activeNode.group || node._type !== "endpoint") continue;
            for (const id of dependencyNeighbors.get(node.id) || []) related.add(id);
          }
          return related;
        }
        for (const id of dependencyNeighbors.get(activeNode.id) || []) related.add(id);
        if (related.size <= 1) {
          for (const id of neighbors.get(activeNode.id) || []) related.add(id);
        } else {
          for (const node of nodes) {
            if (node._type === "namespace" && node.group === activeNode.group) related.add(node.id);
          }
        }
        return related;
      }

      function denseLinkIsFocused(edge, activeNode, related) {
        const sourceId = denseLinkSourceId(edge);
        const targetId = denseLinkTargetId(edge);
        if (sourceId === activeNode.id || targetId === activeNode.id) return true;
        if (activeNode._type === "namespace") {
          return (edge.source.group === activeNode.group || edge.target.group === activeNode.group) &&
            (related.has(sourceId) || related.has(targetId));
        }
        if (activeNode._type === "target-root") {
          return edge.relation === "target-namespace";
        }
        return edge._type === "dependency" && related.has(sourceId) && related.has(targetId);
      }

      function denseLinkCrossesGroup(edge) {
        return edge._type === "dependency" &&
          edge.source &&
          edge.target &&
          edge.source.group &&
          edge.target.group &&
          edge.source.group !== edge.target.group;
      }

      function denseLinkPath(edge) {
        const x1 = edge.source.x;
        const y1 = edge.source.y;
        const x2 = edge.target.x;
        const y2 = edge.target.y;
        if (edge._type !== "dependency") {
          return "M" + x1 + "," + y1 + "L" + x2 + "," + y2;
        }
        const dx = x2 - x1;
        const dy = y2 - y1;
        const distance = Math.max(1, Math.sqrt(dx * dx + dy * dy));
        const curve = edge.source.group === edge.target.group ? 18 : Math.min(72, 24 + distance * 0.08);
        const normalX = -dy / distance;
        const normalY = dx / distance;
        const midX = (x1 + x2) / 2 + normalX * curve;
        const midY = (y1 + y2) / 2 + normalY * curve;
        return "M" + x1 + "," + y1 + "Q" + midX + "," + midY + " " + x2 + "," + y2;
      }

      function denseLinkSourceId(edge) {
        return typeof edge.source === "object" ? edge.source.id : edge.source;
      }

      function denseLinkTargetId(edge) {
        return typeof edge.target === "object" ? edge.target.id : edge.target;
      }

      function cssToken(value) {
        return String(value || "item").replace(/[^a-zA-Z0-9_-]+/g, "-");
      }

      function graphAnchor(node, width, height) {
        if (node.ui && Number.isFinite(node.ui.xRatio) && Number.isFinite(node.ui.yRatio)) {
          return {
            x: width * node.ui.xRatio,
            y: height * node.ui.yRatio
          };
        }
        if (node.ui && Number.isFinite(node.ui.x) && Number.isFinite(node.ui.y)) {
          return {
            x: width * clamp(node.ui.x / 960, 0.08, 0.92),
            y: height * clamp(node.ui.y / 312, 0.12, 0.88)
          };
        }
        const columns = {
          "root-list": 0.18,
          filter: 0.2,
          detail: 0.47,
          payload: 0.74
        };
        const rows = {
          listLogs: 0.48,
          listApiKeys: 0.78,
          getFinishReasons: 0.78,
          getLogActivity: 0.28,
          getLegacyGeneration: 0.56,
          getGenerationRequestPayload: 0.3,
          getGenerationResponsePayload: 0.62
        };
        return {
          x: width * (columns[node.role] || 0.5),
          y: height * (rows[node.id] || 0.5)
        };
      }

      function compactEdgeLabel(edge) {
        const value = edge.parameterMap.id || edge.parameterMap.requestId || edge.parameterMap.apiKeys || edge.parameterMap.finishReasons || edge.relation;
        return String(value).replace("$item.", "item.").replace("$selection[]", "selection[]");
      }

      function curvedEdgePath(edge, nodeWidth, nodeHeight) {
        const source = rectEdgePoint(edge.source, edge.target, nodeWidth, nodeHeight, 1);
        const target = rectEdgePoint(edge.target, edge.source, nodeWidth, nodeHeight, 1);
        const dx = target.x - source.x;
        const dy = target.y - source.y;
        const curve = Math.max(48, Math.min(180, Math.abs(dx) * 0.38));
        return "M" + source.x + "," + source.y +
          " C" + (source.x + Math.sign(dx || 1) * curve) + "," + source.y +
          " " + (target.x - Math.sign(dx || 1) * curve) + "," + target.y +
          " " + target.x + "," + target.y;
      }

      function rectEdgePoint(from, to, width, height) {
        const dx = to.x - from.x;
        const dy = to.y - from.y;
        const scale = Math.max(Math.abs(dx) / (width / 2), Math.abs(dy) / (height / 2), 1);
        return {
          x: from.x + dx / scale,
          y: from.y + dy / scale
        };
      }

      function truncateMiddle(value, maxLength) {
        const text = String(value || "");
        if (text.length <= maxLength) return text;
        const keep = Math.max(4, Math.floor((maxLength - 1) / 2));
        return text.slice(0, keep) + "…" + text.slice(-keep);
      }

      function denseGroupLabel(item) {
        const suffix = " (" + item.count + ")";
        const maxChars = Math.floor(Math.max(0, item.x1 - item.x0 - 20) / 6.2);
        return truncateWithSuffix(item.group, suffix, maxChars);
      }

      function truncateWithSuffix(value, suffix, maxLength) {
        const text = String(value || "");
        const end = String(suffix || "");
        const full = text + end;
        if (maxLength <= 1) return "";
        if (full.length <= maxLength) return full;
        if (maxLength <= end.length + 2) return end.trim();
        return text.slice(0, Math.max(1, maxLength - end.length - 1)) + "…" + end;
      }

      function clamp(value, min, max) {
        return Math.max(min, Math.min(max, value));
      }

      function focusGraphNode(nodeId) {
        if (apiGraph.scope === "all") {
          const node = apiGraph.nodes.find((item) => item.id === nodeId);
          setEvent(node ? node.method + " " + node.path : "Endpoint selected.");
          return;
        }
        if (nodeId === "listLogs") {
          openPage("logs");
          return runListLogs();
        }
        if (!state.selectedId) {
          openPage("logs");
          setEvent("Select a log row before running " + nodeId + ".");
          return;
        }
        if (nodeId === "getLogActivity" || nodeId === "getLegacyGeneration" || nodeId === "getGenerationRequestPayload" || nodeId === "getGenerationResponsePayload") {
          openPage("detail");
          drillOne(state.selectedId, { force: true }).then(() => {
            const tabByNode = {
              getLogActivity: "activity",
              getLegacyGeneration: "generation",
              getGenerationRequestPayload: "requestPayload",
              getGenerationResponsePayload: "responsePayload"
            };
            state.activeTab = tabByNode[nodeId] || state.activeTab;
            renderDetail();
          });
        }
      }

      async function runEndpointFromButton(button) {
        const node = apiGraph.nodes.find((item) => item.id === button.dataset.runEndpoint);
        if (!node) return;
        if (!isEndpointSafeToRun(node) && !confirm("This endpoint may change server state. Run " + node.method + " " + node.path + "?")) {
          return;
        }
        const runner = button.closest("[data-endpoint-runner]");
        let request;
        try {
          request = buildEndpointRequest(node, runner);
        } catch (error) {
          state.endpointRuns[node.id] = { loading: false, error: error.message };
          renderEndpointInspector();
          return;
        }
        state.endpointRuns[node.id] = { loading: true, request };
        renderEndpointInspector();
        try {
          const response = await proxyJson(request.path, {
            method: request.method,
            headers: jsonHeaders(request.body !== undefined),
            body: request.body
          });
          state.endpointRuns[node.id] = { loading: false, request, response };
          if (node.method === "POST" && node.path === "/api/api_key/activity" && Array.isArray(response?.data)) {
            state.logs = response.data;
            state.selectedId = getRequestId(state.logs[0]) || state.selectedId;
            renderLogs(response);
            renderDetail();
          }
          setEvent(node.label + " returned " + summarizeResponse(response) + ".");
        } catch (error) {
          state.endpointRuns[node.id] = { loading: false, request, error: error.message };
          setEvent(node.label + " failed: " + error.message, "error");
        } finally {
          renderEndpointInspector();
        }
      }

      function buildEndpointRequest(node, runner) {
        const spec = operationSpecForNode(node);
        const params = {};
        runner?.querySelectorAll("[data-endpoint-param]").forEach((input) => {
          params[input.dataset.paramIn + ":" + input.dataset.paramName] = input.value.trim();
        });
        let [pathOnly, rawQuery = ""] = String(node.path || "/").split("?");
        for (const match of pathOnly.matchAll(/\\{([^}]+)\\}/g)) {
          const name = match[1];
          const value = params["path:" + name] || "";
          if (!value) throw new Error("Fill path parameter " + name + ".");
          pathOnly = pathOnly.replace(new RegExp("\\\\{" + escapeRegExp(name) + "\\\\}", "g"), encodeURIComponent(value));
        }
        const search = new URLSearchParams(rawQuery);
        for (const param of spec?.parameters || []) {
          if (param.in !== "query") continue;
          const value = params["query:" + param.name] || "";
          if (value) search.set(param.name, value);
          else if (param.required) throw new Error("Fill query parameter " + param.name + ".");
        }
        const query = search.toString();
        const bodyField = runner?.querySelector("[data-endpoint-body]");
        let body;
        if (bodyField) {
          const rawBody = bodyField.value.trim();
          body = rawBody ? JSON.parse(rawBody) : undefined;
        }
        return {
          method: node.method,
          path: pathOnly + (query ? "?" + query : ""),
          body
        };
      }

      function summarizeResponse(response) {
        if (Array.isArray(response)) return response.length + " item(s)";
        if (response && typeof response === "object") {
          if (Array.isArray(response.data)) return response.data.length + " data row(s)";
          return Object.keys(response).length + " field(s)";
        }
        return response === undefined || response === null ? "empty response" : typeof response;
      }

      function renderAiSidebar() {
        const toggle = document.getElementById("ai-sidebar-toggle");
        const prompt = document.getElementById("ai-prompt");
        const run = document.getElementById("ai-run");
        const summary = document.getElementById("ai-summary");
        const engine = document.getElementById("ai-engine");
        const result = document.getElementById("ai-result");
        const tabMeta = document.getElementById("tab-ai-meta");
        if (!toggle || !result) return;
        toggle.classList.toggle("active", Boolean(state.pages.ai));
        toggle.setAttribute("aria-pressed", state.pages.ai ? "true" : "false");
        if (prompt && document.activeElement !== prompt && prompt.value !== state.ai.prompt) {
          prompt.value = state.ai.prompt;
        }
        if (run) run.disabled = state.ai.running;
        const summaryText = state.ai.running
          ? "Running"
          : state.ai.error
            ? "Failed"
            : state.ai.result
              ? summarizeAiResult(state.ai.result)
              : "Ready";
        if (summary) {
          summary.textContent = summaryText;
        }
        if (tabMeta) tabMeta.textContent = summaryText;
        if (engine) engine.textContent = state.ai.engine || "planner";
        result.innerHTML = renderAiSidebarResult();
      }

      function renderAiSidebarResult() {
        if (state.ai.error) {
          return '<div class="empty">' + escapeHtml(state.ai.error) + '</div>' + renderAiSteps();
        }
        if (state.ai.running) {
          const planTitle = state.ai.plan?.title || state.ai.result?.title || "Planning";
          return '<div class="ai-status"><strong>' + escapeHtml(planTitle) + '</strong><div>' + escapeHtml(state.ai.result?.summary || "Preparing browser-session API calls.") + '</div></div>' + renderAiSteps();
        }
        if (!state.ai.result) {
          return '<div class="empty">Ask for a browser-session task, then the sidebar will plan API calls and render the result.</div>';
        }
        const items = Array.isArray(state.ai.result.items) ? state.ai.result.items : [];
        const cards = items.length ? items.map(renderAiItem).join("") : '<div class="empty">No renderable result was found in the scanned calls.</div>';
        return '<div class="ai-status"><strong>' + escapeHtml(state.ai.result.title || "Result") + '</strong><div>' + escapeHtml(state.ai.result.summary || summarizeAiResult(state.ai.result)) + '</div></div>' + cards + renderAiSteps();
      }

      function renderAiSteps() {
        if (!state.ai.steps.length) return "";
        return '<div class="ai-steps-head"><span>Execution log</span><span>' + state.ai.steps.length + ' / 1000</span></div>' +
          '<div class="ai-steps" data-ai-steps="true" aria-live="polite">' + state.ai.steps.map((step) =>
          '<div class="ai-step ' + escapeAttr(step.level || "info") + '"><span>' + escapeHtml(step.message) + '</span></div>'
        ).join("") + '</div>';
      }

      function renderAiItem(item, index) {
        const title = item.title || ("Image result " + (index + 1));
        const images = Array.isArray(item.images) ? item.images : [];
        const texts = Array.isArray(item.texts) ? item.texts.slice(0, 4) : [];
        const imageHtml = images.length ? '<div class="image-grid">' + images.slice(0, 6).map((image) =>
          '<div class="image-card"><img src="' + escapeAttr(image.src) + '" alt="' + escapeAttr(image.label || title) + '" /><div>' + escapeHtml(image.label || "image") + '</div></div>'
        ).join("") + '</div>' : '<div class="empty">No image URL or inline image was detected in this payload.</div>';
        const textHtml = texts.length ? '<div class="text-fragments">' + texts.map((text) =>
          '<div class="text-fragment">' + escapeHtml(text) + '</div>'
        ).join("") + '</div>' : "";
        const rawHtml = item.raw ? '<details><summary class="small muted">Raw payload</summary><pre>' + escapeHtml(JSON.stringify(item.raw, null, 2)) + '</pre></details>' : "";
        return '<article class="ai-card">' +
          '<div class="ai-card-head"><strong title="' + escapeAttr(title) + '">' + escapeHtml(title) + '</strong>' +
            '<button data-ai-detail="' + escapeAttr(item.requestId || "") + '">Detail</button></div>' +
          renderAiMeta(item) +
          imageHtml +
          textHtml +
          rawHtml +
        '</article>';
      }

      function renderAiMeta(item) {
        const rows = [
          ["requestId", item.requestId],
          ["model", item.model],
          ["provider", item.provider],
          ["created", item.createdAt ? formatTime(item.createdAt) : ""]
        ].filter((row) => row[1]);
        return rows.length ? '<div class="ai-meta">' + rows.map((row) =>
          '<div>' + escapeHtml(row[0]) + '</div><div title="' + escapeAttr(row[1]) + '">' + escapeHtml(row[1]) + '</div>'
        ).join("") + '</div>' : "";
      }

      function summarizeAiResult(result) {
        if (!result) return "Ready";
        if (Array.isArray(result.items)) return result.items.length + " rendered item(s)";
        return result.summary || "Done";
      }

      async function runAiSidebar() {
        if (state.ai.running) return;
        openPage("ai");
        const promptField = document.getElementById("ai-prompt");
        const prompt = (promptField?.value || "").trim();
        if (!prompt) {
          state.ai.error = "Enter an AI sidebar request.";
          renderAiSidebar();
          return;
        }
        state.ai.prompt = prompt;
        state.ai.running = true;
        state.ai.engine = "";
        state.ai.plan = null;
        state.ai.result = { title: "Planning", summary: "Preparing a browser-session plan.", items: [] };
        state.ai.error = "";
        state.ai.steps = [];
        pushAiStep("Planning from current API inventory.", "info");
        try {
          const plan = await requestAiPlan(prompt);
          state.ai.plan = plan;
          state.ai.engine = plan.engine || plan.source || "planner";
          pushAiStep("Plan selected: " + (plan.title || plan.type || "endpoint plan") + ".", "ok");
          state.ai.result = await executeAiPlan(plan);
          state.ai.running = false;
          pushAiStep("Finished.", "ok");
          setEvent("AI sidebar finished: " + summarizeAiResult(state.ai.result) + ".");
        } catch (error) {
          state.ai.running = false;
          state.ai.error = error.message;
          pushAiStep(error.message, "err");
          setEvent("AI sidebar failed: " + error.message, "error");
        } finally {
          renderAiSidebar();
        }
      }

      async function requestAiPlan(prompt) {
        const response = await fetch("/__cap/ai/plan", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            prompt,
            selectedRequestId: state.selectedId,
            namespace: state.graph.namespace || state.graph.selectedNamespace || "",
            layout: state.layout
          })
        });
        const text = await response.text();
        let value;
        try {
          value = text ? JSON.parse(text) : null;
        } catch {
          value = { message: text || "Invalid AI planner response" };
        }
        if (!response.ok) {
          throw new Error(value?.message || "AI planner failed with HTTP " + response.status);
        }
        return value;
      }

      async function executeAiPlan(plan) {
        if (!plan || !plan.type) throw new Error("AI planner returned no executable plan.");
        if (plan.type === "zenmux_recent_image_results") return executeRecentImageResultsPlan(plan);
        throw new Error(plan.reason || "This AI plan is not executable by the current MVP.");
      }

      async function executeRecentImageResultsPlan(plan) {
        const limit = clamp(Number(plan.limit || 2), 1, 10);
        const requestedScanLimit = Number(plan.scanLimit || plan.scan || 0);
        const scanLimit = clamp(Math.max(requestedScanLimit, limit * 80, 160), limit, 500);
        const baseBody = buildListLogsBody();
        const items = [];
        let scanned = 0;
        let rows = [];
        let usedFilter = null;

        const filterOptions = await discoverImageLogFilters(plan);
        const attempts = [];
        if (filterOptions.modelSlugs.length || filterOptions.providerSlugs.length) {
          attempts.push({
            label: "image model filters",
            body: {
              ...baseBody,
              modelSlugs: filterOptions.modelSlugs,
              providerSlugs: filterOptions.providerSlugs
            },
            filter: filterOptions
          });
        }
        attempts.push({ label: "unfiltered logs", body: baseBody, filter: null });

        for (const attempt of attempts) {
          if (items.length >= limit) break;
          if (attempt.filter) {
            pushAiStep("Using listLogs filters: " + summarizeLogFilters(attempt.filter) + ".", "ok");
          } else if (attempts.length > 1) {
            pushAiStep("Filtered scan found " + items.length + " result(s); falling back to unfiltered logs.", "info");
          }
          const result = await scanLogAttemptForImages(attempt.body, {
            limit,
            scanLimit,
            items,
            scanned,
            usedFilter: attempt.filter
          });
          rows = rows.concat(result.rows);
          scanned = result.scanned;
          usedFilter = usedFilter || result.usedFilter;
        }

        if (items[0]?.requestId) {
          state.selectedId = items[0].requestId;
          state.logs = dedupeRowsByRequestId(rows);
          renderLogs({ data: state.logs, total: state.logs.length });
          renderDetail();
        }
        return {
          title: plan.title || "Recent image results",
          summary: items.length
            ? "Rendered " + items.length + " call(s) with verified images from " + scanned + " scanned log row(s)."
            : "Scanned " + scanned + " recent log row(s), but no loadable image was detected.",
          items,
          listCount: rows.length,
          scannedCount: scanned,
          filters: usedFilter,
          plan
        };
      }

      async function scanLogAttemptForImages(body, context) {
        const limit = context.limit;
        const scanLimit = context.scanLimit;
        const items = context.items;
        let scanned = context.scanned || 0;
        const pageSize = Math.min(100, Math.max(20, Number(body.pageSize || 100), limit * 20));
        const maxPages = Math.max(1, Math.ceil(scanLimit / pageSize));
        const rows = [];
        let usedFilter = context.usedFilter || null;
        for (let pageNo = 1; pageNo <= maxPages && items.length < limit && scanned < scanLimit; pageNo += 1) {
          const requestBody = { ...body, pageNo, pageSize };
          pushAiStep("Loading log page " + pageNo + " (" + pageSize + " rows).", "info");
          const listResponse = await proxyJson("/api/api_key/activity", {
            method: "POST",
            headers: jsonHeaders(),
            body: requestBody
          });
          const pageRows = Array.isArray(listResponse.data) ? listResponse.data : [];
          rows.push(...pageRows);
          state.logs = dedupeRowsByRequestId(rows);
          state.selectedId = getRequestId(state.logs[0]) || state.selectedId;
          renderLogs({ data: state.logs, total: listResponse.total });
          pushAiStep("Scanning " + pageRows.length + " row(s) from page " + pageNo + ".", pageRows.length ? "ok" : "err");
          for (const row of prioritizeImageRows(pageRows)) {
            if (items.length >= limit || scanned >= scanLimit) break;
            const requestId = getRequestId(row);
            if (!requestId || items.some((item) => item.requestId === requestId)) continue;
            scanned += 1;
            pushAiStep("Fetching detail payloads for " + truncateMiddle(requestId, 18) + ".", "info");
            const detail = await fetchDetailForAi(requestId);
            const candidates = collectDetailImages(detail);
            const images = await resolveRenderableImages(candidates);
            if (!images.length) continue;
            const texts = collectDetailTexts(detail).slice(0, 6);
            items.push({
              requestId,
              title: "Image call " + (items.length + 1),
              model: firstValue(row, ["modelSlug", "model", "modelName"]),
              provider: firstValue(row, ["providerSlug", "provider", "providerName"]),
              createdAt: firstValue(row, ["createdAt", "createAt", "created_at"]),
              images,
              texts,
              raw: detail.responsePayload || detail.generation || detail.activity
            });
            pushAiStep("Rendered " + truncateMiddle(requestId, 18) + " with " + images.length + " verified image(s).", "ok");
          }
          if (pageRows.length < pageSize) break;
        }
        return { rows: dedupeRowsByRequestId(rows), scanned, usedFilter };
      }

      async function discoverImageLogFilters(plan) {
        const directFilters = plan?.filters || {};
        const modelSlugs = new Set(toStringArray(directFilters.modelSlugs));
        const providerSlugs = new Set(toStringArray(directFilters.providerSlugs));
        try {
          pushAiStep("Discovering image-capable model filters.", "info");
          const catalog = await callMaybe(() => proxyJson("/api/frontend/model/provider/price/list", {
            method: "GET",
            headers: jsonHeaders(false)
          }));
          for (const option of collectModelFilterOptions(catalog)) {
            if (option.kind === "model") modelSlugs.add(option.slug);
            if (option.kind === "provider") providerSlugs.add(option.slug);
          }
        } catch {}
        return {
          modelSlugs: [...modelSlugs].slice(0, 80),
          providerSlugs: [...providerSlugs].slice(0, 20)
        };
      }

      function collectModelFilterOptions(value, out = []) {
        if (!value) return out;
        if (Array.isArray(value)) {
          value.forEach((item) => collectModelFilterOptions(item, out));
          return out;
        }
        if (typeof value !== "object") return out;
        const text = safeStringSample(value, 2400);
        const imageTyped = /\\b(image|img|vision|visual|paint|photo|picture|generate[-_ ]?image|text[-_ ]?to[-_ ]?image)\\b/i.test(text) ||
          /\\b(dall|gpt-image|imagen|flux|stable-diffusion|sdxl|midjourney|ideogram|recraft|seedream|wanx|kling|luma|runway|leonardo|playground)\\b/i.test(text);
        if (imageTyped) {
          for (const key of ["modelSlug", "model_slug", "model", "slug", "name", "id"]) {
            const slug = value[key];
            if (typeof slug === "string" && slug.length <= 120 && imageSlugLooksUseful(slug)) {
              out.push({ kind: "model", slug });
              break;
            }
          }
          for (const key of ["providerSlug", "provider_slug", "provider"]) {
            const slug = value[key];
            if (typeof slug === "string" && imageProviderLooksUseful(slug)) out.push({ kind: "provider", slug });
          }
        }
        for (const child of Object.values(value)) {
          if (typeof child === "object") collectModelFilterOptions(child, out);
        }
        return uniqueFilterOptions(out);
      }

      function imageSlugLooksUseful(slug) {
        return /\\b(dall|gpt-image|imagen|flux|stable-diffusion|sdxl|midjourney|ideogram|recraft|seedream|wanx|kling|luma|runway|leonardo|playground|image|img|photo|picture)\\b/i.test(slug);
      }

      function imageProviderLooksUseful(slug) {
        return /\\b(stability|midjourney|ideogram|recraft|fal|replicate|runware|leonardo|luma|kling|runway)\\b/i.test(slug);
      }

      function uniqueFilterOptions(options) {
        const seen = new Set();
        return options.filter((option) => {
          const key = option.kind + ":" + option.slug;
          if (seen.has(key)) return false;
          seen.add(key);
          return true;
        });
      }

      function summarizeLogFilters(filters) {
        const parts = [];
        if (filters.modelSlugs?.length) parts.push(filters.modelSlugs.length + " modelSlugs");
        if (filters.providerSlugs?.length) parts.push(filters.providerSlugs.length + " providerSlugs");
        return parts.join(", ") || "none";
      }

      function prioritizeImageRows(rows) {
        return [...rows].sort((left, right) => Number(rowLooksImageRelated(right)) - Number(rowLooksImageRelated(left)));
      }

      function rowLooksImageRelated(row) {
        const sample = [
          firstValue(row, ["modelSlug", "model", "modelName"]),
          firstValue(row, ["providerSlug", "provider", "providerName"]),
          firstValue(row, ["endpoint", "path", "url"]),
          safeStringSample(row, 1200)
        ].join(" ");
        return /\\b(image|img|vision|visual|photo|picture|dall|gpt-image|imagen|flux|stable-diffusion|sdxl|midjourney|ideogram|recraft|seedream|wanx|kling|luma|runway)\\b/i.test(sample);
      }

      function collectDetailImages(detail) {
        const images = [];
        for (const [label, value] of [
          ["responsePayload", detail.responsePayload],
          ["requestPayload", detail.requestPayload],
          ["generation", detail.generation],
          ["activity", detail.activity]
        ]) {
          const before = images.length;
          collectImages(unwrapPayload(value), "$." + label, images);
          collectImages(value, "$." + label + ".raw", images);
          if (images.length > before) pushAiStep("Found " + (images.length - before) + " image candidate(s) in " + label + ".", "ok");
        }
        return dedupeImages(images);
      }

      function collectDetailTexts(detail) {
        const texts = [];
        for (const value of [detail.responsePayload, detail.requestPayload, detail.generation, detail.activity]) {
          collectTextFragments(unwrapPayload(value), texts);
        }
        return dedupe(texts);
      }

      function dedupeImages(images) {
        const seen = new Set();
        const result = [];
        for (const image of images || []) {
          const src = String(image?.src || "").trim();
          if (!src || seen.has(src)) continue;
          seen.add(src);
          result.push({ ...image, src });
        }
        return result;
      }

      function dedupeRowsByRequestId(rows) {
        const seen = new Set();
        const result = [];
        for (const row of rows || []) {
          const id = getRequestId(row) || JSON.stringify(row).slice(0, 120);
          if (seen.has(id)) continue;
          seen.add(id);
          result.push(row);
        }
        return result;
      }

      function toStringArray(value) {
        if (!value) return [];
        return (Array.isArray(value) ? value : [value])
          .map((item) => String(item || "").trim())
          .filter(Boolean);
      }

      async function fetchDetailForAi(requestId) {
        if (state.details[requestId] && !state.details[requestId].loading && !state.details[requestId].error) {
          return state.details[requestId];
        }
        state.details[requestId] = { loading: true, startedAt: Date.now() };
        const [activity, generation, requestPayload, responsePayload] = await Promise.all([
          callMaybe(() => proxyJson("/api/api_key/activity/" + encodeURIComponent(requestId) + "?id=" + encodeURIComponent(requestId), { method: "GET", headers: jsonHeaders(false) })),
          callMaybe(() => proxyJson("/api/v1/generation?id=" + encodeURIComponent(requestId), { method: "GET", headers: jsonHeaders(false) })),
          callMaybe(() => proxyJson("/api/v1/generation/request?id=" + encodeURIComponent(requestId) + "&type=userRequest", { method: "GET", headers: jsonHeaders(false) })),
          callMaybe(() => proxyJson("/api/v1/generation/response?id=" + encodeURIComponent(requestId) + "&type=userResponse", { method: "GET", headers: jsonHeaders(false) }))
        ]);
        const detail = {
          loading: false,
          requestId,
          activity,
          generation,
          requestPayload,
          responsePayload,
          finishedAt: Date.now()
        };
        state.details[requestId] = detail;
        return detail;
      }

      function looksLikeImageCall(row, detail) {
        const sample = safeStringSample(row, 2000) + " " + safeStringSample(detail.requestPayload, 4000) + " " + safeStringSample(detail.responsePayload, 4000);
        return /\\b(image|images|png|jpg|jpeg|webp|gif|dall|flux|stable-diffusion|imagen|midjourney)\\b/i.test(sample);
      }

      function safeStringSample(value, maxLength) {
        try {
          return JSON.stringify(value).slice(0, maxLength);
        } catch {
          return "";
        }
      }

      function pushAiStep(message, level = "info") {
        state.ai.steps.push({ message, level });
        state.ai.steps = state.ai.steps.slice(-1000);
        renderAiSidebar();
        requestAnimationFrame(() => {
          const steps = document.querySelector("[data-ai-steps]");
          if (steps) steps.scrollTop = steps.scrollHeight;
        });
      }

      function buildListLogsBody() {
        const days = Number(document.getElementById("days")?.value || "7");
        const stopTime = Date.now();
        const requestId = document.getElementById("request-id-filter")?.value.trim();
        const body = {
          apiKeys: [],
          startTime: stopTime - days * 24 * 60 * 60 * 1000,
          stopTime,
          pageNo: Number(document.getElementById("page-no")?.value || "1"),
          pageSize: Number(document.getElementById("page-size")?.value || initialExample.pageSize || "20"),
          modelSlugs: [],
          providerSlugs: [],
          finishReasons: []
        };
        if (requestId) body.requestId = requestId;
        return body;
      }

      async function runListLogs() {
        openPage("logs");
        setBusy(true);
        state.abortDrill = false;
        try {
          const body = buildListLogsBody();
          const response = await proxyJson("/api/api_key/activity", {
            method: "POST",
            headers: jsonHeaders(),
            body
          });
          state.logs = Array.isArray(response.data) ? response.data : [];
          state.selectedId = getRequestId(state.logs[0]) || null;
          setEvent("listLogs returned " + state.logs.length + " rows" + (response.total !== undefined ? " of " + response.total : "") + ".");
          renderLogs(response);
          renderDetail();
        } catch (error) {
          setEvent("listLogs failed: " + error.message, "error");
          document.getElementById("logs-body").innerHTML = '<tr><td colspan="8" class="muted">' + escapeHtml(error.message) + '</td></tr>';
        } finally {
          setBusy(false);
        }
      }

      function renderLogs(response) {
        document.getElementById("list-summary").textContent = state.logs.length + " rows" + (response && response.total !== undefined ? " / total " + response.total : "");
        syncPages();
        document.getElementById("drill-first").disabled = state.logs.length === 0 || state.running;
        document.getElementById("drill-selected").disabled = !state.selectedId || state.running;
        const body = document.getElementById("logs-body");
        if (!state.logs.length) {
          body.innerHTML = '<tr><td colspan="8" class="muted">No rows returned.</td></tr>';
          return;
        }
        body.innerHTML = state.logs.map((item, index) => {
          const id = getRequestId(item);
          const detail = state.details[id];
          const classes = [
            id === state.selectedId ? "selected" : "",
            detail && detail.loading ? "loading" : "",
            detail && detail.error ? "error" : ""
          ].filter(Boolean).join(" ");
          return '<tr class="' + classes + '" data-request-id="' + escapeAttr(id) + '">' +
            '<td title="' + escapeAttr(id) + '"><code>' + escapeHtml(id || "") + '</code></td>' +
            '<td title="' + escapeAttr(firstValue(item, ["modelSlug", "model", "modelName"])) + '">' + escapeHtml(firstValue(item, ["modelSlug", "model", "modelName"])) + '</td>' +
            '<td title="' + escapeAttr(firstValue(item, ["providerSlug", "provider", "providerName"])) + '">' + escapeHtml(firstValue(item, ["providerSlug", "provider", "providerName"])) + '</td>' +
            '<td>' + escapeHtml(firstValue(item, ["finishReason", "finish_reason", "status"])) + '</td>' +
            '<td>' + escapeHtml(formatNumber(firstValue(item, ["latency", "generationTime"]))) + '</td>' +
            '<td>' + escapeHtml(formatCost(firstValue(item, ["billAmount", "usage", "cost"]))) + '</td>' +
            '<td title="' + escapeAttr(firstValue(item, ["createdAt", "createAt", "created_at"])) + '">' + escapeHtml(formatTime(firstValue(item, ["createdAt", "createAt", "created_at"]))) + '</td>' +
            '<td><div class="row-actions"><button data-action="select" data-request-id="' + escapeAttr(id) + '">View</button><button data-action="drill" data-request-id="' + escapeAttr(id) + '">Drill</button></div></td>' +
            '</tr>';
        }).join("");
        body.querySelectorAll("tr[data-request-id]").forEach((row) => {
          row.addEventListener("click", (event) => {
            const button = event.target.closest("button");
            const id = row.dataset.requestId;
            if (!id) return;
            state.selectedId = id;
            if (button && button.dataset.action === "drill") {
              openPage("detail");
              drillMany([id]);
            } else {
              openPage("detail");
              renderLogs({ total: response && response.total });
              renderDetail();
            }
          });
        });
      }

      async function drillMany(ids) {
        if (!ids.length) return;
        openPage("detail");
        state.running = true;
        state.abortDrill = false;
        document.getElementById("stop-drill").disabled = false;
        document.getElementById("drill-first").disabled = true;
        document.getElementById("drill-selected").disabled = true;
        setEvent("Drilling " + ids.length + " request ids.");
        const limit = Math.max(1, Math.min(8, Number(document.getElementById("concurrency").value || "3")));
        await runWithConcurrency(ids, limit, async (id) => {
          if (state.abortDrill) return;
          await drillOne(id);
        });
        state.running = false;
        document.getElementById("stop-drill").disabled = true;
        document.getElementById("drill-first").disabled = state.logs.length === 0;
        document.getElementById("drill-selected").disabled = !state.selectedId;
        renderLogs({ total: undefined });
        renderDetail();
      }

      async function drillOne(requestId, options = {}) {
        if (!requestId) return;
        openPage("detail");
        if (state.details[requestId] && !state.details[requestId].error && !options.force) {
          state.selectedId = requestId;
          renderDetail();
          return state.details[requestId];
        }
        state.selectedId = requestId;
        state.details[requestId] = { loading: true, startedAt: Date.now() };
        renderLogs({ total: undefined });
        renderDetail();
        try {
          const [activity, generation, requestPayload, responsePayload] = await Promise.all([
            callMaybe(() => proxyJson("/api/api_key/activity/" + encodeURIComponent(requestId) + "?id=" + encodeURIComponent(requestId), { method: "GET", headers: jsonHeaders(false) })),
            callMaybe(() => proxyJson("/api/v1/generation?id=" + encodeURIComponent(requestId), { method: "GET", headers: jsonHeaders(false) })),
            callMaybe(() => proxyJson("/api/v1/generation/request?id=" + encodeURIComponent(requestId) + "&type=userRequest", { method: "GET", headers: jsonHeaders(false) })),
            callMaybe(() => proxyJson("/api/v1/generation/response?id=" + encodeURIComponent(requestId) + "&type=userResponse", { method: "GET", headers: jsonHeaders(false) }))
          ]);
          state.details[requestId] = {
            loading: false,
            requestId,
            activity,
            generation,
            requestPayload,
            responsePayload,
            finishedAt: Date.now()
          };
          setEvent("Drilled " + requestId + ".");
        } catch (error) {
          state.details[requestId] = { loading: false, requestId, error: error.message };
          setEvent("Drill failed for " + requestId + ": " + error.message, "error");
        }
        renderLogs({ total: undefined });
        renderDetail();
        return state.details[requestId];
      }

      async function proxyJson(path, options) {
        const targetUrl = new URL(path, "https://" + targetHost).toString();
        const response = await fetch("/__cap/proxy", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            url: targetUrl,
            method: options.method || "GET",
            headers: options.headers || {},
            body: options.body
          })
        });
        const text = await response.text();
        let value;
        try {
          value = text ? JSON.parse(text) : null;
        } catch {
          value = text;
        }
        if (!response.ok) {
          const message = value && typeof value === "object" && value.message ? value.message : "HTTP " + response.status;
          throw new Error(message);
        }
        return value;
      }

      async function callMaybe(fn) {
        try {
          return await fn();
        } catch (error) {
          return { _error: { message: error.message } };
        }
      }

      function renderDetail() {
        syncPages();
        const title = document.getElementById("detail-title");
        const tabs = document.getElementById("detail-tabs");
        const content = document.getElementById("detail-content");
        if (!state.selectedId) {
          title.textContent = "No row selected";
          tabs.innerHTML = "";
          content.innerHTML = '<div class="empty">Select a log row, then drill into request/response payloads.</div>';
          return;
        }
        title.textContent = state.selectedId;
        const detail = state.details[state.selectedId];
        const tabItems = [
          ["responsePayload", "Response"],
          ["requestPayload", "Request"],
          ["activity", "Activity"],
          ["generation", "Generation"],
          ["raw", "Raw"]
        ];
        tabs.innerHTML = tabItems.map(([id, label]) => '<button class="' + (state.activeTab === id ? "active" : "") + '" data-tab="' + id + '">' + label + '</button>').join("");
        tabs.querySelectorAll("button").forEach((button) => {
          button.addEventListener("click", () => {
            state.activeTab = button.dataset.tab;
            renderDetail();
          });
        });
        if (!detail) {
          content.innerHTML = '<div class="empty">No detail loaded yet. Use Drill selected or the row Drill action.</div>';
          return;
        }
        if (detail.loading) {
          content.innerHTML = '<div class="empty">Loading dependent APIs for <code>' + escapeHtml(state.selectedId) + '</code>.</div>';
          return;
        }
        if (detail.error) {
          content.innerHTML = '<div class="empty">' + escapeHtml(detail.error) + '</div>';
          return;
        }
        if (state.activeTab === "raw") {
          content.innerHTML = '<pre>' + escapeHtml(JSON.stringify(detail, null, 2)) + '</pre>';
          return;
        }
        const value = detail[state.activeTab];
        content.innerHTML = renderValuePanel(value, state.activeTab);
      }

      function renderValuePanel(value, label) {
        if (!value) return '<div class="empty">No ' + escapeHtml(label) + ' data.</div>';
        if (value._error) return '<div class="empty">' + escapeHtml(value._error.message || "Request failed") + '</div>';
        const payloadBody = unwrapPayload(value);
        const images = collectImages(payloadBody);
        const texts = collectTextFragments(payloadBody).slice(0, 20);
        const kvHtml = renderSummaryKv(value);
        const imageHtml = images.length ? '<div class="image-grid">' + images.slice(0, 12).map((image) =>
          '<div class="image-card"><img src="' + escapeAttr(image.src) + '" alt="' + escapeAttr(image.label) + '" /><div>' + escapeHtml(image.label) + '</div></div>'
        ).join("") + '</div>' : "";
        const textHtml = texts.length ? '<div class="text-fragments">' + texts.map((text) =>
          '<div class="text-fragment">' + escapeHtml(text) + '</div>'
        ).join("") + '</div>' : "";
        return kvHtml + imageHtml + (textHtml || '<div class="empty">No obvious text/image fragment detected. Raw JSON is below.</div>') + '<pre>' + escapeHtml(JSON.stringify(value, null, 2)) + '</pre>';
      }

      function renderSummaryKv(value) {
        const candidates = ["requestId", "generationId", "model", "modelSlug", "provider", "providerSlug", "finishReason", "latency", "generationTime", "usage", "billAmount"];
        const rows = [];
        for (const key of candidates) {
          const found = findFirstKey(value, key);
          if (found !== undefined && found !== null && typeof found !== "object") {
            rows.push('<div>' + escapeHtml(key) + '</div><div class="code">' + escapeHtml(String(found)) + '</div>');
          }
        }
        return rows.length ? '<div class="kv">' + rows.join("") + '</div>' : "";
      }

      function unwrapPayload(value) {
        if (!value || typeof value !== "object") return value;
        if (value.body !== undefined) return value.body;
        if (value.data && value.data.body !== undefined) return value.data.body;
        if (value.payload !== undefined) return value.payload;
        return value;
      }

      function collectImages(value, path = "$", out = []) {
        if (!value || out.length > 32) return out;
        if (typeof value === "string") {
          collectImagesFromEncodedString(value, path, out);
          for (const src of extractImageRefsFromString(value)) {
            if (!out.some((image) => image.src === src)) out.push({ src, label: path });
          }
          return out;
        }
        if (Array.isArray(value)) {
          value.forEach((item, index) => collectImages(item, path + "[" + index + "]", out));
          return out;
        }
        if (typeof value === "object") {
          const inline = value.inlineData || value.inline_data;
          if (inline && inline.data && inlineMimeType(inline).startsWith("image/")) {
            out.push({ src: "data:" + inlineMimeType(inline) + ";base64," + inline.data, label: path + ".inlineData" });
          }
          const fileData = value.fileData || value.file_data;
          if (fileData && inlineMimeType(fileData).startsWith("image/") && typeof (fileData.fileUri || fileData.file_uri || fileData.uri) === "string") {
            out.push({ src: fileData.fileUri || fileData.file_uri || fileData.uri, label: path + ".fileData" });
          }
          const objectMimeType = inlineMimeType(value);
          const base64 = value.b64_json || value.base64 || value.imageBase64 || value.image_base64;
          if (typeof base64 === "string" && objectMimeType.startsWith("image/")) {
            out.push({ src: "data:" + objectMimeType + ";base64," + base64, label: path + ".base64" });
          }
          const imageUrl = value.image_url && (value.image_url.url || value.image_url);
          if (typeof imageUrl === "string" && isImageRefCandidate(imageUrl)) {
            out.push({ src: imageUrl, label: path + ".image_url" });
          }
          const imageObject = objectLooksImageRelated(value, path);
          for (const key of ["url", "uri", "src", "href", "fileUri", "file_uri", "imageUrl", "image_url", "outputUrl", "output_url"]) {
            const candidate = value[key];
            if (typeof candidate === "string" && isImageRefCandidate(candidate, { strict: !imageObject })) {
              out.push({ src: candidate, label: path + "." + key });
            }
          }
          for (const [key, child] of Object.entries(value)) collectImages(child, path + "." + key, out);
        }
        return out;
      }

      function collectImagesFromEncodedString(value, path, out) {
        const text = String(value || "").trim();
        if (!text) return;
        if ((text.startsWith("{") && text.endsWith("}")) || (text.startsWith("[") && text.endsWith("]"))) {
          try {
            collectImages(JSON.parse(text), path + ".json", out);
          } catch {}
        }
        if (!text.includes("data:")) return;
        for (const line of text.split(/\\r?\\n/)) {
          const trimmed = line.trim();
          if (!trimmed.startsWith("data:")) continue;
          const payload = trimmed.slice(5).trim();
          if (!payload || payload === "[DONE]") continue;
          try {
            collectImages(JSON.parse(payload), path + ".sse", out);
          } catch {}
        }
      }

      function inlineMimeType(value) {
        return String(value?.mimeType || value?.mime_type || value?.contentType || value?.content_type || "");
      }

      function objectLooksImageRelated(value, path) {
        const type = String(value?.type || value?.kind || value?.mimeType || value?.mime_type || "");
        return /\\b(image|img|output_image|input_image|photo|picture)\\b/i.test(type + " " + path);
      }

      function extractImageRefsFromString(value) {
        const text = String(value || "");
        const refs = [];
        if (text.startsWith("data:image/")) refs.push(text);
        const dataMatches = text.match(/data:image\\/[a-zA-Z0-9.+-]+;base64,[a-zA-Z0-9+/=]+/g) || [];
        refs.push(...dataMatches);
        for (const match of text.matchAll(/!\\[[^\\]]*\\]\\(([^)]+)\\)/g)) {
          const cleaned = String(match[1] || "").trim().replace(/^["']|["']$/g, "");
          if (isImageRefCandidate(cleaned)) refs.push(cleaned);
        }
        for (const match of text.matchAll(/<img\\b[^>]*\\bsrc=["']([^"']+)["'][^>]*>/gi)) {
          const cleaned = String(match[1] || "").trim();
          if (isImageRefCandidate(cleaned)) refs.push(cleaned);
        }
        const urlMatches = text.match(/https?:\\/\\/[^\\s"'<>\\])}]+/g) || [];
        for (const raw of urlMatches) {
          const cleaned = raw.replace(/[.,;:!?]+$/g, "");
          if (isImageRefCandidate(cleaned, { strict: true })) refs.push(cleaned);
        }
        return dedupe(refs);
      }

      function isImageRefCandidate(value, options = {}) {
        const text = String(value || "");
        if (text.startsWith("data:image/")) return true;
        if (!/^https?:\\/\\//i.test(text)) return false;
        if (/\\.(png|jpe?g|webp|gif|avif)(\\?|#|$)/i.test(text)) return true;
        if (options.strict) return false;
        if (/\\b(api-docs|openapi|swagger|docs?)\\b/i.test(text)) return false;
        return true;
      }

      async function resolveRenderableImages(images) {
        const seen = new Set();
        const candidates = [];
        for (const image of images || []) {
          const src = String(image?.src || "").trim();
          if (!src || seen.has(src)) continue;
          seen.add(src);
          candidates.push({ ...image, src });
        }
        const resolved = [];
        for (const image of candidates) {
          if (resolved.length >= 12) break;
          if (await imageCanLoad(image.src)) resolved.push(image);
          else pushAiStep("Skipped non-renderable image candidate: " + truncateMiddle(image.src, 72), "info");
        }
        return resolved;
      }

      function imageCanLoad(src) {
        return new Promise((resolve) => {
          if (!src) return resolve(false);
          if (src.startsWith("data:image/")) return resolve(true);
          const image = new Image();
          const timeout = setTimeout(() => {
            image.onload = null;
            image.onerror = null;
            resolve(false);
          }, 8000);
          image.onload = () => {
            clearTimeout(timeout);
            resolve(Boolean(image.naturalWidth || image.width));
          };
          image.onerror = () => {
            clearTimeout(timeout);
            resolve(false);
          };
          image.referrerPolicy = "no-referrer-when-downgrade";
          image.src = src;
        });
      }

      function collectTextFragments(value, out = []) {
        if (!value || out.length > 60) return out;
        if (typeof value === "string") {
          const clean = value.trim();
          const streamText = extractStreamText(clean);
          if (streamText) {
            out.push(streamText);
          } else if (clean && clean.length > 2 && !clean.startsWith("data:image/")) {
            out.push(clean.length > 8000 ? clean.slice(0, 8000) + "\\n..." : clean);
          }
          return out;
        }
        if (Array.isArray(value)) {
          value.forEach((item) => collectTextFragments(item, out));
          return out;
        }
        if (typeof value === "object") {
          for (const [key, child] of Object.entries(value)) {
            if (typeof child === "string" && /^(text|content|output|message|delta|reasoning|caption)$/i.test(key)) {
              collectTextFragments(child, out);
            } else if (typeof child === "object") {
              collectTextFragments(child, out);
            }
          }
        }
        return dedupe(out);
      }

      function extractStreamText(value) {
        if (!value || !value.includes("data:")) return "";
        const fragments = [];
        for (const line of value.split(/\\r?\\n/)) {
          const trimmed = line.trim();
          if (!trimmed.startsWith("data:")) continue;
          const payload = trimmed.slice(5).trim();
          if (!payload || payload === "[DONE]") continue;
          try {
            const json = JSON.parse(payload);
            collectStreamText(json, fragments);
          } catch {
            if (payload.length < 500) fragments.push(payload);
          }
        }
        return fragments.join("").trim();
      }

      function collectStreamText(value, out) {
        if (!value) return;
        if (typeof value === "string") {
          out.push(value);
          return;
        }
        if (Array.isArray(value)) {
          value.forEach((item) => collectStreamText(item, out));
          return;
        }
        if (typeof value !== "object") return;
        if (typeof value.content === "string") out.push(value.content);
        if (typeof value.text === "string") out.push(value.text);
        if (typeof value.output_text === "string") out.push(value.output_text);
        if (value.delta) collectStreamText(value.delta, out);
        if (value.message) collectStreamText(value.message, out);
        if (Array.isArray(value.choices)) {
          value.choices.forEach((choice) => {
            collectStreamText(choice.delta, out);
            collectStreamText(choice.message, out);
            if (typeof choice.text === "string") out.push(choice.text);
          });
        }
        if (Array.isArray(value.output)) collectStreamText(value.output, out);
      }

      function findFirstKey(value, wanted) {
        if (!value || typeof value !== "object") return undefined;
        if (Object.prototype.hasOwnProperty.call(value, wanted)) return value[wanted];
        if (Array.isArray(value)) {
          for (const item of value) {
            const found = findFirstKey(item, wanted);
            if (found !== undefined) return found;
          }
          return undefined;
        }
        for (const child of Object.values(value)) {
          const found = findFirstKey(child, wanted);
          if (found !== undefined) return found;
        }
        return undefined;
      }

      async function runWithConcurrency(items, limit, worker) {
        let index = 0;
        const runners = Array.from({ length: Math.min(limit, items.length) }, async () => {
          while (index < items.length && !state.abortDrill) {
            const current = items[index++];
            await worker(current);
          }
        });
        await Promise.all(runners);
      }

      function jsonHeaders(withContentType = true) {
        const headers = { accept: "application/json", "x-api-version": "2026-04-20" };
        if (withContentType) headers["content-type"] = "application/json";
        return headers;
      }

      function getRequestId(item) {
        return item && (item.requestId || item.generationId || item.id || "");
      }

      function firstValue(item, keys) {
        for (const key of keys) {
          if (item && item[key] !== undefined && item[key] !== null && item[key] !== "") return String(item[key]);
        }
        return "";
      }

      function formatNumber(value) {
        if (value === "" || value === undefined || value === null) return "";
        const number = Number(value);
        return Number.isFinite(number) ? String(Math.round(number)) + " ms" : String(value);
      }

      function formatCost(value) {
        if (value === "" || value === undefined || value === null) return "";
        const number = Number(value);
        return Number.isFinite(number) ? number.toFixed(number >= 1 ? 3 : 6) : String(value);
      }

      function formatTime(value) {
        if (!value) return "";
        const number = Number(value);
        const date = Number.isFinite(number) ? new Date(number) : new Date(value);
        if (Number.isNaN(date.getTime())) return String(value);
        return date.toLocaleString();
      }

      function setBusy(value) {
        document.getElementById("run-list").disabled = value;
      }

      function setEvent(message, level = "info") {
        state.events.unshift({ message, level, at: new Date().toLocaleTimeString() });
        state.events = state.events.slice(0, 8);
        const summary = document.getElementById("graph-summary");
        const eventHtml = state.events.map((event) =>
          '<div class="log-line ' + escapeAttr(event.level) + '"><span class="code">' + escapeHtml(event.at) + '</span> ' + escapeHtml(event.message) + '</div>'
        ).join("");
        summary.innerHTML = [
          ...graphSummaryPills(),
          '<div style="flex-basis:100%"></div>',
          eventHtml
        ].filter(Boolean).join("");
      }

      function dedupe(values) {
        return [...new Set(values)];
      }

      function sleep(ms) {
        return new Promise((resolve) => setTimeout(resolve, ms));
      }

      function escapeRegExp(value) {
        return String(value)
          .replace(/[.*+?^$()|[\\]\\\\]/g, "\\\\$&")
          .replace(/[{}]/g, "\\\\$&");
      }

      function escapeHtml(value) {
        return String(value ?? "")
          .replace(/&/g, "&amp;")
          .replace(/</g, "&lt;")
          .replace(/>/g, "&gt;")
          .replace(/"/g, "&quot;")
          .replace(/'/g, "&#39;");
      }

      function escapeAttr(value) {
        return escapeHtml(value).replace(new RegExp(String.fromCharCode(96), "g"), "&#96;");
      }

      function escapeSvg(value) {
        return escapeHtml(value).replace(/\\$/g, "");
      }
    </script>
  </body>
</html>
`;
}

function createEndpointOperationSpecs(openapi) {
  const specs = [];
  const methods = new Set(["get", "post", "put", "patch", "delete", "head", "options"]);
  for (const [path, pathItem] of Object.entries(openapi.paths || {})) {
    for (const [methodKey, operation] of Object.entries(pathItem || {})) {
      if (!methods.has(methodKey) || !operation) continue;
      const parameters = (operation.parameters || [])
        .map((parameter) => resolveOpenapiRef(openapi, parameter))
        .filter(Boolean)
        .map((parameter) => ({
          name: parameter.name,
          in: parameter.in,
          required: Boolean(parameter.required),
          default: parameter.schema?.default,
          example: parameter.example ?? parameter.schema?.example
        }));
      const requestBodyContent = operation.requestBody?.content?.["application/json"];
      specs.push({
        method: methodKey.toUpperCase(),
        path,
        operationId: operation.operationId,
        parameters,
        hasRequestBody: Boolean(operation.requestBody),
        requestBodyExample: requestBodyExample(requestBodyContent)
      });
    }
  }
  return specs;
}

function resolveOpenapiRef(openapi, value) {
  if (!value?.$ref) return value;
  const parts = value.$ref.replace(/^#\//, "").split("/");
  let cursor = openapi;
  for (const part of parts) {
    cursor = cursor?.[part];
  }
  return cursor || value;
}

function requestBodyExample(content) {
  if (!content) return undefined;
  if (content.example !== undefined) return content.example;
  const firstExample = Object.values(content.examples || {})[0];
  if (firstExample?.value !== undefined) return firstExample.value;
  return content.schema?.example;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
