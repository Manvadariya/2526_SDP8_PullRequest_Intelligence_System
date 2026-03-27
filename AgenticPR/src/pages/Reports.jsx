import React, { useState } from 'react';
import { Loader2, ShieldAlert, Bug } from 'lucide-react';
import useRepoStats from '../hooks/useRepoStats';

export default function Reports() {
  const { stats, loading, error } = useRepoStats();
  const [activeTab, setActiveTab] = useState('Security Overview');

  const cats = stats?.categories || {};
  const issues = stats?.issues || [];
  const totalReviews = stats?.total_reviews || 0;
  const activeIssues = stats?.active_issues || 0;


  const securityIssues = issues.filter(i => i.category === 'Security');
  const bugIssues = issues.filter(i => i.category === 'Bug risk');
  const majorIssues = issues.filter(i => i.severity === 'Major');
  const minorIssues = issues.filter(i => i.severity === 'Minor');

  const navSections = [
    {
      title: "SECURITY AND COMPLIANCE",
      items: ["Security Overview", "Bug Risk Report"]
    },
    {
      title: "INSIGHTS",
      items: ["Code Health Trend"]
    },
  ];



  if (loading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-130px)] bg-[#0E1116]">
        <Loader2 className="w-6 h-6 animate-spin text-[#58a6ff]" />
        <span className="ml-2 text-[#8B949E]">Loading reports...</span>
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
      <div className="w-[280px] shrink-0 border-r border-[#30363D] py-4 overflow-y-auto">
        <div className="flex flex-col gap-6 px-3">
          {navSections.map((section, idx) => (
            <div key={idx}>
              {section.title && (
                <h3 className="text-[11px] font-semibold text-[#8B949E] px-3 mb-2 uppercase tracking-wider">
                  {section.title}
                </h3>
              )}
              <nav className="flex flex-col gap-[2px]">
                {section.items.map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`w-full text-left px-3 py-1.5 rounded-md text-[13px] font-medium transition-colors ${activeTab === tab
                      ? 'bg-[#161B22] text-[#E6EDF3] border-l-2 border-[#3fb950] -ml-px pl-[11px]'
                      : 'text-[#8B949E] hover:text-[#E6EDF3] hover:bg-[#161B22]'
                      }`}
                  >
                    {tab}
                  </button>
                ))}
              </nav>
            </div>
          ))}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 p-6 overflow-y-auto">
        <div className="max-w-[1200px] w-full mx-auto">

          {/* Header */}
          <div className="flex justify-between items-start mb-8">
            <div>
              <h1 className="text-2xl font-semibold text-[#E6EDF3] mb-1">{activeTab}</h1>
              <p className="text-[14px] text-[#8B949E]">
                {activeTab === 'Security Overview' && 'Security issues found in your code reviews.'}
                {activeTab === 'Bug Risk Report' && 'Potential bugs detected during code reviews.'}
                {activeTab === 'Code Health Trend' && 'Overall code health across reviews.'}
              </p>
            </div>
          </div>

          {/* Stats Bar */}
          <div className="flex items-center justify-between border-b border-[#30363D] pb-6 mb-8">
            <div className="flex gap-16">
              <div>
                <h3 className="text-xs font-semibold text-[#8B949E] uppercase tracking-wider mb-2">STATUS</h3>
                <span className={`flex items-center gap-1.5 text-[13px] font-bold tracking-wider ${(activeTab === 'Security Overview' ? cats.security : activeIssues) > 0 ? 'text-[#f85149]' : 'text-[#3fb950]'
                  }`}>
                  <div className={`w-1.5 h-1.5 rounded-full ${(activeTab === 'Security Overview' ? cats.security : activeIssues) > 0 ? 'bg-[#f85149]' : 'bg-[#3fb950]'
                    }`}></div>
                  {(activeTab === 'Security Overview' ? cats.security : activeIssues) > 0 ? 'ISSUES FOUND' : 'PASSING'}
                </span>
              </div>
              <div>
                <h3 className="text-xs font-semibold text-[#8B949E] uppercase tracking-wider mb-2">ACTIVE ISSUES</h3>
                <span className="text-xl font-bold text-[#E6EDF3]">{activeIssues}</span>
              </div>
              <div>
                <h3 className="text-xs font-semibold text-[#8B949E] uppercase tracking-wider mb-2">MAJOR</h3>
                <span className="text-[14px] font-bold text-[#d29922]">{majorIssues.length}</span>
              </div>
              <div>
                <h3 className="text-xs font-semibold text-[#8B949E] uppercase tracking-wider mb-2">MINOR</h3>
                <span className="text-[14px] font-bold text-[#8B949E]">{minorIssues.length}</span>
              </div>
            </div>
          </div>

          {activeTab === 'Security Overview' && (
            <div className="space-y-4">
              {securityIssues.length > 0 ? securityIssues.map((issue, i) => (
                <div key={i} className="bg-[#161B22] border border-[#30363D] rounded-lg p-4 hover:bg-[#21262D] transition-colors">
                  <div className="flex items-start gap-3">
                    <ShieldAlert size={16} className="text-[#f85149] mt-0.5 shrink-0" />
                    <div className="flex-1">
                      <h4 className="text-[14px] font-medium text-[#E6EDF3] mb-1 line-clamp-2">{issue.title}</h4>
                      <div className="flex items-center gap-3 text-xs text-[#8B949E]">
                        {issue.file && <span className="font-mono bg-[#21262D] px-1 py-0.5 rounded">{issue.file}</span>}
                        <span className={issue.severity === 'Major' ? 'text-[#d29922]' : ''}>{issue.severity}</span>
                        {issue.pr_number && <span>PR #{issue.pr_number}</span>}
                      </div>
                    </div>
                  </div>
                </div>
              )) : (
                <div className="bg-[#161B22] border border-[#30363D] rounded-lg p-12 text-center">
                  <ShieldAlert size={40} className="text-[#3fb950] mx-auto mb-3" />
                  <h3 className="text-[15px] font-semibold text-[#E6EDF3] mb-1">No security issues found</h3>
                  <p className="text-[13px] text-[#8B949E]">Your code reviews have not detected any security vulnerabilities.</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'Bug Risk Report' && (
            <div className="space-y-4">
              {bugIssues.length > 0 ? bugIssues.map((issue, i) => (
                <div key={i} className="bg-[#161B22] border border-[#30363D] rounded-lg p-4 hover:bg-[#21262D] transition-colors">
                  <div className="flex items-start gap-3">
                    <Bug size={16} className="text-[#d29922] mt-0.5 shrink-0" />
                    <div className="flex-1">
                      <h4 className="text-[14px] font-medium text-[#E6EDF3] mb-1 line-clamp-2">{issue.title}</h4>
                      <div className="flex items-center gap-3 text-xs text-[#8B949E]">
                        {issue.file && <span className="font-mono bg-[#21262D] px-1 py-0.5 rounded">{issue.file}</span>}
                        <span className={issue.severity === 'Major' ? 'text-[#d29922]' : ''}>{issue.severity}</span>
                        {issue.pr_number && <span>PR #{issue.pr_number}</span>}
                      </div>
                    </div>
                  </div>
                </div>
              )) : (
                <div className="bg-[#161B22] border border-[#30363D] rounded-lg p-12 text-center">
                  <Bug size={40} className="text-[#3fb950] mx-auto mb-3" />
                  <h3 className="text-[15px] font-semibold text-[#E6EDF3] mb-1">No bug risks detected</h3>
                  <p className="text-[13px] text-[#8B949E]">Your code reviews have not found potential bugs.</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'Code Health Trend' && (
            <div className="border border-[#30363D] rounded-lg overflow-hidden flex divide-x divide-[#30363D]">
              <div className="flex-1">
                <div className="px-6 py-4 bg-[#161B22] border-b border-[#30363D]">
                  <h3 className="text-[11px] font-semibold text-[#8B949E] uppercase tracking-wider text-center">TOTAL REVIEWS</h3>
                </div>
                <div className="px-6 py-8 text-center text-xl font-bold text-[#E6EDF3]">{totalReviews}</div>
              </div>
              <div className="flex-1">
                <div className="px-6 py-4 bg-[#161B22] border-b border-[#30363D]">
                  <h3 className="text-[11px] font-semibold text-[#8B949E] uppercase tracking-wider text-center">ACTIVE ISSUES</h3>
                </div>
                <div className="px-6 py-8 text-center text-xl font-bold text-[#E6EDF3]">{activeIssues}</div>
              </div>
              <div className="flex-1">
                <div className="px-6 py-4 bg-[#161B22] border-b border-[#30363D]">
                  <h3 className="text-[11px] font-semibold text-[#8B949E] uppercase tracking-wider text-center">ISSUES PREVENTED</h3>
                </div>
                <div className="px-6 py-8 text-center text-xl font-bold text-[#3fb950]">{stats?.issues_prevented || 0}</div>
              </div>
              <div className="flex-1">
                <div className="px-6 py-4 bg-[#161B22] border-b border-[#30363D]">
                  <h3 className="text-[11px] font-semibold text-[#8B949E] uppercase tracking-wider text-center">SUCCESS RATE</h3>
                </div>
                <div className="px-6 py-8 text-center text-xl font-bold text-[#E6EDF3]">
                  {totalReviews > 0 ? `${Math.round((stats?.succeeded / totalReviews) * 100)}%` : 'N/A'}
                </div>
              </div>
            </div>
          )}



        </div>
      </div>
    </div>
  );
}
