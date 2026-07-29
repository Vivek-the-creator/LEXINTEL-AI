import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  Briefcase, Plus, Trash2, ExternalLink, FileText,
  Shield, Scale, Clock, AlertCircle, Loader2,
} from "lucide-react";
import { casesApi } from "../../api/cases";
import Button from "../../components/ui/Button";
import { cn, formatRelativeTime, formatDate } from "../../utils/helpers";
import toast from "react-hot-toast";

const STATUS_COLORS = {
  analyzed: "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300",
  draft:    "bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300",
  archived: "bg-surface-100 dark:bg-surface-800 text-surface-500",
};

function CaseCard({ c, onDelete }) {
  const navigate = useNavigate();
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async (e) => {
    e.stopPropagation();
    if (!confirm(`Delete "${c.case_name}"? This cannot be undone.`)) return;
    setDeleting(true);
    try {
      await casesApi.delete(c.id);
      onDelete(c.id);
      toast.success("Case deleted");
    } catch {
      toast.error("Failed to delete case");
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div
      onClick={() => navigate(`/dashboard/my-cases/${c.id}`)}
      className="card p-5 cursor-pointer hover:shadow-md hover:border-primary-300 dark:hover:border-primary-700 transition-all group space-y-3"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-9 h-9 rounded-xl bg-primary-50 dark:bg-primary-900/20 flex items-center justify-center flex-shrink-0">
            <Briefcase className="w-5 h-5 text-primary-600" />
          </div>
          <div className="min-w-0">
            <p className="font-semibold text-surface-900 dark:text-surface-100 truncate">{c.case_name}</p>
            <p className="text-xs text-surface-400">{formatDate(c.created_at)}</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <span className={cn("text-xs px-2 py-0.5 rounded-full font-medium capitalize", STATUS_COLORS[c.status] || STATUS_COLORS.draft)}>
            {c.status}
          </span>
          <button
            onClick={handleDelete}
            disabled={deleting}
            className="p-1.5 rounded-lg text-surface-300 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors opacity-0 group-hover:opacity-100"
          >
            {deleting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {c.summary && (
        <p className="text-sm text-surface-600 dark:text-surface-400 line-clamp-2 leading-relaxed">
          {c.summary}
        </p>
      )}

      <div className="flex items-center gap-4 text-xs text-surface-400">
        <span className="flex items-center gap-1">
          <FileText className="w-3.5 h-3.5" />
          {c.document_count} doc{c.document_count !== 1 ? "s" : ""}
        </span>
        <span className="flex items-center gap-1">
          <Shield className="w-3.5 h-3.5" />
          {c.evidence_count} evidence
        </span>
        <span className="flex items-center gap-1 ml-auto">
          <Clock className="w-3.5 h-3.5" />
          {formatRelativeTime(c.updated_at)}
        </span>
      </div>
    </div>
  );
}

export default function MyCasesPage() {
  const navigate = useNavigate();
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const PAGE_SIZE = 12;

  const fetchCases = useCallback(async (p = 1) => {
    setLoading(true);
    try {
      const res = await casesApi.list(p, PAGE_SIZE);
      setCases(res.data.items || []);
      setTotal(res.data.total || 0);
      setPage(p);
    } catch {
      toast.error("Failed to load cases");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchCases(1); }, [fetchCases]);

  const handleDelete = useCallback((id) => {
    setCases((prev) => prev.filter((c) => c.id !== id));
    setTotal((t) => t - 1);
  }, []);

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-surface-900 dark:text-surface-100">My Cases</h1>
          <p className="text-surface-500 dark:text-surface-400 mt-1">
            Your legal workspace — {total} saved case{total !== 1 ? "s" : ""}
          </p>
        </div>
        <Button onClick={() => navigate("/dashboard/cases")} className="gap-2">
          <Plus className="w-4 h-4" />
          New Analysis
        </Button>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="card p-5 space-y-3">
              <div className="flex gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-surface-200 dark:bg-surface-700 animate-pulse flex-shrink-0" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-surface-200 dark:bg-surface-700 rounded animate-pulse w-3/4" />
                  <div className="h-3 bg-surface-200 dark:bg-surface-700 rounded animate-pulse w-1/3" />
                </div>
              </div>
              <div className="h-8 bg-surface-100 dark:bg-surface-800 rounded animate-pulse" />
              <div className="h-3 bg-surface-100 dark:bg-surface-800 rounded animate-pulse w-2/3" />
            </div>
          ))}
        </div>
      ) : cases.length === 0 ? (
        <div className="card p-16 text-center">
          <Briefcase className="w-12 h-12 text-surface-300 dark:text-surface-600 mx-auto mb-4" />
          <p className="font-semibold text-surface-700 dark:text-surface-300">No cases yet</p>
          <p className="text-sm text-surface-400 mt-1 mb-6">
            Run an AI analysis and save the results to create your first case.
          </p>
          <Button onClick={() => navigate("/dashboard/cases")} className="gap-2">
            <Plus className="w-4 h-4" />
            Start New Analysis
          </Button>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {cases.map((c) => (
              <CaseCard key={c.id} c={c} onDelete={handleDelete} />
            ))}
          </div>

          {/* Pagination */}
          {total > PAGE_SIZE && (
            <div className="flex items-center justify-center gap-2">
              <Button
                variant="secondary" size="sm"
                disabled={page === 1}
                onClick={() => fetchCases(page - 1)}
              >
                Previous
              </Button>
              <span className="text-sm text-surface-500">
                Page {page} of {Math.ceil(total / PAGE_SIZE)}
              </span>
              <Button
                variant="secondary" size="sm"
                disabled={page >= Math.ceil(total / PAGE_SIZE)}
                onClick={() => fetchCases(page + 1)}
              >
                Next
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
