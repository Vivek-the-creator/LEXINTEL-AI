import api from "./client";

const BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const chatApi = {
  createSession: (title, caseId) =>
    api.post("/api/chat/session", { title, case_id: caseId }),

  listSessions: (caseId) =>
    api.get("/api/chat/sessions", { params: caseId ? { case_id: caseId } : {} }),

  getSession: (sessionId) => api.get(`/api/chat/session/${sessionId}`),

  deleteSession: (sessionId) => api.delete(`/api/chat/session/${sessionId}`),

  /**
   * Stream a chat message. Calls onChunk(text) for each token, returns full reply.
   */
  streamMessage: async (sessionId, message, caseId, onChunk) => {
    const token = localStorage.getItem("access_token");
    const res = await fetch(`${BASE}/api/chat/message`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ session_id: sessionId, message, case_id: caseId }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Chat failed" }));
      throw new Error(err.detail || "Chat failed");
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let full = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";
      for (const part of parts) {
        for (const line of part.split("\n")) {
          if (line.startsWith("data: ")) {
            const chunk = line.slice(6);
            if (chunk === "[DONE]") return full;
            full += chunk;
            onChunk(chunk);
          }
        }
      }
    }
    return full;
  },
};
