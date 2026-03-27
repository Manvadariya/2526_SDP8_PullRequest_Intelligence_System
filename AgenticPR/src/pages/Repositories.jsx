import React, { useState } from "react";
import { Link } from "react-router-dom";
import { GitPullRequest, Star, Clock, Search, Lock, Globe } from 'lucide-react';
import { useUserRepos } from "../hooks/useApiCache";

export default function Repositories() {
  const { data: repos = [], isLoading: loading, error: queryError, refetch } = useUserRepos();
  const error = queryError?.message || null;
  const [searchTerm, setSearchTerm] = useState("");
  const [filterLang, setFilterLang] = useState("All");

  // Language color map
  const langColors = {
    JavaScript: 'bg-amber-300',
    TypeScript: 'bg-blue-400',
    Python: 'bg-green-400',
    Java: 'bg-orange-400',
    Go: 'bg-cyan-400',
    Rust: 'bg-red-400',
    Ruby: 'bg-red-500',
    C: 'bg-gray-400',
    'C++': 'bg-pink-400',
    'C#': 'bg-purple-400',
    PHP: 'bg-violet-400',
    Shell: 'bg-emerald-400',
    Unknown: 'bg-gray-500',
  };

  const languages = ['All', ...new Set(repos.map(r => r.language).filter(Boolean))];

  const filteredRepos = repos.filter(repo => {
    const matchesSearch = repo.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (repo.description || '').toLowerCase().includes(searchTerm.toLowerCase());
    const matchesLang = filterLang === "All" || repo.language === filterLang;
    return matchesSearch && matchesLang;
  });

  const timeAgo = (dateStr) => {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return isNaN(d.getTime()) ? '' : d.toLocaleString(undefined, {
      month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  };

  return (
    <div className="flex-1 bg-[#0d1117] h-full flex flex-col min-w-0">
      <div className="border-b border-[#30363d] bg-[#0d1117] px-6 py-4 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <Link to="/home" className="text-gray-400 hover:text-white transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m15 18-6-6 6-6" /></svg>
          </Link>
          <h1 className="text-xl font-semibold text-white">
            Repositories
            {!loading && <span className="ml-2 text-sm font-normal text-gray-500">({repos.length})</span>}
          </h1>
        </div>
      </div>

      <div className="p-6 flex-1 overflow-y-auto">
        <div className="max-w-5xl mx-auto">

          {/* Search and Filter */}
          <div className="flex gap-3 mb-6">
            <div className="relative flex-1">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
              <input
                type="text"
                placeholder="Find a repository..."
                className="w-full bg-[#0d1117] border border-[#30363d] rounded-md pl-9 pr-4 py-1.5 text-sm text-gray-300 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none placeholder-gray-500"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <div className="relative group">
              <button className="flex items-center gap-2 px-3 py-1.5 bg-[#21262d] border border-[#30363d] rounded-md text-sm font-medium text-gray-300 hover:bg-[#30363d] hover:text-white transition-colors">
                Language: {filterLang}
                <span className="text-[10px] ml-1">▼</span>
              </button>
              <div className="absolute right-0 top-full mt-1 w-36 bg-[#161b22] border border-[#30363d] rounded-md shadow-xl hidden group-hover:block z-10 py-1 max-h-60 overflow-y-auto">
                {languages.map(l => (
                  <div key={l} onClick={() => setFilterLang(l)} className="px-3 py-1.5 text-xs text-gray-300 hover:bg-[#1f6feb] hover:text-white cursor-pointer">
                    {l}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Loading state */}
          {loading && (
            <div className="flex items-center justify-center py-20">
              <div className="w-8 h-8 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
              <p className="text-gray-400 ml-3">Loading your repositories...</p>
            </div>
          )}

          {/* Error state */}
          {error && (
            <div className="text-center py-16">
              <p className="text-red-400 mb-1 font-medium">Failed to load repositories</p>
              <p className="text-gray-500 text-sm mb-5">{error}</p>
              <button
                onClick={() => refetch()}
                className="px-4 py-1.5 bg-[#21262d] hover:bg-[#30363d] border border-[#30363d] text-sm text-gray-300 rounded-md transition-colors"
              >
                Try Again
              </button>
            </div>
          )}

          {/* Repo list */}
          {!loading && !error && (
            <div className="border border-[#30363d] rounded-md bg-[#0d1117] divide-y divide-[#30363d]">
              {filteredRepos.map((repo) => (
                <div key={repo.id} className="p-4 flex items-start justify-between hover:bg-[#161b22] transition-colors group">
                  <div className="flex items-start gap-4 flex-1 min-w-0">
                    <div className="mt-1">
                      <div className="p-2 rounded bg-gray-800 border border-gray-700">
                        {repo.private ? <Lock size={16} className="text-amber-400" /> : <Globe size={16} className="text-gray-400" />}
                      </div>
                    </div>
                    <div className="flex-1 min-w-0 pr-4">
                      <div className="flex items-center gap-2 mb-1">
                        <Link to={`/repositories/${encodeURIComponent(repo.name)}`} className="text-base font-semibold text-[#58a6ff] hover:underline cursor-pointer">
                          {repo.full_name}
                        </Link>
                        {repo.private && (
                          <span className="border border-[#30363d] px-2 py-0.5 rounded-full text-xs text-gray-400">Private</span>
                        )}
                      </div>
                      <p className="text-sm text-gray-400 mb-3 truncate w-[90%]">
                        {repo.description || 'No description'}
                      </p>
                      <div className="flex items-center gap-4 text-xs text-gray-500">
                        {repo.language && (
                          <div className="flex items-center gap-1">
                            <span className={`w-3 h-3 rounded-full ${langColors[repo.language] || 'bg-gray-500'}`}></span>
                            {repo.language}
                          </div>
                        )}
                        <div className="flex items-center gap-1">
                          <Star size={14} />
                          {repo.stars}
                        </div>
                        <div className="flex items-center gap-1">
                          <Clock size={14} />
                          Updated {timeAgo(repo.updated_at)}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Link
                        to={`/repositories/${encodeURIComponent(repo.name)}`}
                        className="bg-[#21262d] hover:bg-[#30363d] border border-[#30363d] text-xs font-medium text-gray-300 px-3 py-1.5 rounded-md transition-colors"
                      >
                        View Details
                      </Link>
                    </div>
                  </div>
                </div>
              ))}

              {filteredRepos.length === 0 && !loading && (
                <div className="p-8 text-center text-gray-500">
                  <p>No repositories found.</p>
                  <button onClick={() => { setSearchTerm(""); setFilterLang("All"); }} className="text-[#58a6ff] text-sm mt-2 hover:underline">
                    Clear filters
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
