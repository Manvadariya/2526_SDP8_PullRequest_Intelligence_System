const DeepSourceLogo = () => (
    <img
        src="data:image/svg+xml,%3csvg%20width='28'%20height='32'%20viewBox='0%200%2028%2032'%20fill='none'%20xmlns='http://www.w3.org/2000/svg'%3e%3cpath%20d='M0%2032V0H11.2568C14.7546%200%2017.6898%200.763592%2020.1422%202.3315C22.5544%203.85916%2024.4036%205.86922%2025.6099%208.32144C26.8157%2010.7737%2027.4591%2013.3466%2027.4591%2016C27.4591%2018.6937%2026.856%2021.2661%2025.6099%2023.6786C24.4036%2026.1308%2022.5544%2028.1006%2020.1422%2029.6685C17.7296%2031.1962%2014.7546%2032%2011.2568%2032H2.09068C1.46057%2032%200.193974%2032%200%2032Z'%20fill='%23080808'/%3e%3cpath%20d='M4.54303%207.19617H15.9608C16.9257%207.19617%2017.7296%208%2017.7296%208.96479C17.7296%209.92958%2016.9257%2010.7339%2015.9608%2010.7339H4.54303V7.19617Z'%20fill='%233DDC97'/%3e%3cpath%20d='M4.54303%2021.1861H18.5339C19.4988%2021.1861%2020.3027%2021.9899%2020.3027%2022.9547C20.3027%2023.9195%2019.4988%2024.7238%2018.5339%2024.7238H4.54303V21.1861Z'%20fill='%23F12A1F'/%3e%3cpath%20d='M4.54303%2014.1911H12.4631C13.428%2014.1911%2014.2318%2014.995%2014.2318%2015.9598C14.2318%2016.9245%2013.428%2017.7289%2012.4631%2017.7289H4.54303V14.1911Z'%20fill='%23FFB400'/%3e%3c/svg%3e"
        alt="DeepSource"
        className="w-7 h-7"
    />
);

const annotations = [
    {
        file: 'payments/reconciliation.py',
        lineStart: 142,
        lineEnd: 144,
        lines: [
            '            for merchant_id, txn_group in groupby(',
            '                pending_transactions, key=lambda txn: txn.merchant_id',
            '            ):',
        ],
        title: (
            <>
                <code className="inline-code">itertools.groupby</code> without sorting causes incorrect grouping
            </>
        ),
        description: [
            <>
                The code uses <code className="inline-code text-xs">itertools.groupby</code> on{' '}
                <code className="inline-code text-xs">pending_transactions</code>, a queryset without a guaranteed order.{' '}
                <code className="inline-code text-xs">groupby</code> only groups consecutive elements with the same key.
                If transactions for the same merchant are not adjacent, they will be settled in separate batches, leading to
                duplicate payouts.
            </>,
            <>
                Add a sort operation on <code className="inline-code text-xs">pending_transactions</code> by{' '}
                <code className="inline-code text-xs">merchant_id</code> before the{' '}
                <code className="inline-code text-xs">groupby</code> call. This ensures all transactions for the same
                merchant are grouped together for a single settlement.
            </>,
        ],
    },
    {
        file: 'invoicing/services/export.py',
        lineStart: 78,
        lineEnd: 81,
        lines: [
            '        result = subprocess.run(',
            '            cmd,',
            '            shell=True,',
            '            capture_output=True',
        ],
        title: (
            <>
                Potential command injection vulnerability with <code className="inline-code">shell=True</code>
            </>
        ),
        description: [
            <>
                Using <code className="inline-code text-xs">subprocess.run</code> with{' '}
                <code className="inline-code text-xs">shell=True</code> to generate invoice PDFs can lead to command
                injection if the <code className="inline-code text-xs">cmd</code> variable includes merchant-supplied data
                such as invoice numbers or company names.
            </>,
            <>
                Consider using <code className="inline-code text-xs">shell=False</code> and passing the command as a list
                of arguments instead. This prevents shell interpretation of special characters in merchant-provided input.
            </>,
        ],
    },
    {
        file: 'api/middleware/auth.py',
        lineStart: 53,
        lineEnd: 55,
        lines: [
            '        api_key = request.headers.get("X-Api-Key")',
            '        if api_key:',
            '            merchant = db.query(Merchant).filter(Merchant.api_key == api_key).first()',
        ],
        title: 'API key comparison vulnerable to timing attacks',
        description: [
            <>
                The merchant API key is compared directly using <code className="inline-code text-xs">==</code> which is
                vulnerable to timing attacks. An attacker could potentially recover the key character by character by
                measuring response time differences, compromising merchant accounts and payment data.
            </>,
            <>
                Use a constant-time comparison function like{' '}
                <code className="inline-code text-xs">secrets.compare_digest()</code> to prevent timing-based side-channel
                attacks on sensitive API key comparisons.
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
                        Inline review on pull requests
                    </h3>
                    <p className="mt-2 font-medium text-base text-gray-10 leading-relaxed">
                        Catch bugs, anti-patterns, and security vulnerabilities on every pull request. Powered by
                        5,000+ deterministic rules along with our state-of-the-art AI review agent.
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
                                    <DeepSourceLogo />
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
                                    <span className="flex-shrink-0 font-semibold text-gray-12">deepsource</span>
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
                                            <span className="font-semibold text-gray-12">deepsource</span>
                                            <span className="bot-badge border-gray-4 text-gray-8">bot</span>
                                            <span className="text-gray-8">left a comment</span>
                                        </div>
                                    </div>
                                    <div className="px-4 py-3 bg-gray-1">
                                        <p className="text-sm text-gray-11">
                                            DeepSource reviewed changes in the commit range{' '}
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
                                                            <DeepSourceLogo />
                                                        </div>
                                                    </div>
                                                    <div className="flex-1 min-w-0">
                                                        <div className="flex items-center gap-1.5 text-sm">
                                                            <span className="font-semibold text-gray-12">deepsource</span>
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
