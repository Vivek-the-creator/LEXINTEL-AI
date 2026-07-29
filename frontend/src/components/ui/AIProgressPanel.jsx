import { Brain, FileText, Scale, Search, Shield, CheckCircle, Loader2 } from "lucide-react";
import { cn } from "../../utils/helpers";

const STAGES = [
  { key: "scan",     label: "Scanning Case",          icon: FileText },
  { key: "doc",      label: "Document Intelligence",  icon: Brain },
  { key: "legal",    label: "Legal Research",         icon: Scale },
  { key: "cases",    label: "Similar Cases",          icon: Search },
  { key: "evidence", label: "Evidence Analysis",      icon: Shield },
];

function stageIndex(stageName) {
  const s = (stageName || "").toLowerCase();
  if (s.includes("scan") || s.includes("classif")) return 0;
  if (s.includes("document") || s.includes("intel")) return 1;
  if (s.includes("legal") || s.includes("research")) return 2;
  if (s.includes("similar") || s.includes("case")) return 3;
  if (s.includes("evidence")) return 4;
  return 0;
}

export default function AIProgressPanel({ progress }) {
  if (!progress) return null;

  const {
    stage = "",
    agent = "",
    current_file = null,
    files_done = 0,
    files_total = 0,
    message = "",
    classifications = null,
  } = progress;

  const currentStageIdx = stageIndex(stage);
  const pct = files_total > 0 ? Math.round((files_done / files_total) * 100) : 0;

  return (
    <div className="card p-6 space-y-5">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-primary-50 dark:bg-primary-900/20 flex items-center justify-center">
          <Brain className="w-5 h-5 text-primary-600 animate-pulse" />
        </div>
        <div>
          <p className="font-semibold text-surface-900 dark:text-surface-100">AI Analysis Running</p>
          <p className="text-xs text-surface-400">{agent || stage}</p>
        </div>
      </div>

      {/* Stage pipeline */}
      <div className="flex items-center gap-1 overflow-x-auto pb-1">
        {STAGES.map((s, i) => {
          const done = i < currentStageIdx;
          const active = i === currentStageIdx;
          const Icon = s.icon;
          return (
            <div key={s.key} className="flex items-center gap-1 flex-shrink-0">
              <div className={cn(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all",
                done   && "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300",
                active && "bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300",
                !done && !active && "bg-surface-100 dark:bg-surface-800 text-surface-400",
              )}>
                {done ? (
                  <CheckCircle className="w-3.5 h-3.5" />
                ) : active ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Icon className="w-3.5 h-3.5" />
                )}
                <span className="hidden sm:inline">{s.label}</span>
              </div>
              {i < STAGES.length - 1 && (
                <div className={cn(
                  "w-4 h-0.5 flex-shrink-0",
                  i < currentStageIdx ? "bg-green-400" : "bg-surface-200 dark:bg-surface-700"
                )} />
              )}
            </div>
          );
        })}
      </div>

      {/* Current file */}
      {current_file && (
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-surface-50 dark:bg-surface-800 border border-surface-200 dark:border-surface-700">
          <FileText className="w-4 h-4 text-primary-500 flex-shrink-0" />
          <div className="min-w-0">
            <p className="text-xs text-surface-400">Currently Processing</p>
            <p className="text-sm font-medium text-surface-700 dark:text-surface-300 truncate">{current_file}</p>
          </div>
        </div>
      )}

      {/* Progress bar */}
      {files_total > 0 && (
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs text-surface-500">
            <span>{files_done} / {files_total} Files</span>
            <span>{pct}%</span>
          </div>
          <div className="h-2 bg-surface-200 dark:bg-surface-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-primary-500 rounded-full transition-all duration-500"
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>
      )}

      {/* Message */}
      {message && (
        <p className="text-sm text-surface-500 dark:text-surface-400 flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-primary-400 animate-pulse flex-shrink-0" />
          {message}
        </p>
      )}

      {/* File type breakdown */}
      {classifications && Object.keys(classifications).length > 0 && (
        <div className="flex flex-wrap gap-2">
          {Object.entries(classifications).map(([type, count]) => (
            <span key={type} className="inline-flex items-center gap-1 px-2 py-1 rounded-lg bg-surface-100 dark:bg-surface-800 text-xs text-surface-600 dark:text-surface-400">
              <span className="font-semibold text-surface-900 dark:text-surface-100">{count}</span>
              <span className="capitalize">{type.replace("_", " ")}</span>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
