import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  FileText, Download, Trash2, Eye, Loader2,
  AlertCircle, BarChart2, TrendingUp, Lightbulb, Calendar,
} from "lucide-react";
import { reportsApi } from "../../api/reports";
import Button from "../../components/ui/Button";
import { cn, formatDate } from "../../utils/helpers";
import toast from "react-hot-toast";

function RiskBadge({ level }) {
  const colors = {
    Low: "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300",
    Medium: "bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300",
    High: "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300",
  };
  return (
    <span className={cn("text-xs px-2 py-0.5 rounded-full font-medium", colors[level] || colors.Medium)}>
      {level} Risk
    </span>
  );
}

function ReportCard({ report, onView, onDownload, onDelete, downloading }) {
  const pred = report.outcome_prediction || {};
  const strategy = report.legal_strategy || {};
  const strategies = strategy.strategies || [];

  return (
    <div className="card p-5 space-y-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-10 h-10 rounded-xl bg-primary-50 dark:bg-primary-900/20 flex items-center justify-center flex-shrink-0">
            <BarChart2 className="w-5 h-5 text-primary-600" />
          </div>
          <div className="min-w-0">
            <p className="font-semibold text-surface-900 dark:text-surface-100 truncate">{report.case_name}</p>
            <p className="text-xs text-surface-400 flex items-center gap-1 mt-0.5">
              <Calendar className="w-3 h-3" />
              {formatDate(report.created_at)}
            </p>
          </div>
        </div>
        <div className="flex gap-1.5 flex-shrink-0">
          <button
            onClick={() => onView(report.id)}
            className="p-2 rounded-lg text-surface-400 hover:text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-colors"
            title="View report"
          >
            <Eye className="w-4 h-4" />
          </button>
          <button
            onClick={() => onDownload(report.id, report.case_name)}
            disabled={downloading === report.id}
            className="p-2 rounded-lg text-surface-400 hover:text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 transition-colors disabled:opacity-50"
            title="Download PDF"
          >
            {downloading === report.id
              ? <Loader2 className="w-4 h-4 animate-spin" />
              : <Download className="w-4 h-4" />}
          </button>
          <button
            onClick={() => onDelete(report.id)}
            className="p-2 rounded-lg text-surface-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
            title="Delete report"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Prediction summary */}
      {pred.probability_of_success && (
        <div className="grid grid-cols-3 gap-2">
          <div className="flex flex-col items-center p-2.5 rounded-xl bg-surface-50 dark:bg-surface-800">
            <TrendingUp className="w-4 h-4 text-primary-500 mb-1" />
            <span className="text-sm font-bold text-surface-900 dark:text-surface-100">
              {pred.probability_of_success}
            </span>
            <span className="text-xs text-surface-400">Success</span>
          </div>
          <div className="flex flex-col items-center p-2.5 rounded-xl bg-surface-50 dark:bg-surface-800">
            <BarChart2 className="w-4 h-4 text-blue-500 mb-1" />
            <span className="text-sm font-bold text-surface-900 dark:text-surface-100">
              {pred.confidence_level || "N/A"}
            </span>
            <span className="text-xs text-surface-400">Confidence</span>
          </div>
          <div className="flex flex-col items-center p-2.5 rounded-xl bg-surface-50 dark:bg-surface-800">
            <AlertCircle className="w-4 h-4 text-amber-500 mb-1" />
            <span className="text-sm font-bold text-surface-900 dark:text-surface-100">
              {pred.risk_level || "N/A"}
            </span>
            <span className="text-xs text-surface-400">Risk</span>
          </div>
        </div>
      )}

      {/* Strategy count */}
      {strategies.length > 0 && (
        <div className="flex items-center gap-2 text-xs text-surface-500">
          <Lightbulb className="w-3.5 h-3.5 text-amber-500" />
          {strategies.length} legal strateg{strategies.length !== 1 ? "ies" : "y"} recommended
        </div>
      )}
    </div>
  );
}

function ReportDetailModal({ reportId, onClose }) {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    reportsApi.get(reportId)
      .then((res) => setReport(res.data))
      .catch(() => toast.error("Failed to load report"))
      .finally(() => setLoading(false));
  }, [reportId]);

  const downloadPdf = async () => {
    setDownloading(true);
    try {
      await reportsApi.downloadPdf(reportId, `${report.case_name}_AI_Report.pdf`);
    } catch {
      toast.error("PDF download failed");
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-white dark:bg-surface-900 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[85vh] flex flex-col">
        <div className="flex items-center justify-between p-5 border-b border-surface-100 dark:border-surface-800">
          <h2 className="font-semibold text-surface-900 dark:text-surface-100">
            {loading ? "Loading…" : report?.case_name}
          </h2>
          <div className="flex gap-2">
            {report && (
              <Button size="sm" onClick={downloadPdf} loading={downloading} className="gap-2">
                <Download className="w-4 h-4" /> Download PDF
              </Button>
            )}
            <button onClick={onClose} className="p-2 text-surface-400 hover:text-surface-600 dark:hover:text-surface-200">
              ✕
            </button>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 animate-spin text-primary-500" />
            </div>
          ) : !report ? null : (
            <>
              {/* Disclaimer */}
              <div className="p-3 rounded-xl bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800">
                <p className="text-xs text-amber-700 dark:text-amber-400">
                  ⚠️ AI GENERATED REPORT — NOT LEGAL ADVICE. Consult a qualified lawyer before taking action.
                </p>
              </div>

              {/* Executive Summary */}
              {report.report_data?.executive_summary && (
                <div>
                  <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-2">Executive Summary</p>
                  <p className="text-sm text-surface-700 dark:text-surface-300 leading-relaxed bg-surface-50 dark:bg-surface-800 rounded-xl p-4">
                    {report.report_data.executive_summary}
                  </p>
                </div>
              )}

              {/* Prediction */}
              {report.outcome_prediction && (
                <div>
                  <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-2">Outcome Prediction</p>
                  <div className="grid grid-cols-2 gap-2">
                    {[
                      ["Probability of Success", report.outcome_prediction.probability_of_success],
                      ["Case Strength", report.outcome_prediction.case_strength_score],
                      ["Confidence", report.outcome_prediction.confidence_level],
                      ["Risk Level", report.outcome_prediction.risk_level],
                    ].map(([label, val]) => val && (
                      <div key={label} className="p-3 rounded-xl bg-surface-50 dark:bg-surface-800">
                        <p className="text-xs text-surface-400">{label}</p>
                        <p className="text-sm font-semibold text-surface-900 dark:text-surface-100 mt-0.5">{val}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Immediate Next Steps */}
              {report.legal_strategy?.immediate_next_steps?.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-2">Immediate Next Steps</p>
                  <ol className="space-y-1.5">
                    {report.legal_strategy.immediate_next_steps.map((step, i) => (
                      <li key={i} className="flex gap-2 text-sm text-surface-700 dark:text-surface-300">
                        <span className="w-5 h-5 rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 text-xs flex items-center justify-center flex-shrink-0 mt-0.5 font-semibold">
                          {i + 1}
                        </span>
                        {step}
                      </li>
                    ))}
                  </ol>
                </div>
              )}

              {/* Recommendations */}
              {report.report_data?.recommendations?.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-2">Recommendations</p>
                  <ul className="space-y-1">
                    {report.report_data.recommendations.map((r, i) => (
                      <li key={i} className="text-sm text-surface-600 dark:text-surface-400 flex gap-2">
                        <span className="text-green-500 mt-0.5">✓</span>{r}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Strategies */}
              {report.legal_strategy?.strategies?.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-2">Legal Strategies</p>
                  <div className="space-y-2">
                    {report.legal_strategy.strategies.slice(0, 3).map((s, i) => (
                      <div key={i} className="p-3 rounded-xl border border-surface-200 dark:border-surface-700">
                        <p className="text-sm font-semibold text-surface-900 dark:text-surface-100">{s.name}</p>
                        <p className="text-xs text-surface-500 mt-1">{s.description}</p>
                        <div className="flex gap-2 mt-2">
                          <span className="text-xs px-2 py-0.5 rounded-full bg-surface-100 dark:bg-surface-800 text-surface-600 dark:text-surface-400">
                            Effort: {s.effort}
                          </span>
                          <RiskBadge level={s.risk_level} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ReportsPage() {
  const navigate = useNavigate();
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(null);
  const [viewingId, setViewingId] = useState(null);

  const loadReports = useCallback(async () => {
    try {
      const res = await reportsApi.list();
      setReports(res.data.items || []);
    } catch {
      toast.error("Failed to load reports");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadReports(); }, [loadReports]);

  const handleDownload = useCallback(async (id, caseName) => {
    setDownloading(id);
    try {
      await reportsApi.downloadPdf(id, `${caseName}_AI_Report.pdf`);
    } catch {
      toast.error("PDF download failed");
    } finally {
      setDownloading(null);
    }
  }, []);

  const handleDelete = useCallback(async (id) => {
    if (!confirm("Delete this report?")) return;
    try {
      await reportsApi.delete(id);
      setReports((prev) => prev.filter((r) => r.id !== id));
      toast.success("Report deleted");
    } catch {
      toast.error("Failed to delete report");
    }
  }, []);

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-surface-900 dark:text-surface-100">Reports</h1>
          <p className="text-surface-500 dark:text-surface-400 mt-1">
            AI-generated case intelligence reports. Download as PDF or view online.
          </p>
        </div>
        <Button variant="secondary" size="sm" onClick={() => navigate("/dashboard/cases")} className="flex-shrink-0">
          New Analysis
        </Button>
      </div>

      <div className="p-4 rounded-xl bg-blue-50 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-800">
        <p className="text-sm text-blue-700 dark:text-blue-400">
          Reports are saved automatically when you save a case. Run an AI analysis from{" "}
          <button onClick={() => navigate("/dashboard/cases")} className="underline font-medium">
            AI Case Analysis
          </button>{" "}
          and click <strong>Save Case</strong> to generate a report.
        </p>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="card p-5 space-y-3 animate-pulse">
              <div className="flex gap-3">
                <div className="w-10 h-10 rounded-xl bg-surface-200 dark:bg-surface-700" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-surface-200 dark:bg-surface-700 rounded w-3/4" />
                  <div className="h-3 bg-surface-200 dark:bg-surface-700 rounded w-1/2" />
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : reports.length === 0 ? (
        <div className="card py-20 flex flex-col items-center text-center px-6">
          <div className="w-16 h-16 rounded-2xl bg-surface-100 dark:bg-surface-800 flex items-center justify-center mx-auto mb-4">
            <FileText className="w-8 h-8 text-surface-300 dark:text-surface-600" />
          </div>
          <h3 className="text-base font-semibold text-surface-900 dark:text-surface-100 mb-1">No reports yet</h3>
          <p className="text-sm text-surface-400 max-w-sm mb-4">
            Save a case after running AI analysis to generate a report here.
          </p>
          <Button onClick={() => navigate("/dashboard/cases")} className="gap-2">
            <BarChart2 className="w-4 h-4" /> Run AI Analysis
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {reports.map((r) => (
            <ReportCard
              key={r.id}
              report={r}
              onView={setViewingId}
              onDownload={handleDownload}
              onDelete={handleDelete}
              downloading={downloading}
            />
          ))}
        </div>
      )}

      {viewingId && (
        <ReportDetailModal reportId={viewingId} onClose={() => setViewingId(null)} />
      )}
    </div>
  );
}
