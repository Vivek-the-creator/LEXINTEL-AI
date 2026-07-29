import api from "./client";

export const agentsApi = {
  runDocumentIntelligence: (text, caseId) =>
    api.post("/api/agents/document-intelligence/run", { text, case_id: caseId }),

  runDocumentIntelligenceUpload: (file, caseId) => {
    const form = new FormData();
    form.append("file", file);
    if (caseId) form.append("case_id", caseId);
    return api.post("/api/agents/document-intelligence/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 120000,
    });
  },

  runLegalResearch: (text, caseId) =>
    api.post("/api/agents/legal-research/run", { text, case_id: caseId }),

  runSimilarCases: (text, caseId) =>
    api.post("/api/agents/similar-cases/run", { text, case_id: caseId }),

  runEvidenceAnalysis: (text, caseId) =>
    api.post("/api/agents/evidence-analysis/run", { text, case_id: caseId }),

  runPipeline: (text, filePaths, caseId) =>
    api.post(
      "/api/agents/pipeline/phase3a",
      { text, file_paths: filePaths || [], case_id: caseId },
      { timeout: 180000 }
    ),

  runPipelineUpload: (files, caseText, caseId) => {
    const form = new FormData();
    files.forEach((f) => form.append("files", f));
    if (caseText) form.append("case_text", caseText);
    if (caseId) form.append("case_id", caseId);
    return api.post("/api/agents/pipeline/phase3a/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 180000,
    });
  },
};
