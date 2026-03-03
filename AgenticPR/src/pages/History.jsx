import React, { useState } from 'react';
import { 
  GitPullRequest, 
  Search, 
  CheckCircle2
} from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import { useResolveRepo, usePullRequests } from '../hooks/useApiCache';

export default function History() {
  const { repoName } = useParams();
  const { owner, repo } = useResolveRepo(repoName);
  const [filter, setFilter] = useState('open');
  const [searchTerm, setSearchTerm] = useState('');
  const { data: pullRequests = [], isLoading: loading } = usePullRequests(owner, repo, filter);

  const timeAgo = (dateStr) => {
    if (!dateStr) return '';
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  };

  const filteredPRs = pullRequests
    .filter(pr => 
      pr.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      `#${pr.number}`.includes(searchTerm)
    )
    .sort((a, b) => b.number - a.number);

  const openCount = pullRequests.filter(p => p.state === 'open').length;
  const closedCount = pullRequests.length - openCount;

  return (
    <div className="flex bg-[#0E1116] h-[calc(100vh-130px)]">
      
      {/* Sidebar: Filters */}
      <div className="w-[240px] border-r border-[#30363D] shrink-0 overflow-y-auto pt-4 flex flex-col px-3">
        
        <div className="mb-6">
          <div className="flex items-center gap-2 text-[#E6EDF3] font-medium mb-1 px-3 py-1.5 hover:bg-[#161B22] rounded-md cursor-pointer transition-colors">
            <GitPullRequest size={16} className="text-[#8B949E] rotate-[90deg]" />
            <span>Pull requests</span>
            <span className="ml-auto text-xs font-semibold bg-[#21262D] px-1.5 py-[1px] rounded">{pullRequests.length}</span>
          </div>
          
          <div className="pl-6 space-y-0.5 border-l border-[#30363D] ml-5">
            <button 
              onClick={() => setFilter('open')}
              className={`w-full flex justify-between items-center text-left text-[13px] font-medium px-3 py-1.5 rounded-md ${
                filter === 'open' 
                  ? 'text-[#E6EDF3] bg-[#161B22] -ml-px border-l-2 border-[#3fb950]' 
                  : 'text-[#8B949E] hover:text-[#E6EDF3] hover:bg-[#161B22] ml-[1px]'
              }`}
            >
              Open
              <span className="text-xs font-semibold">{filter === 'open' ? filteredPRs.length : openCount}</span>
            </button>
            <button 
              onClick={() => setFilter('closed')}
              className={`w-full flex justify-between items-center text-left text-[13px] px-3 py-1.5 rounded-md ${
                filter === 'closed' 
                  ? 'text-[#E6EDF3] bg-[#161B22] -ml-px border-l-2 border-[#3fb950] font-medium' 
                  : 'text-[#8B949E] hover:text-[#E6EDF3] hover:bg-[#161B22] ml-[1px]'
              }`}
            >
              Closed
              <span className="text-xs font-semibold">{filter === 'closed' ? filteredPRs.length : closedCount}</span>
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

                <div className="flex items-center shrink-0">
                  {pr.state === 'open' ? (
                    <span className="flex items-center gap-1.5 px-3 py-1.5 bg-transparent border border-[#3fb950]/20 rounded-full text-[13px] font-semibold text-[#3fb950]">
                      <GitPullRequest size={14} /> Open
                    </span>
                  ) : (
                    <span className="flex items-center gap-1.5 px-3 py-1.5 bg-transparent border border-[#a371f7]/20 rounded-full text-[13px] font-semibold text-[#a371f7]">
                      <CheckCircle2 size={14} /> Merged
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
