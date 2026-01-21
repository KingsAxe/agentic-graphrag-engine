import React, { useEffect, useState } from "react";
import { open } from "@tauri-apps/plugin-dialog";
import { getSettings, setSettings, getModels } from "../lib/api";

export default function Settings({ onClose }: { onClose: () => void }) {
  const [dir, setDir] = useState("");
  const [defaultModel, setDefaultModel] = useState("");
  const [models, setModels] = useState<string[]>([]);
  const [status, setStatus] = useState("");

  async function refresh() {
    setStatus("");
    const s = await getSettings();
    setDir(s.llm_models_dir || "");
    setDefaultModel(s.default_llm_model || "");

    const m = await getModels().catch(() => ({ models: [] }));
    setModels(m.models || []);
  }

  useEffect(() => {
    refresh().catch((e) => setStatus(String(e.message || e)));
  }, []);

  async function pickDir() {
    const selected = await open({ directory: true, multiple: false });
    if (typeof selected === "string") setDir(selected);
  }

  async function save() {
    setStatus("Saving...");
    await setSettings({
      llm_models_dir: dir,
      default_llm_model: defaultModel ? defaultModel : null,
    });
    setStatus("Saved ✅");
    await refresh();
  }

  return (
    <div className="card" style={{ padding: 14 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ fontWeight: 700 }}>Settings</div>
        <button className="btn" onClick={onClose}>Close</button>
      </div>

      <div style={{ marginTop: 12 }}>
        <div style={{ fontSize: 12, color: "var(--muted)" }}>Models folder</div>
        <div style={{ display: "flex", gap: 8, marginTop: 6 }}>
          <input className="input" value={dir} onChange={(e) => setDir(e.target.value)} placeholder="Path to folder containing .gguf models" />
          <button className="btn" onClick={pickDir}>Choose…</button>
        </div>
      </div>

      <div style={{ marginTop: 12 }}>
        <div style={{ fontSize: 12, color: "var(--muted)" }}>Default model</div>
        <select className="select" value={defaultModel} onChange={(e) => setDefaultModel(e.target.value)}>
          <option value="">(none)</option>
          {models.map((m) => <option key={m} value={m}>{m}</option>)}
        </select>
      </div>

      <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
        <button className="btn btnPrimary" onClick={save} disabled={!dir}>Save</button>
        <button className="btn" onClick={refresh}>Reload</button>
      </div>

      {status && <div style={{ marginTop: 10, fontSize: 12, color: "var(--muted)" }}>{status}</div>}
    </div>
  );
}
