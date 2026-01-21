const BASE = "http://127.0.0.1:8000";

export async function waitForBackend(timeoutMs = 15000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const r = await fetch(`${BASE}/health`);
      if (r.ok) return true;
    } catch {}
    await new Promise((res) => setTimeout(res, 400));
  }
  return false;
}

export async function getSettings() {
  const r = await fetch(`${BASE}/settings`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function setSettings(payload: { llm_models_dir: string; default_llm_model?: string | null }) {
  const r = await fetch(`${BASE}/settings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok) {
    const j = await r.json().catch(() => ({}));
    throw new Error(j.detail || "Failed to save settings");
  }
  return r.json();
}

export async function getModels() {
  const r = await fetch(`${BASE}/models`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function query(payload: { input_text: string; session_id: string; mode: string; model_name?: string | null }) {
  const r = await fetch(`${BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok) {
    const j = await r.json().catch(() => ({}));
    throw new Error(j.detail || "Query failed");
  }
  return r.json();
}
