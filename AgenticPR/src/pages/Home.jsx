import React from 'react';
import { Link } from 'react-router-dom';
import { Search, ChevronDown, GitBranch, Shield, Zap, GitCommit, XCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useActivatedRepos, useJobs } from '../hooks/useApiCache';

export default function Home() {
  const { user } = useAuth();
  const { data: repos = [], isLoading: reposLoading } = useActivatedRepos();
  const { data: allJobs = [], isLoading: jobsLoading } = useJobs();
  const jobs = allJobs.slice(0, 5);
  const loading = reposLoading || jobsLoading;
  
  // Use profile data if auth works, otherwise fallback
  const displayName = user?.username || user?.name || "Developer";

  const timeAgo = (dateStr) => {
    if (!dateStr) return 'just now';
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  };

  // Compute stats from jobs
  const totalReviews = jobs.length;
  const issuesPrevented = jobs.filter(j => j.status === 'success').length;

  return (
    <div className="flex-1 overflow-y-auto bg-[#0E1116] text-[#E6EDF3] p-6">
      <div className="max-w-7xl mx-auto">
        
        {/* Header Greeting */}
        <h1 className="text-2xl font-semibold mb-6">Good afternoon, {displayName}</h1>

        {/* Top Controls: Search & Toggle */}
        <div className="flex items-center gap-4 mb-8">
          <div className="relative flex-1 max-w-2xl">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8B949E]" />
            <input
              type="text"
              placeholder="Search repositories..."
              className="w-full bg-[#161B22] border border-[#30363D] rounded-md py-1.5 pl-9 pr-3 text-sm text-[#E6EDF3] placeholder-[#8B949E] focus:outline-none focus:border-[#58a6ff] focus:ring-1 focus:ring-[#58a6ff] transition-all"
            />
          </div>
          <div className="flex items-center bg-[#161B22] rounded-md border border-[#30363D] overflow-hidden">
            <button className="px-4 py-1.5 text-sm font-medium bg-[#E6EDF3] text-black">
              All repositories
            </button>
          </div>
        </div>

        {/* Main Grid Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          
          {/* Left Column (Repositories & Recent PRs) */}
          <div className="lg:col-span-3 space-y-6">
            
            {/* Repository List */}
            <div className="bg-[#161B22] border border-[#30363D] rounded-lg overflow-hidden">
              {loading ? (
                <div className="h-56 flex items-center justify-center text-[#8B949E]">
                  <div className="w-6 h-6 border-2 border-blue-400 border-t-transparent rounded-full animate-spin mr-2" />
                  Loading repositories...
                </div>
              ) : repos.length > 0 ? (
                repos.map((repo) => (
                  <Link
                    key={repo.id}
                    to={`/repositories/${repo.repo_name}/overview`}
                    className="flex items-center justify-between p-4 hover:bg-[#1C2128] transition-colors border-b border-[#30363D] last:border-b-0"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-5 h-5 flex flex-wrap gap-[1px]">
                        <div className="w-[9px] h-[9px] bg-gray-600 rounded-[2px]" />
                        <div className="w-[9px] h-[9px] bg-gray-600 rounded-[2px]" />
                        <div className="w-[9px] h-[9px] bg-gray-600 rounded-[2px]" />
                        <div className="w-[9px] h-[9px] bg-gray-600 rounded-[2px]" />
                      </div>
                      <h3 className="font-semibold text-[15px] hover:text-[#58a6ff] transition-colors">{repo.repo_full_name}</h3>
                      {repo.language && (
                        <span className="ml-2 text-xs text-[#8B949E] bg-[#21262D] px-1.5 py-0.5 rounded">{repo.language}</span>
                      )}
                    </div>
                    <div className="flex items-center gap-6 text-[#8B949E] text-sm">
                      <span>{timeAgo(repo.activated_at)}</span>
                      <span className="text-[10px] text-[#3fb950] bg-[#3fb950]/10 px-1.5 py-0.5 rounded font-medium">ACTIVE</span>
                    </div>
                  </Link>
                ))
              ) : (
                <div className="h-56 flex flex-col items-center justify-center text-[#8B949E]">
                  <p>No repositories activated yet.</p>
                  <p className="text-sm mt-1">Click "Activate new repository" in the sidebar to get started.</p>
                </div>
              )}
            </div>

            {/* Recent Pull Requests Section */}
            <div>
              <div className="flex items-center justify-between mb-3 border-b border-[#30363D] pb-2">
                <h2 className="text-[15px] font-semibold">Recent pull requests</h2>
                <Link to="/pr" className="text-sm text-[#58a6ff] hover:underline">View all</Link>
              </div>

              <div className="bg-[#161B22] border border-[#30363D] rounded-lg overflow-hidden">
                {jobs.length > 0 ? (
                  jobs.map((job) => (
                    <Link
                      key={job.id}
                      to={`/scan/${job.id}`}
                      className="flex items-start justify-between p-4 hover:bg-[#1C2128] transition-colors group border-b border-[#30363D] last:border-b-0"
                    >
                      <div className="flex items-start gap-3">
                        <XCircle size={16} className={`mt-0.5 ${job.status === 'success' ? 'text-[#3fb950]' : job.status === 'failed' ? 'text-[#f85149]' : 'text-[#d29922]'}`} />
                        <div>
                          <h4 className="font-semibold text-[15px] group-hover:text-[#58a6ff] transition-colors cursor-pointer">
                            PR #{job.pr_number} — {job.repo_full_name}
                          </h4>
                          <div className="flex items-center gap-3 mt-1.5 text-xs text-[#8B949E]">
                            <span className="flex items-center gap-1">
                              <GitBranch size={12} /> #{job.pr_number}
                            </span>
                            <span className={`px-1.5 py-0.5 rounded-sm font-medium tracking-wide ${
                              job.status === 'success' ? 'bg-[#3fb950]/10 text-[#3fb950]' :
                              job.status === 'failed' ? 'bg-[#f85149]/10 text-[#f85149]' :
                              'bg-[#d29922]/10 text-[#d29922]'
                            }`}>
                              {job.status?.toUpperCase()}
                            </span>
                            <span>⏱ {timeAgo(job.created_at)}</span>
                          </div>
                        </div>
                      </div>
                      <div className="w-7 h-7 rounded-md bg-[#21262D] border border-[#30363D] flex items-center justify-center text-xs font-bold shadow-sm">
                        <span className={job.status === 'success' ? 'text-[#3fb950]' : 'text-[#d29922]'}>
                          {job.commit_sha?.substring(0, 3)}
                        </span>
                      </div>
                    </Link>
                  ))
                ) : (
                  <div className="p-8 text-center text-[#8B949E]">
                    <p>No reviews yet.</p>
                    <p className="text-sm mt-1">Reviews will appear here when PRs are analyzed.</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Column (Stats Widget) */}
          <div className="lg:col-span-1">
            <h2 className="text-[15px] font-semibold mb-3">This month so far...</h2>
            <div className="bg-[#161B22] border border-[#30363D] rounded-lg p-4 space-y-4">
              
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2 text-[#8B949E]">
                  <GitCommit size={15} />
                  <span>PRs analyzed</span>
                </div>
                <span className="text-[#E6EDF3] font-semibold">{totalReviews}</span>
              </div>
              
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2 text-[#8B949E]">
                  <Shield size={15} />
                  <span>Reviews succeeded</span>
                </div>
                <span className="text-[#E6EDF3] font-semibold">{issuesPrevented}</span>
              </div>
              
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2 text-[#8B949E]">
                  <Zap size={15} />
                  <span>Repositories tracked</span>
                </div>
                <span className="text-[#E6EDF3] font-semibold">{repos.length}</span>
              </div>

            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
