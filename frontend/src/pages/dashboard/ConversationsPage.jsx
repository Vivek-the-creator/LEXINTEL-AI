import { MessageSquare, Plus, Bot } from "lucide-react";
import Button from "../../components/ui/Button";

export default function ConversationsPage() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-surface-900 dark:text-surface-100">AI Conversations</h1>
          <p className="text-surface-500 dark:text-surface-400 mt-1">Chat with your AI legal assistant.</p>
        </div>
        <Button className="gap-2" disabled>
          <Plus className="w-4 h-4" /> New Conversation
        </Button>
      </div>

      <div className="card p-6 bg-blue-50 dark:bg-blue-900/10 border-blue-200 dark:border-blue-800">
        <div className="flex items-center gap-3">
          <Bot className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0" />
          <p className="text-sm text-blue-700 dark:text-blue-400">
            🤖 Multi-agent AI conversations will be available in Phase 2.
          </p>
        </div>
      </div>

      <div className="card">
        <div className="py-20 flex flex-col items-center text-center px-6">
          <div className="w-16 h-16 rounded-2xl bg-surface-100 dark:bg-surface-800 flex items-center justify-center mx-auto mb-4">
            <MessageSquare className="w-8 h-8 text-surface-300 dark:text-surface-600" />
          </div>
          <h3 className="text-base font-semibold text-surface-900 dark:text-surface-100 mb-1">No conversations yet</h3>
          <p className="text-sm text-surface-400 dark:text-surface-500 max-w-sm">
            Your AI conversations will appear here once the feature is available in Phase 2.
          </p>
        </div>
      </div>
    </div>
  );
}
