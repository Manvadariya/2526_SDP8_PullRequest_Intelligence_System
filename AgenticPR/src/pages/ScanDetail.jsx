import React, { useState, useEffect, useRef } from 'react';
import {
    Search,
    Layers,
    FileText,
    Lock,
    ArrowLeft,
    Copy,
    CheckCircle2,
    XCircle,
    AlertTriangle,
    ShieldAlert,
    Bot,
    ChevronRight,
    Filter,
    MoreHorizontal,
    GitPullRequest
} from 'lucide-react';
import { useParams, Link, useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useJobs } from '../hooks/useApiCache';
import { API_BASE } from '../config';

const ReportRow = ({ label, count, status, onClick }) => (
    <div onClick={onClick} className="flex items-center justify-between py-2 group cursor-pointer hover:bg-[#161b22] px-2 rounded -mx-2 transition-colors">
        <div className="flex items-center gap-2">
            {status === 'success' && <CheckCircle2 size={16} className="text-[#238636]" />}
            {status === 'failed' && <XCircle size={16} className="text-[#da3633]" />}
            {status === 'neutral' && <div className="w-4 h-4 rounded-full border-2 border-gray-600" />}
            <span className="text-sm text-gray-300">{label}</span>
        </div>
        <span className={`text-xs font-mono ${count > 0 ? 'text-gray-300' : 'text-gray-600'}`}>{count}</span>
    </div>
);

const MetricBar = ({ label, passed, failed }) => (
    <div className="flex items-center justify-between bg-[#161b22] border border-[#30363d] rounded-md px-3 py-2 mb-2">
        <div className="flex items-center gap-2">
            <Layers size={16} className="text-gray-400" />
            <span className="text-sm text-gray-300 font-medium">{label}</span>
        </div>
        <div className="flex items-center gap-2">
            {passed && <span className="text-xs bg-[#238636]/20 text-[#3fb950] px-2 py-0.5 rounded border border-[#238636]/50">{passed}</span>}
            {failed && <span className="text-xs bg-[#da3633]/20 text-[#f85149] px-2 py-0.5 rounded border border-[#da3633]/50">{failed}</span>}
            <ChevronRight size={16} className="text-gray-500" />
        </div>
    </div>
);

export default function ScanDetail() {
    const navigate = useNavigate();
    const [selectedJob, setSelectedJob] = useState(null);
    const [jobDetails, setJobDetails] = useState(null);
    const [loading, setLoading] = useState(true);
    const params = useParams();
    const [searchParams] = useSearchParams();
    const { authFetch } = useAuth();
    const { data: jobsList = [], isLoading: jobsListLoading } = useJobs();

    useEffect(() => {
        const fetchJobData = (id) => {
            setLoading(true);
            authFetch(`/api/jobs/${id}`)
                .then(res => res.json())
                .then(data => {
                    const parsedResults = (data.results || []).map(r => ({
                        ...r,
                        output: typeof r.output_json === 'string' ? JSON.parse(r.output_json) : r.output_json
                    }));
                    setSelectedJob(data.job);
                    setJobDetails({ ...data.job, results: parsedResults });
                    setLoading(false);
                })
                .catch(err => {
                    console.error("Failed to fetch job details", err);
                    setLoading(false);
                });
        };

        if (params.id) {
            fetchJobData(params.id);
        } else if (!jobsListLoading) {
            if (jobsList.length > 0) {
                const repoFilter = searchParams.get('repo');
                let target;
                if (repoFilter) {
                    target = jobsList.find(j => j.repo_full_name === repoFilter) || jobsList[0];
                } else {
                    target = jobsList[0];
                }
                fetchJobData(target.id);
            } else {
                setLoading(false);
            }
        }
    }, [params.id, authFetch, searchParams, jobsList, jobsListLoading]);

    // Auto-refresh when job is active (queued/processing)
    useEffect(() => {
        if (!selectedJob) return;
        const isActive = selectedJob.status === 'queued' || selectedJob.status === 'processing';
        if (!isActive) return;

        const interval = setInterval(() => {
            const jobId = selectedJob.id;
            authFetch(`/api/jobs/${jobId}`)
                .then(res => res.json())
                .then(data => {
                    const parsedResults = (data.results || []).map(r => ({
                        ...r,
                        output: typeof r.output_json === 'string' ? JSON.parse(r.output_json) : r.output_json
                    }));
                    setSelectedJob(data.job);
                    setJobDetails({ ...data.job, results: parsedResults });
                })
                .catch(err => console.error("Auto-refresh failed", err));
        }, 4000);

        return () => clearInterval(interval);
    }, [selectedJob?.id, selectedJob?.status, authFetch]);

    const getIssues = () => {
        if (!jobDetails?.results) return [];
        let allIssues = [];
        jobDetails.results.forEach(res => {
            if (!res.output) return;

            // Output might be a stringified summary
            let out = res.output;
            if (typeof out === 'string') {
                try { out = JSON.parse(out); } catch (e) { }
            }

            // Extract from different possible array names returned by agents
            const ic = Array.isArray(out.inline_comments) ? out.inline_comments : [];
            const cm = Array.isArray(out.comments) ? out.comments : [];
            const is = Array.isArray(out.issues) ? out.issues : [];

            let combined = [...ic, ...cm, ...is];

            // Format them uniformly
            const formatted = combined.map(c => ({
                title: c.title || c.rule_id || c.body?.substring(0, 50) || c.message?.substring(0, 50) || "Code finding",
                message: c.description || c.body || c.message || "No description provided.",
                severity: c.severity || c.level || "medium",
                file: c.file || c.path || c.location?.file || "unknown",
                line: c.line || c.start_line || c.location?.line || 0,
                code: c.code || c.snippet
            }));

            allIssues = [...allIssues, ...formatted];

            if (out.findings && Array.isArray(out.findings)) {
                // Security findings often have different structure
                allIssues = [...allIssues, ...out.findings.map(f => ({
                    title: f.title || f.rule_id || "Security Finding",
                    message: f.description || f.message || f.body,
                    severity: f.severity || f.level || "high",
                    file: f.file || f.path || f.location?.file || "unknown",
                    line: f.line || f.start_line || f.location?.line || 0,
                    code: f.code || f.snippet
                }))];
            }
        });
        return allIssues;
    };

    const getSummaryStats = () => {
        if (!jobDetails?.results || jobDetails.results.length === 0) return null;
        let out = jobDetails.results[0].output;
        if (typeof out === 'string') {
            try { out = JSON.parse(out); } catch (e) { }
        }
        return out;
    };

    const summaryStats = getSummaryStats();
    const issues = getIssues();
    const criticalCount = issues.filter(i => (i.severity || '').toLowerCase().includes('critical') || (i.severity || '').toLowerCase().includes('high')).length;
    const [searchTerm, setSearchTerm] = useState('');

    const exactTime = (iso) => {
        if (!iso) return '';
        const d = new Date(iso);
        return isNaN(d.getTime()) ? '' : d.toLocaleString(undefined, {
            month: 'short', day: 'numeric',
            hour: '2-digit', minute: '2-digit'
        });
    };

    const filteredIssues = issues.filter(issue =>
        (issue.title || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (issue.message || '').toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (loading) return <div className="text-white p-8">Loading scan details...</div>;

    if (!selectedJob) return <div className="text-white p-8">No scan selected or found.</div>;

    return (
        <div className="flex-1 flex flex-col min-w-0 bg-[#0d1117] h-full overflow-hidden">

            {/* Top Header */}
            <header className="border-b border-[#30363d] bg-[#0d1117] shrink-0">
                <div className="px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-2 text-sm text-gray-400">
                        <Link to="/repositories" className="hover:text-white flex items-center"><ArrowLeft size={16} className="inline mr-1" />Back</Link>
                        <span className="text-gray-600">/</span>
                        <Lock size={16} />
                        <span className="hover:underline cursor-pointer">{selectedJob?.repo_full_name?.split('/')[0] || 'Org'}</span>
                        <span className="text-gray-600">/</span>
                        <span className="font-semibold text-white hover:underline cursor-pointer">{selectedJob?.repo_full_name?.split('/')[1] || 'Repo'}</span>
                        <span className="text-gray-600">/</span>
                        <span className="font-mono text-xs bg-[#1f2937] px-2 py-0.5 rounded text-gray-300">PR #{selectedJob?.pr_number}</span>
                    </div>
                </div>

            </header>

            {/* Secondary Header (Context) */}
            <div className="border-b border-[#30363d] bg-[#0d1117] px-6 py-4 flex items-center justify-between shrink-0">
                <div className="flex items-center gap-4">
                    <div className={`p-2 rounded-full ${selectedJob.status === 'success' ? 'bg-green-900/20 text-green-500' :
                            selectedJob.status === 'processing' ? 'bg-blue-900/20 text-blue-400 animate-pulse' :
                                selectedJob.status === 'queued' ? 'bg-yellow-900/20 text-yellow-400' :
                                    'bg-red-900/20 text-red-500'
                        }`}>
                        {selectedJob.status === 'success' && <CheckCircle2 size={24} />}
                        {selectedJob.status === 'processing' && <Bot size={24} className="animate-spin" />}
                        {selectedJob.status === 'queued' && <AlertTriangle size={24} />}
                        {selectedJob.status === 'failure' && <AlertTriangle size={24} />}
                    </div>
                    <div>
                        <div className="flex items-center gap-3">
                            <h1 className="text-lg font-semibold text-white">
                                {selectedJob.status === 'processing' ? 'Analyzing PR...' :
                                    selectedJob.status === 'queued' ? 'Review Queued' :
                                        'Analysis Results'}
                            </h1>
                            <span className="bg-[#1f2937] px-2 py-0.5 rounded-full text-xs font-mono text-gray-400 border border-[#30363d] flex items-center gap-1">
                                <GitPullRequest size={12} />
                                {selectedJob.commit_sha ? selectedJob.commit_sha.substring(0, 8) : 'Unknown'}
                            </span>
                        </div>
                        <p className="text-sm text-gray-500">Scan completed at {exactTime(selectedJob.created_at)}</p>
                    </div>
                </div>
                <button className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-gray-300 border border-[#30363d] rounded-md hover:bg-[#1f2937] hover:border-gray-500 transition-colors">
                    <Copy size={14} />
                    Copy JSON
                </button>
            </div>

            {/* Scrollable Content Area */}
            <div className="flex-1 overflow-y-auto bg-[#0d1117] p-6">
                <div className="grid grid-cols-12 gap-6 max-w-[1600px] mx-auto pb-10">

                    {/* Left Column: Report Card */}
                    <div className="col-span-12 lg:col-span-3">
                        <div className="mb-4">
                            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                                <FileText size={16} />
                                Report Card
                            </h3>

                            <div className="bg-[#1f2937]/50 rounded-md p-1 mb-1 border border-[#30363d] flex items-center justify-between px-3 py-2 text-white">
                                <div className="flex items-center gap-2">
                                    {selectedJob.status === 'success' && issues.length === 0 ? <CheckCircle2 size={16} className="text-[#238636]" /> : <AlertTriangle size={16} className="text-[#f85149]" />}
                                    <span className="font-medium">Status</span>
                                </div>
                                <span className={`text-xs px-2 py-0.5 rounded font-bold ${selectedJob.status === 'success' ? 'bg-[#238636]' : 'bg-[#da3633]'}`}>{selectedJob.status ? selectedJob.status.toUpperCase() : 'UNKNOWN'}</span>
                            </div>

                            <div className="space-y-1 mb-6 border-t border-[#30363d] pt-4">
                                <ReportRow
                                    label="Issues Found"
                                    count={issues.length > 0 ? issues.length : (summaryStats?.inline_comments || 0)}
                                    status={(issues.length > 0 || summaryStats?.inline_comments > 0) ? 'failed' : 'success'}
                                    onClick={() => {
                                        if (selectedJob?.repo_full_name && selectedJob?.pr_number) {
                                            window.open(`https://github.com/${selectedJob.repo_full_name}/pull/${selectedJob.pr_number}`, '_blank', 'noreferrer');
                                        }
                                    }}
                                />
                                <ReportRow
                                    label="Critical"
                                    count={criticalCount > 0 ? criticalCount : (summaryStats?.security_issues || 0)}
                                    status={(criticalCount > 0 || summaryStats?.security_issues > 0) ? 'failed' : 'success'}
                                />
                            </div>

                        </div>
                    </div>

                    {/* Right Column: Code/Issues */}
                    <div className="col-span-12 lg:col-span-9">

                        {/* Summary Metrics */}
                        <div className="space-y-2 mb-4">
                            <MetricBar
                                label="Total Issues"
                                passed={(issues.length === 0 && (summaryStats?.inline_comments || 0) === 0) ? "0 Issues" : null}
                                failed={(issues.length > 0 || summaryStats?.inline_comments > 0) ? `${issues.length || summaryStats?.inline_comments} Issues Found` : null}
                            />
                        </div>

                        {/* Search & Filter */}
                        <div className="flex gap-2 mb-4">
                            <div className="relative flex-1">
                                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                                <input
                                    type="text"
                                    placeholder="Search issues..."
                                    className="w-full bg-[#0d1117] border border-[#30363d] rounded-md pl-9 pr-4 py-2 text-sm text-gray-300 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                />
                            </div>
                        </div>

                        {/* Issues List */}
                        <div className="space-y-4">
                            {filteredIssues.map((issue, idx) => (
                                <div key={idx} className="bg-[#161b22] border border-[#30363d] rounded-lg overflow-hidden">
                                    <div className="p-4 border-b border-[#30363d]">
                                        <div className="flex items-start justify-between mb-2">
                                            <h3 className="text-base font-semibold text-gray-100">{issue.title || "Issue Detected"}</h3>
                                        </div>
                                        <p className="text-sm text-gray-400 mb-4 leading-relaxed">
                                            {issue.message}
                                        </p>

                                        <div className="flex items-center gap-2">
                                            <span className={`px-2 py-1 rounded text-xs font-bold ${['critical', 'high'].includes((issue.severity || '').toLowerCase()) ? 'bg-red-900/50 text-red-500' : 'bg-yellow-900/50 text-yellow-500'}`}>
                                                {(issue.severity || 'Medium').toUpperCase()}
                                            </span>
                                            <span className="text-xs text-gray-400 flex items-center gap-1">
                                                <FileText size={10} />
                                                {issue.file}:{issue.line}
                                            </span>
                                        </div>
                                    </div>
                                    {/* Simple Code snippet view if context is available */}
                                    {issue.code && (
                                        <div className="bg-[#0d1117] p-4 overflow-x-auto border-t border-[#30363d]">
                                            <div className="font-mono text-xs leading-6 text-gray-300">
                                                <pre>{issue.code}</pre>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ))}
                            {filteredIssues.length === 0 && issues.length > 0 && (
                                <div className="text-center text-gray-500 py-10 bg-[#161b22] border border-[#30363d] rounded-lg">
                                    <p className="text-gray-400">No issues match your search.</p>
                                </div>
                            )}
                            {issues.length === 0 && (summaryStats?.inline_comments || 0) === 0 && (
                                <div className="text-center text-gray-500 py-10 bg-[#161b22] border border-[#30363d] rounded-lg">
                                    <CheckCircle2 size={48} className="mx-auto text-green-600 mb-2" />
                                    <h3 className="text-lg font-medium text-gray-300">No issues found</h3>
                                    <p>Great job! The code looks clean.</p>
                                </div>
                            )}
                            {issues.length === 0 && (summaryStats?.inline_comments || 0) > 0 && (
                                <div className="text-center text-gray-500 py-10 bg-[#161b22] border border-[#30363d] rounded-lg">
                                    <AlertTriangle size={48} className="mx-auto text-yellow-600 mb-2" />
                                    <h3 className="text-lg font-medium text-gray-300">{summaryStats.inline_comments} issues found</h3>
                                    <p>Please check the PR details page to view the specific inline comments.</p>
                                </div>
                            )}
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
}
