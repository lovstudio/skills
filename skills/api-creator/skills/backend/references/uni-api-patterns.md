# uni-api 网关后端约定（FastAPI 聚合网关）

参考仓库：`github.com/cs-magic/uni-api`。新增 app 网关能力时遵循以下既有约定，不引入新框架。

## 目录结构

```text
uni-api/
├── main.py                  # FastAPI app；docs_url=None + 自定义 /docs
├── settings.py              # pydantic-settings，读取 .env
├── config/app_groups.py     # /docs Tab 分组：APP_GROUPS: dict[str, list[str]]
├── router/                  # 每能力一个文件或一个包
│   ├── __init__.py          # root_router，include_router 汇总
│   ├── llm.py  account.py  spider.py  oss.py  vpn.py  map/  sport/  uni_pusher/  wechat/  cases.py  thoughts.py
├── packages/<domain>/       # 业务逻辑（llm、spider、wechat、fastapi、common …）
├── auth/ models/ schema/ utils/ alembic/ tests/
└── .env                     # 本地必需（见 AGENTS.md）
```

## Router 模式

`router/llm.py` 的骨架：

```python
from fastapi import APIRouter
from packages.common.pydantic import BaseModel
from packages.fastapi.standard_error import standard_error_handler

llm_router = APIRouter(prefix='/llm', tags=['LLM'])

class ILLMBody(BaseModel):
    messages: list
    model: str

@llm_router.post('/base')
@standard_error_handler()
async def call_llm_(body: ILLMBody):
    ...
```

要点：
- `APIRouter(prefix='/<capability>', tags=['<Tag>'])`，tag 是 `/docs` 分组与 `APP_GROUPS` 的键。
- 请求/响应体用 `packages.common.pydantic` 的 `BaseModel`。
- 路由用 `@standard_error_handler()` 装饰，统一错误结构。
- 复杂能力用 `router/<capability>/` 包 + `__init__.py` 导出 router（参考 `router/sport/badminton`）。

## 注册与分组

- `router/__init__.py`：import 各 router，`root_router.include_router(...)`。
- `config/app_groups.py`：`APP_GROUPS` 把 app 展示名映射到 tag 列表，驱动 `/docs` Tab。

```python
APP_GROUPS: dict[str, list[str]] = {
    "核心 AI": ["LLM", "thoughts"],
    "内容采集": ["Spider"],
    ...
}
```

新增能力的 tag 未出现在任何分组时仍会显示在「全部」Tab。

## 配置（settings.py）

- `Settings` 继承 `pydantic_settings.BaseSettings`，`model_config = SettingsConfigDict(env_file=".env", extra="ignore")`。
- 新上游密钥/配置：加字段到 `Settings`，并在 `.env.sample` 补占位；密钥不进源码。
- `@lru_cache def get_settings()` 单例导出。

## 自定义 /docs

- `main.py` 设置 `docs_url=None`，新增 `/docs` 路由渲染 `packages/fastapi/docs_switcher.html`，
  用 `app_groups_json()`（来自 `config/app_groups.py`）替换 `__APP_GROUPS__`。
- 样式为 Lovstudio 暖学术风（陶土 #CC785C / 米色 #F9F9F7 / 炭灰 #181818），改 UI 遵循设计规范，
  勿硬编码科技蓝。

## 运行前提（仓库 AGENTS.md）

- `.env` 必须齐备 `settings.py` 必填字段；`router/oss.py` 模块级 `OSSClient()` 强制要求
  `ALI_AK` / `ALI_SK` / `ALI_OSS_ENDPOINT` / `ALI_OSS_BUCKET_NAME`，缺失直接启动失败。
- 本机 shell 有 `all_proxy=socks5://127.0.0.1:7890`，anthropic SDK import 以 `trust_env` 建
  httpx client，venv 缺 `socksio` 会 ImportError；启动前 `pip install socksio`。
- `/openapi` 路径用 `os.path.dirname(__file__)` 拼接，勿把文件当目录。

## 验收

- `python -c "import main"` 通过。
- `openapi.json` 出现新 tag；启动后 `/docs` 对应 Tab 生效。
- 输出**网关端点清单**（method / path / 说明）作为交付契约。
