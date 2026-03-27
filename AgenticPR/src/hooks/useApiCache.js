/**
 * Centralized cached API hooks using TanStack React Query.
 *
 * Every GET endpoint in the app is wrapped here so that navigating
 * between pages serves data from cache instead of hitting the backend
 * on every mount.  Cache times are tuned per-resource:
 *
 *   /api/user/repos      → 5 min (rarely changes during a session)
 *   /api/activated-repos  → 3 min
 *   /api/jobs             → 1 min (changes as new reviews come in)
 *   /api/jobs/:id         → 5 min (immutable once created)
 *   PR lists / details    → 2 min
 *   PR comments           → 2 min
 *   Review data           → 5 min (immutable per review run)
 *   Repo stats            → 3 min
 */


import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import { useAuth } from '../context/AuthContext';
import { API_BASE } from '../config';


// ─── helpers ────────────────────────────────────────────────────────
const jsonOrThrow = async (res, label) => {
  if (!res.ok) throw new Error(`${label}: ${res.status}`);
  return res.json();
};


// ─── 1. User Repos (most reused – every page resolves owner from this) ──
export function useUserRepos() {
  const { authFetch } = useAuth();
  return useQuery({
    queryKey: ['user-repos'],
    queryFn: () => authFetch('/api/user/repos').then(r => jsonOrThrow(r, 'user-repos')),
    staleTime: 5 * 60 * 1000,
    gcTime: 15 * 60 * 1000,
  });
}


// ─── 2. Activated Repos ─────────────────────────────────────────────
export function useActivatedRepos() {
  const { authFetch } = useAuth();
  return useQuery({
    queryKey: ['activated-repos'],
    queryFn: () => authFetch('/api/activated-repos').then(r => jsonOrThrow(r, 'activated-repos')),
    staleTime: 3 * 60 * 1000,
  });
}


// ─── 3. Jobs list (auto-polls every 3s when active jobs exist) ───────
export function useJobs() {
  const { authFetch } = useAuth();
  return useQuery({
    queryKey: ['jobs'],
    queryFn: () => authFetch('/api/jobs').then(r => jsonOrThrow(r, 'jobs')),
    staleTime: 3 * 1000,
    refetchInterval: (query) => {
      const jobs = query.state.data;
      if (!Array.isArray(jobs)) return false;
      const hasActive = jobs.some(j => j.status === 'queued' || j.status === 'processing');
      return hasActive ? 3000 : false;
    },
  });
}


// ─── 4. Single Job detail (auto-polls when job is active) ───────────
export function useJobDetail(jobId) {
  const { authFetch } = useAuth();
  return useQuery({
    queryKey: ['job', jobId],
    queryFn: () => authFetch(`/api/jobs/${jobId}`).then(r => jsonOrThrow(r, `job-${jobId}`)),
    enabled: !!jobId,
    staleTime: 3 * 1000,
    gcTime: 15 * 60 * 1000,
    refetchInterval: (query) => {
      const job = query.state.data;
      if (!job) return false;
      return (job.status === 'queued' || job.status === 'processing') ? 3000 : false;
    },
  });
}


// ─── 4b. Active job lookup for a specific PR ────────────────────────
export function useActiveJobForPR(repoFullName, prNumber) {
  const { data: jobs = [] } = useJobs();
  if (!repoFullName || !prNumber) return null;
  return jobs.find(
    j => j.repo_full_name === repoFullName &&
      j.pr_number === prNumber &&
      (j.status === 'queued' || j.status === 'processing')
  ) || jobs.find(
    j => j.repo_full_name === repoFullName &&
      j.pr_number === prNumber
  ) || null;
}


// ─── 5. PR list for a repo ──────────────────────────────────────────
export function usePullRequests(owner, repo, state = 'open') {
  const { authFetch } = useAuth();
  return useQuery({
    queryKey: ['pulls', owner, repo, state],
    queryFn: () =>
      authFetch(`/api/user/repos/${owner}/${repo}/pulls?state=${state}`)
        .then(r => jsonOrThrow(r, 'pulls')),
    enabled: !!owner && !!repo,
    staleTime: 2 * 60 * 1000,
  });
}


// ─── 6. Single PR detail ────────────────────────────────────────────
export function usePRDetail(owner, repo, number) {
  const { authFetch } = useAuth();
  return useQuery({
    queryKey: ['pr', owner, repo, number],
    queryFn: () =>
      authFetch(`/api/user/repos/${owner}/${repo}/pulls/${number}`)
        .then(r => jsonOrThrow(r, 'pr-detail')),
    enabled: !!owner && !!repo && !!number,
    staleTime: 2 * 60 * 1000,
  });
}


// ─── 7. PR review data (our agent results) ──────────────────────────
export function usePRReviewData(owner, repo, number) {
  const { authFetch } = useAuth();
  return useQuery({
    queryKey: ['review-data', owner, repo, number],
    queryFn: () =>
      authFetch(`/api/repos/${owner}/${repo}/pr/${number}/review-data`)
        .then(r => jsonOrThrow(r, 'review-data')),
    enabled: !!owner && !!repo && !!number,
    staleTime: 5 * 60 * 1000,
    gcTime: 15 * 60 * 1000,
  });
}


// ─── 8. PR comments ─────────────────────────────────────────────────
export function usePRComments(owner, repo, number) {
  const { authFetch } = useAuth();
  return useQuery({
    queryKey: ['pr-comments', owner, repo, number],
    queryFn: async () => {
      const res = await authFetch(`/api/user/repos/${owner}/${repo}/pulls/${number}/comments`);
      if (!res.ok) throw new Error(`comments: ${res.status}`);
      const data = await res.json();
      return Array.isArray(data) ? data : [];
    },
    enabled: !!owner && !!repo && !!number,
    staleTime: 2 * 60 * 1000,
  });
}


// ─── 9. Repo stats ─────────────────────────────────────────────────
export function useRepoStatsQuery(owner, repo) {
  return useQuery({
    queryKey: ['repo-stats', owner, repo],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/repos/${owner}/${repo}/stats`);
      if (!res.ok) throw new Error(`repo-stats: ${res.status}`);
      return res.json();
    },
    enabled: !!owner && !!repo,
    staleTime: 3 * 60 * 1000,
  });
}


// ─── Helper: resolve owner/repo from repoName param ────────────────
export function useResolveRepo(repoName) {
  const { data: repos } = useUserRepos();
  if (!repos || !repoName) return { owner: null, repo: null, matched: null };
  const matched = repos.find(
    r => r.name.toLowerCase() === repoName.toLowerCase() ||
      r.full_name.toLowerCase().includes(repoName.toLowerCase())
  );
  if (!matched) return { owner: null, repo: null, matched: null };
  const [owner, repo] = matched.full_name.split('/');
  return { owner, repo, matched };
}


// ─── Cache invalidation helpers ─────────────────────────────────────
export function useInvalidateCache() {
  const qc = useQueryClient();
  return {
    invalidateActivatedRepos: () => qc.invalidateQueries({ queryKey: ['activated-repos'] }),
    invalidateJobs: () => qc.invalidateQueries({ queryKey: ['jobs'] }),
    invalidateUserRepos: () => qc.invalidateQueries({ queryKey: ['user-repos'] }),
    invalidateAll: () => qc.invalidateQueries(),
  };
}


// ─── Mutation: Trigger Manual Review ────────────────────────────────
export function useTriggerReview() {
  const { authFetch } = useAuth();
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async ({ owner, repo, prNumber, commitSha }) => {
      const res = await authFetch('/api/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo: `${owner}/${repo}`,
          pr_number: prNumber,
          commit_sha: commitSha || null,
        }),
      });

      if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: 'Failed to trigger review' }));
        throw new Error(error.detail || 'Failed to trigger review');
      }

      return res.json();
    },
    onSuccess: (data) => {
      // Invalidate jobs list to show the new job
      qc.invalidateQueries({ queryKey: ['jobs'] });
      // Invalidate review data for this PR
      qc.invalidateQueries({ queryKey: ['review-data'] });
    },
  });
}



