// import React, { useEffect, useState } from "react";
// import { initTheme, toggleTheme } from "./lib/theme";
// import { waitForBackend, getModels, query } from "./lib/api";
// import Settings from "./components/Settings";

// export default function App() {
//   const [backendReady, setBackendReady] = useState(false);
//   const [theme, setTheme] = useState("light");
//   const [showSettings, setShowSettings] = useState(false);

//   const [models, setModels] = useState<string[]>([]);
//   const [model, setModel] = useState<string>("");

//   const [sessionId, setSessionId] = useState("test-session-1");
//   const [mode, setMode] = useState<"precision" | "exploratory">("precision");
//   const [input, setInput] = useState("");
//   const [result, setResult] = useState<any>(null);
//   const [err, setErr] = useState<string>("");

//   useEffect(() => {
//     const t = initTheme();
//     setTheme(t);
//   }, []);

//   useEffect(() => {
//     (async () => {
//       const ok = await waitForBackend(15000);
//       setBackendReady(ok);
//       if (ok) {
//         const m = await getModels().catch(() => ({ models: [] }));
//         setModels(m.models || []);
//         setModel(m.default || "");
//       }
//     })();
//   }, []);

//   async function runQuery() {
//     setErr("");
//     setResult(null);
//     try {
//       const r = await query({
//         input_text: input,
//         session_id: sessionId,
//         mode,
//         model_name: model || null
//       });
//       setResult(r.data);
//     } catch (e: any) {
//       setErr(e.message || String(e));
//     }
//   }

//   return (
//     <>
//       <div className="topbar">
//         <div style={{ fontWeight: 800 }}>Sovereign Research Engine</div>
//         <span className="badge">{backendReady ? "Backend: Ready" : "Backend: Waiting…"}</span>

//         <div style={{ flex: 1 }} />

//         <select className="select" style={{ maxWidth: 360 }} value={model} onChange={(e) => setModel(e.target.value)}>
//           <option value="">(default)</option>
//           {models.map((m) => <option key={m} value={m}>{m}</option>)}
//         </select>

//         <select className="select" style={{ maxWidth: 180 }} value={mode} onChange={(e) => setMode(e.target.value as any)}>
//           <option value="precision">Precision</option>
//           <option value="exploratory">Exploratory</option>
//         </select>

//         <button className="btn" onClick={() => setTheme(toggleTheme())}>
//           Theme: {theme === "dark" ? "Dark" : "Light"}
//         </button>

//         <button className="btn" onClick={() => setShowSettings(true)}>Settings</button>
//       </div>

//       <div className="grid">
//         {/* Sidebar */}
//         <div className="card" style={{ padding: 12 }}>
//           <div style={{ fontWeight: 700, marginBottom: 10 }}>Sessions</div>
//           <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 6 }}>Session ID</div>
//           <input className="input mono" value={sessionId} onChange={(e) => setSessionId(e.target.value)} />
//           <div style={{ marginTop: 12, fontWeight: 700 }}>Notebook</div>
//           <div style={{ fontSize: 12, color: "var(--muted)" }}>Coming next: entries list + verified filters</div>
//         </div>

//         {/* Main */}
//         <div className="card" style={{ padding: 12, display: "flex", flexDirection: "column", gap: 10 }}>
//           <div style={{ fontWeight: 700 }}>Research Query</div>
//           <textarea
//             className="input"
//             style={{ minHeight: 120, resize: "vertical" }}
//             value={input}
//             onChange={(e) => setInput(e.target.value)}
//             placeholder="Ask a question grounded in your ingested PDFs…"
//           />
//           <div style={{ display: "flex", gap: 8 }}>
//             <button className="btn btnPrimary" onClick={runQuery} disabled={!backendReady || !input.trim()}>
//               Run
//             </button>
//           </div>

//           {err && <div className="card" style={{ padding: 10, borderColor: "var(--risk)" }}>{err}</div>}

//           {result && (
//             <div className="card" style={{ padding: 12 }}>
//               <div style={{ fontWeight: 700, marginBottom: 6 }}>Answer</div>
//               <div style={{ whiteSpace: "pre-wrap" }}>{result.answer}</div>
//             </div>
//           )}
//         </div>

//         {/* Audit Panel */}
//         <div className="card" style={{ padding: 12 }}>
//           <div style={{ fontWeight: 700, marginBottom: 10 }}>Audit</div>

//           {!result && <div style={{ fontSize: 12, color: "var(--muted)" }}>Run a query to see Belief Report + citations.</div>}

//           {result?.belief_report && (
//             <>
//               <div className="badge" style={{ marginBottom: 8 }}>
//                 Epistemic: <span className="mono">{result.belief_report.epistemic_score}</span>
//               </div>

//               <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
//                 <div>
//                   <div style={{ fontSize: 12, color: "var(--muted)" }}>Evidence quality</div>
//                   <div>{result.belief_report.evidence_quality}</div>
//                 </div>
//                 <div>
//                   <div style={{ fontSize: 12, color: "var(--muted)" }}>Hallucination risk</div>
//                   <div>{result.belief_report.hallucination_risk}</div>
//                 </div>
//                 <div>
//                   <div style={{ fontSize: 12, color: "var(--muted)" }}>Reasoning process</div>
//                   <div className="mono" style={{ fontSize: 12, whiteSpace: "pre-wrap" }}>
//                     {result.belief_report.reasoning_process}
//                   </div>
//                 </div>
//               </div>

//               <div style={{ marginTop: 12, fontWeight: 700 }}>Citations</div>
//               <ul style={{ margin: "6px 0 0 18px", padding: 0 }}>
//                 {(result.citations || []).map((c: string, i: number) => (
//                   <li key={i} className="mono" style={{ fontSize: 12, marginBottom: 6 }}>{c}</li>
//                 ))}
//               </ul>
//             </>
//           )}
//         </div>
//       </div>

//       {showSettings && (
//         <div
//           style={{
//             position: "fixed",
//             inset: 0,
//             background: "rgba(0,0,0,0.35)",
//             display: "grid",
//             placeItems: "center",
//             padding: 12,
//           }}
//         >
//           <div style={{ width: 720, maxWidth: "100%" }}>
//             <Settings onClose={() => setShowSettings(false)} />
//           </div>
//         </div>
//       )}
//     </>
//   );
// }
import React, { useEffect, useState } from "react";
import { waitForBackend, getModels, query, getSettings, setSettings } from "./lib/api";

function SettingsModal({ onClose }: { onClose: () => void }) {
  const [dir, setDir] = useState("");
  const [defaultModel, setDefaultModel] = useState("");
  const [status, setStatus] = useState("");

  useEffect(() => {
    (async () => {
      const s = await getSettings();
      setDir(s.llm_models_dir || "");
      setDefaultModel(s.default_llm_model || "");
    })().catch((e) => setStatus(e.message || String(e)));
  }, []);

  async function save() {
    setStatus("Saving...");
    await setSettings({ llm_models_dir: dir, default_llm_model: defaultModel || null });
    setStatus("Saved ✅");
  }

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.35)", display: "grid", placeItems: "center", padding: 12 }}>
      <div className="card" style={{ width: 720, maxWidth: "100%" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ fontWeight: 800 }}>Settings (Test A)</div>
          <button className="btn" onClick={onClose}>Close</button>
        </div>

        <div style={{ marginTop: 12 }}>
          <div style={{ fontSize: 12, opacity: 0.8 }}>Models folder (paste path)</div>
          <input className="input" value={dir} onChange={(e) => setDir(e.target.value)} placeholder="C:\path\to\models\llms" />
        </div>

        <div style={{ marginTop: 12 }}>
          <div style={{ fontSize: 12, opacity: 0.8 }}>Default model (optional)</div>
          <input className="input" value={defaultModel} onChange={(e) => setDefaultModel(e.target.value)} placeholder="qwen2.5-....gguf" />
        </div>

        <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
          <button className="btn btnPrimary" onClick={save} disabled={!dir.trim()}>Save</button>
        </div>

        {status && <div style={{ marginTop: 10, fontSize: 12, opacity: 0.8 }}>{status}</div>}
      </div>
    </div>
  );
}

export default function App() {
  const [backendReady, setBackendReady] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  const [models, setModels] = useState<string[]>([]);
  const [model, setModel] = useState<string>("");

  const [sessionId, setSessionId] = useState("test-session-1");
  const [mode, setMode] = useState<"precision" | "exploratory">("precision");
  const [input, setInput] = useState("");
  const [result, setResult] = useState<any>(null);
  const [err, setErr] = useState<string>("");

  useEffect(() => {
    (async () => {
      const ok = await waitForBackend(15000);
      setBackendReady(ok);
      if (ok) {
        const m = await getModels().catch(() => ({ models: [], default: "" }));
        setModels(m.models || []);
        setModel(m.default || "");
      }
    })();
  }, []);

  async function runQuery() {
    setErr("");
    setResult(null);
    try {
      const r = await query({
        input_text: input,
        session_id: sessionId,
        mode,
        model_name: model || null,
      });
      setResult(r.data);
    } catch (e: any) {
      setErr(e.message || String(e));
    }
  }

  return (
    <>
      <div className="topbar">
        <div className="brand">
          <div className="brandTitle">Sovereign Research Engine</div>
          <div className="brandSub">Epistemic integrity • Offline-first • Audited outputs</div>
        </div>

        <span className="pill">
          {backendReady ? "Backend ready" : "Waiting for backend…"}
        </span>

        <div className="spacer" />

        <select className="select" style={{ maxWidth: 360 }} value={model} onChange={(e) => setModel(e.target.value)}>
          <option value="">(default)</option>
          {models.map((m) => <option key={m} value={m}>{m}</option>)}
        </select>

        <select className="select" style={{ maxWidth: 170 }} value={mode} onChange={(e) => setMode(e.target.value as any)}>
          <option value="precision">Precision</option>
          <option value="exploratory">Exploratory</option>
        </select>

        <button className="btn btnGhost" onClick={() => setShowSettings(true)}>Settings</button>
      </div>

      <div className="grid">
        <div className="card">
          <div style={{ fontWeight: 800, marginBottom: 10 }}>Session</div>
          <div style={{ fontSize: 12, opacity: 0.8 }}>Session ID</div>
          <input className="input" value={sessionId} onChange={(e) => setSessionId(e.target.value)} />
          <div style={{ marginTop: 12, fontSize: 12, opacity: 0.8 }}>Notebook UI next.</div>
        </div>

        <div className="card" style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <div style={{ fontWeight: 800 }}>Research Query</div>
          <textarea value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask something grounded in your PDFs…" style={{ minHeight: 120 }} />
          <div style={{ display: "flex", gap: 8 }}>
            <button className="btn btnPrimary" onClick={runQuery} disabled={!backendReady || !input.trim()}>Run</button>
          </div>

          {err && <div className="card" style={{ borderColor: "#EF4444" }}>{err}</div>}

          {result && (
            <div className="card">
              <div style={{ fontWeight: 800, marginBottom: 6 }}>Answer</div>
              <div style={{ whiteSpace: "pre-wrap" }}>{result.answer}</div>
            </div>
          )}
        </div>

        <div className="card">
          <div style={{ fontWeight: 800, marginBottom: 10 }}>Audit</div>
          {!result && <div style={{ fontSize: 12, opacity: 0.8 }}>Run a query to see belief report + citations.</div>}

          {result?.belief_report && (
            <>
              <div className="badge" style={{ marginBottom: 8 }}>
                Epistemic: {result.belief_report.epistemic_score}
              </div>

              <div style={{ fontSize: 12, opacity: 0.8 }}>Evidence quality</div>
              <div style={{ marginBottom: 8 }}>{result.belief_report.evidence_quality}</div>

              <div style={{ fontSize: 12, opacity: 0.8 }}>Hallucination risk</div>
              <div style={{ marginBottom: 8 }}>{result.belief_report.hallucination_risk}</div>

              <div style={{ fontSize: 12, opacity: 0.8 }}>Reasoning</div>
              <div style={{ fontSize: 12, whiteSpace: "pre-wrap" }}>{result.belief_report.reasoning_process}</div>

              <div style={{ marginTop: 12, fontWeight: 800 }}>Citations</div>
              <ul style={{ margin: "6px 0 0 18px", padding: 0 }}>
                {(result.citations || []).map((c: string, i: number) => (
                  <li key={i} style={{ fontSize: 12, marginBottom: 6 }}>{c}</li>
                ))}
              </ul>
            </>
          )}
        </div>
      </div>

      {showSettings && <SettingsModal onClose={() => setShowSettings(false)} />}
    </>
  );
}
