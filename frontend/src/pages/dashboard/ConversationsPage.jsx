import { useState, useEffect, useCallback, useRef } from "react";
import {
  MessageSquare, Plus, Send, Trash2, Bot, User,
  Loader2, ChevronRight, X, Sparkles,
} from "lucide-react";
import { chatApi } from "../../api/chat";
import { casesApi } from "../../api/cases";
import Button from "../../components/ui/Button";
import { cn, formatDate } from "../../utils/helpers";
import toast from "react-hot-toast";

export default function ConversationsPage() {
  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [streamingText, setStreamingText] = useState("");
  const [cases, setCases] = useState([]);
  const [selectedCaseId, setSelectedCaseId] = useState("");
  const [showCaseSelect, setShowCaseSelect] = useState(false);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  // Load sessions
  const loadSessions = useCallback(async () => {
    try {
      const res = await chatApi.listSessions();
      setSessions(res.data.sessions || []);
    } catch {
      toast.error("Failed to load conversations");
    } finally {
      setLoadingSessions(false);
    }
  }, []);

  // Load cases for context selector
  const loadCases = useCallback(async () => {
    try {
      const res = await casesApi.list();
      setCases(res.data.items || []);
    } catch {}
  }, []);

  useEffect(() => {
    loadSessions();
    loadCases();
  }, [loadSessions, loadCases]);

  // Scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingText]);

  const openSession = useCallback(async (session) => {
    setActiveSession(session);
    setStreamingText("");
    try {
      const res = await chatApi.getSession(session.session_id);
      setMessages(res.data.messages || []);
      setSelectedCaseId(res.data.case_id || "");
    } catch {
      toast.error("Failed to load conversation");
    }
    setTimeout(() => inputRef.current?.focus(), 100);
  }, []);

  const newSession = useCallback(async () => {
    const title = `Conversation ${new Date().toLocaleString("en-IN", { dateStyle: "short", timeStyle: "short" })}`;
    try {
      const res = await chatApi.createSession(title, selectedCaseId || null);
      const session = { session_id: res.data.session_id, title, updated_at: new Date().toISOString() };
      setSessions((prev) => [session, ...prev]);
      setActiveSession(session);
      setMessages([]);
      setStreamingText("");
      setTimeout(() => inputRef.current?.focus(), 100);
    } catch {
      toast.error("Failed to create conversation");
    }
  }, [selectedCaseId]);

  const deleteSession = useCallback(async (sessionId, e) => {
    e.stopPropagation();
    try {
      await chatApi.deleteSession(sessionId);
      setSessions((prev) => prev.filter((s) => s.session_id !== sessionId));
      if (activeSession?.session_id === sessionId) {
        setActiveSession(null);
        setMessages([]);
      }
      toast.success("Conversation deleted");
    } catch {
      toast.error("Failed to delete conversation");
    }
  }, [activeSession]);

  const sendMessage = useCallback(async () => {
    const text = input.trim();
    if (!text || sending) return;
    if (!activeSession) {
      await newSession();
      return;
    }

    const userMsg = { role: "user", content: text, timestamp: new Date().toISOString() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setSending(true);
    setStreamingText("");

    try {
      let accumulated = "";
      await chatApi.streamMessage(
        activeSession.session_id,
        text,
        selectedCaseId || activeSession.case_id || null,
        (chunk) => {
          accumulated += chunk;
          setStreamingText(accumulated);
        }
      );
      const assistantMsg = {
        role: "assistant",
        content: accumulated,
        timestamp: new Date().toISOString(),
        agent: "legal_chat",
      };
      setMessages((prev) => [...prev, assistantMsg]);
      setStreamingText("");
      // Update session title if first message
      setSessions((prev) =>
        prev.map((s) =>
          s.session_id === activeSession.session_id
            ? { ...s, updated_at: new Date().toISOString() }
            : s
        )
      );
    } catch (err) {
      toast.error(err?.message || "Failed to send message");
      setStreamingText("");
    } finally {
      setSending(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [input, sending, activeSession, selectedCaseId, newSession]);

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-4 animate-fade-in">
      {/* Sidebar */}
      <div className="w-64 flex-shrink-0 flex flex-col gap-3">
        <Button onClick={newSession} className="gap-2 w-full">
          <Plus className="w-4 h-4" /> New Conversation
        </Button>

        {/* Case context selector */}
        <div>
          <button
            onClick={() => setShowCaseSelect((v) => !v)}
            className="w-full flex items-center justify-between px-3 py-2 rounded-xl border border-surface-200 dark:border-surface-700 text-sm text-surface-600 dark:text-surface-400 hover:border-primary-400 transition-colors"
          >
            <span className="truncate">
              {selectedCaseId
                ? cases.find((c) => c.id === selectedCaseId)?.case_name || "Case selected"
                : "No case context"}
            </span>
            <ChevronRight className={cn("w-3.5 h-3.5 transition-transform", showCaseSelect && "rotate-90")} />
          </button>
          {showCaseSelect && (
            <div className="mt-1 rounded-xl border border-surface-200 dark:border-surface-700 bg-white dark:bg-surface-900 shadow-lg max-h-48 overflow-y-auto">
              <button
                onClick={() => { setSelectedCaseId(""); setShowCaseSelect(false); }}
                className="w-full text-left px-3 py-2 text-sm text-surface-500 hover:bg-surface-50 dark:hover:bg-surface-800"
              >
                No case context
              </button>
              {cases.map((c) => (
                <button
                  key={c.id}
                  onClick={() => { setSelectedCaseId(c.id); setShowCaseSelect(false); }}
                  className={cn(
                    "w-full text-left px-3 py-2 text-sm truncate hover:bg-surface-50 dark:hover:bg-surface-800",
                    selectedCaseId === c.id && "bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300"
                  )}
                >
                  {c.case_name}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Session list */}
        <div className="flex-1 overflow-y-auto space-y-1">
          {loadingSessions ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-5 h-5 animate-spin text-surface-400" />
            </div>
          ) : sessions.length === 0 ? (
            <p className="text-xs text-surface-400 text-center py-6">No conversations yet</p>
          ) : (
            sessions.map((s) => (
              <button
                key={s.session_id}
                onClick={() => openSession(s)}
                className={cn(
                  "w-full flex items-center gap-2 px-3 py-2.5 rounded-xl text-left transition-colors group",
                  activeSession?.session_id === s.session_id
                    ? "bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300"
                    : "hover:bg-surface-100 dark:hover:bg-surface-800 text-surface-700 dark:text-surface-300"
                )}
              >
                <MessageSquare className="w-3.5 h-3.5 flex-shrink-0" />
                <span className="text-xs truncate flex-1">{s.title || "Conversation"}</span>
                <button
                  onClick={(e) => deleteSession(s.session_id, e)}
                  className="opacity-0 group-hover:opacity-100 p-0.5 text-surface-300 hover:text-red-500 transition-all"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </button>
            ))
          )}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col card overflow-hidden">
        {!activeSession ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-4 p-8 text-center">
            <div className="w-16 h-16 rounded-2xl bg-primary-50 dark:bg-primary-900/20 flex items-center justify-center">
              <Sparkles className="w-8 h-8 text-primary-500" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-surface-900 dark:text-surface-100">LexIntel AI Assistant</h2>
              <p className="text-sm text-surface-400 mt-1 max-w-sm">
                Ask anything about Indian law, your cases, legal procedures, rights, or documents.
                Select a case above to get answers specific to your case.
              </p>
            </div>
            <Button onClick={newSession} className="gap-2">
              <Plus className="w-4 h-4" /> Start Conversation
            </Button>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-lg mt-2">
              {[
                "What are my rights if police refuse to file FIR?",
                "How do I file a consumer complaint against a builder?",
                "What is the process for filing a case in consumer court?",
                "Explain Section 498A IPC and its implications",
              ].map((q) => (
                <button
                  key={q}
                  onClick={async () => {
                    await newSession();
                    setInput(q);
                  }}
                  className="text-left text-xs p-3 rounded-xl border border-surface-200 dark:border-surface-700 hover:border-primary-400 hover:bg-primary-50 dark:hover:bg-primary-900/10 text-surface-600 dark:text-surface-400 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-3 border-b border-surface-100 dark:border-surface-800">
              <div className="flex items-center gap-2">
                <Bot className="w-4 h-4 text-primary-500" />
                <span className="text-sm font-medium text-surface-700 dark:text-surface-300 truncate">
                  {activeSession.title || "Conversation"}
                </span>
                {selectedCaseId && (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300">
                    {cases.find((c) => c.id === selectedCaseId)?.case_name || "Case context"}
                  </span>
                )}
              </div>
              <button
                onClick={() => { setActiveSession(null); setMessages([]); }}
                className="p-1 text-surface-400 hover:text-surface-600 dark:hover:text-surface-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-5 space-y-4">
              {messages.length === 0 && !streamingText && (
                <div className="flex flex-col items-center justify-center h-full gap-3 text-center">
                  <Bot className="w-10 h-10 text-surface-300" />
                  <p className="text-sm text-surface-400">
                    Ask me anything about Indian law or your case.
                  </p>
                </div>
              )}
              {messages.map((msg, i) => (
                <div key={i} className={cn("flex gap-3", msg.role === "user" ? "justify-end" : "justify-start")}>
                  {msg.role === "assistant" && (
                    <div className="w-7 h-7 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Bot className="w-4 h-4 text-primary-600" />
                    </div>
                  )}
                  <div
                    className={cn(
                      "max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap",
                      msg.role === "user"
                        ? "bg-primary-600 text-white rounded-tr-sm"
                        : "bg-surface-100 dark:bg-surface-800 text-surface-800 dark:text-surface-200 rounded-tl-sm"
                    )}
                  >
                    {msg.content}
                  </div>
                  {msg.role === "user" && (
                    <div className="w-7 h-7 rounded-full bg-surface-200 dark:bg-surface-700 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <User className="w-4 h-4 text-surface-500" />
                    </div>
                  )}
                </div>
              ))}

              {/* Streaming response */}
              {streamingText && (
                <div className="flex gap-3 justify-start">
                  <div className="w-7 h-7 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Bot className="w-4 h-4 text-primary-600" />
                  </div>
                  <div className="max-w-[75%] rounded-2xl rounded-tl-sm px-4 py-3 text-sm leading-relaxed bg-surface-100 dark:bg-surface-800 text-surface-800 dark:text-surface-200 whitespace-pre-wrap">
                    {streamingText}
                    <span className="inline-block w-1.5 h-4 bg-primary-500 ml-0.5 animate-pulse rounded-sm" />
                  </div>
                </div>
              )}

              {sending && !streamingText && (
                <div className="flex gap-3">
                  <div className="w-7 h-7 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center flex-shrink-0">
                    <Bot className="w-4 h-4 text-primary-600" />
                  </div>
                  <div className="px-4 py-3 rounded-2xl rounded-tl-sm bg-surface-100 dark:bg-surface-800">
                    <Loader2 className="w-4 h-4 animate-spin text-surface-400" />
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            {/* Input */}
            <div className="px-5 py-4 border-t border-surface-100 dark:border-surface-800">
              <div className="flex gap-2 items-end">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKey}
                  placeholder="Ask about Indian law, your case, legal rights…"
                  rows={1}
                  disabled={sending}
                  className="flex-1 resize-none rounded-xl border border-surface-200 dark:border-surface-700 bg-white dark:bg-surface-800 px-4 py-2.5 text-sm text-surface-900 dark:text-surface-100 placeholder-surface-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:opacity-50 max-h-32 overflow-y-auto"
                  style={{ minHeight: "42px" }}
                  onInput={(e) => {
                    e.target.style.height = "auto";
                    e.target.style.height = Math.min(e.target.scrollHeight, 128) + "px";
                  }}
                />
                <Button
                  onClick={sendMessage}
                  disabled={!input.trim() || sending}
                  className="gap-2 flex-shrink-0 h-[42px]"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
              <p className="text-xs text-surface-400 mt-1.5">
                Press Enter to send · Shift+Enter for new line · AI responses are not legal advice
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
