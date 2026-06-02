const base = import.meta.env.VITE_API_URL ?? "";

async function get(path, init) {
  const res = await fetch(`${base}${path}`, init);
  if (!res.ok) throw new Error((await res.text()) || res.statusText);
  return res.json();
}

export const api = {
  listIncidents: () => get("/api/incidents"),
  createIncident: (title, description) =>
    get("/api/incidents", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, description }),
    }),
  analyzeIncident: (id, form) =>
    get(`/api/incidents/${id}/analyze`, { method: "POST", body: form }),
  ragQuery: (question, incidentId) =>
    get("/api/rag/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, incident_id: incidentId }),
    }),
  ingestDoc: (file) => {
    const fd = new FormData();
    fd.append("file", file);
    return get("/api/rag/ingest", { method: "POST", body: fd });
  },
};
