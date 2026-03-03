const logos = [
    { name: 'GitHub' },
    { name: 'GitLab' },
    { name: 'OpenAI' },
    { name: 'Anthropic' },
    { name: 'OpenRouter' },
    { name: 'Bandit' },
    { name: 'Flake8' },
    { name: 'ESLint' },
];

export default function LogoCarousel() {
    const allLogos = [...logos, ...logos]; // duplicate for infinite scroll

    return (
        <div className="overflow-hidden bg-white">
            <div className="mx-auto max-w-7xl px-6 lg:mx-[5.8rem]">
                <div
                    className="relative w-full h-20 select-none overflow-hidden"
                    style={{ '--spacing': '72px' }}
                >
                    <div className="logo-carousel-track flex items-center h-full gap-[72px] w-max">
                        {allLogos.map((logo, index) => (
                            <span
                                key={`${logo.name}-${index}`}
                                className="text-sm font-semibold tracking-wide text-gray-400 opacity-60 hover:opacity-100 transition-opacity whitespace-nowrap"
                            >
                                {logo.name}
                            </span>
                        ))}
                    </div>
                    {/* Fade edges */}
                    <div className="absolute inset-y-0 left-0 w-16 bg-gradient-to-r from-white to-transparent pointer-events-none z-10" />
                    <div className="absolute inset-y-0 right-0 w-16 bg-gradient-to-l from-white to-transparent pointer-events-none z-10" />
                </div>
            </div>
        </div>
    );
}
