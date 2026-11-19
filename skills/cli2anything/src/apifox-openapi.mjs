import { DSHFIND_CATEGORIES_QUERY } from "./dshfind-openapi.mjs";

const APIFOX_EXAMPLES = {
  suggestPlugins: { q: "memory" },
  listPluginCategories: { query: DSHFIND_CATEGORIES_QUERY },
  executeGraphQLQuery: {},
  getGraphQLSchema: {},
  listPlugins: { q: "memory", page: 1, per_page: 5, sort: "stars", order: "desc" },
  getPlugin: { owner: "deepseek-ai", repo: "deepseek-harness", snapshot_days: 7 },
  getCatalog: {},
  getMarketManifest: {},
  listMarketPlugins: { limit: 5 },
  getHealth: {}
};

export function createApifoxOpenapi(openapi) {
  const spec = structuredClone(openapi);
  spec.info = {
    ...spec.info,
    title: "dshfind 插件目录 API v0.5.0（Apifox 调试版）",
    version: "0.5.0",
    description: [
      "面向 Apifox 文件导入和直接调试的公开只读契约。",
      "导入时启用“导入 Servers 为环境”和“自动生成接口用例”，选择生成的生产环境后即可发送。",
      "所有请求均无需鉴权；示例参数经过约束，不包含会过期的 data_version、cursor、Cookie 或 Token。"
    ].join("\n\n")
  };
  spec.servers = [{
    url: "https://api.dshfind.com",
    description: "生产环境（公开只读，无需鉴权）"
  }];
  spec.security = [];

  for (const pathItem of Object.values(spec.paths || {})) {
    for (const [method, operation] of Object.entries(pathItem || {})) {
      if (!isHttpMethod(method) || !operation) continue;
      operation.security = [];
      const examples = APIFOX_EXAMPLES[operation.operationId] || {};
      for (const parameter of operation.parameters || []) {
        delete parameter.example;
        if (parameter.schema && typeof parameter.schema === "object") {
          delete parameter.schema.example;
          delete parameter.schema.default;
        }
        if (Object.hasOwn(examples, parameter.name)) {
          parameter.example = examples[parameter.name];
          if (parameter.schema && typeof parameter.schema === "object") {
            parameter.schema.default = examples[parameter.name];
          }
        }
      }
    }
  }

  spec.externalDocs = {
    description: "dshfind 插件超市",
    url: "https://dshfind.com/zh/plugins"
  };
  return spec;
}

export function createApifoxReadme() {
  return `# 在 Apifox 中开箱即用调试

导入文件：\`openapi.json\`

定时导入地址：\`https://dshfind.lovstudio.ai/openapi.json\`

导入后先核对项目标题含 \`v0.5.0\`，并且总计显示 10 个接口，其中包括独立的 \`Categories (1)\` 与 \`GraphQL (2)\`。如果仍是旧数量，说明打开的是旧版项目，需要重新从最新版文件导入。

## 推荐：绑定在线数据源

1. 进入“项目设置 → 导入数据 → 定时导入（绑定数据源）”。
2. 数据源格式选择 OpenAPI，URL 填写 \`https://dshfind.lovstudio.ai/openapi.json\`。
3. 设置导入频率，并启用“导入 Servers 为环境”和“自动生成接口用例”。
4. 保存后可立即导入；以后 Apifox 会按频率从同一 URL 刷新。

## 导入

1. 在 Apifox 项目列表选择“导入项目”，或在已有项目中进入“项目设置 → 导入数据 → 手动导入”。
2. 选择本目录的 \`openapi.json\`，格式选择 OpenAPI。
3. 在导入设置中启用：
   - “导入 Servers 为环境”
   - “自动生成接口用例”
4. 导入后选择“生产环境（公开只读，无需鉴权）”。

## 调试

打开任一接口的“运行”页，直接点击“发送”。无需填写 Base URL、Cookie、Token 或 API Key。

已内置安全示例：

- 搜索建议：\`q=memory\`
- 插件分类：公开 GraphQL \`pluginFacets.categories\` 查询，无需填写参数
- GraphQL 查询：在 Body 示例中选择 \`dataset\`、\`facets\`、\`plugins\` 或 \`plugin\`，可直接发送 POST 请求
- GraphQL Schema：直接下载服务端公开 SDL；该服务以此替代 introspection
- 插件列表：\`q=memory&page=1&per_page=5&sort=stars&order=desc\`
- 插件详情：\`deepseek-ai/deepseek-harness?snapshot_days=7\`
- 标准市场分页：\`limit=5\`

\`data_version\` 与 \`cursor\` 会随线上数据变化，因此没有写入默认值；需要连续分页时，把上一响应中的值复制到下一请求即可。

GraphQL \`plugins\` 使用独立的游标分页：把上一响应的 \`pageInfo.endCursor\` 填入下一请求的 \`variables.after\`，并保持 filter、sort、order 不变。
`;
}

function isHttpMethod(value) {
  return new Set(["get", "post", "put", "patch", "delete", "head", "options", "trace"]).has(value);
}
