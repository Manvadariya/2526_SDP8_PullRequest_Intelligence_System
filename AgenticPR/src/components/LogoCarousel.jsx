const logos = [
    { name: 'Uber', src: 'https://deepsource.com/img/logo/customer/uber.svg' },
    { name: 'NASA', src: 'https://deepsource.com/img/logo/customer/nasa.svg' },
    { name: 'Figma', src: 'https://deepsource.com/img/logo/customer/figma.svg' },
    { name: 'Slack', src: 'https://deepsource.com/img/logo/customer/slack.svg' },
    { name: 'Docusign', src: 'https://deepsource.com/img/logo/customer/docusign.svg' },
    { name: '1Password', src: 'https://deepsource.com/img/logo/customer/1password.svg' },
    { name: 'Juspay', src: 'https://deepsource.com/img/logo/customer/juspay.svg' },
    { name: 'Akeso', src: 'https://deepsource.com/img/logo/customer/akeso.svg' },
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
                            <img
                                key={`${logo.name}-${index}`}
                                src={logo.src}
                                alt={logo.name}
                                className="h-8 w-auto opacity-50 hover:opacity-100 transition-opacity grayscale hover:grayscale-0"
                                loading="lazy"
                            />
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
