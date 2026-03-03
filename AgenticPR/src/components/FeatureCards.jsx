import { Bot, ShieldCheck, Code2, KeyRound, SlidersHorizontal, Cpu } from 'lucide-react';

const features = [
    {
        title: 'AI Code Review',
        description: 'Multi-agent LLM-powered review on every PR — detecting bugs, security issues, performance bottlenecks, and anti-patterns with structured inline GitHub comments.',
        Icon: Bot,
    },
    {
        title: 'Security Scanning',
        description: 'Integrates Bandit for Python security analysis, surfacing OWASP Top 10 vulnerabilities and remediation guidance before code reaches production.',
        Icon: ShieldCheck,
    },
    {
        title: 'Multi-Language Linting',
        description: 'Automatic language detection with Flake8, ESLint, Checkstyle, and CppCheck — targeting only the changed files in each PR for fast, focused feedback.',
        Icon: Code2,
    },
    {
        title: 'Secrets Detection',
        description: 'Blocks API keys, tokens, and credentials from reaching your repository. Validated against common secret patterns before any code merges.',
        Icon: KeyRound,
    },
    {
        title: 'Custom Team Rules',
        description: 'Define coding standards in a simple .pr-reviewer.yml or Markdown file. AgenticPR enforces them on every PR — no CI configuration required.',
        Icon: SlidersHorizontal,
    },
    {
        title: 'MCP Agent System',
        description: 'Built on the Model Context Protocol — connect multiple AI agents, swap LLM providers (OpenAI, Claude, OpenRouter), and extend analysis capabilities without code changes.',
        Icon: Cpu,
    },
];

export default function FeatureCards() {
    return (
        <section className="grid grid-cols-1 sm:grid-cols-3 gap-8">
            {features.map((feature) => {
                const IconComponent = feature.Icon;
                return (
                    <div
                        key={feature.title}
                        className="group relative flex flex-col justify-between surface-elevated hover:surface-elevated-md rounded-md p-8 h-52 sm:h-64 overflow-clip transition-[border-color] duration-300 hover:border-juniper-7 before:content-[''] before:absolute before:inset-0 before:rounded-[inherit] before:bg-[radial-gradient(circle_at_100%_100%,_#0e2d19_0%,_#0a1b0f_50%,_transparent_100%)] before:opacity-0 before:z-0 before:pointer-events-none before:transition-opacity before:duration-300 hover:before:opacity-100 cursor-default"
                    >
                        <div className="relative z-10 flex items-start justify-between">
                            <h3 className="text-xl font-semibold tracking-tight text-gray-12">
                                {feature.title}
                            </h3>
                        </div>
                        <p className="relative z-10 font-medium text-base text-gray-11 group-hover:text-gray-12 leading-relaxed">
                            {feature.description}
                        </p>
                        {/* Glow effect */}
                        <div className="absolute -bottom-8 -right-8 w-64 h-64 rounded-full bg-juniper-5 opacity-0 group-hover:opacity-50 blur-3xl transition-opacity duration-300 pointer-events-none" />
                        {/* Feature icon */}
                        <IconComponent
                            className="absolute bottom-4 right-4 w-20 h-20 text-gray-4 group-hover:text-juniper-6 transition-colors duration-300 pointer-events-none translate-x-4 translate-y-4 group-hover:translate-x-2 group-hover:translate-y-2 transition-all"
                            strokeWidth={1}
                        />
                    </div>
                );
            })}
        </section>
    );
}
