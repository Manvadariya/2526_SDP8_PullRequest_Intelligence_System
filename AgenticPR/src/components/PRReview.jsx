const AgenticPRLogo = () => (
    <div className="w-7 h-7 rounded bg-juniper-7 flex items-center justify-center text-white font-bold text-[10px]">PR</div>
);

const annotations = [
    {
        file: 'backend/src/webhooks/agents/reviewer.py',
        lineStart: 84,
        lineEnd: 87,
        lines: [
            '            response = self.llm.chat.completions.create(',
            '                model=model,',
            '                messages=messages,',
            '                temperature=0.0',
        ],
        title: (
            <>
                Missing <code className="inline-code">max_tokens</code> limit may cause unbounded LLM cost spikes
            </>
        ),
        description: [
            <>
                The <code className="inline-code text-xs">chat.completions.create</code> call does not set a{' '}
                <code className="inline-code text-xs">max_tokens</code> parameter. On large PRs with many changed files,
                the model may generate very long responses, leading to unexpected API cost overruns and latency.
            </>,
            <>
                Add <code className="inline-code text-xs">max_tokens=4096</code> (or an env-configurable limit) to the
                completion call. Consider also streaming the response to surface partial output faster.
            </>,
        ],
    },
    {
        file: 'backend/src/webhooks/core/github_client.py',
        lineStart: 112,
        lineEnd: 115,
        lines: [
            '    def post_review_comment(self, repo, pr_number, commit_sha, body, path, line):',
            '        url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}/reviews"',
            '        payload = {"body": body, "event": "COMMENT", "commit_id": commit_sha,',
            '                   "comments": [{"path": path, "line": line, "body": body}]}',
        ],
        title: 'Duplicate review body: top-level body echoes inline comment body',
        description: [
            <>
                The <code className="inline-code text-xs">body</code> field at the top level of the review payload
                duplicates the inline comment body, causing the same feedback to appear twice in GitHub — once as a
                review summary and once as an inline comment.
            </>,
            <>
                Pass an empty string or a distinct summary to the top-level{' '}
                <code className="inline-code text-xs">body</code> field and keep the detailed text only inside the{' '}
                <code className="inline-code text-xs">comments</code> array.
            </>,
        ],
    },
    {
        file: 'backend/src/webhooks/core/orchestrator.py',
        lineStart: 61,
        lineEnd: 64,
        lines: [
            '        repo_path = tempfile.mkdtemp()',
            '        subprocess.run(["git", "clone", pr.clone_url, repo_path], check=True)',
            '        try:',
            '            result = self._run_agents(repo_path, pr)',
        ],
        title: 'Temporary clone directory not cleaned up on agent failure',
        description: [
            <>
                When <code className="inline-code text-xs">_run_agents</code> raises an exception the{' '}
                <code className="inline-code text-xs">tempfile.mkdtemp()</code> directory is never deleted, leaking
                disk space on every failed review job.
            </>,
            <>
                Wrap the clone lifecycle in a{' '}
                <code className="inline-code text-xs">try / finally</code> block (or use{' '}
                <code className="inline-code text-xs">tempfile.TemporaryDirectory</code> as a context manager) to
                guarantee cleanup regardless of outcome.
            </>,
        ],
    },
];

export default function PRReview() {
    return (
        <div className="bento-row grid grid-cols-1 sm:grid-cols-12 gap-8 sm:gap-16">
            {/* Text */}
            <div className="sm:col-span-3 flex flex-col justify-between py-2">
                <div>
                    <h3 className="text-xl font-semibold tracking-tight text-gray-12">
                        Inline AI review on every pull request
                    </h3>
                    <p className="mt-2 font-medium text-base text-gray-10 leading-relaxed">
                        AgenticPR posts inline review comments directly on GitHub PRs — catching security
                        vulnerabilities, logic bugs, and best-practice violations powered by multi-agent
                        LLM analysis.
                    </p>
                </div>
            </div>

            {/* PR Review Demo */}
            <div className="sm:col-span-9">
                <div
                    className="github-pr-review bg-gray-1 px-6 surface-elevated rounded-md h-72 sm:h-[500px] overflow-y-auto no-scrollbar"
                    style={{
                        maskImage: 'linear-gradient(to bottom, transparent, #010409 40px, #010409 calc(100% - 40px), transparent)',
                        WebkitMaskImage: 'linear-gradient(to bottom, transparent, #010409 40px, #010409 calc(100% - 40px), transparent)',
                    }}
                >
                    <div className="relative">
                        {/* Header */}
                        <div className="flex items-center">
                            <div className="flex-shrink-0 mr-3 mt-6 hidden sm:block">
                                <div className="logo-square">
                                    <AgenticPRLogo />
                                </div>
                            </div>
                            <div className="flex flex-col items-center mr-3 flex-shrink-0">
                                <div className="timeline-line-top" />
                                <div className="eye-icon-wrapper">
                                    <svg height="16" viewBox="0 0 16 16" width="16" className="text-[#59636e]" fill="currentColor">
                                        <path d="M8 2c1.981 0 3.671.992 4.933 2.078 1.27 1.091 2.187 2.345 2.637 3.023a1.62 1.62 0 0 1 0 1.798c-.45.678-1.367 1.932-2.637 3.023C11.67 13.008 9.981 14 8 14c-1.981 0-3.671-.992-4.933-2.078C1.797 10.83.88 9.576.43 8.898a1.62 1.62 0 0 1 0-1.798c.45-.677 1.367-1.931 2.637-3.022C4.33 2.992 6.019 2 8 2ZM1.679 7.932a.12.12 0 0 0 0 .136c.411.622 1.241 1.75 2.366 2.717C5.176 11.758 6.527 12.5 8 12.5c1.473 0 2.825-.742 3.955-1.715 1.124-.967 1.954-2.096 2.366-2.717a.12.12 0 0 0 0-.136c-.412-.621-1.242-1.75-2.366-2.717C10.824 4.242 9.473 3.5 8 3.5c-1.473 0-2.825.742-3.955 1.715-1.124.967-1.954 2.096-2.366 2.717ZM8 10a2 2 0 1 1-.001-3.999A2 2 0 0 1 8 10Z" />
                                    </svg>
                                </div>
                            </div>
                            <div className="flex-1 flex items-center justify-between mt-8">
                                <div className="flex items-center gap-2 text-sm">
                                    <span className="flex-shrink-0 font-semibold text-gray-12">agenticpr</span>
                                    <span className="bot-badge border-gray-4 text-gray-8">bot</span>
                                    <span className="text-gray-8">reviewed</span>
                                    <span className="text-gray-8 underline flex-shrink-0 cursor-default">a few minutes ago</span>
                                </div>
                            </div>
                        </div>

                        {/* Comment box */}
                        <div className="flex">
                            <div className="flex-shrink-0 hidden sm:block" style={{ width: 40, marginRight: 12 }} />
                            <div className="flex-shrink-0" style={{ width: 28, marginRight: 12 }}>
                                <div className="timeline-line-vertical" />
                            </div>
                            <div className="flex-1 min-w-0">
                                <div className="comment-box">
                                    <div className="comment-header bg-gray-2 border-gray-4">
                                        <div className="flex items-center gap-1.5 text-sm">
                                            <span className="font-semibold text-gray-12">agenticpr</span>
                                            <span className="bot-badge border-gray-4 text-gray-8">bot</span>
                                            <span className="text-gray-8">left a comment</span>
                                        </div>
                                    </div>
                                    <div className="px-4 py-3 bg-gray-1">
                                        <p className="text-sm text-gray-11">
                                            AgenticPR reviewed changes in the commit range{' '}
                                            <code className="inline-code text-xs bg-gray-3">b76c8fa...63debb2</code> on this pull request.
                                            Below is the summary for the review, and you can see the individual issues we found as
                                            review comments.
                                        </p>
                                    </div>
                                </div>

                                {/* Annotations */}
                                {annotations.map((ann, idx) => (
                                    <div key={idx} className="mt-4">
                                        <div className="annotation-card">
                                            <div className="file-header bg-gray-2 border-gray-4">
                                                <div className="text-xs mono-font text-gray-12">{ann.file}</div>
                                            </div>
                                            <div className="lines-header bg-gray-1 border-gray-4">
                                                <span className="text-xs text-gray-8">
                                                    Comment on lines{' '}
                                                    <span className="text-juniper-7 mono-font">+{ann.lineStart}</span> to{' '}
                                                    <span className="text-juniper-7 mono-font">+{ann.lineEnd}</span>
                                                </span>
                                            </div>
                                            <div className="overflow-x-auto">
                                                <table className="w-full text-sm mono-font">
                                                    <tbody>
                                                        {ann.lines.map((line, lineIdx) => (
                                                            <tr key={lineIdx} className="diff-line-added">
                                                                <td className="diff-line-num">{ann.lineStart + lineIdx}</td>
                                                                <td className="diff-line-sign">+</td>
                                                                <td className="diff-line-code">{line}</td>
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            </div>
                                            <div className="p-4">
                                                <div className="flex gap-3">
                                                    <div className="flex-shrink-0 hidden sm:block">
                                                        <div className="logo-square">
                                                            <AgenticPRLogo />
                                                        </div>
                                                    </div>
                                                    <div className="flex-1 min-w-0">
                                                        <div className="flex items-center gap-1.5 text-sm">
                                                            <span className="font-semibold text-gray-12">agenticpr</span>
                                                            <span className="bot-badge border-gray-4 text-gray-8">bot</span>
                                                            <span className="text-gray-8 underline cursor-default">a few minutes ago</span>
                                                        </div>
                                                        <h4 className="mt-3 text-base font-semibold text-gray-12">{ann.title}</h4>
                                                        <div className="mt-2 text-sm text-gray-9 leading-relaxed">
                                                            {ann.description.map((para, pIdx) => (
                                                                <p key={pIdx} className={pIdx > 0 ? 'mt-3' : ''}>
                                                                    {para}
                                                                </p>
                                                            ))}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))}

                                <div className="h-8 sm:h-12 w-full" />
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
