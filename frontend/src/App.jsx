import { useEffect, useState } from "react";
import { api } from "./api/client";

export default function App() {
  const [incidents, setIncidents] = useState([]);
  const [active, setActive] = useState(null);
  const [title, setTitle] = useState("");
  const [desc, setDesc] = useState("");
  const [logs, setLogs] = useState("");
  const [overrideQ, setOverrideQ] = useState("");
  const [shot, setShot] = useState(null);
  const [askText, setAskText] = useState("");
  const [askReply, setAskReply] = useState("");
  const [busy, setBusy] = useState(false);
  const [flash, setFlash] = useState("");

  async function reload() {
    const list = await api.listIncidents();
    setIncidents(list);
    if (active) {
      const again = list.find((i) => i.id === active.id);
      if (again) setActive(again);
    }
  }

  useEffect(() => {
    reload().catch((e) => setFlash(String(e)));
  }, []);

  async function onCreate(e) {
    e.preventDefault();
    setBusy(true);
    setFlash("");
    try {
      const inc = await api.createIncident(title, desc);
      setTitle("");
      setDesc("");
      setActive(inc);
      await reload();
      setFlash("saved");
    } catch (err) {
      setFlash(String(err));
    } finally {
      setBusy(false);
    }
  }

  async function onAnalyze(e) {
    e.preventDefault();
    if (!active) return;
    setBusy(true);
    setFlash("");
    try {
      const fd = new FormData();
      if (logs) fd.append("logs", logs);
      if (overrideQ) fd.append("question", overrideQ);
      if (shot) fd.append("screenshot", shot);
      const updated = await api.analyzeIncident(active.id, fd);
      setActive(updated);
      await reload();
      setFlash("analysis finished");
    } catch (err) {
      setFlash(String(err));
    } finally {
      setBusy(false);
    }
  }

  async function onAsk(e) {
    e.preventDefault();
    setBusy(true);
    try {
      const res = await api.ragQuery(askText, active?.id);
      setAskReply(res.answer);
    } catch (err) {
      setFlash(String(err));
    } finally {
      setBusy(false);
    }
  }

  async function onDocPick(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setBusy(true);
    try {
      const res = await api.ingestDoc(file);
      setFlash(`indexed ${res.file} (${res.chunks} chunks)`);
    } catch (err) {
      setFlash(String(err));
    } finally {
      setBusy(false);
      e.target.value = "";
    }
  }

  return (
    <div className="wrap">
      <header>
        <h1>Incident desk</h1>
        <p className="sub">logs, screenshots, runbooks — one place</p>
      </header>

      {flash && <p className="flash">{flash}</p>}

      <div className="cols">
        <section className="panel">
          <h2>Open a ticket</h2>
          <form onSubmit={onCreate}>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="prod checkout 502"
              required
            />
            <textarea
              value={desc}
              onChange={(e) => setDesc(e.target.value)}
              placeholder="what broke, when, links..."
              rows={3}
            />
            <button disabled={busy}>Save</button>
          </form>

          <h2 className="gap">Add runbook</h2>
          <input type="file" accept=".pdf,.md,.txt" onChange={onDocPick} />
        </section>

        <section className="panel">
          <h2>Tickets</h2>
          <ul className="list">
            {incidents.map((inc) => (
              <li key={inc.id}>
                <button
                  type="button"
                  className={active?.id === inc.id ? "picked" : ""}
                  onClick={() => setActive(inc)}
                >
                  <span>{inc.title}</span>
                  <small>{inc.status}</small>
                </button>
              </li>
            ))}
            {!incidents.length && <p className="dim">empty so far</p>}
          </ul>
        </section>

        <section className="panel wide">
          <h2>Run analysis</h2>
          {!active ? (
            <p className="dim">pick a ticket first</p>
          ) : (
            <form onSubmit={onAnalyze}>
              <p className="ticket-name">{active.title}</p>
              <textarea
                className="mono"
                value={logs}
                onChange={(e) => setLogs(e.target.value)}
                placeholder="paste logs here"
                rows={9}
              />
              <label>
                screenshot
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => setShot(e.target.files?.[0] ?? null)}
                />
              </label>
              <input
                value={overrideQ}
                onChange={(e) => setOverrideQ(e.target.value)}
                placeholder="custom question (optional)"
              />
              <button disabled={busy}>Run it</button>
            </form>
          )}
        </section>

        <section className="panel">
          <h2>Ask runbook</h2>
          <form onSubmit={onAsk}>
            <textarea
              value={askText}
              onChange={(e) => setAskText(e.target.value)}
              rows={4}
              placeholder="what usually causes 502 after deploy?"
              required
            />
            <button disabled={busy}>Ask</button>
          </form>
          {askReply && <pre className="out">{askReply}</pre>}
        </section>

        <section className="panel wide">
          <h2>Output</h2>
          {!active ? (
            <p className="dim">shows up after you run analysis</p>
          ) : (
            <div className="out-grid">
              <Out label="log summary" text={active.log_summary} />
              <Out label="ocr" text={active.ocr_text} />
              <Out label="screenshot notes" text={active.cv_analysis} />
              <Out label="runbook take" text={active.diagnosis ?? active.rag_answer} />
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

function Out({ label, text }) {
  return (
    <div>
      <h3>{label}</h3>
      <pre>{text || "—"}</pre>
    </div>
  );
}
