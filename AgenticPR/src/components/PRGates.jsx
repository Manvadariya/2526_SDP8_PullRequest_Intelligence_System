const checks = [
    'AgenticPR: Python · Flake8 + Bandit',
    'AgenticPR: JavaScript · ESLint',
    'AgenticPR: AI Code Review',
    'AgenticPR: Secrets Detection',
    'AgenticPR: Custom Checks',
];

const statusTexts = [
    'Linting in progress...',
    'Linting in progress...',
    'LLM analysis in progress...',
    'Scanning for leaked keys...',
    'Running .pr-reviewer.yml rules...',
];

export default function PRGates() {
    return (
        <div className="bento-row grid grid-cols-1 sm:grid-cols-12 gap-8 sm:gap-16">
            {/* Text */}
            <div className="sm:col-span-3 flex flex-col justify-between py-2">
                <div>
                    <h3 className="text-xl font-semibold tracking-tight text-gray-12">Pull request gates</h3>
                    <p className="mt-2 font-medium text-base text-gray-10 leading-relaxed">
                        Block merges automatically when AgenticPR detects critical issues — security
                        vulnerabilities, linter failures, or custom team rule violations.
                    </p>
                </div>
            </div>

            {/* PR Checks Demo */}
            <div className="sm:col-span-9">
                <div
                    className="rounded-lg text-sm min-h-[400px] sm:min-h-[380px]"
                    style={{
                        fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif",
                    }}
                >
                    <div className="text-[#1f2328] flex flex-row gap-4">
                        {/* PR icon */}
                        <div className="shrink-0 flex justify-center">
                            <div className="w-10 h-10 rounded-lg bg-[#656d76] flex items-center justify-center">
                                <svg focusable="false" viewBox="0 0 24 24" width="20" height="20" fill="white">
                                    <path d="M15 13.25a3.25 3.25 0 1 1 6.5 0 3.25 3.25 0 0 1-6.5 0Zm-12.5 6a3.25 3.25 0 1 1 6.5 0 3.25 3.25 0 0 1-6.5 0Zm0-14.5a3.25 3.25 0 1 1 6.5 0 3.25 3.25 0 0 1-6.5 0ZM5.75 6.5a1.75 1.75 0 1 0-.001-3.501A1.75 1.75 0 0 0 5.75 6.5Zm0 14.5a1.75 1.75 0 1 0-.001-3.501A1.75 1.75 0 0 0 5.75 21Zm12.5-6a1.75 1.75 0 1 0-.001-3.501A1.75 1.75 0 0 0 18.25 15Z" />
                                    <path d="M6.5 7.25c0 2.9 2.35 5.25 5.25 5.25h4.5V14h-4.5A6.75 6.75 0 0 1 5 7.25Z" />
                                    <path d="M5.75 16.75A.75.75 0 0 1 5 16V8a.75.75 0 0 1 1.5 0v8a.75.75 0 0 1-.75.75Z" />
                                </svg>
                            </div>
                        </div>

                        {/* Checks panel */}
                        <div className="flex-1 min-w-0 border-[#d1d9e0] rounded-md border overflow-hidden">
                            {/* Header */}
                            <div className="flex items-start gap-3 p-4 border-b border-[#d1d9e0]">
                                <div className="shrink-0 mt-0.5">
                                    {/* Circle progress */}
                                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="32" height="32" fill="none">
                                        <circle cx="50" cy="50" r="44" stroke="#d1d9e0" strokeWidth="12" />
                                        <circle
                                            cx="50"
                                            cy="50"
                                            r="44"
                                            stroke="#bf8700"
                                            strokeWidth="12"
                                            strokeLinecap="round"
                                            strokeDasharray="262.637, 276.46"
                                            style={{
                                                transform: 'rotate(-81deg)',
                                                transformOrigin: '50% 50%',
                                                transition: 'stroke-dasharray 0.3s ease-out',
                                            }}
                                        />
                                    </svg>
                                </div>
                                <div className="flex-1 min-w-0">
                                    <h4 className="font-semibold text-[16px] text-[#1f2328]">
                                        Some checks haven&apos;t completed yet
                                    </h4>
                                    <p className="text-sm text-[#656d76]">5 pending checks</p>
                                </div>
                            </div>

                            {/* Check list */}
                            <div className="bg-[#f6f8fa] px-4">
                                <div className="flex items-center justify-between py-2 text-xs text-[#656d76]">
                                    <button className="flex items-center gap-1 hover:text-[#1f2328]">
                                        <span className="font-medium">5 pending checks</span>
                                        <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor">
                                            <path d="M12.78 6.22a.75.75 0 0 1 0 1.06l-4.25 4.25a.75.75 0 0 1-1.06 0L3.22 7.28a.75.75 0 0 1 1.06-1.06L8 9.94l3.72-3.72a.75.75 0 0 1 1.06 0Z" />
                                        </svg>
                                    </button>
                                </div>

                                <div>
                                    {checks.map((check, idx) => (
                                        <div
                                            key={check}
                                            className={`${idx < checks.length - 1 ? 'border-b border-[#d1d9e0]' : ''} flex items-center gap-3 px-2 py-2.5`}
                                        >
                                            <div className="w-4 h-4 flex items-center justify-center shrink-0">
                                                <div className="w-2.5 h-2.5 rounded-full bg-[#bf8700]" />
                                            </div>
                                            <div className="w-5 h-5 rounded border border-[#d1d9e0] bg-white flex items-center justify-center shrink-0 overflow-hidden">
                                                <div className="w-3 h-3 rounded bg-juniper-7 flex items-center justify-center text-white font-bold" style={{fontSize:'6px'}}>PR</div>
                                            </div>
                                            <div className="flex-1 min-w-0 flex items-center gap-2">
                                                <span className="font-medium text-[#1f2328] flex-shrink-0">{check}</span>
                                                <span className="text-[#656d76] truncate font-medium text-xs tracking-tight">
                                                    Waiting for status to be reported — {statusTexts[idx]}
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
