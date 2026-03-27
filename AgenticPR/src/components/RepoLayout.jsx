import React, { useState } from 'react';
import { Outlet, useLocation, Link, useParams } from 'react-router-dom';
import { Github, Settings, Activity, ShieldAlert, FileText, GitPullRequest, GitCompare, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useResolveRepo, useActivatedRepos, useInvalidateCache } from '../hooks/useApiCache';

export default function RepoLayout() {
  const location = useLocation();
  const { repoName } = useParams();
  const { user, authFetch } = useAuth();
  const displayRepoName = repoName || "unknown-repo";
  const userName = user?.username || "user";

  const { matched: repoObject } = useResolveRepo(repoName);
  const { data: activatedRepos = [] } = useActivatedRepos();
  const { invalidateActivatedRepos } = useInvalidateCache();

  const [isToggling, setIsToggling] = useState(false);

  const isActivated = activatedRepos.some(r => r.repo_full_name === repoObject?.full_name || r.full_name === repoObject?.full_name);

  const handleToggleActive = async () => {
    if (!repoObject) return;
    setIsToggling(true);
    try {
      if (isActivated) {
        const res = await authFetch(`/api/activated-repos/${repoObject.full_name}`, { method: 'DELETE' });
        if (res.ok) {
          invalidateActivatedRepos();
        }
      } else {
        const res = await authFetch('/api/activated-repos', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            repo_full_name: repoObject.full_name,
            repo_name: repoObject.name,
            language: repoObject.language || '',
            description: repoObject.description || '',
            private: repoObject.private || false,
          }),
        });
        if (res.ok) {
          invalidateActivatedRepos();
        }
      }
    } catch (err) {
      console.error('Failed to toggle repo:', err);
    } finally {
      setIsToggling(false);
    }
  };

  // Tab configuration using dynamic repo name from route params
  const basePath = `/repositories/${displayRepoName}`;
  const tabs = [
    { name: 'Overview', path: `${basePath}/overview`, icon: GitCompare },
    // { name: 'Issues', path: `${basePath}/issues`, icon: ShieldAlert },
    { name: 'Metrics', path: `${basePath}/metrics`, icon: Activity },
    // { name: 'Reports', path: `${basePath}/reports`, icon: FileText },
    { name: 'Pull Requests', path: `${basePath}/pull-requests`, icon: GitPullRequest },
    // { name: 'Settings', path: `${basePath}/settings`, icon: Settings },
  ];

  return (
    <div className="flex-1 flex flex-col min-w-0 bg-[#0E1116] text-[#E6EDF3]">
      {/* Top Header */}
      <div className="px-6 py-4 flex flex-col shrink-0 border-b border-[#30363D]">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            {/* Repo Icon (Globe placeholder) */}
            <div className="w-5 h-5 flex items-center justify-center text-gray-500">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
            </div>

            {/* Breadcrumb Path */}
            <h1 className="text-xl font-semibold flex items-center">
              <Link to="/home" className="text-gray-400 font-normal hover:underline cursor-pointer">
                {repoObject ? repoObject.full_name.split('/')[0] : userName}
              </Link>
              <span className="text-gray-500 mx-2 font-normal">/</span>
              {repoObject ? (
                <a href={repoObject.html_url || `https://github.com/${repoObject.full_name}`} target="_blank" rel="noopener noreferrer" className="hover:underline cursor-pointer">
                  {repoObject.name}
                </a>
              ) : (
                <span>{repoName}</span>
              )}
            </h1>

            {/* Quick Actions (Star, GitHub Link) */}
            <div className="flex items-center gap-2 ml-4">
              <button className="text-gray-500 hover:text-gray-300 transition-colors">
                <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
              </button>
              {repoObject && (
                <a href={repoObject.html_url || `https://github.com/${repoObject.full_name}`} target="_blank" rel="noopener noreferrer" className="text-gray-500 hover:text-gray-300 transition-colors">
                  <Github size={16} />
                </a>
              )}
            </div>

            {/* Badges / Actions */}
            <div className="flex items-center gap-2 ml-4">
              {isToggling ? (
                <span className="flex items-center gap-1.5 px-3 py-1 rounded-md border border-[#30363D] bg-[#21262D] text-[12px] font-medium text-[#8B949E]">
                  <Loader2 size={14} className="animate-spin" />
                  Updating...
                </span>
              ) : isActivated ? (
                <button
                  onClick={handleToggleActive}
                  disabled={!repoObject}
                  className="flex items-center gap-1.5 px-3 py-1 rounded-md border border-green-900/50 bg-[#161B22] hover:bg-[#21262D] transition-colors text-[12px] font-medium text-[#3fb950] tracking-wide"
                >
                  <div className="w-1.5 h-1.5 rounded-full bg-[#3fb950]"></div>
                  ACTIVE
                </button>
              ) : (
                <button
                  onClick={handleToggleActive}
                  disabled={!repoObject}
                  className="flex items-center gap-1.5 px-3 py-1 rounded-md border border-[#30363D] bg-[#21262D] hover:bg-[#30363D] hover:text-white transition-colors text-[12px] font-medium text-gray-400 tracking-wide"
                >
                  <div className="w-1.5 h-1.5 rounded-full bg-gray-500 group-hover:bg-white"></div>
                  ACTIVATE REPO
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <nav className="flex gap-6 -mb-[17px]">
          {tabs.map((tab) => {
            const pathEnd = tab.path.split('/').pop();
            const isActive = location.pathname.endsWith(pathEnd) || (pathEnd === 'overview' && location.pathname.endsWith(displayRepoName));
            const Icon = tab.icon;
            return (
              <Link
                key={tab.name}
                to={tab.path}
                className={`flex items-center gap-2 pb-3 text-[14px] font-medium transition-colors border-b-2 ${isActive
                  ? 'border-[#3fb950] text-[#E6EDF3]'
                  : 'border-transparent text-[#8B949E] hover:text-[#E6EDF3] hover:border-gray-600'
                  }`}
              >
                <Icon size={16} className={isActive ? 'text-gray-400' : 'text-[#8B949E]'} />
                {tab.name}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Main Content Area (Nested Pages) */}
      <div className="flex-1 overflow-y-auto">
        <Outlet />
      </div>
    </div>
  );
}
