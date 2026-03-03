import React, { useState, useEffect, useMemo } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useJobs } from "../hooks/useApiCache";

export const PRVisualize = () => {
  const { authFetch } = useAuth();
  const { data: jobsList = [], isLoading: jobsLoading } = useJobs();
  const [prs, setPrs] = useState([]);
  const [selected, setSelected] = useState(null);
  const [viewMode, setViewMode] = useState("list");
  const [loading, setLoading] = useState(true);

  // Once jobs are cached, fetch details for each (these get cached individually too)
  useEffect(() => {
    if (jobsLoading) return;
    if (jobsList.length === 0) { setLoading(false); return; }

    const fetchDetails = async () => {
      try {
        const prData = await Promise.all(
          jobsList.slice(0, 20).map(async (job) => {
            try {
              const detailRes = await authFetch(`/api/jobs/${job.id}`);
              const detail = await detailRes.json();
              const results = (detail.results || []).map(r => ({
                ...r,
                output: typeof r.output_json === 'string' ? JSON.parse(r.output_json) : r.output_json
              }));

              const reviewResult = results.find(r => r.agent_name === 'reviewer' || r.agent_name === 'mcp_reviewer');
              const output = reviewResult?.output || {};

              const verdict = output.verdict || (job.status === 'success' ? 'APPROVE' : 'COMMENT');
              const inlineComments = output.inline_comments || 0;
              const filesChanged = output.file_count || output.files_reviewed || 0;

              return {
                id: job.id,
                number: job.pr_number,
                title: `PR #${job.pr_number}`,
                author: job.repo_full_name?.split('/')[0] || 'unknown',
                repo: job.repo_full_name || 'unknown',
                status: job.status,
                verdict: verdict,
                riskLevel: verdict === 'REQUEST_CHANGES' ? 'high' : verdict === 'COMMENT' && inlineComments > 0 ? 'medium' : 'low',
                riskColor: verdict === 'REQUEST_CHANGES' ? 'text-red-400' : verdict === 'COMMENT' && inlineComments > 0 ? 'text-amber-300' : 'text-green-400',
                riskBg: verdict === 'REQUEST_CHANGES' ? 'bg-red-400/10' : verdict === 'COMMENT' && inlineComments > 0 ? 'bg-amber-300/10' : 'bg-green-400/10',
                filesChanged: filesChanged,
                additions: 0,
                deletions: 0,
                reviewTime: 'N/A',
                createdAt: job.created_at ? new Date(job.created_at).toLocaleString() : 'unknown',
                issues: inlineComments,
                commitSha: job.commit_sha,
                agents: output.mode ? [`MCP (${output.mode})`] : ['Apex Reviewer'],
              };
            } catch {
              return null;
            }
          })
        );

        const validPrs = prData.filter(Boolean).sort((a, b) => b.number - a.number);
        setPrs(validPrs);
        if (validPrs.length > 0) setSelected(validPrs[0]);
      } catch (err) {
        console.error('Failed to fetch PR reviews:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchDetails();
  }, [jobsList, jobsLoading, authFetch]);

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

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-8 h-8 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
            <p className="text-neutral-400 ml-3">Loading reviews...</p>
          </div>
        ) : prs.length === 0 ? (
          <div className="text-center py-20 text-neutral-400">
            <p className="text-lg">No PR reviews found yet.</p>
            <p className="text-sm mt-2">Reviews will appear here when PRs are analyzed by AgenticPR.</p>
          </div>
        ) : (
        <>
        {/* Stats Overview */}
        <div className="border-b-stone-50 border-l-stone-50 border-r-stone-50 box-border caret-transparent gap-x-4 grid grid-cols-2 outline-transparent gap-y-4 border-t-white/10 border-t border-b-white/10 border-b py-6 mb-8 md:grid-cols-4">
          <div className="box-border caret-transparent outline-transparent">
            <span className="text-neutral-500 text-[13px] box-border caret-transparent block tracking-[-0.13px] leading-[19.5px] outline-transparent mb-1">
              Total Reviews
            </span>
            <span className="text-[28px] font-[538] box-border caret-transparent tracking-[-0.5px] outline-transparent">
              {prs.length}
            </span>
          </div>
          <div className="box-border caret-transparent outline-transparent">
            <span className="text-neutral-500 text-[13px] box-border caret-transparent block tracking-[-0.13px] leading-[19.5px] outline-transparent mb-1">
              Approved
            </span>
            <span className="text-green-400 text-[28px] font-[538] box-border caret-transparent tracking-[-0.5px] outline-transparent">
              {prs.filter((p) => p.verdict === "APPROVE").length}
            </span>
          </div>
          <div className="box-border caret-transparent outline-transparent">
            <span className="text-neutral-500 text-[13px] box-border caret-transparent block tracking-[-0.13px] leading-[19.5px] outline-transparent mb-1">
              Changes Requested
            </span>
            <span className="text-red-400 text-[28px] font-[538] box-border caret-transparent tracking-[-0.5px] outline-transparent">
              {prs.filter((p) => p.verdict === "REQUEST_CHANGES").length}
            </span>
          </div>
          <div className="box-border caret-transparent outline-transparent">
            <span className="text-neutral-500 text-[13px] box-border caret-transparent block tracking-[-0.13px] leading-[19.5px] outline-transparent mb-1">
              Repos Covered
            </span>
            <span className="text-[28px] font-[538] box-border caret-transparent tracking-[-0.5px] outline-transparent">
              {new Set(prs.map(p => p.repo)).size}
            </span>
          </div>
        </div>

        {/* View Mode Toggle */}
        <div className="flex items-center gap-2 mb-6">
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
            {prs.map((pr) => {
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
                  {typeof selected.issues === 'number' ? selected.issues : selected.issues?.length || 0}
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
                    🤖 {agent}
                  </span>
                ))}
              </div>
            </div>

            {/* Issues Summary */}
            {(typeof selected.issues === 'number' ? selected.issues > 0 : selected.issues?.length > 0) && (
              <div className="box-border caret-transparent outline-transparent mb-8">
                <h3 className="text-[15px] font-[510] box-border caret-transparent tracking-[-0.165px] outline-transparent mb-3">
                  Issues Found
                </h3>
                <div className="box-border caret-transparent outline-transparent border border-white/10 rounded-lg border-solid overflow-hidden p-4">
                  <p className="text-neutral-400 text-[13px]">
                    {typeof selected.issues === 'number' ? selected.issues : selected.issues?.length || 0} inline comment(s) posted on this PR review.
                    <Link to={`/scan/${selected.id}`} className="text-blue-400 hover:underline ml-2">View full scan details →</Link>
                  </p>
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
                  {(typeof selected.issues === 'number' ? selected.issues > 0 : selected.issues?.length > 0) && (
                    <>
                      <div className="bg-zinc-800 box-border caret-transparent shrink-0 h-px outline-transparent w-full my-3 rounded-full"></div>
                      <div className="text-amber-300 box-border caret-transparent outline-transparent mt-1">
                        ⚠️ {typeof selected.issues === 'number' ? selected.issues : selected.issues?.length || 0} issue(s) found — see inline comments on the PR.
                      </div>
                    </>
                  )}
                  {(typeof selected.issues === 'number' ? selected.issues === 0 : !selected.issues?.length) && (
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
        </>
        )}
      </div>
    </section>
  );
};

export default PRVisualize;
