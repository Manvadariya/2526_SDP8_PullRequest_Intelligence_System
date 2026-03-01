const codeLines = [
    { num: 472, content: '    with self._get_cursor() as cur:' },
    { num: 473, content: '        try:' },
    { num: 474, content: '            # Use JSON_EXTRACT for JSON field access' },
    { num: 475, content: '            cur.execute(' },
    { num: 476, content: '                f"DELETE FROM `{self.table_name}` WHERE JSON_EXTRACT(meta, %s) = %s", 1', highlighted: true },
    { num: 477, content: '                (f"$.{key}", value),' },
    { num: 478, content: '            )' },
    { num: 479, content: '        except Exception as e:' },
    { num: 480, content: '            logger.warning("Error deleting by metadata field: %s", e)' },
    { num: 481, content: '            raise' },
];

export default function Autofix() {
    return (
        <div className="bento-row grid grid-cols-1 sm:grid-cols-12 gap-8 sm:gap-16">
            {/* Text */}
            <div className="sm:col-span-3 flex flex-col justify-between py-2">
                <div>
                    <h3 className="text-xl font-semibold tracking-tight text-gray-12">Autofix™</h3>
                    <p className="mt-2 font-medium text-base text-gray-10 leading-relaxed">
                        Verified, pre-generated patches for most issues, so you can fix issues faster without
                        breaking your flow.
                    </p>
                </div>
            </div>

            {/* Autofix Demo */}
            <div className="sm:col-span-9">
                <section className="surface-elevated rounded-md pl-4 sm:pl-12 pt-4 sm:pt-12 overflow-clip relative z-0">
                    {/* Breathing gradient background */}
                    <div className="absolute inset-0 pointer-events-none overflow-hidden z-0">
                        <div
                            className="absolute inset-0 breathing-gradient"
                            style={{
                                background: 'linear-gradient(135deg, #E0F8ED, #B7ECD4, #FAFEFC, #B7ECD4, #E0F8ED)',
                                backgroundSize: '200% 200%',
                                '--duration': '8s',
                            }}
                        />
                        <svg className="absolute inset-0 w-full h-full" style={{ opacity: 0.12 }}>
                            <filter id="breathing-noise-autofix">
                                <feTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="4" stitchTiles="stitch" />
                            </filter>
                            <rect width="100%" height="100%" filter="url(#breathing-noise-autofix)" />
                        </svg>
                    </div>

                    {/* Code Editor */}
                    <div className="autofix-demo rounded-tl-md overflow-hidden bg-ink-400 text-white font-mono text-[13px] relative z-10">
                        {/* Issue header */}
                        <div className="px-5 pt-5 pb-4">
                            <h3 className="text-[15px] font-semibold text-white font-sans leading-snug">
                                String-based query with{' '}
                                <code className="px-1.5 py-0.5 rounded bg-ink-50 text-[13px] font-mono font-normal">
                                    JSON_EXTRACT
                                </code>{' '}
                                risks SQL injection
                            </h3>
                            <p className="mt-1.5 text-sm text-gray-8 font-sans leading-relaxed">
                                The code constructs an SQL DELETE statement by directly formatting self.table_name into the
                                query string and using user-controllable parameters with JSON_EXTRACT.
                            </p>
                            <div className="flex items-center gap-4 mt-3 text-sm font-sans">
                                <span className="flex items-center gap-1.5 font-medium text-gray-7">
                                    <svg width="14" height="14" viewBox="0 0 16 16" fill="#dd4425">
                                        <rect x="1" y="10" width="3" height="5" rx="0.5" />
                                        <rect x="6" y="6" width="3" height="9" rx="0.5" />
                                        <rect x="11" y="2" width="3" height="13" rx="0.5" />
                                    </svg>
                                    Critical
                                </span>
                                <span className="flex items-center gap-1.5 font-medium text-gray-7">
                                    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
                                        <path d="M8 1L2 4v4c0 4 2.5 6.5 6 7.5 3.5-1 6-3.5 6-7.5V4L8 1z" />
                                    </svg>
                                    Security
                                </span>
                                <span
                                    className="inline-flex h-6 items-center justify-center gap-1 rounded text-[12px] font-medium text-[#23C4F8] px-2 py-1"
                                    style={{
                                        background: 'rgba(35, 196, 248, 0.2)',
                                        border: '0.5px solid rgba(35, 196, 248, 0.4)',
                                    }}
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 9 9" fill="none">
                                        <path
                                            d="M3.3696 5.45639C3.33612 5.32662 3.26848 5.20818 3.17371 5.11341C3.07894 5.01864 2.9605 4.951 2.83073 4.91752L0.530102 4.32427C0.490851 4.31313 0.456305 4.28949 0.431707 4.25693C0.407108 4.22438 0.393799 4.18469 0.393799 4.14389C0.393799 4.10309 0.407108 4.0634 0.431707 4.03085C0.456305 3.9983 0.490851 3.97466 0.530102 3.96352L2.83073 3.36989C2.96046 3.33644 3.07886 3.26886 3.17363 3.17416C3.26839 3.07946 3.33606 2.9611 3.3696 2.83139L3.96285 0.530767C3.97388 0.491362 3.9975 0.456645 4.0301 0.431915C4.0627 0.407185 4.10249 0.393799 4.14341 0.393799C4.18433 0.393799 4.22413 0.407185 4.25673 0.431915C4.28933 0.456645 4.31295 0.491362 4.32398 0.530767L4.91685 2.83139C4.95033 2.96117 5.01798 3.0796 5.11275 3.17437C5.20752 3.26914 5.32595 3.33679 5.45573 3.37027L7.75635 3.96314C7.79591 3.97405 7.8308 3.99765 7.85567 4.0303C7.88053 4.06295 7.894 4.10285 7.894 4.14389C7.894 4.18493 7.88053 4.22484 7.85567 4.25749C7.8308 4.29014 7.79591 4.31373 7.75635 4.32464L5.45573 4.91752C5.32595 4.951 5.20752 5.01864 5.11275 5.11341C5.01798 5.20818 4.95033 5.32662 4.91685 5.45639L4.3236 7.75702C4.31257 7.79642 4.28896 7.83114 4.25636 7.85587C4.22376 7.8806 4.18396 7.89399 4.14304 7.89399C4.10212 7.89399 4.06232 7.8806 4.02972 7.85587C3.99712 7.83114 3.9735 7.79642 3.96248 7.75702L3.3696 5.45639Z"
                                            stroke="#23C4F8"
                                            strokeWidth="0.7875"
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                        />
                                    </svg>
                                    AI REVIEW
                                </span>
                            </div>
                        </div>

                        {/* Code block */}
                        <div className="border-t border-ink-100 overflow-x-auto">
                            <table className="w-full border-collapse">
                                <tbody>
                                    {codeLines.map((line) => (
                                        <tr key={line.num} className={line.highlighted ? 'highlighted-line' : ''}>
                                            <td
                                                className={`w-[50px] pr-3 pl-3 text-right text-gray-9 select-none align-top leading-[22px] border-r border-ink-100 ${line.highlighted ? 'highlighted-num' : ''
                                                    }`}
                                            >
                                                {line.num}
                                            </td>
                                            <td className="pr-4 pl-2 whitespace-pre leading-[22px] align-top">
                                                {line.content}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        {/* Footer */}
                        <div className="flex items-center justify-between px-4 py-3 border-t border-ink-100">
                            <div className="flex items-center gap-2 text-sm text-gray-8 min-w-0 mr-4">
                                <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" className="opacity-60 shrink-0">
                                    <path d="M2 1.75C2 .784 2.784 0 3.75 0h6.586c.464 0 .909.184 1.237.513l2.914 2.914c.329.328.513.773.513 1.237v9.586A1.75 1.75 0 0 1 13.25 16h-9.5A1.75 1.75 0 0 1 2 14.25Zm1.75-.25a.25.25 0 0 0-.25.25v12.5c0 .138.112.25.25.25h9.5a.25.25 0 0 0 .25-.25V6h-2.75A1.75 1.75 0 0 1 9 4.25V1.5Zm6.75.062V4.25c0 .138.112.25.25.25h2.688l-.011-.013-2.914-2.914-.013-.011Z" />
                                </svg>
                                <span className="truncate">api/core/rag/datasource/vdb/doris/doris_vector.py</span>
                            </div>
                            <div className="flex items-center gap-2 font-sans">
                                <button className="cta-pulse footer-btn-primary">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                                        <path d="M6.726 1.71c.075-.28.473-.28.548 0l.872 3.238c.119.442.464.787.906.906l3.238.872c.28.075.28.473 0 .548l-3.238.872a1.28 1.28 0 0 0-.906.906l-.872 3.238c-.075.28-.473.28-.548 0l-.872-3.238a1.28 1.28 0 0 0-.906-.906L1.71 7.274c-.28-.075-.28-.473 0-.548l3.238-.872c.442-.119.787-.464.906-.906zm9.986 6.405a.308.308 0 0 1 .576 0l.898 2.359c.133.349.408.624.757.757l2.359.898c.264.1.264.475 0 .575l-2.36.899a1.3 1.3 0 0 0-.756.756l-.898 2.36a.308.308 0 0 1-.576 0l-.898-2.36a1.3 1.3 0 0 0-.757-.756l-2.359-.899a.308.308 0 0 1 0-.575l2.36-.898c.348-.133.623-.408.756-.757zm-6.465 7.309a.27.27 0 0 1 .506 0l.645 1.693c.129.339.396.606.735.735l1.693.645a.27.27 0 0 1 0 .506l-1.693.645a1.27 1.27 0 0 0-.735.735l-.645 1.693a.27.27 0 0 1-.506 0l-.645-1.693a1.27 1.27 0 0 0-.735-.735l-1.693-.645a.27.27 0 0 1 0-.506l1.693-.645a1.27 1.27 0 0 0 .735-.735z" />
                                    </svg>
                                    Autofix™
                                </button>
                            </div>
                        </div>
                    </div>
                </section>
            </div>
        </div>
    );
}
