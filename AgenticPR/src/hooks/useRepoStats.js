import { useParams } from 'react-router-dom';
import { useResolveRepo, useRepoStatsQuery } from './useApiCache';

/**
 * Shared hook: resolves repoName → owner/repo, then fetches /api/repos/:owner/:repo/stats
 * Now backed by React Query cache — navigating between sub-pages won't re-fetch.
 * Returns { stats, loading, error, owner, repo, repoName }
 */
export default function useRepoStats() {
  const { repoName } = useParams();
  const { owner, repo } = useResolveRepo(repoName);
  const { data: stats = null, isLoading: loading, error: queryError } = useRepoStatsQuery(owner, repo);

  return {
    stats,
    loading,
    error: queryError?.message || null,
    owner: owner || '',
    repo: repo || '',
    repoName,
  };
}
