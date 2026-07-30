import { useState, useEffect, useCallback, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft, FileText, BookOpen, Gavel, ListOrdered, FileSearch,
  Plus, RefreshCw, Loader2, AlertCircle, Clock, Shield, Upload,
  FolderOpen, X, TrendingUp, Lightbulb, PenLine, BarChart2, Download,
} from "lucide-react";
import { casesApi } from "../../api/cases";
import { uploadsApi } from "../../api/uploads";
import { reportsApi } from "../../api/reports";
import Button from "../../components/ui/Button";
import AIProgressPanel from "../../components/ui/AIProgressPanel";
import {
  Section, Pill, AgentStatus,
  DocumentIntelligenceResult, LegalResearchResult,
  SimilarCasesResult, EvidenceResult,
  OutcomePredictionResult, StrategyPlanningResult,
  LegalDraftsResult, CaseReportResult,
} from "../../components/ui/CaseResultComponents";
import { cn, formatDate, formatBytes } from "../../utils/helpers";
import toast from "react-hot-toast";

const SUPPORTED_EXTS = new Set([
  "pdf","doc","docx","rtf","jpg","jpeg","png","webp","bmp","tiff","tif",
  "mp4","mov","avi","mkv","webm","mp3","wav","m4a","ogg",
  "txt","eml","msg","csv","xlsx","xls",
]);
function extOf(name) { return (name.split(".").pop() || "").toLowerCase(); }
function isSupported(name) { return SUPPORTED_EXTS.has(extOf(name)); }

const TABS = [
  { id: "overview",    label: "Overview",       icon: FileSearch },
  { id: "timeline",    label: "Timeline",        icon: Clock },
  { id: "evidence",    label: "Evidence",        icon: Shield },
  { id: "research",    label: "Research",        icon: BookOpen },
  { id: "similar",     label: "Similar Cases",   icon: Gavel },
  { id: "prediction",  label: "Prediction",      icon: TrendingUp },
  { id: "strategy",    label: "Strategy",        icon: Lightbulb },
  { id: "drafts",      label: "Legal Drafts",    icon: PenLine },
  { id: "report",      label: "AI Report",       icon: BarChart2 },
];

export default function CaseDetailPage() {
  const { caseId } = useParams();
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [caseData, setCaseData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");

  const [uploads, setUploads] = useState([]);
  const [loadingUploads, setLoadingUploads] = useState(false);
  const [selectedFileIds, setSelectedFileIds] = useState(new Set());
  const [attaching, setAttaching] = useState(false);

  const [reanalyzeFiles, setReanalyzeFiles] = useState([]);
  const [reanalyzing, setReanalyzing] = useState(false);
  const [progress, setProgress] = useState(null);

  const fetchCase = useCallback(async () => {
    setLoading(true);
    try {
      const res = await casesApi.get(caseId);
      setCaseData(res.data);
    } catch {
      toast.error("Failed to load case");
      navigate("/dashboard/my-cases");
    } finally {
      setLoading(false);
    }
  }, [caseId, navigate]);

  useEffect(() => { fetchCase(); }, [fetchCase]);

  const loadUploads = useCallback(async () => {
    setLoadingUploads(true);
    try {
      const res = await uploadsApi.list();
      setUploads(res.data.items || []);
    } catch {
      toast.error("Failed to load uploads");
    } finally {
      setLoadingUploads(false);
    }
  }, []);

  const attachFiles = useCallback(async () => {
    if (selectedFileIds.size === 0) return;
    setAttaching(true);
    try {
      await casesApi.attachFiles(caseId, Array.from(selectedFileIds));
      toast.success("Files attached to case");
      setSelectedFileIds(new Set());
      fetchCase();
    } catch {
      toast.error("Failed to attach files");
    } finally {
      setAttaching(false);
    }
  }, [caseId, selectedFileIds, fetchCase]);

  const handleNewFilesSelect = useCallback((e) => {
    const fileList = Array.from(e.target.files || []);
    const supported = fileList
      .filter((f) => isSupported(f.name))
      .map((f) => ({
        name: f.name,
        relativePath: (f.webkitRelativePath || f.name).replace(/\\/g, "/"),
        file: f,
        size: f.size,
      }));
    if (supported.length === 0) return toast.error("No supported files selected");
    setReanalyzeFiles(supported);
  }, []);

  const runReanalysis = useCallback(async () => {
    if (reanalyzeFiles.length === 0) return;
    setReanalyzing(true);
    setProgress({ stage: "Scanning Case", agent: "File Classifier", message: "Starting re-analysis…", files_done: 0, files_total: reanalyzeFiles.length });

    try {
      const files = reanalyzeFiles.map((f) => f.file);
      const relPaths = reanalyzeFiles.map((f) => f.relativePath);
      let finalResult = null;

      await casesApi.streamReanalyze(caseId, files, relPaths, (eventName, data) => {
        if (eventName === "progress" || eventName === "agent_start") {
          setProgress(data);
        } else if (eventName === "agent_done") {
          setProgress((prev) => ({ ...prev, ...data }));
        } else if (eventName === "complete") {
          finalResult = data;
          setProgress(null);
          toast.success("Re-analysis complete!");
        } else if (eventName === "error") {
          toast.error(`${data.agent}: ${data.error}`);
        }
      });

      if (finalResult) {
        await casesApi.patchAnalysis(caseId, {
          case_name: caseData.case_name,
          session_id: finalResult.session_id,
          document_intelligence: finalResult.document_intelligence,
          legal_research: finalResult.legal_research,
          similar_cases: finalResult.similar_cases || [],
          evidence_items: finalResult.evidence_items || [],
          evidence_timeline: finalResult.evidence_timeline || [],
          evidence_analysis: finalResult.evidence_analysis,
          missing_evidence_hints: finalResult.missing_evidence_hints || [],
          outcome_prediction: finalResult.outcome_prediction,
          legal_strategy: finalResult.legal_strategy,
          legal_drafts: finalResult.legal_drafts || [],
          case_report: finalResult.case_report,
          agent_executions: finalResult.agent_executions || [],
          errors: finalResult.errors || [],
          warnings: finalResult.warnings || [],
          case_workspace: finalResult.case_workspace,
          metadata: finalResult.metadata || {},
        });
        setReanalyzeFiles([]);
        fetchCase();
      }
    } catch (err) {
      toast.error(err?.message || "Re-analysis failed");
      setProgress(null);
    } finally {
      setReanalyzing(false);
    }
  }, [caseId, reanalyzeFiles, caseData, fetchCase]);

  const exportPdf = useCallback(async () => {
    try {
      await reportsApi.downloadCasePdf(caseId, caseData?.case_name);
    } catch {
      toast.error("PDF export failed");
    }
  }, [caseId, caseData]);

  const saveReport = useCallback(async () => {
    if (!caseData?.case_report) return toast.error("No report available");
    try {
      await reportsApi.save({
        case_id: caseId,
        case_name: caseData.case_name,
        report_data: caseData.case_report,
        outcome_prediction: caseData.outcome_prediction,
        legal_strategy: caseData.legal_strategy,
        legal_drafts: caseData.legal_drafts || [],
        document_intelligence: caseData.document_intelligence,
        legal_research: caseData.legal_research,
        similar_cases: caseData.similar_cases || [],
        evidence_analysis: caseData.evidence_analysis,
        evidence_timeline: caseData.evidence_timeline || [],
        missing_evidence_hints: caseData.missing_evidence_hints || [],
      });
      toast.success("Report saved to Reports section");
    } catch {
      toast.error("Failed to save report");
    }
  }, [caseId, caseData]);

  // ── Export report as Markdown ───────────────────────────────────────────────
  const exportMarkdown = useCallback(() => {
    const c = caseData;
    if (!c) return;
    const report = c.case_report || {};
    const lines = [
      `# ${c.case_name} — AI Case Report`,
      `> Generated by LexIntel AI | ${new Date().toLocaleDateString()}`,
      `> ⚠️ AI GENERATED — NOT LEGAL ADVICE`,
      "",
      "## Executive Summary",
      report.executive_summary || "N/A",
      "",
      "## Outcome Prediction",
      `- Probability of Success: ${c.outcome_prediction?.probability_of_success || "N/A"}`,
      `- Case Strength: ${c.outcome_prediction?.case_strength_score || "N/A"}`,
      `- Confidence: ${c.outcome_prediction?.confidence_level || "N/A"}`,
      `- Risk Level: ${c.outcome_prediction?.risk_level || "N/A"}`,
      "",
      "## Key Strengths",
      ...(c.outcome_prediction?.key_strengths || []).map((s) => `- ${s}`),
      "",
      "## Key Weaknesses",
      ...(c.outcome_prediction?.key_weaknesses || []).map((s) => `- ${s}`),
      "",
      "## Legal Strategy",
      ...((c.legal_strategy?.strategies || []).map((s) =>
        `### ${s.name}\n${s.description}\n- Effort: ${s.effort} | Risk: ${s.risk_level}\n- Timeline: ${s.estimated_timeline}`
      )),
      "",
      "## Recommendations",
      ...(report.recommendations || []).map((r) => `- ${r}`),
      "",
      "## Disclaimer",
      report.disclaimer || c.outcome_prediction?.disclaimer || "",
    ];
    const blob = new Blob([lines.join("\n")], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${c.case_name.replace(/\s+/g, "_")}_AI_Report.md`;
    a.click();
    URL.revokeObjectURL(url);
  }, [caseData]);

  // ── Download a single draft ─────────────────────────────────────────────────
  const downloadDraft = useCallback((draft) => {
    const blob = new Blob([draft.content || ""], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${(draft.title || draft.document_type || "Draft").replace(/\s+/g, "_")}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
      </div>
    );
  }

  if (!caseData) return null;
  const c = caseData;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-start gap-4">
        <button
          onClick={() => navigate("/dashboard/my-cases")}
          className="p-2 rounded-lg text-surface-400 hover:text-surface-700 dark:hover:text-surface-200 hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors mt-0.5"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl font-bold text-surface-900 dark:text-surface-100 truncate">{c.case_name}</h1>
            <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 capitalize">
              {c.status}
            </span>
          </div>
          <div className="flex items-center gap-4 mt-1 text-xs text-surface-400 flex-wrap">
            <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5" /> Created {formatDate(c.created_at)}</span>
            <span className="flex items-center gap-1"><FileText className="w-3.5 h-3.5" /> {c.document_count} documents</span>
            <span className="flex items-center gap-1"><Shield className="w-3.5 h-3.5" /> {c.evidence_count} evidence items</span>
          </div>
        </div>
        <div className="flex gap-2 flex-shrink-0">
          {c.case_report && (
            <>
              <Button size="sm" variant="secondary" onClick={saveReport} className="gap-2">
                <Download className="w-4 h-4" /> Save Report
              </Button>
              <Button size="sm" variant="secondary" onClick={exportPdf} className="gap-2">
                <Download className="w-4 h-4" /> PDF
              </Button>
              <Button size="sm" variant="secondary" onClick={exportMarkdown} className="gap-2">
                <Download className="w-4 h-4" /> Markdown
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Re-analyze progress */}
      {reanalyzing && <AIProgressPanel progress={progress} />}

      {/* Pipeline execution summary */}
      {c.agent_executions?.length > 0 && (
        <div className="card p-5 space-y-3">
          <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide">Pipeline Execution</p>
          <AgentStatus executions={c.agent_executions} />
        </div>
      )}

      {/* Tabs */}
      <div className="card overflow-hidden">
        <div className="flex overflow-x-auto border-b border-surface-100 dark:border-surface-800 scrollbar-hide">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={cn(
                "flex items-center gap-2 px-4 py-3 text-sm font-medium whitespace-nowrap border-b-2 transition-colors flex-shrink-0",
                activeTab === id
                  ? "border-primary-500 text-primary-600 dark:text-primary-400"
                  : "border-transparent text-surface-500 hover:text-surface-700 dark:hover:text-surface-300"
              )}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </div>

        <div className="p-5">
          {activeTab === "overview" && (
            <DocumentIntelligenceResult data={c.document_intelligence} />
          )}
          {activeTab === "timeline" && (
            <EvidenceResult
              items={[]}
              timeline={c.evidence_timeline}
              analysis={null}
              hints={[]}
              timelineOnly
            />
          )}
          {activeTab === "evidence" && (
            <EvidenceResult
              items={c.evidence_items}
              timeline={c.evidence_timeline}
              analysis={c.evidence_analysis}
              hints={c.missing_evidence_hints}
            />
          )}
          {activeTab === "research" && (
            <LegalResearchResult data={c.legal_research} />
          )}
          {activeTab === "similar" && (
            <SimilarCasesResult cases={c.similar_cases} />
          )}
          {activeTab === "prediction" && (
            <OutcomePredictionResult data={c.outcome_prediction} />
          )}
          {activeTab === "strategy" && (
            <StrategyPlanningResult data={c.legal_strategy} />
          )}
          {activeTab === "drafts" && (
            <LegalDraftsResult drafts={c.legal_drafts} onDownload={downloadDraft} />
          )}
          {activeTab === "report" && (
            <CaseReportResult data={c.case_report} onExport={exportMarkdown} />
          )}
        </div>
      </div>

      {/* Add Evidence */}
      <div className="card overflow-hidden">
        <div className="p-5 border-b border-surface-100 dark:border-surface-800">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-blue-50 dark:bg-blue-900/20 flex items-center justify-center">
              <Plus className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="font-semibold text-surface-900 dark:text-surface-100">Add Evidence</p>
              <p className="text-xs text-surface-400">Attach additional files and re-run the full AI pipeline</p>
            </div>
          </div>
        </div>
        <div className="p-5 space-y-4">
          {/* Attach from uploads */}
          <div>
            <p className="text-sm font-medium text-surface-700 dark:text-surface-300 mb-2">From Uploaded Files</p>
            {uploads.length === 0 && !loadingUploads ? (
              <Button size="sm" variant="secondary" onClick={loadUploads}>Load Uploaded Files</Button>
            ) : loadingUploads ? (
              <div className="flex items-center gap-2 text-sm text-surface-400">
                <Loader2 className="w-4 h-4 animate-spin" /> Loading…
              </div>
            ) : (
              <div className="space-y-2">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-48 overflow-y-auto">
                  {uploads.map((f) => {
                    const sel = selectedFileIds.has(f.id);
                    return (
                      <button
                        key={f.id}
                        onClick={() => setSelectedFileIds((prev) => {
                          const next = new Set(prev);
                          sel ? next.delete(f.id) : next.add(f.id);
                          return next;
                        })}
                        className={cn(
                          "flex items-center gap-2 p-2.5 rounded-lg border text-left text-sm transition-all",
                          sel
                            ? "border-primary-500 bg-primary-50 dark:bg-primary-900/20"
                            : "border-surface-200 dark:border-surface-700 hover:border-primary-300"
                        )}
                      >
                        <FileText className="w-4 h-4 text-surface-400 flex-shrink-0" />
                        <span className="truncate text-surface-700 dark:text-surface-300">{f.original_filename}</span>
                      </button>
                    );
                  })}
                </div>
                {selectedFileIds.size > 0 && (
                  <Button size="sm" onClick={attachFiles} loading={attaching} className="gap-2">
                    <Upload className="w-4 h-4" />
                    Attach {selectedFileIds.size} File{selectedFileIds.size !== 1 ? "s" : ""}
                  </Button>
                )}
              </div>
            )}
          </div>

          {/* Re-analyze with new files */}
          <div className="border-t border-surface-100 dark:border-surface-800 pt-4">
            <p className="text-sm font-medium text-surface-700 dark:text-surface-300 mb-2">Re-analyze with New Files</p>
            <input ref={fileInputRef} type="file" multiple className="hidden" onChange={handleNewFilesSelect} />
            {reanalyzeFiles.length === 0 ? (
              <Button size="sm" variant="secondary" onClick={() => fileInputRef.current?.click()} className="gap-2">
                <FolderOpen className="w-4 h-4" />
                Select New Evidence Files
              </Button>
            ) : (
              <div className="space-y-2">
                <div className="space-y-1 max-h-32 overflow-y-auto">
                  {reanalyzeFiles.map((f) => (
                    <div key={f.relativePath} className="flex items-center gap-2 text-sm">
                      <FileText className="w-4 h-4 text-surface-400 flex-shrink-0" />
                      <span className="truncate text-surface-600 dark:text-surface-400 flex-1">{f.name}</span>
                      <span className="text-xs text-surface-400">{formatBytes(f.size)}</span>
                      <button onClick={() => setReanalyzeFiles((prev) => prev.filter((x) => x.relativePath !== f.relativePath))}>
                        <X className="w-3.5 h-3.5 text-surface-300 hover:text-red-500" />
                      </button>
                    </div>
                  ))}
                </div>
                <div className="flex gap-2">
                  <Button size="sm" onClick={runReanalysis} loading={reanalyzing} className="gap-2">
                    <RefreshCw className="w-4 h-4" />
                    Re-analyze Case
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setReanalyzeFiles([])}>Clear</Button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Errors */}
      {c.errors?.length > 0 && (
        <div className="card p-4 border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/10 space-y-2">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-500" />
            <p className="text-sm font-semibold text-red-700 dark:text-red-400">Agent errors during analysis</p>
          </div>
          {c.errors.map((e, i) => (
            <p key={i} className="text-xs text-red-600 dark:text-red-400 pl-6">
              <span className="font-medium capitalize">{e.agent}:</span> {e.error}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
