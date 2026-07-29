import api from "./client";

const BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const casesApi = {
  // ── Analysis (SSE streaming) ──────────────────────────────────────────────

  /**
   * Stream analysis of local folder files.
   * Returns an EventSource-like object via fetch + ReadableStream.
   * onEvent(eventName, data) is called for each SSE event.
   */
  streamAnalyze: async (files, relativePaths, caseName, onEvent) => {
    const form = new FormData();
    form.append("case_name", caseName);
    form.append("relative_paths", JSON.stringify(relativePaths));
    files.forEach((f) => form.append("files", f));

    const token = localStorage.getItem("access_token");
    const res = await fetch(`${BASE}/api/cases/analyze`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Analysis failed" }));
      throw new Error(err.detail || "Analysis failed");
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";
      for (const part of parts) {
        if (!part.trim()) continue;
        const lines = part.split("\n");
        let eventName = "message";
        let dataStr = "";
        for (const line of lines) {
          if (line.startsWith("event: ")) eventName = line.slice(7).trim();
          else if (line.startsWith("data: ")) dataStr = line.slice(6).trim();
        }
        if (dataStr) {
          try {
            onEvent(eventName, JSON.parse(dataStr));
          } catch {
            onEvent(eventName, { raw: dataStr });
          }
        }
      }
    }
  },

  /**
   * Stream analysis of already-uploaded files by their stored filenames.
   */
  streamAnalyzeSaved: async (fileIds, caseName, onEvent) => {
    const form = new FormData();
    form.append("case_name", caseName);
    fileIds.forEach((id) => form.append("file_ids", id));

    const token = localStorage.getItem("access_token");
    const res = await fetch(`${BASE}/api/cases/analyze-saved`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Analysis failed" }));
      throw new Error(err.detail || "Analysis failed");
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";
      for (const part of parts) {
        if (!part.trim()) continue;
        const lines = part.split("\n");
        let eventName = "message";
        let dataStr = "";
        for (const line of lines) {
          if (line.startsWith("event: ")) eventName = line.slice(7).trim();
          else if (line.startsWith("data: ")) dataStr = line.slice(6).trim();
        }
        if (dataStr) {
          try {
            onEvent(eventName, JSON.parse(dataStr));
          } catch {
            onEvent(eventName, { raw: dataStr });
          }
        }
      }
    }
  },

  // ── CRUD ──────────────────────────────────────────────────────────────────

  save: (data) => api.post("/api/cases/", data),

  list: (page = 1, pageSize = 20) =>
    api.get("/api/cases/", { params: { page, page_size: pageSize } }),

  get: (caseId) => api.get(`/api/cases/${caseId}`),

  delete: (caseId) => api.delete(`/api/cases/${caseId}`),

  attachFiles: (caseId, fileIds) =>
    api.post(`/api/cases/${caseId}/files`, { file_ids: fileIds }),

  patchAnalysis: (caseId, data) =>
    api.patch(`/api/cases/${caseId}/analysis`, data),

  exportReport: (caseId) =>
    api.get(`/api/cases/${caseId}/export/markdown`, { responseType: "text" }),

  // ── Re-analyze (SSE streaming) ────────────────────────────────────────────

  streamReanalyze: async (caseId, files, relativePaths, onEvent) => {
    const form = new FormData();
    form.append("relative_paths", JSON.stringify(relativePaths));
    files.forEach((f) => form.append("files", f));

    const token = localStorage.getItem("access_token");
    const res = await fetch(`${BASE}/api/cases/${caseId}/reanalyze`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Re-analysis failed" }));
      throw new Error(err.detail || "Re-analysis failed");
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";
      for (const part of parts) {
        if (!part.trim()) continue;
        const lines = part.split("\n");
        let eventName = "message";
        let dataStr = "";
        for (const line of lines) {
          if (line.startsWith("event: ")) eventName = line.slice(7).trim();
          else if (line.startsWith("data: ")) dataStr = line.slice(6).trim();
        }
        if (dataStr) {
          try {
            onEvent(eventName, JSON.parse(dataStr));
          } catch {
            onEvent(eventName, { raw: dataStr });
          }
        }
      }
    }
  },
};
