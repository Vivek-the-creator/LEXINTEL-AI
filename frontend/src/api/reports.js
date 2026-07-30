import api from "./client";

const BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const reportsApi = {
  save: (data) => api.post("/api/reports/", data),
  list: () => api.get("/api/reports/"),
  get: (id) => api.get(`/api/reports/${id}`),
  delete: (id) => api.delete(`/api/reports/${id}`),

  downloadPdf: async (reportId, filename) => {
    const token = localStorage.getItem("access_token");
    const res = await fetch(`${BASE}/api/reports/${reportId}/pdf`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("PDF download failed");
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename || "AI_Report.pdf";
    a.click();
    URL.revokeObjectURL(url);
  },

  downloadCasePdf: async (caseId, caseName) => {
    const token = localStorage.getItem("access_token");
    const res = await fetch(`${BASE}/api/cases/${caseId}/export/pdf`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("PDF export failed");
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${(caseName || "Case").replace(/\s+/g, "_")}_AI_Report.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  },
};
