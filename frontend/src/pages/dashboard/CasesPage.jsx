import { useState, useEffect, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import {
  Brain, FolderOpen, Upload, FileText, Image, Music, Video,
  File, CheckCircle, AlertCircle, Sparkles, Save, ChevronDown,
  ChevronUp, BookOpen, Gavel, ListOrdered, FileSearch, X,
  TrendingUp, Lightbulb, PenLine, BarChart2,
} from "lucide-react";
import { uploadsApi } from "../../api/uploads";
import { casesApi } from "../../api/cases";
import Button from "../../components/ui/Button";
import AIProgressPanel from "../../components/ui/AIProgressPanel";
import {
  Section, Pill, AgentStatus,
  DocumentIntelligenceResult, LegalResearchResult,
  SimilarCasesResult, EvidenceResult,
  OutcomePredictionResult, StrategyPlanningResult,
  LegalDraftsResult, CaseReportResult,
} from "../../components/ui/CaseResultComponents";
import { cn, formatBytes } from "../../utils/helpers";
import toast from "react-hot-toast";

// ── Supported extensions (must match backend SUPPORTED_EXTENSIONS) ─────────────
const SUPPORTED_EXTS = new Set([
  "pdf","doc","docx","rtf",
  "jpg","jpeg","png","webp","bmp","tiff","tif",
  "mp4","mov","avi","mkv","webm",
  "mp3","wav","m4a","ogg",
  "txt","eml","msg","csv","xlsx","xls",
]);

function extOf(name) { return (name.split(".").pop() || "").toLowerCase(); }
function isSupported(name) { return SUPPORTED_EXTS.has(extOf(name)); }

function fileIcon(name) {
  const ext = extOf(name);
  if (["jpg","jpeg","png","webp","bmp","tiff","tif"].includes(ext)) return Image;
  if (["mp3","wav","m4a","ogg"].includes(ext)) return Music;
  if (["mp4","mov","avi","mkv","webm"].includes(ext)) return Video;
  if (["pdf","doc","docx","rtf"].includes(ext)) return FileText;
  return File;
}

// ── Mode tab ──────────────────────────────────────────────────────────────────
function ModeTab({ active, onClick, icon: Icon, label, desc }) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex-1 flex flex-col items-center gap-2 p-5 rounded-xl border-2 transition-all text-center",
        active
          ? "border-primary-500 bg-primary-50 dark:bg-primary-900/20"
          : "border-surface-200 dark:border-surface-700 hover:border-primary-300 dark:hover:border-primary-700"
      )}
    >
      <div className={cn(
        "w-10 h-10 rounded-xl flex items-center justify-center",
        active ? "bg-primary-100 dark:bg-primary-900/40" : "bg-surface-100 dark:bg-surface-800"
      )}>
        <Icon className={cn("w-5 h-5", active ? "text-primary-600" : "text-surface-400")} />
      </div>
      <div>
        <p className={cn("font-semibold text-sm", active ? "text-primary-700 dark:text-primary-300" : "text-surface-700 dark:text-surface-300")}>{label}</p>
        <p className="text-xs text-surface-400 mt-0.5">{desc}</p>
      </div>
    </button>
  );
}

// ── Folder file list ──────────────────────────────────────────────────────────
function FolderFileList({ files, onRemove }) {
  if (!files.length) return null;
  // Group by folder
  const groups = {};
  files.forEach((f) => {
    const parts = f.relativePath.split("/");
    const folder = parts.length > 1 ? parts.slice(0, -1).join("/") : "(root)";
    (groups[folder] = groups[folder] || []).push(f);
  });

  return (
    <div className="space-y-3 max-h-72 overflow-y-auto pr-1">
      {Object.entries(groups).map(([folder, items]) => (
        <div key={folder}>
          <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-1.5 flex items-center gap-1.5">
            <FolderOpen className="w-3.5 h-3.5" /> {folder}
          </p>
          <div className="space-y-1 pl-4">
            {items.map((f) => {
              const Icon = fileIcon(f.name);
              return (
                <div key={f.relativePath} className="flex items-center gap-2 py-1">
                  <Icon className="w-4 h-4 text-surface-400 flex-shrink-0" />
                  <span className="text-sm text-surface-700 dark:text-surface-300 truncate flex-1">{f.name}</span>
                  <span className="text-xs text-surface-400 flex-shrink-0">{formatBytes(f.size)}</span>
                  <button onClick={() => onRemove(f.relativePath)} className="p-0.5 text-surface-300 hover:text-red-500 transition-colors">
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function CasesPage() {
  const navigate = useNavigate();
  const folderInputRef = useRef(null);

  const [mode, setMode] = useState("folder"); // "folder" | "uploaded"
  const [caseName, setCaseName] = useState("");

  // Folder mode state
  const [folderFiles, setFolderFiles] = useState([]); // [{name, relativePath, file, size}]

  // Uploaded mode state
  const [uploads, setUploads] = useState([]);
  const [loadingUploads, setLoadingUploads] = useState(false);
  const [selectedUploadIds, setSelectedUploadIds] = useState(new Set());

  // Analysis state
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(null);
  const [result, setResult] = useState(null);
  const [errors, setErrors] = useState([]);
  const [saving, setSaving] = useState(false);

  // Load uploads when switching to that mode
  useEffect(() => {
    if (mode === "uploaded" && uploads.length === 0) {
      setLoadingUploads(true);
      uploadsApi.list()
        .then((res) => setUploads(res.data.items || []))
        .catch(() => toast.error("Failed to load uploads"))
        .finally(() => setLoadingUploads(false));
    }
  }, [mode]);

  // ── Folder selection ────────────────────────────────────────────────────────
  const handleFolderSelect = useCallback((e) => {
    const fileList = Array.from(e.target.files || []);
    const supported = fileList
      .filter((f) => isSupported(f.name))
      .map((f) => ({
        name: f.name,
        relativePath: (f.webkitRelativePath || f.name).replace(/\\/g, "/"),
        file: f,
        size: f.size,
      }));

    if (supported.length === 0) {
      toast.error("No supported files found in the selected folder");
      return;
    }
    const skipped = fileList.length - supported.length;
    if (skipped > 0) toast(`${skipped} unsupported file(s) ignored`, { icon: "ℹ️" });

    setFolderFiles(supported);
    // Auto-fill case name from folder name
    if (!caseName && supported[0]?.relativePath) {
      const rootFolder = supported[0].relativePath.split("/")[0];
      if (rootFolder && rootFolder !== supported[0].name) {
        setCaseName(rootFolder);
      }
    }
    setResult(null);
    setErrors([]);
  }, [caseName]);

  const removeFile = useCallback((relPath) => {
    setFolderFiles((prev) => prev.filter((f) => f.relativePath !== relPath));
  }, []);

  // ── Toggle upload selection ─────────────────────────────────────────────────
  const toggleUpload = useCallback((id) => {
    setSelectedUploadIds((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }, []);

  // ── Run analysis ────────────────────────────────────────────────────────────
  const runAnalysis = useCallback(async () => {
    const name = caseName.trim() || "Untitled Case";

    if (mode === "folder") {
      if (folderFiles.length === 0) return toast.error("Select a case folder first");
    } else {
      if (selectedUploadIds.size === 0) return toast.error("Select at least one file");
    }

    setRunning(true);
    setResult(null);
    setErrors([]);
    setProgress({ stage: "Scanning Case", agent: "File Classifier", message: "Starting…", files_done: 0, files_total: 0 });

    try {
      const onEvent = (eventName, data) => {
        if (eventName === "progress" || eventName === "agent_start") {
          setProgress(data);
        } else if (eventName === "agent_done") {
          setProgress((prev) => ({ ...prev, ...data }));
        } else if (eventName === "complete") {
          setResult(data);
          setProgress(null);
          if (data.errors?.length) setErrors(data.errors);
          toast.success("Analysis complete!");
        } else if (eventName === "error") {
          setErrors((prev) => [...prev, data]);
        }
      };

      if (mode === "folder") {
        const files = folderFiles.map((f) => f.file);
        const relPaths = folderFiles.map((f) => f.relativePath);
        await casesApi.streamAnalyze(files, relPaths, name, onEvent);
      } else {
        // Get stored filenames for selected uploads
        const selectedUploads = uploads.filter((u) => selectedUploadIds.has(u.id));
        const fileIds = selectedUploads.map((u) => u.filename);
        await casesApi.streamAnalyzeSaved(fileIds, name, onEvent);
      }
    } catch (err) {
      const msg = err?.message || "Analysis failed";
      toast.error(msg);
      setErrors([{ agent: "pipeline", error: msg }]);
      setProgress(null);
    } finally {
      setRunning(false);
    }
  }, [mode, folderFiles, selectedUploadIds, uploads, caseName]);

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

  // ── Export report as Markdown ───────────────────────────────────────────────
  const exportMarkdown = useCallback(() => {
    if (!result) return;
    const report = result.case_report || {};
    const lines = [
      `# ${caseName || result.case_name || "Case"} — AI Case Report`,
      `> Generated by LexIntel AI | ${new Date().toLocaleDateString()}`,
      `> ⚠️ AI GENERATED — NOT LEGAL ADVICE`,
      "",
      "## Executive Summary",
      report.executive_summary || "N/A",
      "",
      "## Outcome Prediction",
      `- Probability of Success: ${result.outcome_prediction?.probability_of_success || "N/A"}`,
      `- Case Strength: ${result.outcome_prediction?.case_strength_score || "N/A"}`,
      `- Confidence: ${result.outcome_prediction?.confidence_level || "N/A"}`,
      `- Risk Level: ${result.outcome_prediction?.risk_level || "N/A"}`,
      "",
      "## Recommendations",
      ...(report.recommendations || []).map((r) => `- ${r}`),
      "",
      "## Disclaimer",
      report.disclaimer || result.outcome_prediction?.disclaimer || "",
    ];
    const blob = new Blob([lines.join("\n")], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${(caseName || "Case").replace(/\s+/g, "_")}_AI_Report.md`;
    a.click();
    URL.revokeObjectURL(url);
  }, [result, caseName]);

  // ── Save case ───────────────────────────────────────────────────────────────
  const saveCase = useCallback(async () => {
    if (!result) return;
    setSaving(true);
    try {
      const res = await casesApi.save({
        case_name: caseName.trim() || result.case_name || "Untitled Case",
        session_id: result.session_id,
        document_intelligence: result.document_intelligence,
        legal_research: result.legal_research,
        similar_cases: result.similar_cases || [],
        evidence_items: result.evidence_items || [],
        evidence_timeline: result.evidence_timeline || [],
        evidence_analysis: result.evidence_analysis,
        missing_evidence_hints: result.missing_evidence_hints || [],
        outcome_prediction: result.outcome_prediction,
        legal_strategy: result.legal_strategy,
        legal_drafts: result.legal_drafts || [],
        case_report: result.case_report,
        agent_executions: result.agent_executions || [],
        errors: result.errors || [],
        warnings: result.warnings || [],
        case_workspace: result.case_workspace,
        metadata: result.metadata || {},
      });
      toast.success("Case saved!");
      navigate(`/dashboard/my-cases/${res.data.id}`);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Failed to save case");
    } finally {
      setSaving(false);
    }
  }, [result, caseName, navigate]);

  const canRun = mode === "folder" ? folderFiles.length > 0 : selectedUploadIds.size > 0;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-surface-900 dark:text-surface-100">AI Case Analysis</h1>
          <p className="text-surface-500 dark:text-surface-400 mt-1">
            Analyze a complete legal case folder or select uploaded files.
          </p>
        </div>
        <Button variant="secondary" size="sm" onClick={() => navigate("/dashboard/my-cases")} className="flex-shrink-0">
          My Cases
        </Button>
      </div>

      {/* Case name */}
      <div className="card p-5 space-y-4">
        <div>
          <label className="label">Case Name</label>
          <input
            className="input"
            placeholder="e.g. State vs Sharma — Property Dispute 2024"
            value={caseName}
            onChange={(e) => setCaseName(e.target.value)}
            disabled={running}
          />
        </div>

        {/* Mode selector */}
        <div className="flex gap-3">
          <ModeTab
            active={mode === "folder"}
            onClick={() => { setMode("folder"); setResult(null); setErrors([]); }}
            icon={FolderOpen}
            label="Analyze Local Case Folder"
            desc="Select a folder from your computer"
          />
          <ModeTab
            active={mode === "uploaded"}
            onClick={() => { setMode("uploaded"); setResult(null); setErrors([]); }}
            icon={Upload}
            label="Analyze Uploaded Files"
            desc="Use files already in the system"
          />
        </div>
      </div>

      {/* ── Folder mode ── */}
      {mode === "folder" && (
        <div className="card p-5 space-y-4">
          <input
            ref={folderInputRef}
            type="file"
            // @ts-ignore
            webkitdirectory=""
            directory=""
            multiple
            className="hidden"
            onChange={handleFolderSelect}
          />
          {folderFiles.length === 0 ? (
            <button
              onClick={() => folderInputRef.current?.click()}
              className="w-full border-2 border-dashed border-surface-300 dark:border-surface-600 rounded-xl p-10 text-center hover:border-primary-400 dark:hover:border-primary-500 hover:bg-surface-50 dark:hover:bg-surface-800/50 transition-all"
            >
              <FolderOpen className="w-10 h-10 text-surface-300 dark:text-surface-600 mx-auto mb-3" />
              <p className="font-semibold text-surface-700 dark:text-surface-300">Select Case Folder</p>
              <p className="text-sm text-surface-400 mt-1">
                All supported files inside the folder and subfolders will be included
              </p>
              <p className="text-xs text-surface-300 dark:text-surface-600 mt-3">
                PDF · DOC · DOCX · TXT · Images · Audio · Video · CSV · XLSX · Email
              </p>
            </button>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold text-surface-700 dark:text-surface-300">
                  {folderFiles.length} supported file{folderFiles.length !== 1 ? "s" : ""} selected
                </p>
                <div className="flex gap-2">
                  <Button size="sm" variant="ghost" onClick={() => folderInputRef.current?.click()}>
                    Change Folder
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setFolderFiles([])}>
                    Clear
                  </Button>
                </div>
              </div>
              <FolderFileList files={folderFiles} onRemove={removeFile} />
            </div>
          )}
        </div>
      )}

      {/* ── Uploaded files mode ── */}
      {mode === "uploaded" && (
        <div className="card p-5 space-y-3">
          {loadingUploads ? (
            <div className="space-y-2">
              {[1,2,3].map((i) => (
                <div key={i} className="h-12 bg-surface-100 dark:bg-surface-800 rounded-xl animate-pulse" />
              ))}
            </div>
          ) : uploads.length === 0 ? (
            <div className="flex items-center gap-3 p-4 rounded-xl bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800">
              <Upload className="w-5 h-5 text-amber-500 flex-shrink-0" />
              <p className="text-sm text-amber-700 dark:text-amber-400">
                No files uploaded yet. Go to <strong>Uploads</strong> to upload files first.
              </p>
            </div>
          ) : (
            <>
              <p className="text-xs text-surface-400">{selectedUploadIds.size} of {uploads.length} selected</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 max-h-72 overflow-y-auto pr-1">
                {uploads.map((f) => {
                  const Icon = fileIcon(f.original_filename);
                  const selected = selectedUploadIds.has(f.id);
                  return (
                    <button
                      key={f.id}
                      onClick={() => toggleUpload(f.id)}
                      className={cn(
                        "flex items-center gap-2.5 p-3 rounded-xl border text-left transition-all",
                        selected
                          ? "border-primary-500 bg-primary-50 dark:bg-primary-900/20 ring-2 ring-primary-500/20"
                          : "border-surface-200 dark:border-surface-700 hover:border-primary-300 dark:hover:border-primary-700"
                      )}
                    >
                      <Icon className="w-4 h-4 text-surface-400 flex-shrink-0" />
                      <span className="text-sm text-surface-700 dark:text-surface-300 truncate flex-1">
                        {f.original_filename}
                      </span>
                      {selected && <CheckCircle className="w-4 h-4 text-primary-500 flex-shrink-0" />}
                    </button>
                  );
                })}
              </div>
            </>
          )}
        </div>
      )}

      {/* Run button */}
      <div className="flex items-center gap-3">
        <Button onClick={runAnalysis} disabled={!canRun || running} className="gap-2">
          <Sparkles className="w-4 h-4" />
          {running ? "Analysing…" : "Run AI Analysis"}
        </Button>
        {mode === "folder" && folderFiles.length > 0 && !running && (
          <p className="text-sm text-surface-500">
            {folderFiles.length} file{folderFiles.length !== 1 ? "s" : ""} ready
          </p>
        )}
      </div>

      {/* Progress panel */}
      {running && <AIProgressPanel progress={progress} />}

      {/* Errors */}
      {errors.length > 0 && (
        <div className="card p-4 border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/10 space-y-2">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-500" />
            <p className="text-sm font-semibold text-red-700 dark:text-red-400">Agent errors (pipeline still completed)</p>
          </div>
          {errors.map((e, i) => (
            <p key={i} className="text-xs text-red-600 dark:text-red-400 pl-6">
              <span className="font-medium capitalize">{e.agent}:</span> {e.error}
            </p>
          ))}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {/* Save Case CTA */}
          <div className="card p-5 flex items-center justify-between gap-4 bg-gradient-to-r from-primary-50 to-green-50 dark:from-primary-900/20 dark:to-green-900/20 border-primary-200 dark:border-primary-800">
            <div>
              <p className="font-semibold text-surface-900 dark:text-surface-100">Analysis Complete</p>
              <p className="text-sm text-surface-500 mt-0.5">Save this case to your workspace to revisit it later.</p>
            </div>
            <Button onClick={saveCase} loading={saving} className="gap-2 flex-shrink-0">
              <Save className="w-4 h-4" />
              Save Case
            </Button>
          </div>

          {/* Agent execution summary */}
          {result.agent_executions?.length > 0 && (
            <div className="card p-5 space-y-3">
              <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide">Pipeline Execution</p>
              <AgentStatus executions={result.agent_executions} />
            </div>
          )}

          <Section icon={FileSearch} title="Document Intelligence" color="primary">
            <DocumentIntelligenceResult data={result.document_intelligence} />
          </Section>

          <Section icon={BookOpen} title="Legal Research" color="green">
            <LegalResearchResult data={result.legal_research} />
          </Section>

          <Section icon={Gavel} title="Similar Cases" color="purple" defaultOpen={false}>
            <SimilarCasesResult cases={result.similar_cases} />
          </Section>

          <Section icon={ListOrdered} title="Evidence Analysis" color="amber" defaultOpen={false}>
            <EvidenceResult
              items={result.evidence_items}
              timeline={result.evidence_timeline}
              analysis={result.evidence_analysis}
              hints={result.missing_evidence_hints}
            />
          </Section>

          {result.outcome_prediction && (
            <Section icon={TrendingUp} title="Outcome Prediction" color="rose" defaultOpen={false}>
              <OutcomePredictionResult data={result.outcome_prediction} />
            </Section>
          )}

          {result.legal_strategy && (
            <Section icon={Lightbulb} title="Legal Strategy" color="purple" defaultOpen={false}>
              <StrategyPlanningResult data={result.legal_strategy} />
            </Section>
          )}

          {result.legal_drafts?.length > 0 && (
            <Section icon={PenLine} title="Legal Drafts" color="blue" defaultOpen={false}>
              <LegalDraftsResult drafts={result.legal_drafts} onDownload={downloadDraft} />
            </Section>
          )}

          {result.case_report && (
            <Section icon={BarChart2} title="AI Case Report" color="green" defaultOpen={false}>
              <CaseReportResult data={result.case_report} onExport={exportMarkdown} />
            </Section>
          )}
        </div>
      )}
    </div>
  );
}
