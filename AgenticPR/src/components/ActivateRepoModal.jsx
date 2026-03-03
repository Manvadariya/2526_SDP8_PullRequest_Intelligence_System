import React, { useState, useMemo } from 'react';
import { X, Search, Check, Loader2, Lock, Globe } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useUserRepos, useActivatedRepos, useInvalidateCache } from '../hooks/useApiCache';

export default function ActivateRepoModal({ isOpen, onClose }) {
  const { authFetch } = useAuth();
  const { data: allRepos = [], isLoading: reposLoading } = useUserRepos();
  const { data: activatedRepos = [], isLoading: activatedLoading } = useActivatedRepos();
  const { invalidateActivatedRepos } = useInvalidateCache();
  const loading = reposLoading || activatedLoading;

  const [activatedSet, setActivatedSet] = useState(new Set());
  const [searchTerm, setSearchTerm] = useState('');
  const [activating, setActivating] = useState(null);

  // Sync activatedSet from cached data
  useMemo(() => {
    if (activatedRepos.length > 0) {
      setActivatedSet(new Set(activatedRepos.map(r => r.repo_full_name)));
    }
  }, [activatedRepos]);

  const toggleRepo = async (repo) => {
    const fullName = repo.full_name;
    setActivating(fullName);

    try {
      if (activatedSet.has(fullName)) {
        const res = await authFetch(`/api/activated-repos/${fullName}`, { method: 'DELETE' });
        if (res.ok) {
          setActivatedSet(prev => {
            const next = new Set(prev);
            next.delete(fullName);
            return next;
          });
          invalidateActivatedRepos();
        }
      } else {
        const res = await authFetch('/api/activated-repos', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            repo_full_name: repo.full_name,
            repo_name: repo.name,
            language: repo.language || '',
            description: repo.description || '',
            private: repo.private || false,
          }),
        });
        if (res.ok) {
          setActivatedSet(prev => new Set(prev).add(fullName));
          invalidateActivatedRepos();
        }
      }
    } catch (err) {
      console.error('Failed to toggle repo:', err);
    } finally {
      setActivating(null);
    }
  };

  const filteredRepos = allRepos.filter(r =>
    r.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    r.full_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-[#161B22] border border-[#30363D] rounded-xl w-full max-w-lg mx-4 shadow-2xl flex flex-col max-h-[80vh]">
        
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-[#30363D]">
          <div>
            <h2 className="text-[16px] font-semibold text-[#E6EDF3]">Activate Repository</h2>
            <p className="text-[13px] text-[#8B949E] mt-0.5">Select repositories to track for AI review</p>
          </div>
          <button
            onClick={onClose}
            className="text-[#8B949E] hover:text-[#E6EDF3] transition-colors p-1 rounded hover:bg-[#21262D]"
          >
            <X size={18} />
          </button>
        </div>

        {/* Search */}
        <div className="px-5 py-3 border-b border-[#30363D]">
          <div className="relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#8B949E]" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Filter repositories..."
              className="w-full bg-[#0E1116] border border-[#30363D] rounded-md py-1.5 pl-8 pr-3 text-sm text-[#E6EDF3] placeholder-[#8B949E] focus:outline-none focus:border-[#58a6ff] focus:ring-1 focus:ring-[#58a6ff]"
              autoFocus
            />
          </div>
        </div>

        {/* Repo List */}
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center py-12 text-[#8B949E]">
              <Loader2 size={20} className="animate-spin mr-2" />
              Loading repositories...
            </div>
          ) : filteredRepos.length === 0 ? (
            <div className="text-center py-12 text-[#8B949E] text-sm">
              {searchTerm ? `No repositories matching "${searchTerm}"` : 'No repositories found.'}
            </div>
          ) : (
            filteredRepos.map((repo) => {
              const isActivated = activatedSet.has(repo.full_name);
              const isToggling = activating === repo.full_name;
              return (
                <div
                  key={repo.id}
                  onClick={() => !isToggling && toggleRepo(repo)}
                  className={`flex items-center justify-between px-5 py-3 border-b border-[#30363D]/50 cursor-pointer transition-colors hover:bg-[#1C2128] ${
                    isActivated ? 'bg-[#3fb950]/5' : ''
                  }`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="shrink-0">
                      {repo.private 
                        ? <Lock size={14} className="text-amber-400" />
                        : <Globe size={14} className="text-[#8B949E]" />
                      }
                    </div>
                    <div className="min-w-0">
                      <div className="text-[14px] font-medium text-[#E6EDF3] truncate">{repo.full_name}</div>
                      {repo.description && (
                        <div className="text-[12px] text-[#8B949E] truncate mt-0.5">{repo.description}</div>
                      )}
                    </div>
                    {repo.language && (
                      <span className="text-[11px] text-[#8B949E] bg-[#21262D] px-1.5 py-0.5 rounded shrink-0">{repo.language}</span>
                    )}
                  </div>

                  <div className="shrink-0 ml-3">
                    {isToggling ? (
                      <Loader2 size={16} className="animate-spin text-[#8B949E]" />
                    ) : isActivated ? (
                      <div className="w-6 h-6 rounded-md bg-[#3fb950] flex items-center justify-center">
                        <Check size={14} className="text-black" />
                      </div>
                    ) : (
                      <div className="w-6 h-6 rounded-md border border-[#30363D] bg-[#0E1116] hover:border-[#58a6ff] transition-colors" />
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-[#30363D] flex items-center justify-between">
          <span className="text-[12px] text-[#8B949E]">
            {activatedSet.size} repositor{activatedSet.size === 1 ? 'y' : 'ies'} activated
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-[#238636] hover:bg-[#2ea043] text-white text-[13px] font-medium rounded-md transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
