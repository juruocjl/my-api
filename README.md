# My API Proxy

一个可配置模型路由的 OpenAI 兼容 API 中转服务，支持多 Provider、多 API Key 负载均衡、按模型自定义计费以及每日使用量统计。

## 功能

- OpenAI 兼容接口
  - GET /v1/models
  - POST /v1/chat/completions
  - POST /v1/embeddings
- 多 Provider + 多 API Key
  - 按模型路由到不同 Provider
  - 同一 Provider 下多个 Key 按权重负载
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
uv run uvicorn app.main:app --reload
```

4. 打开接口文档

- Swagger UI: http://127.0.0.1:8000/docs
- 管理页面: http://127.0.0.1:8000/admin/ui

## 最小可用配置示例

1. 新增 Provider

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/admin/providers -ContentType "application/json" -Body '{
  "name": "openai-main",
  "base_url": "https://api.openai.com",
  "api_type": "openai",
  "enabled": true
}'
```

2. 添加多个 API Key（负载均衡）

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/admin/providers/1/keys -ContentType "application/json" -Body '{
  "key_name": "k1",
  "api_key": "sk-xxx",
  "weight": 2,
  "enabled": true
}'

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/admin/providers/1/keys -ContentType "application/json" -Body '{
  "key_name": "k2",
  "api_key": "sk-yyy",
  "weight": 1,
  "enabled": true
}'
```

3. 配置模型路由

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/admin/providers/routes -ContentType "application/json" -Body '{
  "public_model": "gpt-4o-mini",
  "provider_id": 1,
  "upstream_model": "gpt-4o-mini",
  "priority": 100,
  "enabled": true
}'
```

4. 配置模型计费（每模型独立）

```powershell
Invoke-RestMethod -Method Put -Uri http://127.0.0.1:8000/admin/pricing -ContentType "application/json" -Body '{
  "public_model": "gpt-4o-mini",
  "input_unit_price": 0.15,
  "cached_input_unit_price": 0.075,
  "output_unit_price": 0.6,
  "unit_tokens": 1000000
}'
```

5. 调用中转接口

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/v1/chat/completions -ContentType "application/json" -Body '{
  "model": "gpt-4o-mini",
  "messages": [
    {"role": "user", "content": "hello"}
  ]
}'
```

6. 查询每日统计

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/admin/stats/daily?start_date=2026-03-11&end_date=2026-03-11"
```

## 管理接口示例

- 新增 Provider: POST /admin/providers
- 为 Provider 添加 Key: POST /admin/providers/{provider_id}/keys
- 新增模型路由: POST /admin/providers/routes
- 配置模型计费: PUT /admin/pricing
- 查询每日统计: GET /admin/stats/daily?start_date=2026-03-10&end_date=2026-03-11

## 说明

- 当前版本不支持 stream 模式。
- 当前版本默认内网使用，不包含客户端鉴权与限流。
- SQLite 适合轻量场景，后续可替换为 PostgreSQL。
- 编辑器若提示依赖未解析，请将 Python 解释器切换到项目虚拟环境 .venv。
