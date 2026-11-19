export const DSHFIND_CATEGORIES_QUERY = "query DshFindCategories { pluginFacets { categories { value count } } }";
export const DSHFIND_DATASET_QUERY = "query DshFindDataset { dataset { dataVersion asOf } }";
export const DSHFIND_FACETS_QUERY = "query DshFindFacets { pluginFacets { categories { value count } languages { value count } tags { value count } grades { value count } } }";
export const DSHFIND_GRAPHQL_PLUGINS_QUERY = "query DshFindPlugins($first: Int = 20, $after: String, $filter: PluginFilter, $sort: PluginSort = DEFAULT, $order: SortOrder = DESC) { plugins(first: $first, after: $after, filter: $filter, sort: $sort, order: $order) { totalCount dataVersion asOf nodes { id fullName name owner repositoryUrl description tags language stars contributors pushedAt archived category score grade isFeatured isOfficial isInsider isRisky riskNote isPlugin install { cmd source kind pkgName npmPublished releaseTgzUrl releaseTag probedAt } } pageInfo { hasNextPage endCursor } } }";
export const DSHFIND_GRAPHQL_PLUGIN_QUERY = "query DshFindPlugin($fullName: ID!, $locale: String, $days: Int = 30) { plugin(fullName: $fullName) { id fullName name owner repositoryUrl description tags language stars contributors pushedAt archived category score grade rating { score grade calculatedAt version } isFeatured isOfficial isInsider isRisky riskNote isPlugin install { cmd source kind pkgName npmPublished releaseTgzUrl releaseTag probedAt } firstSeenAt lastSyncedAt i18n(locale: $locale) { locale description intro highlights updatedAt } snapshots(days: $days) { date stars contributors pushedAt } growth { windowDays stars contributors } } }";

export function createDshFindOpenapi() {
  return {
    openapi: "3.1.0",
    info: {
      title: "dshfind Public Plugin Directory API",
      version: "0.5.0",
      description:
        "Observed read-only contract for the public dshfind plugin directory and its standard DSH market feed. Built from the public /zh/plugins page, the public source contract, and live unauthenticated response samples."
    },
    servers: [{ url: "https://api.dshfind.com" }],
    security: [],
    tags: [
      { name: "Plugins", description: "Public plugin search, listing, detail, and bulk catalog endpoints." },
      { name: "Categories", description: "Public plugin category facets used by directory filters." },
      { name: "GraphQL", description: "Public read-only field-selectable GraphQL endpoint and published SDL." },
      { name: "Market", description: "Standard DSH catalog-source manifest and cursor-paginated market feed." },
      { name: "Service", description: "Public service health and loaded-catalog status." }
    ],
    paths: {
      "/v1/suggest": {
        get: {
          tags: ["Plugins"],
          operationId: "suggestPlugins",
          summary: "Suggest plugins by keyword",
          parameters: [query("q", string({ maxLength: 64, example: "memory" }), false, "At least two trimmed characters are needed for results.")],
          responses: jsonResponses("Plugin suggestions", ref("SuggestionResponse"))
        }
      },
      "/graphql": {
        get: {
          tags: ["Categories"],
          operationId: "listPluginCategories",
          summary: "Get available plugin categories and counts",
          description: "Read the public GraphQL pluginFacets category dimension used to populate category filters.",
          parameters: [
            query("query", string({ example: DSHFIND_CATEGORIES_QUERY }), true, "Fixed read-only GraphQL category-facet query.")
          ],
          responses: jsonResponses("Plugin category facets", ref("GraphQLCategoriesResponse"))
        },
        post: {
          tags: ["GraphQL"],
          operationId: "executeGraphQLQuery",
          summary: "Execute a public read-only GraphQL query",
          description: "Run any query allowed by the published SDL. Mutations, subscriptions, directives, introspection, and private fields are not supported.",
          requestBody: {
            required: true,
            content: {
              "application/json": {
                schema: ref("GraphQLRequest"),
                examples: {
                  dataset: graphqlExample("Dataset metadata", DSHFIND_DATASET_QUERY, {}, "DshFindDataset"),
                  facets: graphqlExample("All filter facets", DSHFIND_FACETS_QUERY, {}, "DshFindFacets"),
                  plugins: graphqlExample("Filtered cursor page", DSHFIND_GRAPHQL_PLUGINS_QUERY, {
                    first: 5,
                    after: null,
                    filter: { category: "memory", hasInstall: true },
                    sort: "STARS",
                    order: "DESC"
                  }, "DshFindPlugins"),
                  plugin: graphqlExample("Rich plugin detail", DSHFIND_GRAPHQL_PLUGIN_QUERY, {
                    fullName: "deepseek-ai/deepseek-harness",
                    locale: "zh",
                    days: 7
                  }, "DshFindPlugin")
                }
              }
            }
          },
          responses: jsonResponses("GraphQL result", ref("GraphQLResponse"))
        }
      },
      "/graphql/schema": {
        get: {
          tags: ["GraphQL"],
          operationId: "getGraphQLSchema",
          summary: "Download the published GraphQL SDL",
          description: "The service intentionally disables introspection and publishes its current read-only schema at this endpoint instead.",
          responses: {
            "200": {
              description: "GraphQL SDL",
              content: { "application/graphql": { schema: string() } }
            },
            default: jsonResponse("API error", ref("Error"))
          }
        }
      },
      "/v1/plugins": {
        get: {
          tags: ["Plugins"],
          operationId: "listPlugins",
          summary: "List and filter public plugins",
          parameters: [
            query("page", integer({ minimum: 1, default: 1 })),
            query("per_page", integer({ minimum: 1, maximum: 100, default: 20 })),
            query("q", string({ maxLength: 64, example: "memory" })),
            query("category", string({ example: "memory" })),
            query("language", string({ example: "TypeScript" })),
            query("grade", { type: "string", enum: ["S", "A", "B", "C"] }),
            query("owner", string({ example: "omdsh-dev" })),
            query("tag", string({ example: "agent-memory" })),
            query("min_score", integer({ minimum: 0, maximum: 100 })),
            ...["featured", "official", "archived", "insider", "has_install"].map((name) => query(name, bool())),
            query("is_plugin", { oneOf: [bool(), { type: "integer", enum: [0, 1] }] }),
            query("sort", { type: "string", enum: ["stars", "updated", "score", "name"] }),
            query("order", { type: "string", enum: ["asc", "desc"] }),
            query("data_version", string({ example: "sha256:40737aa648314fda85e3be3ac4c24f681b2478be29ca043af1369a54fc0d68f0" }))
          ],
          responses: {
            ...jsonResponses("Plugin page", ref("PluginListResponse")),
            "409": jsonResponse("The pinned data version is stale; restart at page 1.", ref("Error"))
          }
        }
      },
      "/v1/plugins/{owner}/{repo}": {
        get: {
          tags: ["Plugins"],
          operationId: "getPlugin",
          summary: "Get one plugin with localized details and growth",
          parameters: [
            path("owner", "Repository owner", "deepseek-ai"),
            path("repo", "Repository name", "deepseek-harness"),
            query("snapshot_days", integer({ minimum: 1, maximum: 90, default: 30 }))
          ],
          responses: {
            ...jsonResponses("Plugin detail", ref("PluginDetail")),
            "404": jsonResponse("Plugin not found", ref("Error"))
          }
        }
      },
      "/v1/catalog": {
        get: {
          tags: ["Plugins"],
          operationId: "getCatalog",
          summary: "Download the complete plugin catalog snapshot",
          description: "The response can be several megabytes. Pass a data_version learned from listPlugins to request a stable snapshot.",
          parameters: [query("data_version", string({ example: "sha256:40737aa648314fda85e3be3ac4c24f681b2478be29ca043af1369a54fc0d68f0" }))],
          responses: jsonResponses("Complete plugin catalog", ref("CatalogResponse"))
        }
      },
      "/market/manifest.json": {
        get: {
          tags: ["Market"],
          operationId: "getMarketManifest",
          summary: "Get the standard DSH catalog-source manifest",
          responses: jsonResponses("Catalog source manifest", ref("MarketManifest"))
        }
      },
      "/market/v1/plugins": {
        get: {
          tags: ["Market"],
          operationId: "listMarketPlugins",
          summary: "Page through the standard DSH market catalog",
          parameters: [
            query("q", string({ example: "memory" })),
            query("category", string({ example: "memory" })),
            query("limit", integer({ minimum: 1, maximum: 100, default: 50 })),
            query("cursor", string({ description: "Opaque cursor from the previous page.nextCursor value." }))
          ],
          responses: jsonResponses("Standard market catalog page", ref("MarketPage"))
        }
      },
      "/healthz": {
        get: {
          tags: ["Service"],
          operationId: "getHealth",
          summary: "Read public service health",
          responses: {
            "200": jsonResponse("API and plugin snapshot are healthy", ref("Health")),
            "503": jsonResponse("Plugin snapshot is unavailable", ref("Health"))
          }
        }
      }
    },
    components: {
      schemas: {
        Error: object({ error: string(), message: string() }),
        InstallInfo: object({
          cmd: nullable(string()),
          source: nullable({ type: "string", enum: ["manual", "auto"] }),
          kind: nullable({ type: "string", enum: ["release", "npm", "git", "build-required", "not-installable"] }),
          pkg_name: nullable(string()),
          pkg_version: nullable(string()),
          npm_published: nullable(bool()),
          probed_at: nullable(dateTime())
        }),
        Plugin: object({
          full_name: string({ example: "deepseek-ai/deepseek-harness" }),
          name: string({ example: "deepseek-harness" }),
          owner: string({ example: "deepseek-ai" }),
          url: uri(),
          repository_url: uri(),
          description: nullable(string()),
          tags: array(string()),
          language: nullable(string()),
          stars: integer({ minimum: 0 }),
          contributors: nullable(integer({ minimum: 0 })),
          pushed_at: nullable(dateTime()),
          archived: bool(),
          category: string(),
          score: nullable(integer({ minimum: 0, maximum: 100 })),
          grade: nullable({ type: "string", enum: ["S", "A", "B", "C"] }),
          scored_at: nullable(dateTime()),
          score_version: nullable(string()),
          is_featured: bool(),
          is_official: bool(),
          is_insider: bool(),
          is_risky: bool(),
          risk_note: nullable(string()),
          is_plugin: nullable(bool()),
          install: nullable(ref("InstallInfo")),
          first_seen_at: nullable(dateTime()),
          last_synced_at: nullable(dateTime())
        }, ["full_name", "name", "owner", "repository_url", "tags", "stars"]),
        PluginListResponse: object({
          data: array(ref("Plugin")),
          page: integer(),
          per_page: integer(),
          total: integer(),
          total_pages: integer(),
          data_version: string(),
          as_of: dateTime(),
          generated_at: dateTime()
        }, ["data", "page", "per_page", "total", "total_pages", "data_version"]),
        CatalogResponse: object({
          data: array(ref("Plugin")),
          total: integer(),
          data_version: string(),
          as_of: dateTime(),
          generated_at: dateTime()
        }, ["data", "total", "data_version"]),
        Suggestion: object({
          type: { type: "string", const: "plugin" },
          id: string(),
          label: string(),
          sub: string(),
          href: string({ example: "/plugins/omdsh-dev/dsh-mnemon" }),
          stars: integer({ minimum: 0 }),
          featured: bool()
        }, ["type", "id", "label", "href", "stars", "featured"]),
        SuggestionResponse: object({ items: array(ref("Suggestion"), { maxItems: 10 }) }, ["items"]),
        PluginFacet: object({
          value: string({ example: "memory" }),
          count: integer({ minimum: 0, example: 468 })
        }, ["value", "count"]),
        GraphQLError: object({ message: string() }, ["message"]),
        GraphQLRequest: object({
          query: string({ description: "A read-only operation accepted by the published SDL." }),
          variables: { type: "object", additionalProperties: true },
          operationName: nullable(string())
        }, ["query"]),
        GraphQLResponse: object({
          data: nullable({ type: "object", additionalProperties: true }),
          errors: array(ref("GraphQLError"))
        }),
        GraphQLCategoriesResponse: object({
          data: nullable(object({
            pluginFacets: object({ categories: array(ref("PluginFacet")) }, ["categories"])
          }, ["pluginFacets"])),
          errors: array(ref("GraphQLError"))
        }),
        LocalizedPluginCopy: object({
          description: nullable(string()),
          intro: nullable(string()),
          highlights: array(string()),
          updated_at: nullable(dateTime())
        }),
        PluginSnapshot: object({
          date: { type: "string", format: "date" },
          stars: integer({ minimum: 0 }),
          contributors: nullable(integer({ minimum: 0 })),
          pushed_at: nullable(dateTime())
        }),
        PluginGrowth: object({
          window_days: integer({ minimum: 1 }),
          stars: integer(),
          contributors: integer()
        }),
        PluginDetail: {
          allOf: [
            ref("Plugin"),
            object({
              i18n: { type: "object", additionalProperties: ref("LocalizedPluginCopy") },
              snapshots: array(ref("PluginSnapshot")),
              growth: ref("PluginGrowth"),
              data_version: string(),
              as_of: dateTime()
            })
          ]
        },
        MarketManifest: object({
          manifestVersion: { type: "string", const: "1.0.0" },
          providerId: string(),
          name: string(),
          description: string(),
          homepage: uri(),
          attribution: object({ name: string(), url: uri() }),
          transport: object({ kind: { type: "string", const: "https-json" }, endpoint: uri(), method: { type: "string", const: "GET" } }),
          query: object({ supported: array(string()), defaultLimit: integer(), maxLimit: integer(), sorts: array(string()) })
        }, ["manifestVersion", "providerId", "name", "transport", "query"]),
        MarketItem: object({
          id: string(),
          name: string(),
          displayName: string(),
          summary: string(),
          homepage: uri(),
          latestVersion: string(),
          license: string(),
          categories: array(string()),
          keywords: array(string()),
          repository: object({ url: uri() }),
          package: object({ registry: { type: "string", const: "npm" }, name: string() }),
          publisher: object({ name: string(), url: uri() }),
          updatedAt: dateTime()
        }, ["id", "name", "displayName", "summary"]),
        MarketPage: object({
          schemaVersion: { type: "string", const: "1.0.0" },
          generatedAt: dateTime(),
          revision: string(),
          items: array(ref("MarketItem")),
          page: object({ nextCursor: string(), total: integer({ minimum: 0 }) }, ["total"])
        }, ["schemaVersion", "generatedAt", "revision", "items", "page"]),
        Health: object({
          status: string(),
          plugins_loaded: integer({ minimum: 0 }),
          commit_sha: string(),
          deployment_id: string(),
          cache_loaded_at: dateTime(),
          audit_queue: integer({ minimum: 0 }),
          audit_dropped: integer({ minimum: 0 }),
          rate_limit_backend: string(),
          rate_limit_redis_fallbacks: integer({ minimum: 0 })
        }, ["status", "plugins_loaded"])
      }
    },
    "x-cli-anything-links": [
      {
        id: "listPlugins-to-getPlugin",
        from: "listPlugins",
        to: "getPlugin",
        sourceSelector: "$.data[*].full_name",
        parameterMap: { owner: "$item.owner", repo: "$item.name" }
      },
      {
        id: "listPlugins-to-getCatalog",
        from: "listPlugins",
        to: "getCatalog",
        sourceSelector: "$.data_version",
        parameterMap: { data_version: "$.data_version" }
      },
      {
        id: "getMarketManifest-to-listMarketPlugins",
        from: "getMarketManifest",
        to: "listMarketPlugins",
        sourceSelector: "$.transport.endpoint",
        parameterMap: {}
      }
    ]
  };
}

function ref(name) {
  return { $ref: `#/components/schemas/${name}` };
}

function string(extra = {}) {
  return { type: "string", ...extra };
}

function integer(extra = {}) {
  return { type: "integer", ...extra };
}

function bool(extra = {}) {
  return { type: "boolean", ...extra };
}

function array(items, extra = {}) {
  return { type: "array", items, ...extra };
}

function object(properties, required = []) {
  return { type: "object", properties, ...(required.length ? { required } : {}), additionalProperties: false };
}

function nullable(schema) {
  return { anyOf: [schema, { type: "null" }] };
}

function uri() {
  return string({ format: "uri" });
}

function dateTime() {
  return string({ format: "date-time" });
}

function query(name, schema, required = false, description) {
  return { name, in: "query", required, schema, ...(description ? { description } : {}) };
}

function path(name, description, example) {
  return { name, in: "path", required: true, description, schema: string({ example }) };
}

function jsonResponse(description, schema) {
  return { description, content: { "application/json": { schema } } };
}

function jsonResponses(description, schema) {
  return {
    "200": jsonResponse(description, schema),
    default: jsonResponse("API error", ref("Error"))
  };
}

function graphqlExample(summary, queryText, variables, operationName) {
  return { summary, value: { query: queryText, variables, operationName } };
}
