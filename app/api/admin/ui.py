from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["admin-ui"])


@router.get("/admin/ui", response_class=HTMLResponse)
async def admin_ui() -> str:
    return """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>My API Proxy Admin</title>
  <style>
    :root {
      --bg: #f4f1ea;
      --card: #fffdf8;
      --text: #1d2228;
      --muted: #5d6670;
      --line: #d8cfbf;
      --accent: #0a6a62;
      --accent-2: #0e8a7f;
      --danger: #b0372f;
      --ok: #276749;
    }
    * { box-sizing: border-box; }
    body { margin: 0; color: var(--text); background: var(--bg); font-family: "Segoe UI", "Microsoft YaHei", sans-serif; }
    .container { width: min(1280px, 95vw); margin: 18px auto 40px; display: grid; gap: 12px; }
    .header { display: flex; justify-content: space-between; align-items: center; background: #fff; border: 1px solid var(--line); border-radius: 12px; padding: 12px 14px; }
    .title { margin: 0; font-size: 22px; }
    .sub { color: var(--muted); font-size: 13px; margin-top: 2px; }
    .grid { display: grid; grid-template-columns: repeat(12, 1fr); gap: 12px; }
    .card { background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: 12px; grid-column: span 12; }
    .span-6 { grid-column: span 6; }
    .span-12 { grid-column: span 12; }
    .row { display: grid; grid-template-columns: repeat(12, 1fr); gap: 8px; margin-bottom: 8px; }
    .c2 { grid-column: span 2; } .c3 { grid-column: span 3; } .c4 { grid-column: span 4; } .c6 { grid-column: span 6; } .c12 { grid-column: span 12; }
    label { display: block; font-size: 12px; color: var(--muted); margin-bottom: 4px; }
    input, select { width: 100%; border: 1px solid var(--line); border-radius: 8px; padding: 7px 9px; }
    .btn { border: none; border-radius: 8px; padding: 7px 10px; font-weight: 600; cursor: pointer; background: var(--accent); color: #fff; }
    .btn:hover { background: var(--accent-2); }
    .btn-sm { padding: 4px 8px; font-size: 12px; }
    .btn-danger { background: var(--danger); }
    .status { min-height: 18px; font-size: 12px; margin-top: 6px; }
    .ok { color: var(--ok); } .err { color: var(--danger); }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td { border-bottom: 1px solid var(--line); padding: 7px 6px; text-align: left; vertical-align: middle; }
    th { color: var(--muted); font-weight: 600; }
    .ops { display: flex; gap: 6px; }
    .pill { border: 1px solid var(--line); border-radius: 999px; padding: 3px 7px; margin-right: 6px; font-size: 12px; background: #fff; }
    @media (max-width: 980px) {
      .span-6 { grid-column: span 12; }
      .c2,.c3,.c4,.c6,.c12 { grid-column: span 12; }
      table { display: block; overflow-x: auto; white-space: nowrap; }
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div>
        <h1 class="title">My API Proxy 管理台</h1>
        <div class="sub">一行一条数据，支持编辑与删除</div>
      </div>
      <button class="btn" onclick="refreshAll()">刷新全部</button>
    </div>

    <div class="grid">
      <section class="card span-6">
        <h3>Provider</h3>
        <div class="row">
          <div class="c4"><label>名称</label><input id="p_name" /></div>
          <div class="c6"><label>Base URL</label><input id="p_url" placeholder="https://api.openai.com" /></div>
          <div class="c2"><label>启用</label><select id="p_enabled"><option value="true">true</option><option value="false">false</option></select></div>
        </div>
        <button class="btn" onclick="createProvider()">新增 Provider</button>
        <div id="providers_status" class="status"></div>
        <table>
          <thead><tr><th>ID</th><th>名称</th><th>Base URL</th><th>启用</th><th>操作</th></tr></thead>
          <tbody id="providers_body"></tbody>
        </table>
      </section>

      <section class="card span-6">
        <h3>API Key</h3>
        <div class="row">
          <div class="c3"><label>Provider ID</label><input id="k_provider_id" type="number" /></div>
          <div class="c3"><label>名称</label><input id="k_name" /></div>
          <div class="c6"><label>初始余额</label><input id="k_balance" type="number" step="0.01" value="100" /></div>
        </div>
        <div class="row"><div class="c12"><label>API Key</label><input id="k_value" /></div></div>
        <button class="btn" onclick="addKey()">添加 Key</button>
        <button class="btn" onclick="listKeys()">加载全部 Key</button>
        <div style="margin:8px 0;">
          <span id="keys_total_balance" class="pill">总额度: 0.000000</span>
        </div>
        <div id="keys_status" class="status"></div>
        <table>
          <thead><tr><th>ID</th><th>Provider</th><th>名称</th><th>余额</th><th>启用</th><th>失败次数</th><th>操作</th></tr></thead>
          <tbody id="keys_body"></tbody>
        </table>
      </section>

      <section class="card span-6">
        <h3>Model Route</h3>
        <div class="row">
          <div class="c3"><label>Public Model</label><input id="r_public_model" /></div>
          <div class="c3"><label>Provider ID</label><input id="r_provider_id" type="number" /></div>
          <div class="c4"><label>Upstream Model</label><input id="r_upstream_model" /></div>
          <div class="c2"><label>Priority</label><input id="r_priority" type="number" value="100" /></div>
        </div>
        <button class="btn" onclick="createRoute()">新增 Route</button>
        <div id="routes_status" class="status"></div>
        <table>
          <thead><tr><th>ID</th><th>Public</th><th>Provider</th><th>Upstream</th><th>Priority</th><th>启用</th><th>操作</th></tr></thead>
          <tbody id="routes_body"></tbody>
        </table>
      </section>

      <section class="card span-6">
        <h3>Model Pricing</h3>
        <div class="row">
          <div class="c3"><label>Public Model</label><input id="m_public_model" /></div>
          <div class="c3"><label>Input</label><input id="m_in" type="number" step="0.000001" value="0" /></div>
          <div class="c3"><label>Cached</label><input id="m_cached" type="number" step="0.000001" value="0" /></div>
          <div class="c3"><label>Output</label><input id="m_out" type="number" step="0.000001" value="0" /></div>
        </div>
        <div class="row"><div class="c3"><label>Unit Tokens</label><input id="m_unit" type="number" value="1000000" /></div></div>
        <button class="btn" onclick="upsertPricing()">保存 Pricing</button>
        <div id="pricing_status" class="status"></div>
        <table>
          <thead><tr><th>Model</th><th>Input</th><th>Cached</th><th>Output</th><th>Unit</th><th>操作</th></tr></thead>
          <tbody id="pricing_body"></tbody>
        </table>
      </section>

      <section class="card span-12">
        <h3>Daily Stats</h3>
        <div class="row">
          <div class="c3"><label>Start Date</label><input id="s_start" type="date" /></div>
          <div class="c3"><label>End Date</label><input id="s_end" type="date" /></div>
          <div class="c3"><label>Model(可选)</label><input id="s_model" /></div>
          <div class="c3"><label>Provider ID(可选)</label><input id="s_provider_id" type="number" /></div>
        </div>
        <button class="btn" onclick="queryStats()">查询统计</button>
        <div id="stats_status" class="status"></div>
        <div style="margin:8px 0;">
          <span id="total_input_tokens" class="pill">input: 0</span>
          <span id="total_cached_tokens" class="pill">cached: 0</span>
          <span id="total_output_tokens" class="pill">output: 0</span>
          <span id="total_tokens" class="pill">total token: 0</span>
          <span id="total_cost" class="pill">cost: 0</span>
          <span id="total_requests" class="pill">requests: 0</span>
          <span id="total_estimated" class="pill">estimated: 0</span>
        </div>
        <table>
          <thead><tr><th>Date</th><th>Model</th><th>Provider</th><th>Key</th><th>Input</th><th>Cached</th><th>Output</th><th>Cost</th><th>Req</th><th>Estimated</th></tr></thead>
          <tbody id="stats_body"></tbody>
        </table>
        <h4 style="margin:12px 0 6px;">访问明细（每次请求时间）</h4>
        <table>
          <thead><tr><th>Time</th><th>Request ID</th><th>Endpoint</th><th>Model</th><th>Provider</th><th>Key</th><th>Input</th><th>Cached</th><th>Output</th><th>Cost</th><th>Latency(ms)</th></tr></thead>
          <tbody id="event_body"></tbody>
        </table>
      </section>
    </div>
  </div>

  <script>
    const byId = (id) => document.getElementById(id);
    const esc = (s) => String(s ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
    const enc = (s) => encodeURIComponent(String(s ?? ""));

    function formatUtcToLocal(value) {
      if (!value) return "";
      const raw = String(value).trim();
      if (!raw) return "";
      const hasTimezone = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(raw);
      const normalized = hasTimezone ? raw : `${raw}Z`;
      const dt = new Date(normalized);
      if (Number.isNaN(dt.getTime())) return raw;
      return dt.toLocaleString("zh-CN", { hour12: false });
    }

    function localDateForInput() {
      const now = new Date();
      const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
      return local.toISOString().slice(0, 10);
    }

    function setStatus(id, msg, ok = true) {
      const el = byId(id);
      el.className = `status ${ok ? "ok" : "err"}`;
      el.textContent = msg;
    }

    async function api(url, options = {}) {
      const res = await fetch(url, { headers: { "Content-Type": "application/json" }, ...options });
      const text = await res.text();
      let data = {};
      try { data = text ? JSON.parse(text) : {}; } catch { data = { raw: text }; }
      if (!res.ok) throw new Error(`${res.status} ${data?.detail || JSON.stringify(data)}`);
      return data;
    }

    async function createProvider() {
      try {
        await api("/admin/providers", { method: "POST", body: JSON.stringify({
          name: byId("p_name").value.trim(),
          base_url: byId("p_url").value.trim(),
          api_type: "openai",
          enabled: byId("p_enabled").value === "true",
        })});
        await listProviders();
        setStatus("providers_status", "Provider 创建成功");
      } catch (e) { setStatus("providers_status", e.message, false); }
    }

    async function listProviders() {
      const data = await api("/admin/providers");
      byId("providers_body").innerHTML = data.map((p) => `
        <tr>
          <td>${p.id}</td><td>${esc(p.name)}</td><td>${esc(p.base_url)}</td><td>${p.enabled}</td>
          <td class="ops">
            <button class="btn btn-sm" onclick="editProvider(${p.id}, decodeURIComponent('${enc(p.name)}'), decodeURIComponent('${enc(p.base_url)}'), ${p.enabled})">修改</button>
            <button class="btn btn-sm btn-danger" onclick="deleteProvider(${p.id})">删除</button>
          </td>
        </tr>`).join("");
      return data;
    }

    async function editProvider(id, oldName, oldBaseUrl, oldEnabled) {
      try {
        const name = prompt("Provider 名称", oldName); if (name === null) return;
        const baseUrl = prompt("Base URL", oldBaseUrl); if (baseUrl === null) return;
        const enabled = confirm("点击确定=启用，取消=禁用");
        await api(`/admin/providers/${id}`, { method: "PATCH", body: JSON.stringify({ name, base_url: baseUrl, enabled }) });
        await listProviders();
        setStatus("providers_status", "Provider 修改成功");
      } catch (e) { setStatus("providers_status", e.message, false); }
    }

    async function deleteProvider(id) {
      try {
        if (!confirm(`确认删除 Provider ${id} 及其关联 Key/Route 吗？`)) return;
        await api(`/admin/providers/${id}`, { method: "DELETE" });
        await Promise.all([listProviders(), listRoutes(), listKeys()]);
        setStatus("providers_status", "Provider 删除成功");
      } catch (e) { setStatus("providers_status", e.message, false); }
    }

    async function addKey() {
      try {
        const providerId = Number(byId("k_provider_id").value);
        if (!providerId || providerId < 1) throw new Error("Provider ID 必须大于 0");
        await api(`/admin/providers/${providerId}/keys`, { method: "POST", body: JSON.stringify({
          key_name: byId("k_name").value.trim(),
          api_key: byId("k_value").value.trim(),
          balance: Number(byId("k_balance").value || 0),
          enabled: true,
        })});
        await listKeys();
        setStatus("keys_status", "Key 添加成功");
      } catch (e) { setStatus("keys_status", e.message, false); }
    }

    async function listKeys() {
      try {
        const data = await api(`/admin/providers/keys`);
        const totalBalance = data.reduce((sum, k) => sum + Number(k.balance || 0), 0);
        byId("keys_body").innerHTML = data.map((k) => `
          <tr>
            <td>${k.id}</td><td>${k.provider_id}</td><td>${esc(k.key_name)}</td><td>${k.balance.toFixed(6)}</td><td>${k.enabled}</td><td>${k.consecutive_failures}</td>
            <td class="ops">
              <button class="btn btn-sm" onclick="editKey(${k.id})">修改</button>
              <button class="btn btn-sm btn-danger" onclick="deleteKey(${k.id})">删除</button>
            </td>
          </tr>`).join("");
        byId("keys_total_balance").textContent = `总额度: ${totalBalance.toFixed(6)}`;
        setStatus("keys_status", "全部 Key 已刷新");
      } catch (e) { setStatus("keys_status", e.message, false); }
    }

    async function editKey(id) {
      try {
        const balanceDeltaText = prompt("余额增量(可正可负)", "0"); if (balanceDeltaText === null) return;
        const enabled = confirm("点击确定=启用，取消=禁用");
        await api(`/admin/providers/keys/${id}`, { method: "PATCH", body: JSON.stringify({
          balance_delta: Number(balanceDeltaText),
          enabled,
        })});
        await listKeys();
        setStatus("keys_status", "Key 修改成功");
      } catch (e) { setStatus("keys_status", e.message, false); }
    }

    async function deleteKey(id) {
      try {
        if (!confirm(`确认删除 Key ${id} 吗？`)) return;
        await api(`/admin/providers/keys/${id}`, { method: "DELETE" });
        await listKeys();
        setStatus("keys_status", "Key 删除成功");
      } catch (e) { setStatus("keys_status", e.message, false); }
    }

    async function createRoute() {
      try {
        await api("/admin/providers/routes", { method: "POST", body: JSON.stringify({
          public_model: byId("r_public_model").value.trim(),
          provider_id: Number(byId("r_provider_id").value),
          upstream_model: byId("r_upstream_model").value.trim(),
          priority: Number(byId("r_priority").value || 100),
          enabled: true,
        })});
        await listRoutes();
        setStatus("routes_status", "Route 创建成功");
      } catch (e) { setStatus("routes_status", e.message, false); }
    }

    async function listRoutes() {
      const data = await api("/admin/providers/routes");
      byId("routes_body").innerHTML = data.map((r) => `
        <tr>
          <td>${r.id}</td><td>${esc(r.public_model)}</td><td>${r.provider_id}</td><td>${esc(r.upstream_model)}</td><td>${r.priority}</td><td>${r.enabled}</td>
          <td class="ops">
            <button class="btn btn-sm" onclick="editRoute(${r.id}, decodeURIComponent('${enc(r.public_model)}'), ${r.provider_id}, decodeURIComponent('${enc(r.upstream_model)}'), ${r.priority}, ${r.enabled})">修改</button>
            <button class="btn btn-sm btn-danger" onclick="deleteRoute(${r.id})">删除</button>
          </td>
        </tr>`).join("");
      return data;
    }

    async function editRoute(id, oldPublic, oldProviderId, oldUpstream, oldPriority, oldEnabled) {
      try {
        const publicModel = prompt("Public model", oldPublic); if (publicModel === null) return;
        const providerId = prompt("Provider ID", String(oldProviderId)); if (providerId === null) return;
        const upstreamModel = prompt("Upstream model", oldUpstream); if (upstreamModel === null) return;
        const priority = prompt("Priority", String(oldPriority)); if (priority === null) return;
        const enabled = confirm("点击确定=启用，取消=禁用");
        await api(`/admin/providers/routes/${id}`, { method: "PATCH", body: JSON.stringify({
          public_model: publicModel,
          provider_id: Number(providerId),
          upstream_model: upstreamModel,
          priority: Number(priority),
          enabled,
        })});
        await listRoutes();
        setStatus("routes_status", "Route 修改成功");
      } catch (e) { setStatus("routes_status", e.message, false); }
    }

    async function deleteRoute(id) {
      try {
        if (!confirm(`确认删除 Route ${id} 吗？`)) return;
        await api(`/admin/providers/routes/${id}`, { method: "DELETE" });
        await listRoutes();
        setStatus("routes_status", "Route 删除成功");
      } catch (e) { setStatus("routes_status", e.message, false); }
    }

    async function upsertPricing() {
      try {
        await api("/admin/pricing", { method: "PUT", body: JSON.stringify({
          public_model: byId("m_public_model").value.trim(),
          input_unit_price: Number(byId("m_in").value || 0),
          cached_input_unit_price: Number(byId("m_cached").value || 0),
          output_unit_price: Number(byId("m_out").value || 0),
          unit_tokens: Number(byId("m_unit").value || 1000000),
        })});
        await listPricing();
        setStatus("pricing_status", "Pricing 保存成功");
      } catch (e) { setStatus("pricing_status", e.message, false); }
    }

    async function listPricing() {
      const data = await api("/admin/pricing");
      byId("pricing_body").innerHTML = data.map((p) => `
        <tr>
          <td>${esc(p.public_model)}</td><td>${p.input_unit_price}</td><td>${p.cached_input_unit_price}</td><td>${p.output_unit_price}</td><td>${p.unit_tokens}</td>
          <td class="ops">
            <button class="btn btn-sm" onclick="editPricing(decodeURIComponent('${enc(p.public_model)}'), ${p.input_unit_price}, ${p.cached_input_unit_price}, ${p.output_unit_price}, ${p.unit_tokens})">修改</button>
            <button class="btn btn-sm btn-danger" onclick="deletePricing(${p.id}, decodeURIComponent('${enc(p.public_model)}'))">删除</button>
          </td>
        </tr>`).join("");
      return data;
    }

    async function editPricing(model, oldIn, oldCached, oldOut, oldUnit) {
      try {
        const inPrice = prompt("Input 单价", String(oldIn)); if (inPrice === null) return;
        const cachedPrice = prompt("Cached Input 单价", String(oldCached)); if (cachedPrice === null) return;
        const outPrice = prompt("Output 单价", String(oldOut)); if (outPrice === null) return;
        const unitTokens = prompt("Unit Tokens", String(oldUnit)); if (unitTokens === null) return;
        await api("/admin/pricing", { method: "PUT", body: JSON.stringify({
          public_model: model,
          input_unit_price: Number(inPrice),
          cached_input_unit_price: Number(cachedPrice),
          output_unit_price: Number(outPrice),
          unit_tokens: Number(unitTokens),
        })});
        await listPricing();
        setStatus("pricing_status", "Pricing 修改成功");
      } catch (e) { setStatus("pricing_status", e.message, false); }
    }

    async function deletePricing(id, model) {
      try {
        const label = model && model.length > 0 ? model : `(id=${id}, 空模型名)`;
        if (!confirm(`确认删除 ${label} 的定价吗？`)) return;
        await api(`/admin/pricing/id/${id}`, { method: "DELETE" });
        await listPricing();
        setStatus("pricing_status", "Pricing 删除成功");
      } catch (e) { setStatus("pricing_status", e.message, false); }
    }

    async function queryStats() {
      try {
        const start = byId("s_start").value;
        const end = byId("s_end").value;
        if (!start || !end) throw new Error("请先填写开始和结束日期");
        const q = new URLSearchParams({ start_date: start, end_date: end });
        if (byId("s_model").value.trim()) q.set("model", byId("s_model").value.trim());
        if (byId("s_provider_id").value) q.set("provider_id", byId("s_provider_id").value);
        const data = await api(`/admin/stats/daily?${q.toString()}`);
        const events = await api(`/admin/stats/events?${q.toString()}`);
        const t = data.totals;
        byId("total_input_tokens").textContent = `input: ${t.input_tokens}`;
        byId("total_cached_tokens").textContent = `cached: ${t.cached_input_tokens}`;
        byId("total_output_tokens").textContent = `output: ${t.output_tokens}`;
        byId("total_tokens").textContent = `token: ${t.input_tokens + t.cached_input_tokens + t.output_tokens}`;
        byId("total_cost").textContent = `cost: ${Number(t.total_cost).toFixed(6)}`;
        byId("total_requests").textContent = `requests: ${t.request_count}`;
        byId("total_estimated").textContent = `estimated: ${t.estimated_count}`;
        byId("stats_body").innerHTML = data.items.map((i) => `
          <tr>
            <td>${i.usage_date}</td><td>${esc(i.public_model)}</td><td>${i.provider_id}</td><td>${i.api_key_id}</td>
            <td>${i.input_tokens}</td><td>${i.cached_input_tokens}</td><td>${i.output_tokens}</td><td>${Number(i.total_cost).toFixed(6)}</td><td>${i.request_count}</td><td>${i.estimated_count}</td>
          </tr>`).join("");

        byId("event_body").innerHTML = events.items.map((i) => `
          <tr>
            <td>${formatUtcToLocal(i.created_at)}</td><td>${esc(i.request_id)}</td><td>${esc(i.endpoint)}</td><td>${esc(i.public_model)}</td><td>${i.provider_id}</td><td>${i.api_key_id}</td>
            <td>${i.input_tokens}</td><td>${i.cached_input_tokens}</td><td>${i.output_tokens}</td><td>${Number(i.total_cost).toFixed(6)}</td><td>${i.latency_ms}</td>
          </tr>`).join("");
        setStatus("stats_status", "统计查询成功");
      } catch (e) { setStatus("stats_status", e.message, false); }
    }

    async function refreshAll() {
      try {
        await Promise.all([listProviders(), listRoutes(), listPricing(), listKeys()]);
        setStatus("providers_status", "已刷新");
      } catch (e) {
        setStatus("providers_status", e.message, false);
      }
    }

    (() => {
      const today = localDateForInput();
      byId("s_start").value = today;
      byId("s_end").value = today;
      refreshAll();
    })();
  </script>
</body>
</html>
    """
