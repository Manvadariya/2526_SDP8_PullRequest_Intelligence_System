import React, { useState } from "react";
import { Link } from "react-router-dom";

const MOCK_PRS = [
  {
    id: 1,
    number: 247,
    title: "feat: add user authentication with OAuth2",
    author: "sarah-dev",
    repo: "frontend-app",
    status: "changes_requested",
    verdict: "REQUEST_CHANGES",
    riskLevel: "high",
    riskColor: "text-red-400",
    riskBg: "bg-red-400/10",
    filesChanged: 12,
    additions: 342,
    deletions: 45,
    reviewTime: "47s",
    createdAt: "2 hours ago",
    issues: [
      { type: "Security", severity: "High", description: "Unsanitized user input in SQL query", line: 42 },
      { type: "Bug Risk", severity: "Medium", description: "Missing null check on response.data", line: 78 },
    ],
    agents: ["Sentinel", "Architect", "Optimizer", "Mentor"],
  },
  {
    id: 2,
    number: 246,
    title: "fix: resolve memory leak in WebSocket handler",
    author: "mike-eng",
    repo: "api-gateway",
    status: "approved",
    verdict: "APPROVE",
    riskLevel: "low",
    riskColor: "text-green-400",
    riskBg: "bg-green-400/10",
    filesChanged: 3,
    additions: 28,
    deletions: 15,
    reviewTime: "23s",
    createdAt: "5 hours ago",
    issues: [],
    agents: ["Sentinel", "Optimizer"],
  },
  {
    id: 3,
    number: 245,
    title: "refactor: migrate database queries to prepared statements",
    author: "alex-sec",
    repo: "api-gateway",
    status: "approved",
    verdict: "APPROVE",
    riskLevel: "low",
    riskColor: "text-green-400",
    riskBg: "bg-green-400/10",
    filesChanged: 8,
    additions: 156,
    deletions: 132,
    reviewTime: "38s",
    createdAt: "1 day ago",
    issues: [],
    agents: ["Sentinel", "Architect", "Mentor"],
  },
  {
    id: 4,
    number: 244,
    title: "feat: implement real-time notification system",
    author: "lisa-dev",
    repo: "frontend-app",
    status: "comment",
    verdict: "COMMENT",
    riskLevel: "medium",
    riskColor: "text-amber-300",
    riskBg: "bg-amber-300/10",
    filesChanged: 7,
    additions: 203,
    deletions: 12,
    reviewTime: "52s",
    createdAt: "1 day ago",
    issues: [
      { type: "Performance", severity: "Medium", description: "N+1 query pattern detected in notification fetch", line: 156 },
    ],
    agents: ["Optimizer", "Architect", "Mentor"],
  },
  {
    id: 5,
    number: 243,
    title: "chore: update dependencies and fix security vulnerabilities",
    author: "bot-renovate",
    repo: "ml-pipeline",
    status: "approved",
    verdict: "APPROVE",
    riskLevel: "low",
    riskColor: "text-green-400",
    riskBg: "bg-green-400/10",
    filesChanged: 2,
    additions: 89,
    deletions: 87,
    reviewTime: "15s",
    createdAt: "2 days ago",
    issues: [],
    agents: ["Sentinel"],
  },
];

export const PRVisualize = () => {
  const [selected, setSelected] = useState(MOCK_PRS[0]);
  const [viewMode, setViewMode] = useState("list");

  const getVerdictStyles = (verdict) => {
    switch (verdict) {
      case "APPROVE":
        return { text: "text-green-400", bg: "bg-green-400/10", border: "border-green-400/20", icon: "✅" };
      case "REQUEST_CHANGES":
        return { text: "text-red-400", bg: "bg-red-400/10", border: "border-red-400/20", icon: "🔴" };
      case "COMMENT":
        return { text: "text-amber-300", bg: "bg-amber-300/10", border: "border-amber-300/20", icon: "💬" };
      default:
        return { text: "text-neutral-400", bg: "bg-neutral-400/10", border: "border-neutral-400/20", icon: "⏳" };
    }
  };

  return (
    <section className="bg-[linear-gradient(rgba(255,255,255,0.03),rgba(0,0,0,0)_40%)] box-border caret-transparent isolate outline-transparent overflow-x-hidden overflow-y-auto py-12 md:py-32">
      <div className="box-border caret-transparent max-w-screen-lg outline-transparent w-full mx-auto px-6">
        {/* Page Header */}
        <div className="box-border caret-transparent outline-transparent mb-8">
          <h1 className="text-[40px] font-[538] box-border caret-transparent tracking-[-0.6px] leading-[44px] outline-transparent mb-2">
            PR Reviews
          </h1>
          <p className="text-neutral-400 text-[17px] box-border caret-transparent leading-[24.5px] outline-transparent">
            Visualize AI review results across all your pull requests.
          </p>
        </div>

        {/* Stats Overview */}
        <div className="border-b-stone-50 border-l-stone-50 border-r-stone-50 box-border caret-transparent gap-x-4 grid grid-cols-2 outline-transparent gap-y-4 border-t-white/10 border-t border-b-white/10 border-b py-6 mb-8 md:grid-cols-4">
          <div className="box-border caret-transparent outline-transparent">
            <span className="text-neutral-500 text-[13px] box-border caret-transparent block tracking-[-0.13px] leading-[19.5px] outline-transparent mb-1">
              Total Reviews
            </span>
            <span className="text-[28px] font-[538] box-border caret-transparent tracking-[-0.5px] outline-transparent">
              {MOCK_PRS.length}
            </span>
          </div>
          <div className="box-border caret-transparent outline-transparent">
            <span className="text-neutral-500 text-[13px] box-border caret-transparent block tracking-[-0.13px] leading-[19.5px] outline-transparent mb-1">
              Approved
            </span>
            <span className="text-green-400 text-[28px] font-[538] box-border caret-transparent tracking-[-0.5px] outline-transparent">
              {MOCK_PRS.filter((p) => p.verdict === "APPROVE").length}
            </span>
          </div>
          <div className="box-border caret-transparent outline-transparent">
            <span className="text-neutral-500 text-[13px] box-border caret-transparent block tracking-[-0.13px] leading-[19.5px] outline-transparent mb-1">
              Changes Requested
            </span>
            <span className="text-red-400 text-[28px] font-[538] box-border caret-transparent tracking-[-0.5px] outline-transparent">
              {MOCK_PRS.filter((p) => p.verdict === "REQUEST_CHANGES").length}
            </span>
          </div>
          <div className="box-border caret-transparent outline-transparent">
            <span className="text-neutral-500 text-[13px] box-border caret-transparent block tracking-[-0.13px] leading-[19.5px] outline-transparent mb-1">
              Avg Review Time
            </span>
            <span className="text-[28px] font-[538] box-border caret-transparent tracking-[-0.5px] outline-transparent">
              35s
            </span>
          </div>
        </div>

        {/* View Toggle */}
        <div className="items-center box-border caret-transparent flex outline-transparent gap-x-1 mb-6">
          <button
            onClick={() => setViewMode("list")}
            className={`text-[13px] font-[510] items-center box-border caret-transparent flex h-8 justify-center outline-transparent text-nowrap px-3 rounded-lg ${viewMode === "list" ? "text-stone-50 bg-zinc-800 border border-zinc-700 border-solid" : "text-neutral-400 bg-transparent"}`}
          >
            List View
          </button>
          <button
            onClick={() => setViewMode("detail")}
            className={`text-[13px] font-[510] items-center box-border caret-transparent flex h-8 justify-center outline-transparent text-nowrap px-3 rounded-lg ${viewMode === "detail" ? "text-stone-50 bg-zinc-800 border border-zinc-700 border-solid" : "text-neutral-400 bg-transparent"}`}
          >
            Detail View
          </button>
        </div>

        {viewMode === "list" ? (
          /* List View */
          <div className="box-border caret-transparent outline-transparent">
            {MOCK_PRS.map((pr) => {
              const verdictStyle = getVerdictStyles(pr.verdict);
              return (
                <div
                  key={pr.id}
                  onClick={() => { setSelected(pr); setViewMode("detail"); }}
                  className="border-b-white/10 border-b box-border caret-transparent flex outline-transparent py-4 gap-x-4 items-start hover:bg-white/[0.02] px-2 -mx-2 rounded-lg transition-colors cursor-pointer"
                >
                  {/* Verdict Badge */}
                  <div className={`${verdictStyle.bg} box-border caret-transparent flex items-center justify-center h-10 w-10 outline-transparent shrink-0 rounded-lg mt-0.5 border ${verdictStyle.border} border-solid`}>
                    <span className="text-[16px]">{verdictStyle.icon}</span>
                  </div>

                  {/* PR Info */}
                  <div className="box-border caret-transparent outline-transparent grow min-w-0">
                    <div className="items-center box-border caret-transparent flex outline-transparent gap-x-2 mb-1 flex-wrap">
                      <span className="text-stone-50 text-[15px] font-[510] box-border caret-transparent tracking-[-0.165px] outline-transparent">
                        {pr.title}
                      </span>
                      <span className="text-neutral-500 text-[13px] box-border caret-transparent tracking-[-0.13px] outline-transparent font-berkeley_mono">
                        #{pr.number}
                      </span>
                    </div>
                    <div className="items-center box-border caret-transparent flex outline-transparent gap-x-3 flex-wrap gap-y-1">
                      <span className="text-neutral-500 text-[12px] box-border caret-transparent tracking-[-0.12px] leading-[18px] outline-transparent">
                        {pr.repo}
                      </span>
                      <span className="text-neutral-500 text-[12px] box-border caret-transparent outline-transparent">•</span>
                      <span className="text-neutral-500 text-[12px] box-border caret-transparent tracking-[-0.12px] leading-[18px] outline-transparent">
                        by {pr.author}
                      </span>
                      <span className="text-neutral-500 text-[12px] box-border caret-transparent outline-transparent">•</span>
                      <span className="text-neutral-500 text-[12px] box-border caret-transparent tracking-[-0.12px] leading-[18px] outline-transparent">
                        {pr.createdAt}
                      </span>
                      <span className="text-neutral-500 text-[12px] box-border caret-transparent outline-transparent">•</span>
                      <span className="text-neutral-500 text-[12px] box-border caret-transparent tracking-[-0.12px] leading-[18px] outline-transparent">
                        Reviewed in {pr.reviewTime}
                      </span>
                    </div>
                  </div>

                  {/* Risk + Changes */}
                  <div className="box-border caret-transparent outline-transparent shrink-0 text-right">
                    <span className={`${pr.riskColor} text-[13px] font-[510] ${pr.riskBg} box-border caret-transparent outline-transparent border ${pr.riskColor === "text-red-400" ? "border-red-400/20" : pr.riskColor === "text-amber-300" ? "border-amber-300/20" : "border-green-400/20"} px-2 py-0.5 rounded-md border-solid text-nowrap`}>
                      {pr.riskLevel}
                    </span>
                    <div className="text-neutral-500 text-[12px] box-border caret-transparent tracking-[-0.12px] leading-[18px] outline-transparent mt-1">
                      <span className="text-green-400">+{pr.additions}</span> <span className="text-red-400">-{pr.deletions}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          /* Detail View */
          <div className="box-border caret-transparent outline-transparent">
            {/* Back Button */}
            <button
              onClick={() => setViewMode("list")}
              className="text-neutral-400 text-[13px] font-[510] items-center box-border caret-transparent flex h-8 outline-transparent text-nowrap gap-x-1 mb-6 hover:text-stone-50"
            >
              <svg className="box-border caret-transparent shrink-0 h-4 outline-transparent w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
              </svg>
              Back to list
            </button>

            {/* PR Detail Header */}
            <div className="border-b-white/10 border-b box-border caret-transparent outline-transparent pb-6 mb-6">
              <div className="items-center box-border caret-transparent flex outline-transparent gap-x-3 mb-2">
                <span className={`${getVerdictStyles(selected.verdict).text} text-[13px] font-[510] ${getVerdictStyles(selected.verdict).bg} box-border caret-transparent outline-transparent border ${getVerdictStyles(selected.verdict).border} px-2 py-0.5 rounded-md border-solid`}>
                  {getVerdictStyles(selected.verdict).icon} {selected.verdict}
                </span>
                <span className={`${selected.riskColor} text-[13px] font-[510] ${selected.riskBg} box-border caret-transparent outline-transparent border ${selected.riskColor === "text-red-400" ? "border-red-400/20" : selected.riskColor === "text-amber-300" ? "border-amber-300/20" : "border-green-400/20"} px-2 py-0.5 rounded-md border-solid`}>
                  Risk: {selected.riskLevel}
                </span>
              </div>
              <h2 className="text-[21px] font-[510] box-border caret-transparent tracking-[-0.37px] leading-7 outline-transparent mb-1">
                {selected.title}
              </h2>
              <div className="items-center box-border caret-transparent flex outline-transparent gap-x-3 flex-wrap">
                <span className="text-neutral-500 text-[13px] box-border caret-transparent tracking-[-0.13px] leading-[19.5px] outline-transparent font-berkeley_mono">
                  #{selected.number}
                </span>
                <span className="text-neutral-500 text-[13px] box-border caret-transparent outline-transparent">•</span>
                <span className="text-neutral-400 text-[13px] box-border caret-transparent tracking-[-0.13px] leading-[19.5px] outline-transparent">
                  {selected.repo}
                </span>
                <span className="text-neutral-500 text-[13px] box-border caret-transparent outline-transparent">•</span>
                <span className="text-neutral-400 text-[13px] box-border caret-transparent tracking-[-0.13px] leading-[19.5px] outline-transparent">
                  by {selected.author}
                </span>
                <span className="text-neutral-500 text-[13px] box-border caret-transparent outline-transparent">•</span>
                <span className="text-neutral-400 text-[13px] box-border caret-transparent tracking-[-0.13px] leading-[19.5px] outline-transparent">
                  Reviewed in {selected.reviewTime}
                </span>
              </div>
            </div>

            {/* Stats Grid */}
            <div className="box-border caret-transparent gap-x-4 grid grid-cols-2 outline-transparent gap-y-4 mb-8 md:grid-cols-4">
              <div className="relative bg-[linear-gradient(134deg,rgba(255,255,255,0.08),rgba(255,255,255,0.02),rgba(255,255,255,0)_55%)] box-border caret-transparent outline-transparent border border-white/10 p-4 rounded-lg border-solid">
                <span className="text-neutral-500 text-[12px] box-border caret-transparent block tracking-[-0.12px] leading-[18px] outline-transparent mb-1">
                  Files Changed
                </span>
                <span className="text-[21px] font-[510] box-border caret-transparent tracking-[-0.37px] outline-transparent">
                  {selected.filesChanged}
                </span>
              </div>
              <div className="relative bg-[linear-gradient(134deg,rgba(255,255,255,0.08),rgba(255,255,255,0.02),rgba(255,255,255,0)_55%)] box-border caret-transparent outline-transparent border border-white/10 p-4 rounded-lg border-solid">
                <span className="text-neutral-500 text-[12px] box-border caret-transparent block tracking-[-0.12px] leading-[18px] outline-transparent mb-1">
                  Additions
                </span>
                <span className="text-green-400 text-[21px] font-[510] box-border caret-transparent tracking-[-0.37px] outline-transparent">
                  +{selected.additions}
                </span>
              </div>
              <div className="relative bg-[linear-gradient(134deg,rgba(255,255,255,0.08),rgba(255,255,255,0.02),rgba(255,255,255,0)_55%)] box-border caret-transparent outline-transparent border border-white/10 p-4 rounded-lg border-solid">
                <span className="text-neutral-500 text-[12px] box-border caret-transparent block tracking-[-0.12px] leading-[18px] outline-transparent mb-1">
                  Deletions
                </span>
                <span className="text-red-400 text-[21px] font-[510] box-border caret-transparent tracking-[-0.37px] outline-transparent">
                  -{selected.deletions}
                </span>
              </div>
              <div className="relative bg-[linear-gradient(134deg,rgba(255,255,255,0.08),rgba(255,255,255,0.02),rgba(255,255,255,0)_55%)] box-border caret-transparent outline-transparent border border-white/10 p-4 rounded-lg border-solid">
                <span className="text-neutral-500 text-[12px] box-border caret-transparent block tracking-[-0.12px] leading-[18px] outline-transparent mb-1">
                  Issues Found
                </span>
                <span className="text-[21px] font-[510] box-border caret-transparent tracking-[-0.37px] outline-transparent">
                  {selected.issues.length}
                </span>
              </div>
            </div>

            {/* Agents Used */}
            <div className="box-border caret-transparent outline-transparent mb-8">
              <h3 className="text-[15px] font-[510] box-border caret-transparent tracking-[-0.165px] outline-transparent mb-3">
                Review Agents
              </h3>
              <div className="items-center box-border caret-transparent flex outline-transparent gap-x-2 flex-wrap gap-y-2">
                {selected.agents.map((agent) => (
                  <span
                    key={agent}
                    className="text-slate-300 text-[13px] font-[510] items-center bg-zinc-800 box-border caret-transparent flex h-7 outline-transparent gap-x-1.5 text-nowrap border border-zinc-700 px-2.5 rounded-md border-solid"
                  >
                    {agent === "Sentinel" && "🛡️"}
                    {agent === "Architect" && "🏛️"}
                    {agent === "Optimizer" && "⚡"}
                    {agent === "Mentor" && "🎓"}
                    {" "}{agent}
                  </span>
                ))}
              </div>
            </div>

            {/* Issues Table */}
            {selected.issues.length > 0 && (
              <div className="box-border caret-transparent outline-transparent mb-8">
                <h3 className="text-[15px] font-[510] box-border caret-transparent tracking-[-0.165px] outline-transparent mb-3">
                  Issues Found
                </h3>
                <div className="box-border caret-transparent outline-transparent border border-white/10 rounded-lg border-solid overflow-hidden">
                  {/* Table Header */}
                  <div className="items-center bg-zinc-900/60 box-border caret-transparent gap-x-4 grid grid-cols-[80px_80px_1fr_60px] outline-transparent p-3 border-b border-white/10 border-solid">
                    <span className="text-neutral-500 text-[12px] font-[510] box-border caret-transparent tracking-[-0.12px] outline-transparent">Type</span>
                    <span className="text-neutral-500 text-[12px] font-[510] box-border caret-transparent tracking-[-0.12px] outline-transparent">Severity</span>
                    <span className="text-neutral-500 text-[12px] font-[510] box-border caret-transparent tracking-[-0.12px] outline-transparent">Description</span>
                    <span className="text-neutral-500 text-[12px] font-[510] box-border caret-transparent tracking-[-0.12px] outline-transparent">Line</span>
                  </div>
                  {/* Table Rows */}
                  {selected.issues.map((issue, idx) => (
                    <div
                      key={idx}
                      className="items-center box-border caret-transparent gap-x-4 grid grid-cols-[80px_80px_1fr_60px] outline-transparent p-3 border-b border-white/5 border-solid last:border-b-0"
                    >
                      <span className="text-slate-300 text-[13px] box-border caret-transparent tracking-[-0.13px] outline-transparent">
                        {issue.type === "Security" && "🔒"} {issue.type === "Bug Risk" && "🐛"} {issue.type === "Performance" && "⚡"} {issue.type}
                      </span>
                      <span className={`text-[13px] font-[510] box-border caret-transparent tracking-[-0.13px] outline-transparent ${issue.severity === "High" ? "text-red-400" : issue.severity === "Medium" ? "text-amber-300" : "text-green-400"}`}>
                        {issue.severity}
                      </span>
                      <span className="text-neutral-400 text-[13px] box-border caret-transparent tracking-[-0.13px] leading-[19.5px] outline-transparent">
                        {issue.description}
                      </span>
                      <span className="text-neutral-500 text-[13px] box-border caret-transparent tracking-[-0.13px] outline-transparent font-berkeley_mono">
                        L{issue.line}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Sample Review Output */}
            <div className="box-border caret-transparent outline-transparent">
              <h3 className="text-[15px] font-[510] box-border caret-transparent tracking-[-0.165px] outline-transparent mb-3">
                Review Output
              </h3>
              <div className="relative bg-[linear-gradient(134deg,rgba(255,255,255,0.08),rgba(255,255,255,0.02),rgba(255,255,255,0)_55%)] box-border caret-transparent isolate outline-transparent overflow-hidden rounded-[10px] border border-white/10 border-solid">
                {/* Terminal Header */}
                <div className="items-center bg-zinc-900/60 box-border caret-transparent flex outline-transparent gap-x-2 px-4 py-3 border-b border-white/5 border-solid">
                  <div className="bg-red-500/80 box-border caret-transparent h-3 outline-transparent w-3 rounded-full"></div>
                  <div className="bg-amber-500/80 box-border caret-transparent h-3 outline-transparent w-3 rounded-full"></div>
                  <div className="bg-green-500/80 box-border caret-transparent h-3 outline-transparent w-3 rounded-full"></div>
                  <span className="text-neutral-500 text-[12px] box-border caret-transparent tracking-[-0.12px] outline-transparent ml-2 font-berkeley_mono">
                    AgenticPR Review — #{selected.number}
                  </span>
                </div>
                {/* Terminal Content */}
                <div className="box-border caret-transparent outline-transparent px-4 py-4 font-berkeley_mono text-[13px] leading-[22px]">
                  <div className="text-green-400 box-border caret-transparent outline-transparent">
                    🦅 Axiom Ultra Code Review
                  </div>
                  <div className="box-border caret-transparent outline-transparent mt-2">
                    <span className="text-slate-300">🚦 Verdict: </span>
                    <span className={`${getVerdictStyles(selected.verdict).text} font-[510]`}>{selected.verdict}</span>
                  </div>
                  <div className="bg-zinc-800 box-border caret-transparent shrink-0 h-px outline-transparent w-full my-3 rounded-full"></div>
                  <div className="text-slate-400 box-border caret-transparent outline-transparent mb-2">🔥 Risk Assessment</div>
                  <div className="box-border caret-transparent grid grid-cols-2 gap-1 outline-transparent pl-4 text-[12px]">
                    <span className="text-neutral-500">Security Risk:</span>
                    <span className={selected.riskLevel === "high" ? "text-red-400" : selected.riskLevel === "medium" ? "text-amber-300" : "text-green-400"}>
                      {selected.riskLevel === "high" ? "High" : selected.riskLevel === "medium" ? "Medium" : "Low"}
                    </span>
                    <span className="text-neutral-500">Reliability Risk:</span>
                    <span className="text-green-400">Low</span>
                    <span className="text-neutral-500">Maintainability:</span>
                    <span className={selected.riskLevel === "high" ? "text-amber-300" : "text-green-400"}>
                      {selected.riskLevel === "high" ? "Medium" : "Low"}
                    </span>
                  </div>
                  {selected.issues.length > 0 && (
                    <>
                      <div className="bg-zinc-800 box-border caret-transparent shrink-0 h-px outline-transparent w-full my-3 rounded-full"></div>
                      {selected.issues.map((issue, i) => (
                        <div key={i} className={`${issue.severity === "High" ? "text-red-400" : "text-amber-300"} box-border caret-transparent outline-transparent mt-1`}>
                          {issue.severity === "High" ? "🔴" : "🟡"} [{issue.type}] {issue.description} at line {issue.line}
                        </div>
                      ))}
                    </>
                  )}
                  {selected.issues.length === 0 && (
                    <>
                      <div className="bg-zinc-800 box-border caret-transparent shrink-0 h-px outline-transparent w-full my-3 rounded-full"></div>
                      <div className="text-green-400 box-border caret-transparent outline-transparent">
                        ✅ No critical issues found. Code is clean and well-structured.
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
};
