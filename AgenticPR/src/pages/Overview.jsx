import React from 'react';
import { Activity, ShieldAlert, Code2, AlertTriangle, Bug, FileCheck, CheckCircle2, GitPullRequestDraft, Loader2 } from 'lucide-react';
import useRepoStats from '../hooks/useRepoStats';

export default function Overview() {
  const { stats, loading, error } = useRepoStats();

  const cats = stats?.categories || {};
  const summaryCards = [
    { title: "Performance Issues", count: cats.performance || 0, icon: Activity },
    { title: "Style Issues", count: cats.style || 0, icon: Code2 },
    { title: "Documentation Issues", count: cats.documentation || 0, icon: FileCheck },
    { title: "Anti patterns", count: cats.anti_pattern || 0, icon: AlertTriangle },
    { title: "Security issues", count: cats.security || 0, icon: ShieldAlert },
    { title: "Bug risk", count: cats.bug_risk || 0, icon: Bug }
  ];

  const activeIssues = stats?.active_issues || 0;
  const issuesPrevented = stats?.issues_prevented || 0;
  const latestJob = stats?.latest_job;
  const commitShort = latestJob?.commit_sha?.substring(0, 7) || '—';
  const securityIssues = cats.security || 0;
  const languages = stats?.languages || [];

  const langBadges = {
    JavaScript: { label: 'JS', bg: '#f1e05a', text: 'black', border: 'border-yellow-400' },
    TypeScript: { label: 'TS', bg: '#3178c6', text: 'white', border: '' },
    Python:     { label: 'Py', bg: '#3572A5', text: 'white', border: '' },
    Java:       { label: 'Ja', bg: '#b07219', text: 'white', border: '' },
    Go:         { label: 'Go', bg: '#00add8', text: 'black', border: '' },
    Rust:       { label: 'Rs', bg: '#dea584', text: 'black', border: '' },
    C:          { label: 'C',  bg: '#555555', text: 'white', border: '' },
    'C++':      { label: 'C+', bg: '#f34b7d', text: 'white', border: '' },
    Ruby:       { label: 'Rb', bg: '#701516', text: 'white', border: '' },
    PHP:        { label: 'PH', bg: '#4F5D95', text: 'white', border: '' },
    Shell:      { label: 'Sh', bg: '#89e051', text: 'black', border: '' },
  };

  const timeAgo = (iso) => {
    if (!iso) return '';
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  };

  // Category distribution for the chart section
  const categoryDistribution = Object.entries(cats)
    .filter(([, v]) => v > 0)
    .map(([k, v]) => ({ name: k.replace('_', ' '), count: v }));
  const totalCatIssues = categoryDistribution.reduce((s, c) => s + c.count, 0);

  const catColors = {
    'bug risk': '#f85149',
    'anti pattern': '#d29922',
    'security': '#da3633',
    'performance': '#58a6ff',
    'style': '#8b949e',
    'documentation': '#3fb950',
    'coverage': '#a371f7',
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
        
        {/* Top Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          
          {/* Main Stats Grid */}
          <div className="md:col-span-2 grid grid-cols-2 md:grid-cols-3 gap-[1px] bg-[#30363D] border border-[#30363D] rounded-lg overflow-hidden shrink-0">
            {summaryCards.map((card, i) => {
              const hasIssues = card.count > 0;
              return (
                <div key={i} className="bg-[#161B22] p-5 flex flex-col justify-between aspect-[2/1] min-h-[120px]">
                  <div className="flex items-center gap-2 text-[#E6EDF3] text-sm font-medium">
                    <card.icon size={16} className={hasIssues ? "text-[#E6EDF3]" : "text-[#8B949E]"} />
                    <span>{card.title}</span>
                  </div>
                  <span className={`text-2xl font-semibold mt-4 ${hasIssues ? 'text-[#E6EDF3]' : 'text-[#8B949E]'}`}>
                    {card.count}
                  </span>
                </div>
              );
            })}
          </div>

          {/* Right Summary Panel */}
          <div className="bg-[#161B22] border border-[#30363D] rounded-lg p-5 flex flex-col justify-between">
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
                        const badge = langBadges[lang] || { label: lang.substring(0,2), bg: '#30363D', text: 'white', border: '' };
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
                        <GitPullRequestDraft size={12} className="text-[#8B949E]"/> {commitShort}
                    </span>
                    <span className="text-[#8B949E]">{timeAgo(latestJob?.created_at)}</span>
                </div>
            </div>
          </div>
        </div>

        {/* Bottom Charts Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* OWASP / Security panel */}
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
                        <ShieldAlert size={14} className="text-[#8B949E]"/> {securityIssues} security issue{securityIssues !== 1 ? 's' : ''}
                    </span>
                </div>
                
                {/* Review summary stats */}
                <div className="flex-1 flex flex-col gap-3">
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

            {/* Issue Distribution by Category */}
            <div className="bg-[#161B22] border border-[#30363D] rounded-lg p-5 min-h-[250px] flex flex-col">
                <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                        <h3 className="text-[15px] font-semibold text-[#E6EDF3]">Issue Distribution by Category</h3>
                    </div>
                </div>
                <div className="flex items-center gap-3 mb-6">
                    <span className="text-sm font-medium text-[#E6EDF3] flex items-center gap-1">
                        <Activity size={14} className="text-[#8B949E]"/> {activeIssues} active issue{activeIssues !== 1 ? 's' : ''}
                    </span>
                </div>

                {categoryDistribution.length > 0 ? (
                  <div className="flex-1 flex flex-col gap-3">
                    {/* Stacked bar */}
                    <div className="w-full h-3 bg-[#21262D] rounded-full overflow-hidden flex">
                      {categoryDistribution.map((cat, i) => (
                        <div key={i} className="h-full" style={{ width: `${(cat.count / totalCatIssues) * 100}%`, backgroundColor: catColors[cat.name] || '#8B949E' }}></div>
                      ))}
                    </div>
                    {/* Legend */}
                    <div className="flex flex-col gap-2 mt-2">
                      {categoryDistribution.map((cat, i) => (
                        <div key={i} className="flex items-center justify-between text-sm">
                          <div className="flex items-center gap-2">
                            <div className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: catColors[cat.name] || '#8B949E' }}></div>
                            <span className="text-[#E6EDF3] capitalize">{cat.name}</span>
                          </div>
                          <span className="text-[#8B949E] font-semibold">{cat.count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="flex-1 flex items-center justify-center">
                    <div className="text-sm text-[#8B949E]">No issues found yet. Run a PR review to see results.</div>
                  </div>
                )}
            </div>
        </div>

      </div>
    </div>
  );
}
