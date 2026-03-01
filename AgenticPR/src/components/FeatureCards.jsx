const features = [
    {
        title: 'Secrets Detection',
        description: 'Prevent API keys, tokens, and sensitive credentials from ever reaching production. Validated against 165+ providers.',
        icon: 'https://deepsource.com/img/icon/feature/secrets.svg',
    },
    {
        title: 'OSS Vulnerability Scanning',
        description: 'See which dependency vulnerabilities actually affect your code with reachability and taint analysis.',
        icon: 'https://deepsource.com/img/icon/feature/sca.svg',
    },
    {
        title: 'Code Coverage',
        description: 'Track coverage and see which lines in your code are untested. Enforce thresholds so nothing ships without tests.',
        icon: 'https://deepsource.com/img/icon/feature/coverage.svg',
    },
    {
        title: 'Compliance Reporting',
        description: 'Stay audit-ready with security vulnerability reports mapped to OWASP® Top 10 and SANS Top 25.',
        icon: 'https://deepsource.com/img/icon/feature/compliance.svg',
    },
    {
        title: 'IaC Analysis',
        description: 'Detect advanced misconfigurations across Terraform, CloudFormation, and Kubernetes manifests.',
        icon: 'https://deepsource.com/img/icon/feature/iac.svg',
    },
    {
        title: 'IDE Extension',
        description: 'Surface real-time issues as you type, powered by the same analysis engine as your CI pipeline.',
        icon: 'https://deepsource.com/img/icon/feature/ide.svg',
    },
];

export default function FeatureCards() {
    return (
        <section className="grid grid-cols-1 sm:grid-cols-3 gap-8">
            {features.map((feature) => (
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
                    <div
                        className="absolute bottom-0 right-0 h-48 w-48 transform translate-x-1/3 translate-y-1/3 group-hover:translate-x-1/4 group-hover:translate-y-1/4 transition-all duration-300 pointer-events-none bg-current text-gray-4 group-hover:text-juniper-6"
                        style={{
                            WebkitMaskImage: `url(${feature.icon})`,
                            WebkitMaskSize: 'contain',
                            WebkitMaskRepeat: 'no-repeat',
                            WebkitMaskPosition: 'center',
                            maskImage: `url(${feature.icon})`,
                            maskSize: 'contain',
                            maskRepeat: 'no-repeat',
                            maskPosition: 'center',
                        }}
                    />
                </div>
            ))}
        </section>
    );
}
