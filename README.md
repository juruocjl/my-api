# My API Proxy

一个可配置模型路由的 OpenAI 兼容 API 中转服务，支持多 Provider、多 API Key 负载均衡、按模型自定义计费以及每日使用量统计。

## 功能

- OpenAI 兼容接口
  - 需要 `Authorization: Bearer <client_api_key>`
  - GET /v1/models
  - POST /v1/chat/completions
  - POST /v1/embeddings
- 多 Provider + 多 API Key
  - 按模型路由到不同 Provider
  - 同一 Provider 下多个 Key 按优先级(weight)从高到低选择；同优先级再按创建顺序
  - 429/5xx 自动故障退避与冷却恢复
- 计费逻辑
  - 每个模型独立配置 input、cached input、output 单价
  - 按 token 数实时计算费用并落库
- 统计
  - 每日聚合 token 和费用
  - 支持按日期区间、模型、provider、key 查询

## 快速开始

1. 同步依赖（uv）

```powershell
uv python install 3.12
uv sync
```

2. 配置环境变量

```powershell
copy .env.example .env
```

3. 启动服务

```powershell
uv run python -m app.main
```

- Host/Port/Reload 来自 `.env`：`APP_HOST`、`APP_PORT`、`APP_RELOAD`。
- LLM 接口认证 Key 来自 `.env`：`CLIENT_API_KEYS`（多个 Key 用英文逗号分隔）。
- 管理接口认证 Token 来自 `.env`：`ADMIN_TOKEN`。
- 统计口径时区来自 `.env`：`BUSINESS_TIMEZONE`，默认是 `Asia/Shanghai`。

4. 打开接口文档

- Swagger UI: http://127.0.0.1:8000/docs
- 管理页面: http://127.0.0.1:8000/admin/ui?token=你的ADMIN_TOKEN

### 管理端认证

- 所有 `/admin/*` 接口均要求管理员 Token。
- 可通过 `X-Admin-Token` 请求头或 `Authorization: Bearer <token>` 认证。
- 浏览器管理页支持通过 URL 参数传入：`/admin/ui?token=...`。

## 最小可用配置示例

1. 新增 Provider

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/admin/providers -Headers @{"X-Admin-Token"="change-me"} -ContentType "application/json" -Body '{
  "name": "openai-main",
  "base_url": "https://api.openai.com",
  "api_type": "openai",
  "enabled": true
}'
```

2. 添加多个 API Key（负载均衡）

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/admin/providers/1/keys -Headers @{"X-Admin-Token"="change-me"} -ContentType "application/json" -Body '{
  "key_name": "k1",
  "api_key": "sk-xxx",
  "enabled": true
}'

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/admin/providers/1/keys -Headers @{"X-Admin-Token"="change-me"} -ContentType "application/json" -Body '{
  "key_name": "k2",
  "api_key": "sk-yyy",
  "enabled": true
}'
```

3. 配置模型路由

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/admin/providers/routes -Headers @{"X-Admin-Token"="change-me"} -ContentType "application/json" -Body '{
  "public_model": "gpt-4o-mini",
  "provider_id": 1,
  "upstream_model": "gpt-4o-mini",
  "priority": 100,
  "enabled": true
}'
```

4. 配置模型计费（每模型独立）

```powershell
Invoke-RestMethod -Method Put -Uri http://127.0.0.1:8000/admin/pricing -Headers @{"X-Admin-Token"="change-me"} -ContentType "application/json" -Body '{
  "public_model": "gpt-4o-mini",
  "input_unit_price": 0.15,
  "cached_input_unit_price": 0.075,
  "output_unit_price": 0.6,
  "unit_tokens": 1000000
}'
```

5. 调用中转接口

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/v1/chat/completions -Headers @{"Authorization"="Bearer sk-your-client-key"} -ContentType "application/json" -Body '{
  "model": "gpt-4o-mini",
  "messages": [
    {"role": "user", "content": "hello"}
  ]
}'
```

6. 查询每日统计

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/admin/stats/daily?start_date=2026-03-11&end_date=2026-03-11" -Headers @{"X-Admin-Token"="change-me"}

# 仅查询区间总花费
Invoke-RestMethod "http://127.0.0.1:8000/admin/stats/total-cost?start_date=2026-03-11&end_date=2026-03-11" -Headers @{"X-Admin-Token"="change-me"}

# 细粒度时间范围查询总花费（精确到秒，基于请求明细）
Invoke-RestMethod "http://127.0.0.1:8000/admin/stats/total-cost?start_time=2026-03-11T10:00:00&end_time=2026-03-11T10:30:00" -Headers @{"X-Admin-Token"="change-me"}

# 查询全局剩余额度汇总
Invoke-RestMethod "http://127.0.0.1:8000/admin/stats/remaining-quota" -Headers @{"X-Admin-Token"="change-me"}
```

## 管理接口示例

- 新增 Provider: POST /admin/providers
- 为 Provider 添加 Key: POST /admin/providers/{provider_id}/keys
- 新增模型路由: POST /admin/providers/routes
- 配置模型计费: PUT /admin/pricing
- 查询每日统计: GET /admin/stats/daily?start_date=2026-03-10&end_date=2026-03-11
- 查询区间总花费: GET /admin/stats/total-cost?start_date=2026-03-10&end_date=2026-03-11
- 查询细粒度总花费: GET /admin/stats/total-cost?start_time=2026-03-11T10:00:00&end_time=2026-03-11T10:30:00
- 查询剩余额度汇总: GET /admin/stats/remaining-quota

## 说明

- 当前版本不支持 stream 模式。
- `/v1/*` 已支持 OpenAI 风格 `Authorization: Bearer <key>` 客户端认证。
- `/admin/*` 已支持管理员 Token 认证；生产环境请务必在 `.env` 设置强随机 `ADMIN_TOKEN`。
- SQLite 适合轻量场景，后续可替换为 PostgreSQL。
- 编辑器若提示依赖未解析，请将 Python 解释器切换到项目虚拟环境 .venv。
