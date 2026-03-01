const categories = [
    { name: 'Security', issues: 4, grade: 'B', gradeColor: '#F6D87C', gradeBorder: '#FBEFC8' },
    { name: 'Reliability', issues: 19, grade: 'C', gradeColor: '#EE7C4B', gradeBorder: '#FFBB9D' },
    { name: 'Complexity', issues: 3, grade: 'D', gradeColor: '#D22F43', gradeBorder: '#E998A2' },
    { name: 'Hygiene', issues: 0, grade: 'A', gradeColor: '#33CB9A', gradeBorder: '#94E4CA' },
    { name: 'Coverage', issues: 11, grade: 'B', gradeColor: '#F6D87C', gradeBorder: '#FBEFC8' },
];

function GradeBadge({ grade, color, borderColor }) {
    const gradeIdx = { A: 0, B: 1, C: 2, D: 3 };
    const idx = gradeIdx[grade] || 0;

    return (
        <span className="shrink-0 h-4 flex gap-[1px]">
            {[0, 1, 2, 3].map((seg) => (
                <span
                    key={seg}
                    className="inline-block w-[6px] h-4 rounded-sm text-[10px] font-bold"
                    style={
                        seg === idx
                            ? {
                                width: 20,
                                background: color,
                                display: 'inline-flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                color: '#121317',
                                fontSize: 11,
                                fontWeight: 700,
                                borderRadius: 2,
                                fontFamily: 'ui-monospace, monospace',
                            }
                            : {
                                background: `${color}33`,
                                borderRadius: 1,
                            }
                    }
                >
                    {seg === idx ? grade : ''}
                </span>
            ))}
        </span>
    );
}

export default function PRReportCard() {
    return (
        <div className="bento-row grid grid-cols-1 sm:grid-cols-12 gap-8 sm:gap-16">
            {/* Text */}
            <div className="sm:col-span-3 flex flex-col justify-between py-2">
                <div>
                    <h3 className="text-xl font-semibold tracking-tight text-gray-12">PR Report Card</h3>
                    <p className="mt-2 font-medium text-base text-gray-10 leading-relaxed">
                        More than just issues. Structured feedback to your AI agent to help improve quality of any
                        pull request.
                    </p>
                </div>
            </div>

            {/* Report Card Demo */}
            <div className="sm:col-span-9">
                <section className="surface-elevated rounded-md px-6 relative z-0 pt-8 sm:pt-32 flex flex-col justify-end">
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
                            <filter id="breathing-noise-report">
                                <feTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="4" stitchTiles="stitch" />
                            </filter>
                            <rect width="100%" height="100%" filter="url(#breathing-noise-report)" />
                        </svg>
                    </div>

                    {/* Stacked card effect */}
                    <div className="relative max-w-[700px] mx-auto z-10">
                        {[1, 2, 3].map((i) => (
                            <div
                                key={i}
                                className="absolute bottom-0 rounded-t-md bg-ink-300 border border-ink-100 border-b-0 hidden sm:block"
                                style={{
                                    left: `${i * 12}px`,
                                    right: `${i * 12}px`,
                                    top: `${-i * 16}px`,
                                    zIndex: -i,
                                    opacity: 1 - i * 0.25,
                                }}
                            />
                        ))}

                        {/* Report Card */}
                        <div className="pr-report-card rounded-t-md overflow-hidden bg-ink-400 text-white font-sans text-[13px] border border-ink-100 border-b-0">
                            {/* Card header */}
                            <div className="flex items-center gap-1.5 px-4 py-3 bg-ink-300">
                                <svg width="16" height="16" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path
                                        d="M4.66671 1.16663V3.49996M7.00004 1.16663V3.49996M9.33337 1.16663V3.49996M4.66671 5.83329H8.16671M4.66671 8.16663H9.33337M4.66671 10.5H7.58337M3.50004 2.33329H10.5C11.1444 2.33329 11.6667 2.85563 11.6667 3.49996V11.6666C11.6667 12.311 11.1444 12.8333 10.5 12.8333H3.50004C2.85571 12.8333 2.33337 12.311 2.33337 11.6666V3.49996C2.33337 2.85563 2.85571 2.33329 3.50004 2.33329Z"
                                        stroke="#EEEEEE"
                                        strokeWidth="1.16667"
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                    />
                                </svg>
                                <span className="text-base font-medium text-white">PR Report Card</span>
                            </div>
                            <div className="border-t border-ink-100" />

                            <div className="flex flex-col sm:flex-row bg-ink-400">
                                {/* Categories */}
                                <div className="flex-1 min-w-0">
                                    {categories.map((cat, idx) => (
                                        <div
                                            key={cat.name}
                                            className={`${idx < categories.length - 1 ? 'border-b border-ink-100' : ''} flex items-center justify-between px-4 py-3`}
                                        >
                                            <div className="flex items-center gap-3">
                                                <span className="shrink-0 w-4 h-4 flex items-center justify-center">
                                                    <CategoryIcon name={cat.name} />
                                                </span>
                                                <span className="text-[#f5f5f5] text-base">{cat.name}</span>
                                            </div>
                                            <div className="flex items-center gap-3">
                                                <div className="flex items-center gap-0.5">
                                                    <svg width="12" height="12" viewBox="0 0 8 8" fill="none" className="text-gray-8">
                                                        <path d="M1.5 1.5L6.5 6.5M6.5 1.5L1.5 6.5" stroke="currentColor" strokeWidth="1" strokeLinecap="round" />
                                                    </svg>
                                                    <span className="inline-flex h-4 items-center justify-center px-1 rounded-sm bg-ink-200 text-[13.5px] font-mono text-[#c0c1c3]">
                                                        {cat.issues}
                                                    </span>
                                                </div>
                                                <GradeBadge grade={cat.grade} color={cat.gradeColor} borderColor={cat.gradeBorder} />
                                            </div>
                                        </div>
                                    ))}
                                </div>

                                {/* Divider */}
                                <div className="w-px bg-ink-100 self-stretch hidden sm:block" />
                                <div className="border-t border-ink-100 sm:hidden" />

                                {/* Summary */}
                                <div className="flex flex-1 flex-col gap-6 px-4 py-6 sm:py-3">
                                    <div className="flex items-center justify-between">
                                        <span className="text-base text-[#c0c1c3]">Overall PR Quality</span>
                                        <GradeBadge grade="B" color="#F6D87C" borderColor="#FBEFC8" />
                                    </div>
                                    <div className="flex items-center justify-between">
                                        <span className="text-base text-[#c0c1c3]">Focus Area</span>
                                        <span className="text-base font-medium text-white">Reliability</span>
                                    </div>
                                    <div className="flex flex-col gap-2.5">
                                        <span className="text-base text-[#c0c1c3]">Guidance</span>
                                        <p className="text-[14px] text-white leading-relaxed">
                                            Fix the high-severity{' '}
                                            <code className="px-0.5 py-0.5 rounded-sm bg-ink-200 text-[13.5px] font-mono text-[#c0c1c3] inline">
                                                _check_milestones
                                            </code>{' '}
                                            call outside transaction risk in contrib/referrals/team_referral.py to prevent
                                            inconsistent states.
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>
            </div>
        </div>
    );
}

function CategoryIcon({ name }) {
    const icons = {
        Security: (
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M1.33709 3.07262C3.78216 2.63402 4.79306 2.30918 6.99998 1.3125C9.20689 2.30918 10.2178 2.63402 12.6629 3.07262C13.1058 10.0934 7.42162 12.5177 6.99998 12.6875C6.57834 12.5177 0.894117 10.0934 1.33709 3.07262Z" stroke="#F5F5F5" strokeWidth="0.875" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M7 1.3125C9.20691 2.30918 10.2178 2.63402 12.6629 3.07262C13.1059 10.0934 7.42164 12.5177 7 12.6875V1.3125Z" fill="#F5F5F5" />
            </svg>
        ),
        Reliability: (
            <svg width="14" height="14" viewBox="0 0 14 14" fill="#F5F5F5">
                <path d="M11.6484 7.27351C11.3633 7.27383 11.0843 7.3566 10.8451 7.51185C10.606 7.6671 10.4168 7.8882 10.3004 8.14851H9.62117L8.88289 5.93367C8.84207 5.81204 8.76343 5.70664 8.65846 5.63287C8.55349 5.55911 8.42768 5.52084 8.29942 5.52365C8.17115 5.52646 8.04714 5.5702 7.9455 5.64849C7.84386 5.72678 7.76991 5.83552 7.73445 5.95882L6.71727 9.51898L5.40477 1.81515C5.38147 1.67936 5.31226 1.55568 5.20872 1.46478C5.10518 1.37389 4.97358 1.3213 4.83591 1.31579C4.69824 1.31028 4.56286 1.3522 4.45239 1.43453C4.34191 1.51686 4.26305 1.63462 4.22898 1.76812L2.59273 8.14851H0.875V9.35163H3.0625C3.19663 9.35162 3.3269 9.30678 3.43263 9.22425C3.53835 9.14171 3.61346 9.0262 3.64602 8.89609L4.69465 4.7032L5.96914 12.185C5.99141 12.3199 6.05896 12.4431 6.16065 12.5345C6.26234 12.6258 6.39211 12.6798 6.52859 12.6876H6.5625C6.69336 12.6875 6.82063 12.6447 6.92499 12.5658C7.02936 12.4868 7.10513 12.376 7.14082 12.2501L8.3568 8.1589L8.61684 8.94148C8.65696 9.06103 8.73364 9.16495 8.83605 9.23855C8.93845 9.31215 9.06139 9.35171 9.1875 9.35163H10.3004C10.4086 9.5943 10.5804 9.80326 10.7975 9.95647C11.0146 10.1097 11.269 10.2015 11.5339 10.2222C11.7988 10.2428 12.0644 10.1917 12.3027 10.074C12.5409 9.95633 12.743 9.77656 12.8876 9.55364C13.0322 9.33071 13.114 9.07289 13.1243 8.80737C13.1346 8.54185 13.0731 8.27847 12.9462 8.045C12.8193 7.81153 12.6318 7.61663 12.4034 7.48085C12.175 7.34507 11.9142 7.27343 11.6484 7.27351Z" />
            </svg>
        ),
        Complexity: (
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M3.79163 2.33337C4.22913 2.33337 4.97288 2.33337 5.25404 3.8095C5.53871 5.30254 5.63788 6.66404 6.12496 7.00004C5.63788 7.33604 5.53871 8.69754 5.25404 10.1906C4.97288 11.667 4.22913 11.6667 3.79163 11.6667M10.2083 11.6667C9.77079 11.6667 9.02704 11.667 8.74588 10.1906C8.46121 8.69754 8.36204 7.33604 7.87496 7.00004C8.36204 6.66404 8.46121 5.30254 8.74588 3.8095C9.02704 2.33337 9.77079 2.33337 10.2083 2.33337" stroke="#F5F5F5" strokeWidth="1.16667" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M6.12496 8.16671C5.48063 8.16671 4.95829 7.64437 4.95829 7.00004C4.95829 6.35571 5.48063 5.83337 6.12496 5.83337C6.76929 5.83337 7.29163 6.35571 7.29163 7.00004C7.29163 7.64437 6.76929 8.16671 6.12496 8.16671Z" fill="#F5F5F5" />
                <path d="M7.87496 8.16671C7.23063 8.16671 6.70829 7.64437 6.70829 7.00004C6.70829 6.35571 7.23063 5.83337 7.87496 5.83337C8.51929 5.83337 9.04163 6.35571 9.04163 7.00004C9.04163 7.64437 8.51929 8.16671 7.87496 8.16671Z" fill="#F5F5F5" />
            </svg>
        ),
        Hygiene: (
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M1.51225 9.31996C1.90425 7.84996 3.10271 6.70837 4.62404 6.70837C6.05175 6.70837 7.00521 7.999 6.97371 9.42671L6.95708 10.176C6.95085 10.4551 7.00191 10.7325 7.10711 10.991C7.21231 11.2496 7.36941 11.4838 7.56871 11.6792L7.89129 11.996C8.35387 12.4501 8.08379 13.228 7.43775 13.2817C6.60183 13.3508 5.56817 13.4167 4.66662 13.4167C3.50521 13.4167 2.34408 13.3073 1.61871 13.2225C1.18937 13.1723 0.872624 12.806 0.913749 12.376C1.00708 11.3952 1.25617 10.2795 1.51225 9.31996Z" stroke="#F5F5F5" strokeWidth="0.875" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
        ),
        Coverage: (
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M7 7.4375V11.8125C7 12.0446 6.90781 12.2671 6.74372 12.4312C6.57962 12.5953 6.35706 12.6875 6.125 12.6875C5.89294 12.6875 5.67038 12.5953 5.50628 12.4312C5.34219 12.2671 5.25 12.0446 5.25 11.8125M7 7.4375L6.73504 7.23871C6.32287 6.92964 5.81306 6.77959 5.29918 6.8161C4.78529 6.85262 4.30182 7.07325 3.9375 7.4375C3.76514 7.26513 3.56052 7.1284 3.33532 7.03512C3.11013 6.94183 2.86876 6.89382 2.625 6.89382C2.38124 6.89382 2.13987 6.94183 1.91468 7.03512C1.68948 7.1284 1.48486 7.26513 1.3125 7.4375C1.3125 4.29625 3.85875 1.75 7 1.75M7 7.4375L7.26496 7.23871C7.67713 6.92964 8.18694 6.77959 8.70082 6.8161C9.21471 6.85262 9.69818 7.07325 10.0625 7.4375C10.2349 7.26513 10.4395 7.1284 10.6647 7.03512C10.8899 6.94183 11.1312 6.89382 11.375 6.89382C11.6188 6.89382 11.8601 6.94183 12.0853 7.03512C12.3105 7.1284 12.5151 7.26513 12.6875 7.4375C12.6875 4.29625 10.1412 1.75 7 1.75M7 1.75V1.3125" stroke="#F5F5F5" strokeWidth="0.875" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
        ),
    };
    return icons[name] || null;
}
