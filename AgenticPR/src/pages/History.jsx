import React, { useState } from 'react';
import {
  GitPullRequest,
  Search,
  CheckCircle2,
  Zap,
  Loader2,
  X,
  AlertCircle,
  Rocket
} from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import { useResolveRepo, usePullRequests, useTriggerReview, useJobs } from '../hooks/useApiCache';


export default function History() {
  const { repoName } = useParams();
  const { owner, repo } = useResolveRepo(repoName);
  const [filter, setFilter] = useState('open');
  const [searchTerm, setSearchTerm] = useState('');
  const { data: openPRs = [], isLoading: loadingOpen } = usePullRequests(owner, repo, 'open');
  const { data: closedPRs = [], isLoading: loadingClosed } = usePullRequests(owner, repo, 'closed');
  const pullRequests = filter === 'open' ? openPRs : closedPRs;
  const loading = filter === 'open' ? loadingOpen : loadingClosed;
  const triggerReview = useTriggerReview();
  const [triggeringPRs, setTriggeringPRs] = useState(new Set());
  const [toast, setToast] = useState(null);
  const { data: allJobs = [] } = useJobs();

  // Find the latest job for a specific PR
  const getJobForPR = (prNumber) => {
    const repoFullName = owner && repo ? `${owner}/${repo}` : '';
    return allJobs.find(
      j => j.repo_full_name === repoFullName && j.pr_number === prNumber
    ) || null;
  };


  const timeAgo = (dateStr) => {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return isNaN(d.getTime()) ? '' : d.toLocaleString(undefined, {
      month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  };


  const filteredPRs = pullRequests
    .filter(pr =>
      pr.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      `#${pr.number}`.includes(searchTerm)
    )
    .sort((a, b) => b.number - a.number);


  const openCount = openPRs.length;
  const closedCount = closedPRs.length;

  const showToast = (type, title, message) => {
    setToast({ type, title, message });
    setTimeout(() => setToast(null), 5000);
  };

  const handleTriggerReview = async (e, pr) => {
    e.preventDefault();
    e.stopPropagation();

    setTriggeringPRs(prev => new Set(prev).add(pr.number));

    try {
      await triggerReview.mutateAsync({
        owner,
        repo,
        prNumber: pr.number,
        commitSha: pr.head_sha,
      });

      showToast(
        'success',
        'Review Triggered!',
        `AI review has been queued for PR #${pr.number}. You'll see the results on GitHub shortly.`
      );
    } catch (error) {
      showToast(
        'error',
        'Review Failed',
        `Could not trigger review for PR #${pr.number}: ${error.message}`
      );
    } finally {
      setTriggeringPRs(prev => {
        const next = new Set(prev);
        next.delete(pr.number);
        return next;
      });
    }
  };


  return (
    <div className="flex bg-[#0E1116] h-[calc(100vh-130px)]">

      {/* Toast Notification */}
      {toast && (
        <div className="fixed top-6 right-6 z-50 animate-[slideIn_0.3s_ease-out]">
          <div className={`flex items-start gap-3 p-4 rounded-xl border shadow-2xl backdrop-blur-sm min-w-[340px] max-w-[420px] ${toast.type === 'success'
            ? 'bg-[#0d1f17]/95 border-[#238636]/40 shadow-[#238636]/10'
            : 'bg-[#2d1117]/95 border-[#da3633]/40 shadow-[#da3633]/10'
            }`}>
            <div className={`p-2 rounded-lg shrink-0 ${toast.type === 'success' ? 'bg-[#238636]/20' : 'bg-[#da3633]/20'
              }`}>
              {toast.type === 'success' ? (
                <Rocket size={20} className="text-[#3fb950]" />
              ) : (
                <AlertCircle size={20} className="text-[#f85149]" />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <h4 className={`text-sm font-semibold mb-0.5 ${toast.type === 'success' ? 'text-[#3fb950]' : 'text-[#f85149]'
                }`}>{toast.title}</h4>
              <p className="text-xs text-[#8B949E] leading-relaxed">{toast.message}</p>
            </div>
            <button
              onClick={() => setToast(null)}
              className="text-[#8B949E] hover:text-[#E6EDF3] transition-colors shrink-0 mt-0.5"
            >
              <X size={14} />
            </button>
          </div>
        </div>
      )}

      <style>{`
        @keyframes slideIn {
          from { opacity: 0; transform: translateX(40px); }
          to { opacity: 1; transform: translateX(0); }
        }
      `}</style>

      {/* Sidebar: Filters */}
      <div className="w-[240px] border-r border-[#30363D] shrink-0 overflow-y-auto pt-4 flex flex-col px-3">

        <div className="mb-6">
          <div className="flex items-center gap-2 text-[#E6EDF3] font-medium mb-1 px-3 py-1.5 hover:bg-[#161B22] rounded-md cursor-pointer transition-colors">
            <GitPullRequest size={16} className="text-[#8B949E] rotate-[90deg]" />
            <span>Pull requests</span>
            <span className="ml-auto text-xs font-semibold bg-[#21262D] px-1.5 py-[1px] rounded">{openCount + closedCount}</span>
          </div>

          <div className="pl-6 space-y-0.5 border-l border-[#30363D] ml-5">
            <button
              onClick={() => setFilter('open')}
              className={`w-full flex justify-between items-center text-left text-[13px] font-medium px-3 py-1.5 rounded-md ${filter === 'open'
                ? 'text-[#E6EDF3] bg-[#161B22] -ml-px border-l-2 border-[#3fb950]'
                : 'text-[#8B949E] hover:text-[#E6EDF3] hover:bg-[#161B22] ml-[1px]'
                }`}
            >
              Open
              <span className="text-xs font-semibold">{openCount}</span>
            </button>
            <button
              onClick={() => setFilter('closed')}
              className={`w-full flex justify-between items-center text-left text-[13px] px-3 py-1.5 rounded-md ${filter === 'closed'
                ? 'text-[#E6EDF3] bg-[#161B22] -ml-px border-l-2 border-[#3fb950] font-medium'
                : 'text-[#8B949E] hover:text-[#E6EDF3] hover:bg-[#161B22] ml-[1px]'
                }`}
            >
              Closed
              <span className="text-xs font-semibold">{closedCount}</span>
            </button>
          </div>
        </div>
      </div>


      {/* Main Content Area */}
      <div className="flex-1 min-w-0 bg-[#0E1116] p-4 flex flex-col">

        {/* Search */}
        <div className="relative mb-4 shrink-0">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8B949E]" />
          <input
            type="text"
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            placeholder="Search pull request titles or numbers..."
            className="w-full bg-[#161B22] border border-[#30363D] rounded-lg py-2 pl-9 pr-3 text-sm text-[#E6EDF3] placeholder-[#8B949E] focus:outline-none focus:border-[#58a6ff] focus:ring-1 focus:ring-[#58a6ff]"
          />
        </div>


        {/* PR List */}
        <div className="flex-1 overflow-y-auto w-full">
          {loading ? (
            <div className="flex items-center justify-center h-40 text-[#8B949E] text-sm">Loading pull requests...</div>
          ) : filteredPRs.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-40 text-[#8B949E] text-sm">
              <GitPullRequest size={32} className="mb-2 opacity-40" />
              <span>No {filter} pull requests found{searchTerm ? ` matching "${searchTerm}"` : ''}.</span>
            </div>
          ) : (
            filteredPRs.map((pr) => (
              <Link
                to={`/repositories/${repoName}/pr/${pr.number}`}
                key={pr.number}
                className="flex border border-transparent hover:border-[#30363D] border-b-[#30363D] transition-colors p-4 group cursor-pointer hover:bg-[#161B22]/50"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    {pr.state === 'open' ? (
                      <GitPullRequest size={14} className="text-[#3fb950]" />
                    ) : (
                      <CheckCircle2 size={14} className="text-[#a371f7]" />
                    )}
                    <h3 className="text-[15px] font-semibold text-[#E6EDF3] group-hover:text-[#58a6ff] transition-colors">
                      <span className="text-[#8B949E] font-normal mr-1">#{pr.number}</span>
                      {pr.title}
                    </h3>
                  </div>

                  <div className="flex items-center gap-3 pl-5.5 text-[13px] text-[#8B949E]">
                    <span>{timeAgo(pr.created_at)}</span>
                    <span>by {pr.author}</span>
                    <span className="text-xs">{pr.head_branch} → {pr.base_branch}</span>
                    {(pr.additions > 0 || pr.deletions > 0) && (
                      <span className="flex items-center gap-1 text-xs">
                        <span className="text-[#3fb950]">+{pr.additions}</span>
                        <span className="text-[#f85149]">-{pr.deletions}</span>
                      </span>
                    )}
                  </div>
                </div>


                <div className="flex items-center gap-2 shrink-0">
                  {/* Live Review Status Badge */}
                  {(() => {
                    const job = getJobForPR(pr.number);
                    if (!job) return null;
                    if (job.status === 'processing') return (
                      <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-[#0d419d]/20 border border-[#58a6ff]/30 text-[#58a6ff] animate-pulse">
                        <Loader2 size={12} className="animate-spin" />
                        Reviewing...
                      </span>
                    );
                    if (job.status === 'queued') return (
                      <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-[#6e4e00]/20 border border-[#d29922]/30 text-[#d29922]">
                        <span className="w-1.5 h-1.5 rounded-full bg-[#d29922] animate-pulse"></span>
                        Queued
                      </span>
                    );
                    if (job.status === 'success') return (
                      <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-[#238636]/15 border border-[#238636]/30 text-[#3fb950]">
                        <CheckCircle2 size={12} />
                        Reviewed
                      </span>
                    );
                    if (job.status === 'failure') return (
                      <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-[#da3633]/15 border border-[#da3633]/30 text-[#f85149]">
                        <AlertCircle size={12} />
                        Failed
                      </span>
                    );
                    return null;
                  })()}
                  {/* Trigger Review Button - ONLY for open PRs */}
                  {pr.state === 'open' && (
                    <button
                      onClick={(e) => handleTriggerReview(e, pr)}
                      disabled={triggeringPRs.has(pr.number)}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-[#21262d] hover:bg-[#30363d] border border-[#30363D] rounded-md text-[13px] font-medium text-[#E6EDF3] transition-colors disabled:opacity-50 disabled:cursor-not-allowed group/btn"
                      title="Trigger AI Review"
                    >
                      {triggeringPRs.has(pr.number) ? (
                        <>
                          <Loader2 size={14} className="animate-spin" />
                          <span>Triggering...</span>
                        </>
                      ) : (
                        <>
                          <Zap size={14} className="text-[#58a6ff] group-hover/btn:text-[#79c0ff]" />
                          <span>Review</span>
                        </>
                      )}
                    </button>
                  )}


                  {/* Status Badge */}
                  {pr.state === 'open' ? (
                    <span className="flex items-center gap-1.5 px-3 py-1.5 bg-transparent border border-[#3fb950]/20 rounded-full text-[13px] font-semibold text-[#3fb950]">
                      <GitPullRequest size={14} /> Open
                    </span>
                  ) : pr.merged_at ? (
                    <span className="flex items-center gap-1.5 px-3 py-1.5 bg-transparent border border-[#a371f7]/20 rounded-full text-[13px] font-semibold text-[#a371f7]">
                      <CheckCircle2 size={14} /> Merged
                    </span>
                  ) : (
                    <span className="flex items-center gap-1.5 px-3 py-1.5 bg-transparent border border-[#f85149]/20 rounded-full text-[13px] font-semibold text-[#f85149]">
                      <X size={14} /> Closed
                    </span>
                  )}
                </div>
              </Link>
            ))
          )}
        </div>


      </div>
    </div>
  );
}
