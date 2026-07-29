import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  FolderOpen, Upload, FileText, MessageSquare,
  Clock, ArrowRight, Plus, Activity, Inbox
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { uploadsApi } from "../../api/uploads";
import { CardSkeleton } from "../../components/ui/Skeleton";
import { cn, formatRelativeTime, ROLE_LABELS, ROLE_COLORS } from "../../utils/helpers";

const STAT_META = [
  { label: "Total Cases",         key: "cases",         icon: FolderOpen,    color: "text-blue-600 dark:text-blue-400",   bg: "bg-blue-100 dark:bg-blue-900/30" },
  { label: "Uploaded Documents",  key: "uploads",       icon: Upload,        color: "text-purple-600 dark:text-purple-400", bg: "bg-purple-100 dark:bg-purple-900/30" },
  { label: "Generated Reports",   key: "reports",       icon: FileText,      color: "text-green-600 dark:text-green-400",  bg: "bg-green-100 dark:bg-green-900/30" },
  { label: "AI Conversations",    key: "conversations", icon: MessageSquare, color: "text-amber-600 dark:text-amber-400",  bg: "bg-amber-100 dark:bg-amber-900/30" },
];

const QUICK_ACTIONS = [
  { label: "New Case",    icon: FolderOpen,    to: "/dashboard/cases",         color: "bg-blue-600 hover:bg-blue-700" },
  { label: "Upload File", icon: Upload,        to: "/dashboard/uploads",       color: "bg-purple-600 hover:bg-purple-700" },
  { label: "New Report",  icon: FileText,      to: "/dashboard/reports",       color: "bg-green-600 hover:bg-green-700" },
  { label: "AI Chat",     icon: MessageSquare, to: "/dashboard/conversations", color: "bg-amber-600 hover:bg-amber-700" },
];

function EmptyState({ message }) {
  return (
    <div className="px-6 py-10 flex flex-col items-center text-center">
      <Inbox className="w-8 h-8 text-surface-300 dark:text-surface-600 mb-2" />
      <p className="text-sm text-surface-400 dark:text-surface-500">{message}</p>
    </div>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ cases: 0, uploads: 0, reports: 0, conversations: 0 });
  const [recentUploads, setRecentUploads] = useState([]);

  useEffect(() => {
    uploadsApi.list(1, 5)
      .then((res) => {
        const items = res.data.items || [];
        setRecentUploads(items);
        setStats((s) => ({ ...s, uploads: res.data.total }));
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-surface-900 dark:text-surface-100">
            {greeting}, {user?.full_name?.split(" ")[0]} 👋
          </h1>
          <p className="text-surface-500 dark:text-surface-400 mt-1">
            Here's an overview of your workspace.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className={cn("badge", ROLE_COLORS[user?.role])}>
            {ROLE_LABELS[user?.role]}
          </span>
          <span className="text-xs text-surface-400 dark:text-surface-500">
            {new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })}
          </span>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {loading
          ? Array.from({ length: 4 }).map((_, i) => <CardSkeleton key={i} />)
          : STAT_META.map(({ label, key, icon: Icon, color, bg }) => (
              <div key={label} className="card p-6 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm text-surface-500 dark:text-surface-400">{label}</p>
                    <p className="text-3xl font-bold text-surface-900 dark:text-surface-100 mt-1">
                      {stats[key]}
                    </p>
                    <p className="text-xs text-surface-400 dark:text-surface-500 mt-1">
                      {stats[key] === 0 ? "No data yet" : "Total count"}
                    </p>
                  </div>
                  <div className={cn("w-12 h-12 rounded-xl flex items-center justify-center", bg)}>
                    <Icon className={cn("w-6 h-6", color)} />
                  </div>
                </div>
              </div>
            ))}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Quick Actions</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {QUICK_ACTIONS.map(({ label, icon: Icon, to, color }) => (
            <Link
              key={label}
              to={to}
              className={cn(
                "flex items-center gap-3 p-4 rounded-xl text-white font-medium text-sm transition-all duration-150 hover:shadow-lg hover:-translate-y-0.5",
                color
              )}
            >
              <Icon className="w-5 h-5" />
              {label}
            </Link>
          ))}
        </div>
      </div>

      {/* Bottom panels */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Recent Uploads */}
        <div className="card">
          <div className="flex items-center justify-between p-6 border-b border-surface-200 dark:border-surface-700">
            <div className="flex items-center gap-2">
              <Upload className="w-5 h-5 text-surface-500" />
              <h2 className="font-semibold text-surface-900 dark:text-surface-100">Recent Uploads</h2>
            </div>
            <Link to="/dashboard/uploads" className="text-sm text-primary-600 dark:text-primary-400 hover:underline flex items-center gap-1">
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          <div className="divide-y divide-surface-100 dark:divide-surface-800">
            {loading
              ? Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="px-6 py-4 flex gap-3">
                    <div className="w-8 h-8 rounded-full bg-surface-200 dark:bg-surface-700 animate-pulse flex-shrink-0" />
                    <div className="flex-1 space-y-2">
                      <div className="h-3 bg-surface-200 dark:bg-surface-700 rounded animate-pulse w-3/4" />
                      <div className="h-3 bg-surface-200 dark:bg-surface-700 rounded animate-pulse w-1/3" />
                    </div>
                  </div>
                ))
              : recentUploads.length === 0
              ? <EmptyState message="No files uploaded yet. Upload your first file to get started." />
              : recentUploads.map((file) => (
                  <div key={file.id} className="px-6 py-4 flex items-center gap-3 hover:bg-surface-50 dark:hover:bg-surface-800/50 transition-colors">
                    <div className="w-8 h-8 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center flex-shrink-0">
                      <Upload className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-surface-900 dark:text-surface-100 truncate">{file.original_filename}</p>
                      <p className="text-xs text-surface-400 dark:text-surface-500">{formatRelativeTime(file.created_at)}</p>
                    </div>
                  </div>
                ))}
          </div>
          {!loading && recentUploads.length === 0 && (
            <div className="p-4 border-t border-surface-200 dark:border-surface-700">
              <Link to="/dashboard/uploads">
                <button className="w-full flex items-center justify-center gap-2 py-2 text-sm text-primary-600 dark:text-primary-400 hover:bg-primary-50 dark:hover:bg-primary-900/20 rounded-lg transition-colors">
                  <Plus className="w-4 h-4" /> Upload a File
                </button>
              </Link>
            </div>
          )}
        </div>

        {/* Recent Activity */}
        <div className="card">
          <div className="flex items-center justify-between p-6 border-b border-surface-200 dark:border-surface-700">
            <div className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-surface-500" />
              <h2 className="font-semibold text-surface-900 dark:text-surface-100">Recent Activity</h2>
            </div>
          </div>
          <div className="divide-y divide-surface-100 dark:divide-surface-800">
            {loading
              ? Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="px-6 py-4 flex gap-3">
                    <div className="w-8 h-8 rounded-full bg-surface-200 dark:bg-surface-700 animate-pulse flex-shrink-0" />
                    <div className="flex-1 space-y-2">
                      <div className="h-3 bg-surface-200 dark:bg-surface-700 rounded animate-pulse w-3/4" />
                      <div className="h-3 bg-surface-200 dark:bg-surface-700 rounded animate-pulse w-1/2" />
                    </div>
                  </div>
                ))
              : recentUploads.length === 0
              ? <EmptyState message="No activity yet. Your actions will appear here." />
              : recentUploads.map((file) => (
                  <div key={file.id} className="px-6 py-4 flex items-start gap-3 hover:bg-surface-50 dark:hover:bg-surface-800/50 transition-colors">
                    <div className="w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Clock className="w-4 h-4 text-primary-600 dark:text-primary-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-surface-900 dark:text-surface-100">Uploaded a file</p>
                      <p className="text-xs text-surface-500 dark:text-surface-400 truncate">{file.original_filename}</p>
                    </div>
                    <span className="text-xs text-surface-400 dark:text-surface-500 flex-shrink-0">
                      {formatRelativeTime(file.created_at)}
                    </span>
                  </div>
                ))}
          </div>
        </div>

      </div>
    </div>
  );
}
