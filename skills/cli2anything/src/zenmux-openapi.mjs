import { createZenmuxDrilldownLinks } from "./api-graph.mjs";

export function createZenmuxOpenapi() {
  const listLogsExample = createListLogsExample();
  const requestIdExample = "paste-request-id-from-listLogs";

  return {
    openapi: "3.1.0",
    info: {
      title: "ZenMux Observed Logs API",
      version: "0.1.0",
      description:
        "Observed OpenAPI contract for ZenMux log list/detail workflows. Endpoints are derived from public documentation and public frontend bundle evidence; use only with an authorized ZenMux account/API key."
    },
    servers: [{ url: "https://zenmux.ai" }],
    security: [{ bearerAuth: [] }],
    tags: [{ name: "Logs" }, { name: "Generation payloads" }],
    paths: {
      "/api/api_key/activity": {
        post: {
          tags: ["Logs"],
          operationId: "listLogs",
          summary: "List request logs",
          description:
            "Dashboard log list endpoint observed in the ZenMux frontend bundle. Live API-key-only calls reach this endpoint but fail without console CSRF/session credentials.",
          security: [
            { consoleCookie: [], csrfToken: [] },
            { bearerAuth: [], csrfToken: [] }
          ],
          parameters: [{ $ref: "#/components/parameters/ApiVersionHeader" }],
          requestBody: {
            required: true,
            content: {
              "application/json": {
                schema: { $ref: "#/components/schemas/ListLogsRequest" },
                example: listLogsExample,
                examples: {
                  recentLogs: {
                    summary: "Recent logs, first page",
                    description: "Works in browser-session mode. Replace filter arrays or requestId only when you want to narrow the result.",
                    value: listLogsExample
                  }
                }
              }
            }
          },
          responses: {
            "200": {
              description: "Log list response",
              content: {
                "application/json": {
                  schema: { $ref: "#/components/schemas/ListLogsResponse" }
                }
              },
              links: createListLogsResponseLinks()
            },
            default: { $ref: "#/components/responses/Error" }
          }
        }
      },
      "/api/api_key/activity/{requestId}": {
        get: {
          tags: ["Logs"],
          operationId: "getLogActivity",
          summary: "Get dashboard log activity detail",
          description:
            "Dashboard activity detail endpoint observed in the ZenMux frontend bundle. It uses the same console CSRF/session credential model as the log list endpoint.",
          security: [
            { consoleCookie: [], csrfToken: [] },
            { bearerAuth: [], csrfToken: [] }
          ],
          parameters: [
            { $ref: "#/components/parameters/ApiVersionHeader" },
            { $ref: "#/components/parameters/RequestIdPath" },
            {
              name: "id",
              in: "query",
              required: false,
              schema: { type: "string", default: requestIdExample },
              example: requestIdExample,
              description: "The frontend also forwards the request id as a query parameter. Use a requestId returned by listLogs."
            }
          ],
          responses: {
            "200": {
              description: "Dashboard detail object",
              content: {
                "application/json": {
                  schema: { $ref: "#/components/schemas/LogActivityDetail" }
                }
              }
            },
            default: { $ref: "#/components/responses/Error" }
          }
        }
      },
      "/api/api_key/list": {
        get: {
          tags: ["Logs"],
          operationId: "listApiKeys",
          summary: "List API keys for log filters",
          description: "Dashboard dependency used by the Logs UI to populate API key filter options.",
          security: [
            { consoleCookie: [], csrfToken: [] },
            { bearerAuth: [], csrfToken: [] }
          ],
          parameters: [{ $ref: "#/components/parameters/ApiVersionHeader" }],
          responses: {
            "200": {
              description: "API key list response",
              content: {
                "application/json": {
                  schema: { $ref: "#/components/schemas/ApiKeyListResponse" }
                }
              }
            },
            default: { $ref: "#/components/responses/Error" }
          }
        }
      },
      "/api/api_key/list_all": {
        get: {
          tags: ["Logs"],
          operationId: "listAllApiKeys",
          summary: "List all API keys for dashboard selectors",
          description: "Dashboard dependency observed with the Logs route bundle and adjacent API key selectors.",
          security: [
            { consoleCookie: [], csrfToken: [] },
            { bearerAuth: [], csrfToken: [] }
          ],
          parameters: [{ $ref: "#/components/parameters/ApiVersionHeader" }],
          responses: {
            "200": {
              description: "All API key list response",
              content: {
                "application/json": {
                  schema: { $ref: "#/components/schemas/ApiKeyListResponse" }
                }
              }
            },
            default: { $ref: "#/components/responses/Error" }
          }
        }
      },
      "/api/api_key/finish_reasons": {
        get: {
          tags: ["Logs"],
          operationId: "getFinishReasons",
          summary: "List finish reasons for log filters",
          description: "Dashboard dependency used by the Logs UI to populate finish reason filter options.",
          security: [
            { consoleCookie: [], csrfToken: [] },
            { bearerAuth: [], csrfToken: [] }
          ],
          parameters: [{ $ref: "#/components/parameters/ApiVersionHeader" }],
          responses: {
            "200": {
              description: "Finish reason list response",
              content: {
                "application/json": {
                  schema: { $ref: "#/components/schemas/FinishReasonsResponse" }
                }
              }
            },
            default: { $ref: "#/components/responses/Error" }
          }
        }
      },
      "/api/v1/management/generation": {
        get: {
          tags: ["Logs"],
          operationId: "getGeneration",
          summary: "Get generation metering and billing detail with API-key auth",
          description:
            "Official documented endpoint for retrieving generation usage/cost details. It requires API-key authorization and is not the browser-session dashboard endpoint; use /api/v1/generation for pure logged-in browser reuse.",
          parameters: [{ $ref: "#/components/parameters/RequestIdQuery" }],
          responses: {
            "200": {
              description: "Generation metadata",
              content: {
                "application/json": {
                  schema: { $ref: "#/components/schemas/GenerationDetail" }
                }
              }
            },
            default: { $ref: "#/components/responses/Error" }
          }
        }
      },
      "/api/v1/generation": {
        get: {
          tags: ["Logs"],
          operationId: "getLegacyGeneration",
          summary: "Get dashboard generation metering and billing detail",
          description:
            "Dashboard generation detail URL observed in the ZenMux frontend bundle. This is the browser-session compatible generation metadata endpoint used by the Logs UI.",
          parameters: [
            { $ref: "#/components/parameters/ApiVersionHeader" },
            { $ref: "#/components/parameters/RequestIdQuery" }
          ],
          responses: {
            "200": {
              description: "Generation metadata",
              content: {
                "application/json": {
                  schema: { $ref: "#/components/schemas/GenerationDetail" }
                }
              }
            },
            default: { $ref: "#/components/responses/Error" }
          }
        }
      },
      "/api/v1/generation/request": {
        get: {
          tags: ["Generation payloads"],
          operationId: "getGenerationRequestPayload",
          summary: "Get raw request payload for a generation",
          security: [
            { bearerAuth: [] },
            { consoleCookie: [], csrfToken: [] }
          ],
          parameters: [
            { $ref: "#/components/parameters/RequestIdQuery" },
            {
              name: "type",
              in: "query",
              required: true,
              schema: { enum: ["userRequest", "providerRequest"], default: "userRequest" },
              example: "userRequest"
            }
          ],
          responses: {
            "200": {
              description: "Raw request payload wrapper",
              content: {
                "application/json": {
                  schema: { $ref: "#/components/schemas/GenerationPayload" }
                }
              }
            },
            default: { $ref: "#/components/responses/Error" }
          }
        }
      },
      "/api/v1/generation/response": {
        get: {
          tags: ["Generation payloads"],
          operationId: "getGenerationResponsePayload",
          summary: "Get raw response payload for a generation",
          security: [
            { bearerAuth: [] },
            { consoleCookie: [], csrfToken: [] }
          ],
          parameters: [
            { $ref: "#/components/parameters/RequestIdQuery" },
            {
              name: "type",
              in: "query",
              required: true,
              schema: { enum: ["userResponse", "providerResponse"], default: "userResponse" },
              example: "userResponse"
            }
          ],
          responses: {
            "200": {
              description: "Raw response payload wrapper. Streaming responses may be returned as stream-shaped JSON or text depending on account/backend state.",
              content: {
                "application/json": {
                  schema: { $ref: "#/components/schemas/GenerationPayload" }
                },
                "text/event-stream": {
                  schema: { type: "string" }
                }
              }
            },
            default: { $ref: "#/components/responses/Error" }
          }
        }
      }
    },
    components: {
      securitySchemes: {
        bearerAuth: {
          type: "http",
          scheme: "bearer",
          bearerFormat: "ZENMUX_API_KEY"
        },
        consoleCookie: {
          type: "apiKey",
          in: "header",
          name: "Cookie",
          description:
            "Authenticated ZenMux console cookie header. Required by dashboard-derived log endpoints when the backend enforces CSRF/session checks."
        },
        csrfToken: {
          type: "apiKey",
          in: "header",
          name: "X-XSRF-TOKEN",
          description:
            "Console CSRF token header observed from the public frontend bundle. Axios reads the XSRF-TOKEN cookie and sends it as X-XSRF-TOKEN. The SDK can be configured with ZENMUX_CSRF_HEADER if ZenMux changes this header name."
        }
      },
      parameters: {
        ApiVersionHeader: {
          name: "x-api-version",
          in: "header",
          required: false,
          schema: { type: "string", default: "2026-04-20" },
          description:
            "Frontend API version header observed from the public bundle. The SDK defaults to this value and supports ZENMUX_API_VERSION override."
        },
        RequestIdPath: {
          name: "requestId",
          in: "path",
          required: true,
          schema: { type: "string", default: requestIdExample },
          example: requestIdExample,
          description: "Use a requestId returned by listLogs.data[].requestId."
        },
        RequestIdQuery: {
          name: "id",
          in: "query",
          required: true,
          schema: { type: "string", default: requestIdExample },
          example: requestIdExample,
          description: "Generation/request id. Use a requestId returned by listLogs.data[].requestId."
        }
      },
      responses: {
        Error: {
          description: "Error response",
          content: {
            "application/json": {
              schema: { $ref: "#/components/schemas/ErrorResponse" }
            }
          }
        }
      },
      schemas: {
        ListLogsRequest: {
          type: "object",
          additionalProperties: false,
          example: listLogsExample,
          properties: {
            apiKeys: { type: "array", items: { type: "string" }, default: [], example: [] },
            startTime: {
              type: "integer",
              description: "Unix epoch milliseconds.",
              default: listLogsExample.startTime,
              example: listLogsExample.startTime
            },
            stopTime: {
              type: "integer",
              description: "Unix epoch milliseconds.",
              default: listLogsExample.stopTime,
              example: listLogsExample.stopTime
            },
            pageNo: { type: "integer", minimum: 1, default: 1 },
            pageSize: { type: "integer", minimum: 5, maximum: 200, default: 20, example: 20 },
            requestId: { type: "string", example: requestIdExample },
            modelSlugs: { type: "array", items: { type: "string" }, default: [], example: [] },
            providerSlugs: { type: "array", items: { type: "string" }, default: [], example: [] },
            finishReasons: { type: "array", items: { type: "string" }, default: [], example: [] }
          }
        },
        ListLogsResponse: {
          type: "object",
          additionalProperties: true,
          properties: {
            data: {
              type: "array",
              items: { $ref: "#/components/schemas/LogListItem" }
            },
            total: { type: "integer" },
            pageNo: { type: "integer" },
            pageSize: { type: "integer" }
          }
        },
        LogListItem: {
          type: "object",
          additionalProperties: true,
          properties: {
            requestId: { type: "string" },
            generationId: { type: "string" },
            modelSlug: { type: "string" },
            providerSlug: { type: "string" },
            api: { type: "string" },
            createdAt: { type: "string" },
            inputTokens: { type: "integer" },
            outputTokens: { type: "integer" },
            billAmount: { type: ["string", "number", "null"] },
            latency: { type: ["integer", "null"] },
            generationTime: { type: ["integer", "null"] },
            throughput: { type: ["string", "number", "null"] },
            finishReason: { type: ["string", "null"] },
            streamed: { type: "boolean" }
          }
        },
        LogActivityDetail: {
          type: "object",
          additionalProperties: true,
          properties: {
            requestId: { type: "string" },
            api: { type: "string" },
            modelSlug: { type: "string" },
            providerSlug: { type: "string" },
            streamed: { type: "boolean" }
          }
        },
        ApiKeyListResponse: {
          type: "object",
          additionalProperties: true,
          properties: {
            data: {
              type: "array",
              items: { $ref: "#/components/schemas/ApiKeyListItem" }
            }
          }
        },
        ApiKeyListItem: {
          type: "object",
          additionalProperties: true,
          properties: {
            id: { type: "string" },
            name: { type: "string" },
            token: { type: "string", description: "Usually a display-safe token preview rather than the full secret." },
            label: { type: "string" },
            value: { type: "string" },
            disabled: { type: "boolean" }
          }
        },
        FinishReasonsResponse: {
          oneOf: [
            {
              type: "object",
              additionalProperties: true,
              properties: {
                data: { type: "array", items: { type: "string" } }
              }
            },
            { type: "array", items: { type: "string" } }
          ]
        },
        GenerationDetail: {
          type: "object",
          additionalProperties: true,
          properties: {
            api: { type: "string" },
            generationId: { type: "string" },
            model: { type: "string" },
            createAt: { type: "string" },
            generationTime: { type: "integer" },
            latency: { type: "integer" },
            streamed: { type: "boolean" },
            finishReason: { type: "string" },
            usage: { type: "number" },
            nativeTokens: { type: "object", additionalProperties: true },
            ratingResponses: { type: "object", additionalProperties: true }
          }
        },
        GenerationPayload: {
          type: "object",
          additionalProperties: true,
          properties: {
            body: {
              description: "Protocol-native request/response body. Can include text, image inlineData/base64, fileData, tool calls, grounding chunks, or provider-specific fields.",
              oneOf: [
                { type: "object", additionalProperties: true },
                { type: "array", items: true },
                { type: "string" }
              ]
            }
          }
        },
        ErrorResponse: {
          type: "object",
          additionalProperties: true,
          properties: {
            error: { type: ["string", "object"] },
            message: { type: "string" }
          }
        }
      }
    },
    "x-cli-anything-links": createZenmuxDrilldownLinks(),
    "x-cli2anything": {
      target: "zenmux.ai",
      transportModes: [
        "direct-http with explicit API key/session headers",
        "browser-session via Chrome DevTools Protocol, where credentials stay inside the user's logged-in browser context"
      ],
      credentialHandling:
        "The browser-session SDK adapter does not export cookies or API keys. It executes same-origin fetch calls inside an attached browser page and redacts credential headers from capture artifacts.",
      evidence: [
        "Public docs: GET /api/v1/management/generation?id=<generation_id>",
        "Public frontend bundle route /platform/logs: POST api/api_key/activity",
        "Public frontend bundle route /platform/logs/detail/:id: GET api/api_key/activity/{id}, GET /api/v1/generation/request, GET /api/v1/generation/response"
      ],
      safety: "Use only on accounts and traffic you are authorized to inspect."
    }
  };
}

function createListLogsResponseLinks() {
  return {
    firstLogActivity: {
      operationId: "getLogActivity",
      parameters: {
        "path.requestId": "$response.body#/data/0/requestId",
        "query.id": "$response.body#/data/0/requestId"
      },
      description: "Use the first list row requestId to load dashboard activity detail."
    },
    firstGenerationMetadata: {
      operationId: "getLegacyGeneration",
      parameters: {
        "query.id": "$response.body#/data/0/requestId"
      },
      description: "Use the first list row requestId to load browser-session generation metadata."
    },
    firstGenerationRequestPayload: {
      operationId: "getGenerationRequestPayload",
      parameters: {
        "query.id": "$response.body#/data/0/requestId",
        "query.type": "userRequest"
      },
      description: "Use the first list row requestId to load the user request payload."
    },
    firstGenerationResponsePayload: {
      operationId: "getGenerationResponsePayload",
      parameters: {
        "query.id": "$response.body#/data/0/requestId",
        "query.type": "userResponse"
      },
      description: "Use the first list row requestId to load the user response payload."
    }
  };
}

function createListLogsExample() {
  const stopTime = Date.now();
  return {
    apiKeys: [],
    startTime: stopTime - 7 * 24 * 60 * 60 * 1000,
    stopTime,
    pageNo: 1,
    pageSize: 20,
    modelSlugs: [],
    providerSlugs: [],
    finishReasons: []
  };
}
