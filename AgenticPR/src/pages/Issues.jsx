import React, { useState, useMemo } from 'react';
import { 
  ShieldAlert, 
  Zap, 
  Search, 
  ArrowUpDown, 
  Bug,
  AlertTriangle,
  Lock,
  Activity,
  Code2,
  FileCheck,
  Paintbrush,
  BookOpen,
  Loader2
} from 'lucide-react';
import useRepoStats from '../hooks/useRepoStats';

export default function Issues() {
  const { stats, loading, error } = useRepoStats();
  const [activeCategory, setActiveCategory] = useState('All issues');
  const [searchTerm, setSearchTerm] = useState('');

  const cats = stats?.categories || {};
  const issues = stats?.issues || [];
  const totalIssues = issues.length;

  // Build sidebar category counts
  const sidebarCategories = useMemo(() => [
    { name: "All issues", count: totalIssues, icon: null, key: 'all' },
    { name: "Bug Risk", count: cats.bug_risk || 0, icon: Bug, key: 'Bug risk' },
    { name: "Anti-pattern", count: cats.anti_pattern || 0, icon: AlertTriangle, key: 'Anti-pattern' },
    { name: "Security", count: cats.security || 0, icon: ShieldAlert, key: 'Security' },
    { name: "Performance", count: cats.performance || 0, icon: Activity, key: 'Performance' },
    { name: "Style", count: cats.style || 0, icon: Paintbrush, key: 'Style' },
    { name: "Documentation", count: cats.documentation || 0, icon: BookOpen, key: 'Documentation' },
  ], [totalIssues, cats]);

  // Filter issues based on selected category and search term
  const filteredIssues = useMemo(() => {
    let filtered = issues;
    if (activeCategory !== 'All issues') {
      const catKey = sidebarCategories.find(c => c.name === activeCategory)?.key;
      if (catKey) filtered = filtered.filter(issue => issue.category === catKey);
    }
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(issue => 
        issue.title?.toLowerCase().includes(term) || 
        issue.file?.toLowerCase().includes(term) ||
        issue.id?.toLowerCase().includes(term)
      );
    }
    return filtered;
  }, [issues, activeCategory, searchTerm, sidebarCategories]);

  // Map category to icon & color
  const catIconMap = {
    'Bug risk': { icon: Bug, color: 'text-[#d29922]' },
    'Anti-pattern': { icon: AlertTriangle, color: 'text-gray-400' },
    'Security': { icon: ShieldAlert, color: 'text-[#f85149]' },
    'Performance': { icon: Activity, color: 'text-[#58a6ff]' },
    'Style': { icon: Paintbrush, color: 'text-[#8B949E]' },
    'Documentation': { icon: BookOpen, color: 'text-[#3fb950]' },
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-130px)] bg-[#0E1116]">
        <Loader2 className="w-6 h-6 animate-spin text-[#58a6ff]" />
        <span className="ml-2 text-[#8B949E]">Loading issues...</span>
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
      
      {/* Issues Left Sidebar */}
      <div className="w-[240px] border-r border-[#30363D] shrink-0 overflow-y-auto pt-4 flex flex-col">
        <nav className="px-3 space-y-[2px]">
          {sidebarCategories.map((cat, i) => {
            const isActive = activeCategory === cat.name;
            return (
              <button
                key={i}
                onClick={() => setActiveCategory(cat.name)}
                className={`w-full flex items-center justify-between px-3 py-1.5 rounded-md text-[13px] ${isActive ? 'bg-[#161B22] text-[#E6EDF3] font-medium' : 'text-[#8B949E] hover:text-[#E6EDF3] hover:bg-[#1C2128]'}`}
              >
                <div className="flex items-center gap-2">
                  {cat.icon && <cat.icon size={14} className="text-[#8B949E]" />}
                  {!cat.icon && i === 0 && <svg className="w-3.5 h-3.5 text-[#8B949E]" viewBox="0 0 16 16" fill="currentColor"><path d="M2 4h12v1H2zM2 7.5h12v1H2zM2 11h12v1H2z"></path></svg>}
                  <span>{cat.name}</span>
                </div>
                {cat.count > 0 ? (
                  <span className="text-[#8B949E] text-xs font-semibold">{cat.count}</span>
                ) : (
                  <span className="text-gray-600 text-xs">0</span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Main Issue List */}
      <div className="flex-1 flex flex-col min-w-0 bg-[#0E1116]">
        
        {/* Top Controls Toolbar */}
        <div className="flex items-center justify-between px-6 py-3 border-b border-[#30363D]">
          <div className="flex items-center gap-4">
            <span className="text-[13px] text-[#8B949E] font-medium">
              {filteredIssues.length} issue{filteredIssues.length !== 1 ? 's' : ''}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <button className="flex items-center gap-1 text-[13px] text-[#8B949E] hover:text-[#E6EDF3] font-medium mr-2">
              <ArrowUpDown size={14} /> Sort
            </button>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#8B949E]" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search for an issue..."
                className="w-56 bg-[#161B22] border border-[#30363D] rounded-md py-1.5 pl-8 pr-3 text-[13px] text-[#E6EDF3] placeholder-[#8B949E] focus:outline-none focus:border-[#58a6ff] focus:ring-1 focus:ring-[#58a6ff]"
              />
            </div>
          </div>
        </div>

        {/* Issue Cards */}
        <div className="flex-1 overflow-y-auto pb-8">
          {filteredIssues.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-[#8B949E]">
              <Bug size={48} className="mb-4 text-[#30363D]" />
              <p className="text-[15px] font-medium mb-1">No issues found</p>
              <p className="text-[13px]">
                {totalIssues === 0
                  ? 'Run a PR review to start detecting issues.'
                  : 'Try adjusting your filters or search term.'}
              </p>
            </div>
          ) : (
            filteredIssues.map((issue, idx) => {
              const catInfo = catIconMap[issue.category] || { icon: AlertTriangle, color: 'text-gray-400' };
              const IssueIcon = catInfo.icon;
              return (
                <div key={idx} className="flex border-b border-[#30363D] hover:bg-[#161B22]/50 transition-colors group cursor-pointer">
                  <div className="flex-1 p-5">
                    <h3 className="text-[15px] font-semibold text-[#E6EDF3] mb-2 group-hover:text-[#58a6ff] transition-colors line-clamp-2">
                      {issue.title || 'Untitled issue'}
                      <span className="text-[#8B949E] font-normal text-[13px] ml-2">{issue.id}</span>
                    </h3>
                    
                    <div className="flex items-center gap-4 text-[13px] text-[#8B949E]">
                      <span className="flex items-center gap-1.5">
                        <IssueIcon size={14} className={catInfo.color} />
                        {issue.category}
                      </span>
                      <span className="flex items-center gap-1.5">
                        <span className={`w-1 h-3 rounded-full ${issue.severity === 'Major' ? 'bg-[#d29922]' : 'bg-gray-400'}`}></span>
                        {issue.severity}
                      </span>
                      {issue.file && (
                        <span className="font-mono text-xs bg-[#21262D] px-1.5 py-0.5 rounded">
                          {issue.file}{issue.line ? `:${issue.line}` : ''}
                        </span>
                      )}
                      {issue.pr_number && (
                        <span>PR #{issue.pr_number}</span>
                      )}
                      <span>{timeAgo(issue.created_at)}</span>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
