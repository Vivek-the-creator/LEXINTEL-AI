import { FileText, Plus } from "lucide-react";
import Button from "../../components/ui/Button";

export default function ReportsPage() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-surface-900 dark:text-surface-100">Reports</h1>
          <p className="text-surface-500 dark:text-surface-400 mt-1">AI-generated legal analysis and case reports.</p>
        </div>
        <Button className="gap-2" disabled>
          <Plus className="w-4 h-4" /> Generate Report
        </Button>
      </div>

      <div className="card p-6 bg-amber-50 dark:bg-amber-900/10 border-amber-200 dark:border-amber-800">
        <p className="text-sm text-amber-700 dark:text-amber-400">
          🚧 AI report generation will be available in Phase 2.
        </p>
      </div>

      <div className="card">
        <div className="py-20 flex flex-col items-center text-center px-6">
          <div className="w-16 h-16 rounded-2xl bg-surface-100 dark:bg-surface-800 flex items-center justify-center mx-auto mb-4">
            <FileText className="w-8 h-8 text-surface-300 dark:text-surface-600" />
          </div>
          <h3 className="text-base font-semibold text-surface-900 dark:text-surface-100 mb-1">No reports yet</h3>
          <p className="text-sm text-surface-400 dark:text-surface-500 max-w-sm">
            AI-generated reports will appear here once the feature is available in Phase 2.
          </p>
        </div>
      </div>
    </div>
  );
}
