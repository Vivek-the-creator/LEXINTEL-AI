import { useState } from "react";
import {
  ChevronDown, ChevronUp, CheckCircle, AlertCircle,
  Loader2, Clock, Download, TrendingUp, Lightbulb,
  PenLine, BarChart2, AlertTriangle, Info,
} from "lucide-react";
import { cn } from "../../utils/helpers";

// ── Primitives ────────────────────────────────────────────────────────────────

export function Section({ icon: Icon, title, color = "primary", children, defaultOpen = true }) {
  const [open, setOpen] = useState(defaultOpen);
  const colors = {
    primary: "text-primary-600 bg-primary-50 dark:bg-primary-900/20",
    green:   "text-green-600 bg-green-50 dark:bg-green-900/20",
    purple:  "text-purple-600 bg-purple-50 dark:bg-purple-900/20",
    amber:   "text-amber-600 bg-amber-50 dark:bg-amber-900/20",
    rose:    "text-rose-600 bg-rose-50 dark:bg-rose-900/20",
    blue:    "text-blue-600 bg-blue-50 dark:bg-blue-900/20",
  };
  return (
    <div className="card overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between p-5 hover:bg-surface-50 dark:hover:bg-surface-800/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className={cn("w-9 h-9 rounded-xl flex items-center justify-center", colors[color])}>
            <Icon className="w-5 h-5" />
          </div>
          <span className="font-semibold text-surface-900 dark:text-surface-100">{title}</span>
        </div>
        {open ? <ChevronUp className="w-4 h-4 text-surface-400" /> : <ChevronDown className="w-4 h-4 text-surface-400" />}
      </button>
      {open && <div className="px-5 pb-5 border-t border-surface-100 dark:border-surface-800 pt-4">{children}</div>}
    </div>
  );
}

export function Pill({ children, color = "surface" }) {
  const colors = {
    surface: "bg-surface-100 dark:bg-surface-800 text-surface-700 dark:text-surface-300",
    blue:    "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300",
    green:   "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300",
    amber:   "bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300",
    rose:    "bg-rose-100 dark:bg-rose-900/30 text-rose-700 dark:text-rose-300",
    purple:  "bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300",
    red:     "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300",
  };
  return (
    <span className={cn("inline-block px-2.5 py-1 rounded-lg text-xs font-medium", colors[color])}>
      {children}
    </span>
  );
}

// ── Agent execution summary ───────────────────────────────────────────────────

export function AgentStatus({ executions }) {
  if (!executions?.length) return null;
  const statusColor = { done: "text-green-500", failed: "text-red-500", running: "text-amber-500" };
  const StatusIcon = { done: CheckCircle, failed: AlertCircle, running: Loader2 };
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      {executions.map((e) => {
        const Icon = StatusIcon[e.status] || Clock;
        return (
          <div key={e.agent} className="flex flex-col gap-1 p-3 rounded-xl bg-surface-50 dark:bg-surface-800 border border-surface-200 dark:border-surface-700">
            <div className="flex items-center gap-1.5">
              <Icon className={cn("w-3.5 h-3.5", statusColor[e.status] || "text-surface-400", e.status === "running" && "animate-spin")} />
              <span className="text-xs font-medium text-surface-700 dark:text-surface-300 truncate capitalize">
                {e.agent.replace(/_/g, " ")}
              </span>
            </div>
            {e.elapsed_ms && (
              <span className="text-xs text-surface-400">{(e.elapsed_ms / 1000).toFixed(1)}s</span>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ── Document Intelligence ─────────────────────────────────────────────────────

export function DocumentIntelligenceResult({ data }) {
  if (!data) return <p className="text-sm text-surface-400">No document intelligence data.</p>;
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2 items-center">
        <Pill color="blue">{data.document_type}</Pill>
        {data.ocr_used && <Pill color="amber">OCR Used</Pill>}
        <Pill color="surface">{data.page_count} page{data.page_count !== 1 ? "s" : ""}</Pill>
        <Pill color="green">Confidence {Math.round((data.confidence || 0) * 100)}%</Pill>
      </div>
      {data.summary && (
        <p className="text-sm text-surface-700 dark:text-surface-300 leading-relaxed bg-surface-50 dark:bg-surface-800 rounded-xl p-4">
          {data.summary}
        </p>
      )}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {[
          { label: "Parties", items: data.parties, color: "blue" },
          { label: "Organizations", items: data.organizations, color: "purple" },
          { label: "Locations", items: data.locations, color: "green" },
          { label: "Dates", items: data.dates, color: "amber" },
        ].map(({ label, items, color }) =>
          items?.length > 0 && (
            <div key={label}>
              <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-2">{label}</p>
              <div className="flex flex-wrap gap-1.5">
                {items.map((item, i) => <Pill key={i} color={color}>{item}</Pill>)}
              </div>
            </div>
          )
        )}
      </div>
      {data.legal_sections?.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-2">Legal Sections</p>
          <div className="flex flex-wrap gap-1.5">
            {data.legal_sections.map((s, i) => <Pill key={i} color="rose">{s}</Pill>)}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Legal Research ────────────────────────────────────────────────────────────

export function LegalResearchResult({ data }) {
  if (!data) return <p className="text-sm text-surface-400">No legal research data.</p>;
  return (
    <div className="space-y-4">
      {data.research_summary && (
        <p className="text-sm text-surface-700 dark:text-surface-300 leading-relaxed bg-surface-50 dark:bg-surface-800 rounded-xl p-4">
          {data.research_summary}
        </p>
      )}
      {data.applicable_acts?.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-2">Applicable Acts</p>
          <div className="flex flex-wrap gap-1.5">
            {data.applicable_acts.map((a, i) => <Pill key={i} color="blue">{a}</Pill>)}
          </div>
        </div>
      )}
      {data.provisions?.length > 0 && (
        <div className="space-y-3">
          <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide">Provisions</p>
          {data.provisions.map((p, i) => (
            <div key={i} className="p-4 rounded-xl border border-surface-200 dark:border-surface-700 space-y-2">
              <div className="flex items-center gap-2 flex-wrap">
                <Pill color="rose">§ {p.section}</Pill>
                <span className="text-sm font-semibold text-surface-900 dark:text-surface-100">{p.title}</span>
                <Pill color="green">{Math.round((p.relevance_score || 0) * 100)}% relevant</Pill>
              </div>
              {p.plain_language && (
                <p className="text-sm text-surface-600 dark:text-surface-400">{p.plain_language}</p>
              )}
            </div>
          ))}
        </div>
      )}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {data.remedies?.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-2">Remedies</p>
            <ul className="space-y-1">
              {data.remedies.map((r, i) => (
                <li key={i} className="text-sm text-surface-600 dark:text-surface-400 flex gap-2">
                  <span className="text-green-500 mt-0.5">✓</span>{r}
                </li>
              ))}
            </ul>
          </div>
        )}
        {data.legal_principles?.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-2">Legal Principles</p>
            <ul className="space-y-1">
              {data.legal_principles.map((p, i) => (
                <li key={i} className="text-sm text-surface-600 dark:text-surface-400 flex gap-2">
                  <span className="text-purple-500 mt-0.5">•</span>{p}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Similar Cases ─────────────────────────────────────────────────────────────

export function SimilarCasesResult({ cases }) {
  if (!cases?.length) return (
    <p className="text-sm text-surface-400 italic">
      No similar cases found. The case judgments index will be populated when legal data is seeded in Phase 3B.
    </p>
  );
  return (
    <div className="space-y-3">
      {cases.map((c, i) => (
        <div key={i} className="p-4 rounded-xl border border-surface-200 dark:border-surface-700 space-y-2">
          <div className="flex items-start justify-between gap-2 flex-wrap">
            <span className="text-sm font-semibold text-surface-900 dark:text-surface-100">{c.case_name}</span>
            <Pill color="green">{Math.round((c.similarity_score || 0) * 100)}% match</Pill>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {c.citation && <Pill color="blue">{c.citation}</Pill>}
            {c.court && <Pill color="surface">{c.court}</Pill>}
            {c.year && <Pill color="surface">{c.year}</Pill>}
            {c.verdict && <Pill color={c.verdict.toLowerCase().includes("convict") ? "rose" : "green"}>{c.verdict}</Pill>}
          </div>
          {c.summary && <p className="text-sm text-surface-600 dark:text-surface-400">{c.summary}</p>}
        </div>
      ))}
    </div>
  );
}

// ── Evidence ──────────────────────────────────────────────────────────────────

export function EvidenceResult({ items, timeline, analysis, hints }) {
  const inventory = {};
  (items || []).forEach((e) => {
    inventory[e.file_type] = (inventory[e.file_type] || 0) + 1;
  });

  return (
    <div className="space-y-4">
      {/* Inventory */}
      {Object.keys(inventory).length > 0 && (
        <div>
          <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-3">Evidence Inventory</p>
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
            {Object.entries(inventory).map(([type, count]) => (
              <div key={type} className="flex flex-col items-center p-3 rounded-xl bg-surface-50 dark:bg-surface-800 border border-surface-200 dark:border-surface-700">
                <span className="text-2xl font-bold text-surface-900 dark:text-surface-100">{count}</span>
                <span className="text-xs text-surface-500 capitalize mt-0.5">{type}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {analysis?.analysis_summary && (
        <p className="text-sm text-surface-700 dark:text-surface-300 leading-relaxed bg-surface-50 dark:bg-surface-800 rounded-xl p-4">
          {analysis.analysis_summary}
        </p>
      )}

      {timeline?.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-3">Timeline</p>
          <div className="relative pl-5 space-y-4 border-l-2 border-surface-200 dark:border-surface-700">
            {timeline.map((entry, i) => (
              <div key={i} className="relative">
                <div className="absolute -left-[1.4rem] w-3 h-3 rounded-full bg-primary-500 border-2 border-white dark:border-surface-900 top-1" />
                <p className="text-xs text-surface-400 mb-0.5">{entry.timestamp}</p>
                <p className="text-sm text-surface-700 dark:text-surface-300">{entry.event_description}</p>
                <Pill color="surface">{Math.round((entry.confidence || 0) * 100)}% confidence</Pill>
              </div>
            ))}
          </div>
        </div>
      )}

      {hints?.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-2">Missing Evidence Hints</p>
          <div className="flex flex-wrap gap-1.5">
            {hints.map((h, i) => <Pill key={i} color="amber">{h}</Pill>)}
          </div>
        </div>
      )}

      {!timeline?.length && !hints?.length && !Object.keys(inventory).length && (
        <p className="text-sm text-surface-400 italic">No evidence data — provide files for full analysis.</p>
      )}
    </div>
  );
}

// ── Outcome Prediction ────────────────────────────────────────────────────────

export function OutcomePredictionResult({ data }) {
  if (!data) return <p className="text-sm text-surface-400">No prediction data.</p>;

  const strengthPct = Math.round((data.case_strength_score || 0) * 100);
  const riskColor = { High: "rose", Medium: "amber", Low: "green" }[data.risk_level] || "surface";
  const confColor = { High: "green", Medium: "amber", Low: "rose" }[data.confidence_level] || "surface";

  return (
    <div className="space-y-5">
      {/* Disclaimer */}
      {data.disclaimer && (
        <div className="flex gap-2 p-3 rounded-xl bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800">
          <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
          <p className="text-xs text-amber-700 dark:text-amber-400">{data.disclaimer}</p>
        </div>
      )}

      {/* Key metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-4 rounded-xl bg-surface-50 dark:bg-surface-800 border border-surface-200 dark:border-surface-700 text-center">
          <p className="text-2xl font-bold text-primary-600">{data.probability_of_success || "N/A"}</p>
          <p className="text-xs text-surface-500 mt-1">Probability of Success</p>
        </div>
        <div className="p-4 rounded-xl bg-surface-50 dark:bg-surface-800 border border-surface-200 dark:border-surface-700 text-center">
          <p className="text-2xl font-bold text-surface-900 dark:text-surface-100">{strengthPct}%</p>
          <p className="text-xs text-surface-500 mt-1">Case Strength</p>
        </div>
        <div className="p-4 rounded-xl bg-surface-50 dark:bg-surface-800 border border-surface-200 dark:border-surface-700 text-center">
          <Pill color={confColor}>{data.confidence_level || "N/A"}</Pill>
          <p className="text-xs text-surface-500 mt-2">Confidence</p>
        </div>
        <div className="p-4 rounded-xl bg-surface-50 dark:bg-surface-800 border border-surface-200 dark:border-surface-700 text-center">
          <Pill color={riskColor}>{data.risk_level || "N/A"}</Pill>
          <p className="text-xs text-surface-500 mt-2">Risk Level</p>
        </div>
      </div>

      {data.confidence_reason && (
        <p className="text-sm text-surface-600 dark:text-surface-400 italic">{data.confidence_reason}</p>
      )}

      {/* Strengths & Weaknesses */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {data.key_strengths?.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-2">Key Strengths</p>
            <ul className="space-y-1">
              {data.key_strengths.map((s, i) => (
                <li key={i} className="text-sm text-surface-700 dark:text-surface-300 flex gap-2">
                  <span className="text-green-500 mt-0.5">✓</span>{s}
                </li>
              ))}
            </ul>
          </div>
        )}
        {data.key_weaknesses?.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-2">Key Weaknesses</p>
            <ul className="space-y-1">
              {data.key_weaknesses.map((w, i) => (
                <li key={i} className="text-sm text-surface-700 dark:text-surface-300 flex gap-2">
                  <span className="text-rose-500 mt-0.5">✗</span>{w}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Outcome scenarios */}
      {data.outcome_scenarios?.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-3">Outcome Scenarios</p>
          <div className="space-y-2">
            {data.outcome_scenarios.map((s, i) => (
              <div key={i} className="p-3 rounded-xl border border-surface-200 dark:border-surface-700 space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-surface-900 dark:text-surface-100">{s.scenario}</span>
                  <Pill color="blue">{s.probability}</Pill>
                </div>
                {s.description && <p className="text-sm text-surface-600 dark:text-surface-400">{s.description}</p>}
                {s.reasoning && <p className="text-xs text-surface-400 italic">{s.reasoning}</p>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Counter arguments */}
      {data.counter_arguments?.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-2">Possible Counter Arguments</p>
          <ul className="space-y-1">
            {data.counter_arguments.map((c, i) => (
              <li key={i} className="text-sm text-surface-600 dark:text-surface-400 flex gap-2">
                <span className="text-amber-500 mt-0.5">⚡</span>{c}
              </li>
            ))}
          </ul>
        </div>
      )}

      {data.missing_evidence_impact && (
        <div className="p-3 rounded-xl bg-rose-50 dark:bg-rose-900/10 border border-rose-200 dark:border-rose-800">
          <p className="text-xs font-semibold text-rose-600 dark:text-rose-400 mb-1">Missing Evidence Impact</p>
          <p className="text-sm text-rose-700 dark:text-rose-300">{data.missing_evidence_impact}</p>
        </div>
      )}
    </div>
  );
}

// ── Strategy Planning ─────────────────────────────────────────────────────────

export function StrategyPlanningResult({ data }) {
  if (!data) return <p className="text-sm text-surface-400">No strategy data.</p>;
  const [openIdx, setOpenIdx] = useState(0);

  return (
    <div className="space-y-5">
      {data.disclaimer && (
        <div className="flex gap-2 p-3 rounded-xl bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800">
          <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
          <p className="text-xs text-amber-700 dark:text-amber-400">{data.disclaimer}</p>
        </div>
      )}

      {/* Immediate next steps */}
      {data.immediate_next_steps?.length > 0 && (
        <div className="p-4 rounded-xl bg-primary-50 dark:bg-primary-900/10 border border-primary-200 dark:border-primary-800">
          <p className="text-xs font-semibold text-primary-600 dark:text-primary-400 uppercase tracking-wide mb-2">Immediate Next Steps</p>
          <ol className="space-y-1">
            {data.immediate_next_steps.map((s, i) => (
              <li key={i} className="text-sm text-surface-700 dark:text-surface-300 flex gap-2">
                <span className="text-primary-500 font-bold flex-shrink-0">{i + 1}.</span>{s}
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Strategies */}
      {data.strategies?.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide">Recommended Strategies</p>
          {data.strategies.map((s, i) => (
            <div key={i} className="border border-surface-200 dark:border-surface-700 rounded-xl overflow-hidden">
              <button
                onClick={() => setOpenIdx(openIdx === i ? -1 : i)}
                className="w-full flex items-center justify-between p-4 hover:bg-surface-50 dark:hover:bg-surface-800/50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className="text-sm font-semibold text-surface-900 dark:text-surface-100">{s.name}</span>
                  <Pill color={{ Low: "green", Medium: "amber", High: "rose" }[s.risk_level] || "surface"}>
                    {s.risk_level} Risk
                  </Pill>
                  <Pill color="surface">{s.effort} Effort</Pill>
                  {s.estimated_timeline && <Pill color="blue">{s.estimated_timeline}</Pill>}
                </div>
                {openIdx === i ? <ChevronUp className="w-4 h-4 text-surface-400" /> : <ChevronDown className="w-4 h-4 text-surface-400" />}
              </button>
              {openIdx === i && (
                <div className="px-4 pb-4 border-t border-surface-100 dark:border-surface-800 pt-3 space-y-3">
                  {s.description && <p className="text-sm text-surface-600 dark:text-surface-400">{s.description}</p>}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {s.pros?.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-green-600 mb-1">Pros</p>
                        <ul className="space-y-0.5">
                          {s.pros.map((p, j) => <li key={j} className="text-sm text-surface-600 dark:text-surface-400 flex gap-1.5"><span className="text-green-500">+</span>{p}</li>)}
                        </ul>
                      </div>
                    )}
                    {s.cons?.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-rose-600 mb-1">Cons</p>
                        <ul className="space-y-0.5">
                          {s.cons.map((c, j) => <li key={j} className="text-sm text-surface-600 dark:text-surface-400 flex gap-1.5"><span className="text-rose-500">−</span>{c}</li>)}
                        </ul>
                      </div>
                    )}
                  </div>
                  {s.recommended_actions?.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-1">Actions</p>
                      <ol className="space-y-0.5">
                        {s.recommended_actions.map((a, j) => (
                          <li key={j} className="text-sm text-surface-600 dark:text-surface-400 flex gap-1.5">
                            <span className="text-primary-500 font-bold flex-shrink-0">{j + 1}.</span>{a}
                          </li>
                        ))}
                      </ol>
                    </div>
                  )}
                  {s.legal_basis?.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {s.legal_basis.map((b, j) => <Pill key={j} color="rose">{b}</Pill>)}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {data.important_deadlines?.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-2">Important Deadlines</p>
            <ul className="space-y-1">
              {data.important_deadlines.map((d, i) => (
                <li key={i} className="text-sm text-surface-600 dark:text-surface-400 flex gap-2">
                  <span className="text-amber-500 mt-0.5">⏰</span>{d}
                </li>
              ))}
            </ul>
          </div>
        )}
        {data.potential_legal_risks?.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-2">Legal Risks</p>
            <ul className="space-y-1">
              {data.potential_legal_risks.map((r, i) => (
                <li key={i} className="text-sm text-surface-600 dark:text-surface-400 flex gap-2">
                  <span className="text-rose-500 mt-0.5">⚠</span>{r}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Legal Drafts ──────────────────────────────────────────────────────────────

export function LegalDraftsResult({ drafts, onDownload }) {
  const [activeIdx, setActiveIdx] = useState(0);
  if (!drafts?.length) return <p className="text-sm text-surface-400">No legal drafts generated.</p>;

  const draft = drafts[activeIdx];

  return (
    <div className="space-y-4">
      {/* Draft selector tabs */}
      <div className="flex flex-wrap gap-2">
        {drafts.map((d, i) => (
          <button
            key={i}
            onClick={() => setActiveIdx(i)}
            className={cn(
              "px-3 py-1.5 rounded-lg text-sm font-medium transition-colors",
              activeIdx === i
                ? "bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300"
                : "bg-surface-100 dark:bg-surface-800 text-surface-600 dark:text-surface-400 hover:bg-surface-200 dark:hover:bg-surface-700"
            )}
          >
            {d.document_type || d.title || `Draft ${i + 1}`}
          </button>
        ))}
      </div>

      {/* Active draft */}
      {draft && (
        <div className="space-y-3">
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-semibold text-surface-900 dark:text-surface-100">{draft.title || draft.document_type}</span>
              <Pill color="amber">AI Generated</Pill>
              <Pill color="rose">Requires Lawyer Review</Pill>
            </div>
            {onDownload && (
              <button
                onClick={() => onDownload(draft)}
                className="flex items-center gap-1.5 text-sm text-primary-600 hover:text-primary-700 font-medium"
              >
                <Download className="w-4 h-4" /> Download
              </button>
            )}
          </div>

          {draft.filing_instructions && (
            <div className="flex gap-2 p-3 rounded-xl bg-blue-50 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-800">
              <Info className="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-blue-700 dark:text-blue-300">{draft.filing_instructions}</p>
            </div>
          )}

          <pre className="text-sm text-surface-700 dark:text-surface-300 bg-surface-50 dark:bg-surface-800 rounded-xl p-4 whitespace-pre-wrap font-mono leading-relaxed max-h-96 overflow-y-auto border border-surface-200 dark:border-surface-700">
            {draft.content || "Draft content unavailable."}
          </pre>

          {draft.placeholders?.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-2">Placeholders Requiring Lawyer Input</p>
              <div className="flex flex-wrap gap-1.5">
                {draft.placeholders.map((p, i) => <Pill key={i} color="amber">{p}</Pill>)}
              </div>
            </div>
          )}

          {draft.lawyer_review_notes?.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-2">Lawyer Review Notes</p>
              <ul className="space-y-1">
                {draft.lawyer_review_notes.map((n, i) => (
                  <li key={i} className="text-sm text-surface-600 dark:text-surface-400 flex gap-2">
                    <span className="text-amber-500 mt-0.5">•</span>{n}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Case Report & Explainability ──────────────────────────────────────────────

export function CaseReportResult({ data, onExport }) {
  const [showExplain, setShowExplain] = useState(false);
  if (!data) return <p className="text-sm text-surface-400">No report generated.</p>;

  return (
    <div className="space-y-5">
      {data.disclaimer && (
        <div className="flex gap-2 p-3 rounded-xl bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800">
          <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
          <p className="text-xs text-amber-700 dark:text-amber-400">{data.disclaimer}</p>
        </div>
      )}

      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          {data.ai_confidence_overall != null && (
            <Pill color="green">AI Confidence: {Math.round((data.ai_confidence_overall || 0) * 100)}%</Pill>
          )}
          {data.generated_at && (
            <span className="text-xs text-surface-400">Generated {new Date(data.generated_at).toLocaleString()}</span>
          )}
        </div>
        {onExport && (
          <button
            onClick={onExport}
            className="flex items-center gap-1.5 text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            <Download className="w-4 h-4" /> Export Markdown
          </button>
        )}
      </div>

      {/* Executive Summary */}
      {data.executive_summary && (
        <div>
          <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-2">Executive Summary</p>
          <p className="text-sm text-surface-700 dark:text-surface-300 leading-relaxed bg-surface-50 dark:bg-surface-800 rounded-xl p-4">
            {data.executive_summary}
          </p>
        </div>
      )}

      {/* Case Overview */}
      {data.case_overview && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {Object.entries(data.case_overview).map(([k, v]) => v && (
            <div key={k} className="p-3 rounded-xl bg-surface-50 dark:bg-surface-800 border border-surface-200 dark:border-surface-700">
              <p className="text-xs text-surface-400 capitalize mb-1">{k.replace(/_/g, " ")}</p>
              <p className="text-sm font-medium text-surface-900 dark:text-surface-100">{v}</p>
            </div>
          ))}
        </div>
      )}

      {/* Evidence Inventory */}
      {data.evidence_inventory?.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-2">Evidence Inventory</p>
          <div className="space-y-1">
            {data.evidence_inventory.map((e, i) => (
              <div key={i} className="flex items-center gap-3 p-2.5 rounded-lg border border-surface-200 dark:border-surface-700">
                <Pill color={e.status === "present" ? "green" : "rose"}>{e.status}</Pill>
                <span className="text-sm font-medium text-surface-700 dark:text-surface-300 flex-1">{e.item}</span>
                {e.significance && <span className="text-xs text-surface-400 hidden sm:block">{e.significance}</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Outcome Analysis */}
      {data.outcome_analysis && (
        <div className="p-4 rounded-xl bg-primary-50 dark:bg-primary-900/10 border border-primary-200 dark:border-primary-800 space-y-2">
          <p className="text-xs font-semibold text-primary-600 dark:text-primary-400 uppercase tracking-wide">Outcome Analysis</p>
          <p className="text-sm font-semibold text-surface-900 dark:text-surface-100">{data.outcome_analysis.prediction}</p>
          {data.outcome_analysis.confidence && (
            <Pill color="blue">{data.outcome_analysis.confidence}</Pill>
          )}
          {data.outcome_analysis.reasoning && (
            <p className="text-sm text-surface-600 dark:text-surface-400">{data.outcome_analysis.reasoning}</p>
          )}
        </div>
      )}

      {/* Recommendations */}
      {data.recommendations?.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-2">Recommendations</p>
          <ol className="space-y-1">
            {data.recommendations.map((r, i) => (
              <li key={i} className="text-sm text-surface-700 dark:text-surface-300 flex gap-2">
                <span className="text-primary-500 font-bold flex-shrink-0">{i + 1}.</span>{r}
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Legal Risks */}
      {data.legal_risks?.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-2">Legal Risks</p>
          <div className="flex flex-wrap gap-1.5">
            {data.legal_risks.map((r, i) => <Pill key={i} color="rose">{r}</Pill>)}
          </div>
        </div>
      )}

      {/* Explainability */}
      {data.explainability?.length > 0 && (
        <div>
          <button
            onClick={() => setShowExplain((v) => !v)}
            className="flex items-center gap-2 text-sm font-semibold text-surface-700 dark:text-surface-300 hover:text-primary-600 transition-colors"
          >
            <Info className="w-4 h-4" />
            AI Explainability ({data.explainability.length} conclusions)
            {showExplain ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
          {showExplain && (
            <div className="mt-3 space-y-3">
              {data.explainability.map((ex, i) => (
                <div key={i} className="p-4 rounded-xl border border-surface-200 dark:border-surface-700 space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-surface-900 dark:text-surface-100">{ex.conclusion}</span>
                    {ex.confidence_score != null && (
                      <Pill color="green">{Math.round((ex.confidence_score || 0) * 100)}% confidence</Pill>
                    )}
                  </div>
                  {ex.reasoning_chain && (
                    <p className="text-sm text-surface-600 dark:text-surface-400">{ex.reasoning_chain}</p>
                  )}
                  <div className="flex flex-wrap gap-1.5">
                    {(ex.evidence_used || []).map((e, j) => <Pill key={j} color="blue">{e}</Pill>)}
                    {(ex.legal_references || []).map((r, j) => <Pill key={j} color="rose">{r}</Pill>)}
                    {(ex.similar_judgments || []).map((s, j) => <Pill key={j} color="purple">{s}</Pill>)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
