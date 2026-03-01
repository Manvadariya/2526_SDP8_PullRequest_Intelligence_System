import React, { useState } from "react";
import { Link } from "react-router-dom";
import { GitPullRequest, Star, Clock, MoreHorizontal, Search, Filter } from 'lucide-react';

const MOCK_REPOS = [
  {
    id: 1,
    name: "frontend-app",
    owner: "acme-corp",
    description: "Next.js frontend application with TypeScript and Tailwind CSS",
    language: "TypeScript",
    languageColor: "bg-blue-400",
    stars: 142,
    openPRs: 5,
    lastReview: "2 hours ago",
    status: "active",
  },
  {
    id: 2,
    name: "api-gateway",
    owner: "acme-corp",
    description: "Express.js API gateway with authentication and rate limiting",
    language: "JavaScript",
    languageColor: "bg-amber-300",
    stars: 89,
    openPRs: 3,
    lastReview: "5 hours ago",
    status: "active",
  },
  {
    id: 3,
    name: "docs-site",
    owner: "acme-corp",
    description: "Documentation site built with Docusaurus",
    language: "Markdown",
    languageColor: "bg-gray-400",
    stars: 45,
    openPRs: 1,
    lastReview: "1 day ago",
    status: "archived",
  },
  {
    id: 4,
    name: "design-system",
    owner: "acme-corp",
    description: "Shared React component library and design tokens",
    language: "TypeScript",
    languageColor: "bg-blue-400",
    stars: 210,
    openPRs: 8,
    lastReview: "30 mins ago",
    status: "active",
  },
];

export default function Repositories() {
  const [searchTerm, setSearchTerm] = useState("");
  const [filterLang, setFilterLang] = useState("All");

  const filteredRepos = MOCK_REPOS.filter(repo => {
     const matchesSearch = repo.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
                           repo.description.toLowerCase().includes(searchTerm.toLowerCase());
     const matchesLang = filterLang === "All" || repo.language === filterLang;
     return matchesSearch && matchesLang;
  });

  return (
    <div className="flex-1 bg-[#0d1117] h-full flex flex-col min-w-0">
      <div className="border-b border-[#30363d] bg-[#0d1117] px-6 py-4 flex items-center justify-between shrink-0">
        <h1 className="text-xl font-semibold text-white">Repositories</h1>
        <button className="bg-[#238636] hover:bg-[#2ea043] text-white px-4 py-1.5 rounded-md text-sm font-medium transition-colors border border-[rgba(240,246,252,0.1)] shadow-sm">
          New repository
        </button>
      </div>

      <div className="p-6 flex-1 overflow-y-auto">
        <div className="max-w-5xl mx-auto">
          
          {/* Search and Filter Bar */}
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
            
            <div className="flex gap-2">
                <button className="flex items-center gap-2 px-3 py-1.5 bg-[#21262d] border border-[#30363d] rounded-md text-sm font-medium text-gray-300 hover:bg-[#30363d] hover:text-white transition-colors">
                    Type
                    <span className="text-[10px] ml-1">▼</span>
                </button>
                <div className="relative group">
                    <button className="flex items-center gap-2 px-3 py-1.5 bg-[#21262d] border border-[#30363d] rounded-md text-sm font-medium text-gray-300 hover:bg-[#30363d] hover:text-white transition-colors">
                        Language: {filterLang}
                        <span className="text-[10px] ml-1">▼</span>
                    </button>
                    {/* Simple dropdown overlay on hover for demo */}
                    <div className="absolute right-0 top-full mt-1 w-32 bg-[#161b22] border border-[#30363d] rounded-md shadow-xl hidden group-hover:block z-10 py-1">
                        {['All', 'TypeScript', 'JavaScript', 'Markdown'].map(l => (
                            <div key={l} onClick={() => setFilterLang(l)} className="px-3 py-1.5 text-xs text-gray-300 hover:bg-[#1f6feb] hover:text-white cursor-pointer">
                                {l}
                            </div>
                        ))}
                    </div>
                </div>
            </div>
          </div>

          {/* List */}
          <div className="border border-[#30363d] rounded-md bg-[#0d1117] divide-y divide-[#30363d]">
          {filteredRepos.map((repo) => (
            <div key={repo.id} className="p-4 flex items-start justify-between hover:bg-[#161b22] transition-colors group">
              <div className="flex items-start gap-4 flex-1 min-w-0">
                <div className="mt-1">
                    <div className="p-2 rounded bg-gray-800 border border-gray-700">
                        <GitPullRequest size={16} className="text-gray-400" />
                    </div>
                </div>
                <div className="flex-1 min-w-0 pr-4">
                  <div className="flex items-center gap-2 mb-1">
                    <Link to="/scan" className="text-base font-semibold text-[#58a6ff] hover:underline cursor-pointer group-hover:text-[#58a6ff]">
                      {repo.owner}/{repo.name}
                    </Link>
                    <span className="border border-[#30363d] px-2 py-0.5 rounded-full text-xs text-gray-400 capitalize">{repo.status}</span>
                  </div>
                  <p className="text-sm text-gray-400 mb-3 truncate w-[90%]">
                    {repo.description}
                  </p>
                  
                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    <div className="flex items-center gap-1">
                      <span className={`w-3 h-3 rounded-full ${repo.languageColor}`}></span>
                      {repo.language}
                    </div>
                    <div className="flex items-center gap-1 hover:text-[#58a6ff] cursor-pointer">
                      <Star size={14} />
                      {repo.stars}
                    </div>
                    <div className="flex items-center gap-1 hover:text-[#58a6ff] cursor-pointer">
                      <GitPullRequest size={14} />
                      {repo.openPRs}
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock size={14} />
                      Updated {repo.lastReview}
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button className="p-2 text-gray-400 hover:text-white hover:bg-[#30363d] rounded-md">
                        <Star size={16} />
                    </button>
                    <Link to="/scan" className="bg-[#21262d] hover:bg-[#30363d] border border-[#30363d] text-xs font-medium text-gray-300 px-3 py-1.5 rounded-md transition-colors shadow-[0_1px_0_rgba(27,31,35,0.04),inset_0_1px_0_rgba(255,255,255,0.03)] inline-block">
                        Analyze
                    </Link>
                </div>
              </div>
            </div>
          ))}
          {filteredRepos.length === 0 && (
              <div className="p-8 text-center text-gray-500">
                  <p>No repositories found matching your search.</p>
                  <button onClick={() => {setSearchTerm(""); setFilterLang("All");}} className="text-[#58a6ff] text-sm mt-2 hover:underline">Clear filters</button>
              </div>
          )}
          </div>
        </div>
      </div>
    </div>
  );
}
