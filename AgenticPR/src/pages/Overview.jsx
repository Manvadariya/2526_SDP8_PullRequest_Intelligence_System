import React from 'react';
import { ShieldAlert, CheckCircle2, GitPullRequestDraft, Loader2 } from 'lucide-react';
import useRepoStats from '../hooks/useRepoStats';

export default function Overview() {
  const { stats, loading, error } = useRepoStats();

  const activeIssues = stats?.active_issues || 0;
  const issuesPrevented = stats?.issues_prevented || 0;
  const latestJob = stats?.latest_job;
  const commitShort = latestJob?.commit_sha?.substring(0, 8) || '—';

  const cats = stats?.categories || {};
  const securityIssues = cats.security || 0;

  const languages = stats?.languages || [];

  const langBadges = {
    JavaScript: { label: 'JS', bg: '#f1e05a', text: 'black', border: 'border-yellow-400' },
    TypeScript: { label: 'TS', bg: '#3178c6', text: 'white', border: '' },
    Python: { label: 'Py', bg: '#3572A5', text: 'white', border: '' },
    Java: { label: 'Ja', bg: '#b07219', text: 'white', border: '' },
    Go: { label: 'Go', bg: '#00add8', text: 'black', border: '' },
    Rust: { label: 'Rs', bg: '#dea584', text: 'black', border: '' },
    C: { label: 'C', bg: '#555555', text: 'white', border: '' },
    'C++': { label: 'C+', bg: '#f34b7d', text: 'white', border: '' },
    Ruby: { label: 'Rb', bg: '#701516', text: 'white', border: '' },
    PHP: { label: 'PH', bg: '#4F5D95', text: 'white', border: '' },
    Shell: { label: 'Sh', bg: '#89e051', text: 'black', border: '' },
  };

  const timeAgo = (iso) => {
    if (!iso) return '';
    const d = new Date(iso);
    return isNaN(d.getTime()) ? '' : d.toLocaleString(undefined, {
      month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-130px)] bg-[#0E1116]">
        <Loader2 className="w-6 h-6 animate-spin text-[#58a6ff]" />
        <span className="ml-2 text-[#8B949E]">Loading overview...</span>
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
    <div className="flex bg-[#0E1116] h-[calc(100vh-130px)] p-6 overflow-y-auto">
      <div className="max-w-[1200px] w-full mx-auto flex flex-col gap-6">

        {/* Overview Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

          {/* Summary Panel */}
          <div className="bg-[#161B22] border border-[#30363D] rounded-lg p-5 flex flex-col justify-between min-h-[250px]">
            <div>
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h3 className="text-xs font-semibold text-[#8B949E] uppercase tracking-wider mb-1">ACTIVE ISSUES</h3>
                  <span className="text-2xl font-bold text-[#E6EDF3]">{activeIssues}</span>
                </div>
                <div>
                  <h3 className="text-xs font-semibold text-[#8B949E] uppercase tracking-wider mb-1">ISSUES PREVENTED</h3>
                  <span className="text-2xl font-bold text-[#E6EDF3]">{issuesPrevented}</span>
                </div>
              </div>

              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-xs font-semibold text-[#8B949E] uppercase tracking-wider mb-1">TOTAL REVIEWS</h3>
                  <div className="flex items-center gap-1.5 text-sm text-[#E6EDF3]">
                    <CheckCircle2 size={14} className="text-[#3fb950]" />
                    {stats?.total_reviews || 0}
                  </div>
                </div>
                <div>
                  <h3 className="text-xs font-semibold text-[#8B949E] uppercase tracking-wider mb-2">LANGUAGES</h3>
                  <div className="flex items-center gap-1 flex-wrap">
                    {languages.length > 0 ? languages.map(lang => {
                      const badge = langBadges[lang] || { label: lang.substring(0, 2), bg: '#30363D', text: 'white', border: '' };
                      return (
                        <div key={lang} className={`w-5 h-5 rounded flex items-center justify-center text-[10px] font-bold ${badge.border}`}
                          style={{ backgroundColor: badge.bg, color: badge.text }}>
                          {badge.label}
                        </div>
                      );
                    }) : (
                      <span className="text-xs text-[#8B949E]">—</span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-8 pt-4 border-t border-[#30363D] flex items-center justify-between text-sm">
              <div className="flex items-center gap-2 text-[#8B949E]">
                {latestJob?.status === 'success' ? (
                  <span className="text-[#3fb950]">✓</span>
                ) : latestJob?.status === 'failure' ? (
                  <span className="text-[#f85149]">✕</span>
                ) : (
                  <span className="text-[#8B949E]">—</span>
                )}
                Last analyzed
              </div>
              <div className="flex items-center gap-3">
                <span className="font-mono text-xs bg-[#21262D] px-1.5 py-0.5 rounded text-[#E6EDF3] flex items-center gap-1">
                  <GitPullRequestDraft size={12} className="text-[#8B949E]" /> {commitShort}
                </span>
                <span className="text-[#8B949E]">{timeAgo(latestJob?.created_at)}</span>
              </div>
            </div>
          </div>

          {/* Security Overview panel */}
          <div className="bg-[#161B22] border border-[#30363D] rounded-lg p-5 min-h-[250px] flex flex-col relative">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <h3 className="text-[15px] font-semibold text-[#E6EDF3]">Security Overview</h3>
                <div className="w-4 h-4 rounded-full bg-[#21262D] flex items-center justify-center text-[10px] text-[#8B949E] cursor-help">?</div>
              </div>
            </div>
            <div className="flex items-center gap-3 mb-6">
              <span className={`flex items-center gap-1.5 px-2 py-0.5 rounded-full border ${securityIssues > 0 ? 'border-red-900/50 text-[#f85149]' : 'border-green-900/50 text-[#3fb950]'} bg-[#161B22] text-[10px] font-bold tracking-wider`}>
                <div className={`w-1.5 h-1.5 rounded-full ${securityIssues > 0 ? 'bg-[#f85149]' : 'bg-[#3fb950]'}`}></div>
                {securityIssues > 0 ? 'ISSUES FOUND' : 'PASSING'}
              </span>
              <span className="text-sm font-medium text-[#E6EDF3] flex items-center gap-1">
                <ShieldAlert size={14} className="text-[#8B949E]" /> {securityIssues} security issue{securityIssues !== 1 ? 's' : ''}
              </span>
            </div>

            {/* Review summary stats */}
            <div className="flex-1 flex flex-col justify-end gap-3 mt-4">
              <div className="flex items-center justify-between text-sm">
                <span className="text-[#8B949E]">Total reviews</span>
                <span className="text-[#E6EDF3] font-semibold">{stats?.total_reviews || 0}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-[#8B949E]">Succeeded</span>
                <span className="text-[#3fb950] font-semibold">{stats?.succeeded || 0}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-[#8B949E]">Failed</span>
                <span className="text-[#f85149] font-semibold">{stats?.failed || 0}</span>
              </div>
              {stats?.total_reviews > 0 && (
                <div className="mt-2">
                  <div className="flex items-center justify-between text-xs text-[#8B949E] mb-1">
                    <span>Success rate</span>
                    <span>{Math.round((stats.succeeded / stats.total_reviews) * 100)}%</span>
                  </div>
                  <div className="w-full h-2 bg-[#21262D] rounded-full overflow-hidden">
                    <div className="h-full bg-[#3fb950] rounded-full" style={{ width: `${(stats.succeeded / stats.total_reviews) * 100}%` }}></div>
                  </div>
                </div>
              )}
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}