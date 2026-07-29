import { Scale } from "lucide-react";

export default function LoadingScreen() {
  return (
    <div className="fixed inset-0 bg-surface-50 dark:bg-surface-950 flex flex-col items-center justify-center z-50">
      <div className="flex flex-col items-center gap-4 animate-fade-in">
        <div className="relative">
          <div className="w-16 h-16 rounded-2xl bg-primary-600 flex items-center justify-center shadow-lg shadow-primary-500/30">
            <Scale className="w-8 h-8 text-white" />
          </div>
          <div className="absolute -inset-1 rounded-2xl border-2 border-primary-400/30 animate-ping" />
        </div>
        <div className="text-center">
          <p className="text-lg font-semibold text-surface-900 dark:text-surface-100">LexIntel AI</p>
          <p className="text-sm text-surface-500 dark:text-surface-400 mt-1">Loading your workspace...</p>
        </div>
        <div className="flex gap-1.5 mt-2">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="w-2 h-2 rounded-full bg-primary-500 animate-bounce"
              style={{ animationDelay: `${i * 0.15}s` }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
