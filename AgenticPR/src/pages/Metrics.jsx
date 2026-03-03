import React, { useState } from 'react';
import { Loader2, CheckCircle2, XCircle, Activity, TrendingUp, GitPullRequest, Bug } from 'lucide-react';
import useRepoStats from '../hooks/useRepoStats';

export default function Metrics() {
  const { stats, loading, error } = useRepoStats();
  const [activeTab, setActiveTab] = useState('Review Summary');

  const tabs = [
    'Review Summary',
    'Issue Breakdown',
    'Review Timeline',
  ];

  const totalReviews = stats?.total_reviews || 0;
  const succeeded = stats?.succeeded || 0;
  const failed = stats?.failed || 0;
  const activeIssues = stats?.active_issues || 0;
  const issuesPrevented = stats?.issues_prevented || 0;
  const successRate = totalReviews > 0 ? Math.round((succeeded / totalReviews) * 100) : 0;
  const cats = stats?.categories || {};

  const categoryRows = [
    { name: 'Bug Risk', count: cats.bug_risk || 0, color: '#f85149' },
    { name: 'Anti-pattern', count: cats.anti_pattern || 0, color: '#d29922' },
    { name: 'Security', count: cats.security || 0, color: '#da3633' },
    { name: 'Performance', count: cats.performance || 0, color: '#58a6ff' },
    { name: 'Style', count: cats.style || 0, color: '#8B949E' },
    { name: 'Documentation', count: cats.documentation || 0, color: '#3fb950' },
  ];

  const maxCatCount = Math.max(...categoryRows.map(c => c.count), 1);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-130px)] bg-[#0E1116]">
        <Loader2 className="w-6 h-6 animate-spin text-[#58a6ff]" />
        <span className="ml-2 text-[#8B949E]">Loading metrics...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-130px)] bg-[#0E1116]">
        <span className="text-[#f85149]">Error: {error}</span>
      </div>
    );
  }

  return (
    <div className="flex bg-[#0E1116] h-[calc(100vh-130px)]">
      {/* Sidebar Navigation */}
      <div className="w-[240px] shrink-0 border-r border-[#30363D] py-4">
        <nav className="flex flex-col gap-[2px] px-3">
          {tabs.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`w-full text-left px-3 py-1.5 rounded-md text-[13px] font-medium transition-colors ${
                activeTab === tab
                  ? 'bg-[#161B22] text-[#E6EDF3] border-l-2 border-[#3fb950] -ml-px pl-[11px]'
                  : 'text-[#8B949E] hover:text-[#E6EDF3] hover:bg-[#161B22]'
              }`}
            >
              {tab}
            </button>
          ))}
        </nav>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 p-6 overflow-y-auto">
        <div className="max-w-[1200px] w-full mx-auto">
          
          {/* Header */}
          <div className="mb-6">
            <h1 className="text-xl font-semibold text-[#E6EDF3] mb-2">{activeTab}</h1>
            <p className="text-[13px] text-[#8B949E]">
              {activeTab === 'Review Summary' && 'Overview of all PR reviews conducted on this repository.'}
              {activeTab === 'Issue Breakdown' && 'Distribution of issues found across categories.'}
              {activeTab === 'Review Timeline' && 'Review activity over time.'}
            </p>
          </div>

          {activeTab === 'Review Summary' && (
            <>
              {/* Stats cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                <div className="bg-[#161B22] border border-[#30363D] rounded-lg p-5">
                  <div className="flex items-center gap-2 text-[#8B949E] text-xs font-semibold uppercase tracking-wider mb-3">
                    <GitPullRequest size={14} />
                    Total Reviews
                  </div>
                  <span className="text-3xl font-bold text-[#E6EDF3]">{totalReviews}</span>
                </div>
                <div className="bg-[#161B22] border border-[#30363D] rounded-lg p-5">
                  <div className="flex items-center gap-2 text-[#8B949E] text-xs font-semibold uppercase tracking-wider mb-3">
                    <CheckCircle2 size={14} className="text-[#3fb950]" />
                    Succeeded
                  </div>
                  <span className="text-3xl font-bold text-[#3fb950]">{succeeded}</span>
                </div>
                <div className="bg-[#161B22] border border-[#30363D] rounded-lg p-5">
                  <div className="flex items-center gap-2 text-[#8B949E] text-xs font-semibold uppercase tracking-wider mb-3">
                    <XCircle size={14} className="text-[#f85149]" />
                    Failed
                  </div>
                  <span className="text-3xl font-bold text-[#f85149]">{failed}</span>
                </div>
                <div className="bg-[#161B22] border border-[#30363D] rounded-lg p-5">
                  <div className="flex items-center gap-2 text-[#8B949E] text-xs font-semibold uppercase tracking-wider mb-3">
                    <TrendingUp size={14} className="text-[#58a6ff]" />
                    Success Rate
                  </div>
                  <span className="text-3xl font-bold text-[#E6EDF3]">{successRate}%</span>
                </div>
              </div>

              {/* Success rate bar */}
              {totalReviews > 0 && (
                <div className="bg-[#161B22] border border-[#30363D] rounded-lg p-5 mb-8">
                  <h3 className="text-[14px] font-medium text-[#E6EDF3] mb-4">Review Success Rate</h3>
                  <div className="w-full h-4 bg-[#21262D] rounded-full overflow-hidden flex">
                    {succeeded > 0 && (
                      <div className="h-full bg-[#3fb950] transition-all" style={{ width: `${successRate}%` }}></div>
                    )}
                    {failed > 0 && (
                      <div className="h-full bg-[#f85149] transition-all" style={{ width: `${100 - successRate}%` }}></div>
                    )}
                  </div>
                  <div className="flex justify-between mt-2 text-xs text-[#8B949E]">
                    <span className="flex items-center gap-1"><span className="w-2 h-2 bg-[#3fb950] rounded-sm"></span> Succeeded ({succeeded})</span>
                    <span className="flex items-center gap-1"><span className="w-2 h-2 bg-[#f85149] rounded-sm"></span> Failed ({failed})</span>
                  </div>
                </div>
              )}

              {/* Issues summary */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-[#161B22] border border-[#30363D] rounded-lg p-5">
                  <div className="flex items-center gap-2 text-[#8B949E] text-xs font-semibold uppercase tracking-wider mb-3">
                    <Bug size={14} />
                    Active Issues
                  </div>
                  <span className="text-3xl font-bold text-[#E6EDF3]">{activeIssues}</span>
                  <p className="text-xs text-[#8B949E] mt-1">Issues found across all reviews</p>
                </div>
                <div className="bg-[#161B22] border border-[#30363D] rounded-lg p-5">
                  <div className="flex items-center gap-2 text-[#8B949E] text-xs font-semibold uppercase tracking-wider mb-3">
                    <Activity size={14} />
                    Issues Prevented
                  </div>
                  <span className="text-3xl font-bold text-[#3fb950]">{issuesPrevented}</span>
                  <p className="text-xs text-[#8B949E] mt-1">Successful reviews that caught issues before merge</p>
                </div>
              </div>

              {totalReviews === 0 && (
                <div className="bg-[#161B22] border border-[#30363D] rounded-lg p-12 mt-8">
                  <div className="flex flex-col items-center justify-center text-center max-w-sm mx-auto">
                    <div className="w-16 h-16 bg-[#21262D] rounded-full flex items-center justify-center mb-6">
                      <GitPullRequest size={32} className="text-[#58a6ff]" />
                    </div>
                    <h2 className="text-lg font-semibold text-[#E6EDF3] mb-2">No reviews yet</h2>
                    <p className="text-[14px] text-[#8B949E]">
                      Create a pull request in this repository to see review metrics here.
                    </p>
                  </div>
                </div>
              )}
            </>
          )}

          {activeTab === 'Issue Breakdown' && (
            <div className="bg-[#161B22] border border-[#30363D] rounded-lg p-6">
              <h3 className="text-[14px] font-medium text-[#E6EDF3] mb-6">Issues by Category</h3>
              {activeIssues > 0 ? (
                <div className="space-y-4">
                  {categoryRows.map((cat, i) => (
                    <div key={i}>
                      <div className="flex items-center justify-between text-sm mb-1">
                        <span className="text-[#E6EDF3]">{cat.name}</span>
                        <span className="text-[#8B949E] font-semibold">{cat.count}</span>
                      </div>
                      <div className="w-full h-2.5 bg-[#21262D] rounded-full overflow-hidden">
                        <div className="h-full rounded-full transition-all" style={{ width: `${(cat.count / maxCatCount) * 100}%`, backgroundColor: cat.color }}></div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-12 text-[#8B949E]">
                  <Bug size={40} className="mb-3 text-[#30363D]" />
                  <p className="text-sm">No issues detected yet.</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'Review Timeline' && (
            <div className="bg-[#161B22] border border-[#30363D] rounded-lg p-6">
              <h3 className="text-[14px] font-medium text-[#E6EDF3] mb-6">Recent Reviews</h3>
              {stats?.latest_job ? (
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-sm border-b border-[#30363D] pb-3">
                    <span className="text-[#8B949E] w-24">Latest</span>
                    <span className="text-[#E6EDF3]">PR #{stats.latest_job.pr_number}</span>
                    <span className="font-mono text-xs bg-[#21262D] px-1.5 py-0.5 rounded text-[#E6EDF3]">{stats.latest_job.commit_sha?.substring(0, 7)}</span>
                    <span className={`text-xs font-semibold ${stats.latest_job.status === 'success' ? 'text-[#3fb950]' : 'text-[#f85149]'}`}>
                      {stats.latest_job.status}
                    </span>
                    <span className="text-[#8B949E] text-xs">{stats.latest_job.created_at ? new Date(stats.latest_job.created_at).toLocaleString() : ''}</span>
                  </div>
                  <p className="text-xs text-[#8B949E] mt-2">Showing data for the most recent review. Historical timeline data accumulates as more PRs are reviewed.</p>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-12 text-[#8B949E]">
                  <Activity size={40} className="mb-3 text-[#30363D]" />
                  <p className="text-sm">No review timeline data available yet.</p>
                </div>
              )}
            </div>
          )}
          
        </div>
      </div>
    </div>
  );
}
