export default function PRDashboard() {
    return (
        <section className="relative overflow-hidden max-w-7xl mx-auto px-6 lg:mx-[5.8rem]">
            <div className="relative rounded-xl border border-gray-4 bg-gray-2 overflow-hidden min-h-[340px] flex flex-col">
                {/* Fake browser chrome */}
                <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-4 bg-gray-1">
                    <div className="w-3 h-3 rounded-full bg-[#ff5f57]" />
                    <div className="w-3 h-3 rounded-full bg-[#febc2e]" />
                    <div className="w-3 h-3 rounded-full bg-[#28c840]" />
                    <div className="ml-4 flex-1 rounded bg-gray-3 h-6 max-w-xs text-[11px] text-gray-8 flex items-center px-3">
                        app.agenticpr.dev/home
                    </div>
                </div>
                {/* PR list mockup */}
                <div className="flex-1 p-6 space-y-3">
                    {[
                        { pr: '#214', title: 'feat: add MCP tool for inline PR commenting', status: 'reviewed', lang: 'Python', issues: 2 },
                        { pr: '#213', title: 'fix: handle missing GITHUB_TOKEN gracefully', status: 'passed', lang: 'Python', issues: 0 },
                        { pr: '#212', title: 'chore: upgrade ESLint to v9 flat config', status: 'reviewing', lang: 'JavaScript', issues: 5 },
                        { pr: '#211', title: 'feat: add OpenRouter multi-model support', status: 'passed', lang: 'Python', issues: 0 },
                        { pr: '#210', title: 'security: rotate webhook secret and add HMAC', status: 'reviewed', lang: 'Python', issues: 1 },
                    ].map((item) => (
                        <div key={item.pr} className="flex items-center justify-between rounded-md border border-gray-4 bg-gray-1 px-4 py-3 text-sm">
                            <div className="flex items-center gap-3 min-w-0">
                                <span className="shrink-0 text-xs font-mono text-gray-8">{item.pr}</span>
                                <span className="truncate text-gray-12 font-medium">{item.title}</span>
                                <span className="shrink-0 text-xs px-2 py-0.5 rounded bg-gray-3 text-gray-9 border border-gray-4">{item.lang}</span>
                            </div>
                            <div className="flex items-center gap-3 shrink-0 ml-4">
                                {item.issues > 0 && (
                                    <span className="text-xs text-amber-400">{item.issues} issue{item.issues > 1 ? 's' : ''}</span>
                                )}
                                <span className={`text-xs px-2 py-0.5 rounded font-medium ${
                                    item.status === 'passed' ? 'bg-juniper-2 text-juniper-11 border border-juniper-5' :
                                    item.status === 'reviewed' ? 'bg-blue-950 text-blue-300 border border-blue-800' :
                                    'bg-amber-950 text-amber-300 border border-amber-800'
                                }`}>{item.status}</span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
}
