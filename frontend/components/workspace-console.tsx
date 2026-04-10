"use client";

import { FormEvent, useEffect, useState, useTransition } from "react";

type ReadinessResponse = {
  status: string;
  service: string;
  readiness: {
    project_name: string;
    api_prefix: string;
    llm: {
      provider: string;
      model: string;
      base_url: string | null;
      configured: boolean;
      blocking: boolean;
      missing: string[];
    };
    services: {
      postgres: { host: string; port: number; configured: boolean };
      neo4j: { uri: string; configured: boolean };
      qdrant: { host: string; port: number; configured: boolean };
      redis: { host: string; port: number; configured: boolean };
    };
  };
};

type RecentDocumentsResponse = {
  workspace_id: string;
  documents: Array<{
    document_id: string;
    filename: string;
    mime_type: string;
    created_at: string;
    job: null | {
      job_id: string;
      status: string;
      error_message: string | null;
      created_at: string;
      completed_at: string | null;
      is_terminal: boolean;
      can_retry: boolean;
      action_hint: string;
    };
  }>;
};

type TraceEvent = {
  step: string;
  title: string;
  detail: string;
  status: string;
  timestamp: string;
};

type QueryResponse = {
  query: string;
  response: string;
  trace: TraceEvent[];
  scope: "workspace" | "documents";
  document_ids: string[];
  workspace_id: string;
};

const defaultApiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
const defaultApiKey = "Bearer rag-dev-123456789";

function LoadingDots({ active }: { active: boolean }) {
  const [count, setCount] = useState(1);

  useEffect(() => {
    if (!active) {
      setCount(1);
      return;
    }

    const timer = window.setInterval(() => {
      setCount((current) => (current >= 4 ? 1 : current + 1));
    }, 380);

    return () => window.clearInterval(timer);
  }, [active]);

  return <span className="loading-dots">{active ? ".".repeat(count) : ""}</span>;
}

async function parseError(response: Response) {
  const text = await response.text();
  try {
    const parsed = JSON.parse(text);
    return parsed.detail ?? parsed.message ?? text;
  } catch {
    return text || `Request failed with status ${response.status}`;
  }
}

export function WorkspaceConsole() {
  const [apiBaseUrl, setApiBaseUrl] = useState(defaultApiBase);
  const [apiKey, setApiKey] = useState(defaultApiKey);
  const [query, setQuery] = useState("What is in the uploaded document?");
  const [queryScope, setQueryScope] = useState<"workspace" | "documents">("workspace");
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<string[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
  const [documents, setDocuments] = useState<RecentDocumentsResponse["documents"]>([]);
  const [trace, setTrace] = useState<TraceEvent[]>([]);
  const [responseText, setResponseText] = useState("");
  const [activeJobId, setActiveJobId] = useState("");
  const [statusMessage, setStatusMessage] = useState("Ready.");
  const [workspaceId, setWorkspaceId] = useState("");
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    const storedApiBase = window.localStorage.getItem("sovereignrag.apiBaseUrl");
    const storedApiKey = window.localStorage.getItem("sovereignrag.apiKey");
    if (storedApiBase) {
      setApiBaseUrl(storedApiBase);
    }
    if (storedApiKey) {
      setApiKey(storedApiKey);
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem("sovereignrag.apiBaseUrl", apiBaseUrl);
  }, [apiBaseUrl]);

  useEffect(() => {
    window.localStorage.setItem("sovereignrag.apiKey", apiKey);
  }, [apiKey]);

  useEffect(() => {
    if (queryScope === "workspace") {
      setSelectedDocumentIds([]);
    }
  }, [queryScope]);

  async function fetchReadiness() {
    setStatusMessage("Refreshing backend readiness...");
    const response = await fetch(`${apiBaseUrl}/`, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(await parseError(response));
    }
    const data: ReadinessResponse = await response.json();
    setReadiness(data);
    setStatusMessage("Backend readiness loaded.");
  }

  async function fetchRecentDocuments() {
    const response = await fetch(`${apiBaseUrl}/api/v1/documents/recent`, {
      headers: { Authorization: apiKey },
      cache: "no-store",
    });
    if (!response.ok) {
      throw new Error(await parseError(response));
    }
    const data: RecentDocumentsResponse = await response.json();
    setDocuments(data.documents);
    setWorkspaceId(data.workspace_id);
  }

  async function bootstrapDashboard() {
    await fetchReadiness();
    await fetchRecentDocuments();
  }

  useEffect(() => {
    startTransition(() => {
      bootstrapDashboard().catch((error: Error) => {
        setStatusMessage(error.message);
      });
    });
  }, []);

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedFile) {
      setStatusMessage("Choose a file before uploading.");
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

    setStatusMessage(`Uploading ${selectedFile.name}...`);
    const response = await fetch(`${apiBaseUrl}/api/v1/documents/upload`, {
      method: "POST",
      headers: { Authorization: apiKey },
      body: formData,
    });

    if (!response.ok) {
      setStatusMessage(await parseError(response));
      return;
    }

    const data = await response.json();
    setActiveJobId(data.job_id);
    setStatusMessage(`Upload accepted. Tracking job ${data.job_id}.`);
    await fetchRecentDocuments();
  }

  async function checkJob(jobId: string) {
    setStatusMessage(`Checking job ${jobId}...`);
    const response = await fetch(`${apiBaseUrl}/api/v1/documents/${jobId}/status`, {
      headers: { Authorization: apiKey },
      cache: "no-store",
    });

    if (!response.ok) {
      setStatusMessage(await parseError(response));
      return;
    }

    const data = await response.json();
    setActiveJobId(jobId);
    setStatusMessage(data.action_hint ?? `Job ${jobId} is ${data.status}.`);
    await fetchRecentDocuments();
  }

  async function retryJob(jobId: string) {
    setStatusMessage(`Retrying job ${jobId}...`);
    const response = await fetch(`${apiBaseUrl}/api/v1/documents/${jobId}/retry`, {
      method: "POST",
      headers: { Authorization: apiKey },
    });

    if (!response.ok) {
      setStatusMessage(await parseError(response));
      return;
    }

    const data = await response.json();
    setActiveJobId(data.retry_job.job_id);
    setStatusMessage(`Retry queued as job ${data.retry_job.job_id}.`);
    await fetchRecentDocuments();
  }

  async function resetWorkspace() {
    setStatusMessage("Resetting workspace data...");
    const response = await fetch(`${apiBaseUrl}/api/v1/documents/reset-workspace`, {
      method: "POST",
      headers: { Authorization: apiKey },
    });

    if (!response.ok) {
      setStatusMessage(await parseError(response));
      return;
    }

    const data = await response.json();
    setDocuments([]);
    setTrace([]);
    setResponseText("");
    setActiveJobId("");
    setStatusMessage(
      `Workspace reset. Deleted ${data.deleted_documents} documents and ${data.deleted_upload_files} upload files.`
    );
    await fetchRecentDocuments();
  }

  async function runStreamedQuery() {
    if (queryScope === "documents" && selectedDocumentIds.length === 0) {
      setStatusMessage("Select at least one document before running a document-scoped query.");
      return;
    }

    setStatusMessage("Streaming reasoning trace...");
    setTrace([]);
    setResponseText("");

    const payload =
      queryScope === "documents"
        ? { query, scope: queryScope, document_ids: selectedDocumentIds }
        : { query, scope: queryScope };

    const response = await fetch(`${apiBaseUrl}/api/v1/query/stream`, {
      method: "POST",
      headers: {
        Authorization: apiKey,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok || !response.body) {
      setStatusMessage(await parseError(response));
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        if (!line.trim()) {
          continue;
        }

        const message = JSON.parse(line) as
          | { type: "trace"; data: TraceEvent }
          | { type: "final"; data: QueryResponse }
          | { type: "error"; data: { detail: string } };

        if (message.type === "trace") {
          setTrace((current) => [...current, message.data]);
          setStatusMessage(`Trace: ${message.data.title}`);
        }

        if (message.type === "final") {
          setResponseText(message.data.response);
          setTrace(message.data.trace);
          setWorkspaceId(message.data.workspace_id);
          setStatusMessage(
            message.data.scope === "documents"
              ? `Query completed with ${message.data.document_ids.length} selected document(s).`
              : "Query completed across the full workspace."
          );
        }

        if (message.type === "error") {
          setStatusMessage(message.data.detail);
        }
      }
    }
  }

  return (
    <main className="console-shell">
      <section className="hero-panel">
        <div className="hero-copy">
          <p className="eyebrow">Week 6 Product Layer</p>
          <h1>SovereignRAG Workspace Console</h1>
          <p className="hero-text">
            A frontend for workspace-bound uploads, job tracking, streamed reasoning traces, and iterative query testing.
          </p>
        </div>
        <div className="hero-metrics">
          <div className="metric-card">
            <span>Workspace</span>
            <strong>{workspaceId || "Not loaded yet"}</strong>
          </div>
          <div className="metric-card">
            <span>Documents</span>
            <strong>{documents.length}</strong>
          </div>
          <div className="metric-card">
            <span>Tracked Job</span>
            <strong>{activeJobId || "None"}</strong>
          </div>
        </div>
      </section>

      <section className="grid-shell">
        <article className="panel panel-wide">
          <div className="panel-header">
            <h2>Connection</h2>
            <button className="ghost-button" onClick={() => startTransition(() => bootstrapDashboard().catch((error: Error) => setStatusMessage(error.message)))}>
              Refresh
            </button>
          </div>
          <div className="field-grid">
            <label className="field">
              <span>API Base URL</span>
              <input value={apiBaseUrl} onChange={(event) => setApiBaseUrl(event.target.value)} />
            </label>
            <label className="field">
              <span>Authorization Header</span>
              <input value={apiKey} onChange={(event) => setApiKey(event.target.value)} />
            </label>
          </div>
          <div className="readiness-grid">
            <div className="readiness-card">
              <span>Service</span>
              <strong>{readiness?.service ?? "Loading..."}</strong>
            </div>
            <div className="readiness-card">
              <span>LLM Provider</span>
              <strong>{readiness?.readiness.llm.provider ?? "Loading..."}</strong>
            </div>
            <div className="readiness-card">
              <span>LLM Model</span>
              <strong>{readiness?.readiness.llm.model ?? "Loading..."}</strong>
            </div>
            <div className="readiness-card">
              <span>Configured</span>
              <strong>{readiness?.readiness.llm.configured ? "Yes" : "No"}</strong>
            </div>
          </div>
        </article>

        <article className="panel">
          <div className="panel-header">
            <h2>Ingestion</h2>
            <button className="danger-button" onClick={() => startTransition(() => resetWorkspace().catch((error: Error) => setStatusMessage(error.message)))}>
              Reset Workspace
            </button>
          </div>
          <form className="stack" onSubmit={(event) => startTransition(() => handleUpload(event).catch((error: Error) => setStatusMessage(error.message)))}>
            <label className="upload-zone">
              <span>{selectedFile ? selectedFile.name : "Choose a PDF or TXT file"}</span>
              <input
                type="file"
                accept=".pdf,.txt,text/plain,application/pdf"
                onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
              />
            </label>
            <button className="primary-button" type="submit">
              Upload Document
            </button>
          </form>
          <p className="status-text">{statusMessage}</p>
        </article>

        <article className="panel">
          <div className="panel-header">
            <h2>Documents</h2>
            <button className="ghost-button" onClick={() => startTransition(() => fetchRecentDocuments().catch((error: Error) => setStatusMessage(error.message)))}>
              Reload
            </button>
          </div>
          <div className="document-list">
            {documents.length === 0 ? (
              <p className="muted-copy">No workspace documents yet.</p>
            ) : (
              documents.map((item) => (
                <div className="document-card" key={item.document_id}>
                  <div>
                    <p className="document-title">{item.filename}</p>
                    <p className="document-meta">{new Date(item.created_at).toLocaleString()}</p>
                  </div>
                  <div className="job-block">
                    <span className={`pill pill-${item.job?.status?.toLowerCase() ?? "idle"}`}>
                      {item.job?.status ?? "NO JOB"}
                      <LoadingDots active={item.job?.status === "PENDING" || item.job?.status === "PROCESSING"} />
                    </span>
                    {item.job && (
                      <>
                        <button className="ghost-button small-button" onClick={() => startTransition(() => checkJob(item.job!.job_id).catch((error: Error) => setStatusMessage(error.message)))}>
                          Check Job
                        </button>
                        {item.job.can_retry && (
                          <button className="ghost-button small-button" onClick={() => startTransition(() => retryJob(item.job!.job_id).catch((error: Error) => setStatusMessage(error.message)))}>
                            Retry
                          </button>
                        )}
                      </>
                    )}
                  </div>
                  {item.job?.action_hint && <p className="document-meta">{item.job.action_hint}</p>}
                  {item.job?.error_message && <p className="error-copy">{item.job.error_message}</p>}
                </div>
              ))
            )}
          </div>
        </article>

        <article className="panel panel-wide">
          <div className="panel-header">
            <h2>Query Console</h2>
            <button className="primary-button" onClick={() => startTransition(() => runStreamedQuery().catch((error: Error) => setStatusMessage(error.message)))}>
              Run Streamed Query
            </button>
          </div>
          <label className="field">
            <span>Question</span>
            <textarea rows={4} value={query} onChange={(event) => setQuery(event.target.value)} />
          </label>
          <div className="field-grid">
            <label className="field">
              <span>Retrieval Scope</span>
              <select value={queryScope} onChange={(event) => setQueryScope(event.target.value as "workspace" | "documents")}>
                <option value="workspace">Full workspace</option>
                <option value="documents">Selected documents only</option>
              </select>
            </label>
            <label className="field">
              <span>Selected Documents</span>
              <select
                multiple
                value={selectedDocumentIds}
                disabled={queryScope !== "documents" || documents.length === 0}
                onChange={(event) =>
                  setSelectedDocumentIds(Array.from(event.target.selectedOptions, (option) => option.value))
                }
              >
                {documents.map((item) => (
                  <option key={item.document_id} value={item.document_id}>
                    {item.filename}
                  </option>
                ))}
              </select>
            </label>
          </div>
          {queryScope === "documents" && selectedDocumentIds.length === 0 && (
            <p className="muted-copy">Select at least one document to run a document-scoped query.</p>
          )}
          <div className="response-grid">
            <div className="response-panel">
              <h3>Reasoning Trace</h3>
              <div className="trace-list">
                {trace.length === 0 ? (
                  <p className="muted-copy">No trace events yet.</p>
                ) : (
                  trace.map((item) => (
                    <div className="trace-card" key={`${item.step}-${item.timestamp}`}>
                      <div className="trace-head">
                        <strong>{item.title}</strong>
                        <span className={`trace-status trace-status-${item.status}`}>{item.status}</span>
                      </div>
                      <p>{item.detail}</p>
                    </div>
                  ))
                )}
              </div>
            </div>
            <div className="response-panel">
              <h3>Agent Response</h3>
              <pre className="response-copy">{responseText || "No response yet."}</pre>
            </div>
          </div>
        </article>
      </section>

      <footer className="footer-bar">
        <span>{isPending ? "Working..." : "Idle"}</span>
        <span>Frontend ready for faster iterative testing.</span>
      </footer>
    </main>
  );
}
