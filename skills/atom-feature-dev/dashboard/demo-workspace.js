"use strict";

// Read-only snapshot used only when index.html is opened directly with file://.
window.ATOM_WORKBENCH_DEMO = {
  workspace: {
    name: "demo-project",
    connected: false,
    run_enabled: false,
    write_enabled: false,
    mode: "file-preview",
  },
  manifest: {
    schema: "lovstudio/atom-feature/v1",
    version: "0.2.0",
    feature: {
      id: "markdown-to-pdf",
      title: "Markdown to PDF",
      summary: "把 Markdown 与 Profile Preset 转成带目录、可搜索的 PDF，并让每个 surface 返回同一业务结果。",
      status: "planned",
    },
    contracts: {
      feature: ".atom-feature/contract.schema.json",
      profiles: ".atom-feature/profiles.schema.json",
      acceptance: ".atom-feature/acceptance.json",
    },
    surfaces: {
      sdk: {
        status: "implemented",
        artifact: "sdk.py",
        contract: ".atom-feature/contract.schema.json",
        command: ["python3", "sdk.py"],
        verification: [],
        reason: null,
      },
      cli: {
        status: "implemented",
        artifact: "sdk.py",
        contract: ".atom-feature/contract.schema.json",
        command: ["python3", "sdk.py"],
        verification: [],
        reason: null,
      },
      api: {
        status: "planned",
        artifact: null,
        contract: ".atom-feature/contract.schema.json",
        command: null,
        verification: [],
        reason: null,
      },
      ui: {
        status: "planned",
        artifact: null,
        contract: ".atom-feature/contract.schema.json",
        command: null,
        verification: [],
        reason: null,
      },
      agent: {
        status: "planned",
        artifact: null,
        contract: ".atom-feature/contract.schema.json",
        command: null,
        verification: [],
        reason: null,
      },
    },
    operations: {
      docs: { status: "implemented", artifact: "docs.md", verification: [], reason: null },
      tests: { status: "implemented", artifact: "sdk.py", verification: [], reason: null },
      seo: { status: "not-applicable", artifact: null, verification: [], reason: "Local export feature" },
      geo: { status: "not-applicable", artifact: null, verification: [], reason: "No public discovery surface" },
      auth: { status: "not-applicable", artifact: null, verification: [], reason: "Single-user local workflow" },
      payment: { status: "not-applicable", artifact: null, verification: [], reason: "No commercial entitlement" },
      analytics: { status: "planned", artifact: null, verification: [], reason: null },
      support: { status: "planned", artifact: null, verification: [], reason: null },
    },
    dashboard: {
      status: "implemented",
      artifact: "dashboard-entry.json",
      route: "http://127.0.0.1:6174/",
      verification: [],
    },
  },
  contract: {
    $schema: "https://json-schema.org/draft/2020-12/schema",
    $id: "urn:lovstudio:atom-feature:markdown-to-pdf:contract",
    title: "Markdown to PDF",
    type: "object",
    properties: {
      input: {
        type: "object",
        properties: {
          source: { type: "string", minLength: 1 },
          paper: { type: "string", enum: ["A4", "Letter"] },
          tocDepth: { type: "integer", minimum: 1, maximum: 6 },
          searchable: { type: "boolean" },
        },
        required: ["source"],
      },
      output: {
        type: "object",
        properties: {
          artifact: { type: "string" },
          paper: { type: "string" },
          tocDepth: { type: "integer" },
          searchable: { type: "boolean" },
        },
        required: ["artifact", "paper", "tocDepth", "searchable"],
      },
    },
    required: ["input"],
    additionalProperties: false,
  },
  profiles_schema: {
    $schema: "https://json-schema.org/draft/2020-12/schema",
    $id: "urn:lovstudio:atom-feature:markdown-to-pdf:profiles",
    title: "Markdown to PDF Profile Preset",
    type: "object",
    properties: {
      name: { type: "string", minLength: 1 },
      values: {
        type: "object",
        properties: {
          paper: { type: "string", enum: ["A4", "Letter"] },
          tocDepth: { type: "integer", minimum: 1, maximum: 6 },
          searchable: { type: "boolean" },
        },
        additionalProperties: false,
      },
    },
    required: ["name", "values"],
    additionalProperties: false,
  },
  acceptance: {
    schema: "lovstudio/atom-feature/v1",
    vectors: [
      {
        id: "balanced-export",
        name: "Balanced export",
        input: { source: "demo.md" },
        expected: { artifact: "demo.pdf", paper: "A4", tocDepth: 3, searchable: true },
      },
      {
        id: "deep-outline",
        name: "Deep outline",
        input: { source: "demo.md", tocDepth: 5 },
        expected: { artifact: "demo.pdf", paper: "A4", tocDepth: 5, searchable: true },
      },
    ],
  },
  presets: {
    active: "balanced",
    presets: [
      {
        id: "balanced",
        name: "Balanced",
        values: { paper: "A4", tocDepth: 3, searchable: true },
      },
      {
        id: "print-letter",
        name: "Print · Letter",
        values: { paper: "Letter", tocDepth: 2, searchable: true },
      },
    ],
  },
  status: { schema: "lovstudio/atom-feature/v1", runs: [] },
};
