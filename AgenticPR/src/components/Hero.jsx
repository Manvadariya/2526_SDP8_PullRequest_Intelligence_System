const providers = [
    { name: 'GitHub', key: 'gh', icon: 'https://deepsource.com/_vercel/image?url=%2Fimg%2Ficon%2Fintegration%2Fgithub.svg&w=1536&q=100' },
    { name: 'GitLab', key: 'gl', icon: 'https://deepsource.com/_vercel/image?url=%2Fimg%2Ficon%2Fintegration%2Fgitlab.svg&w=1536&q=100' },
    { name: 'Bitbucket', key: 'bb', icon: 'https://deepsource.com/_vercel/image?url=%2Fimg%2Ficon%2Fintegration%2Fbitbucket.svg&w=1536&q=100' },
    { name: 'Azure', key: 'ads', icon: 'https://deepsource.com/_vercel/image?url=%2Fimg%2Ficon%2Fintegration%2Fads.svg&w=1536&q=100' },
];

export default function Hero() {
    return (
        <div>
            {/* Spacer */}
            <div
                style={{ '--spacer-mobile': '6.8rem', '--spacer-desktop': '9rem', height: 'var(--spacer-mobile)' }}
                aria-hidden="true"
                data-v-e2e5eed3=""
            />

            <div className="relative overflow-visible">
                <div className="relative mx-auto max-w-7xl px-6 lg:mx-[7.44rem] lg:flex flex flex-col">
                    {/* Heading */}
                    <div className="border-b border-gray-4 pb-4 sm:pb-5 mb-4 sm:mb-5">
                        <h1 className="mt-4 text-[2.255rem] leading-tight font-bold text-juniper-12 sm:text-[3.5rem] tracking-tight sm:max-w-xl">
                            Your green light to ship with confidence.
                        </h1>
                    </div>

                    {/* Two-column content */}
                    <section className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                            <h2 className="font-semibold sm:font-medium text-[0.902rem] text-juniper-12/80">
                                AI Code Review Platform
                            </h2>
                        </div>
                        <div>
                            <p className="text-[1.014rem] sm:text-[1.127rem] leading-7 sm:leading-8 text-gray-12/90 tracking-tight font-[450]">
                                Your team is writing more code with AI. DeepSource automates code reviews, so you can
                                ship to production faster with confidence.
                            </p>

                            <div className="mt-4 flex flex-col items-center sm:items-start gap-y-4 w-full">
                                <div className="flex flex-col items-stretch sm:items-start sm:flex-row gap-6 w-full sm:w-auto">
                                    {/* Quickstart button — Desktop */}
                                    <div className="relative flex flex-col items-stretch sm:items-start">
                                        <div
                                            style={{ width: '281px' }}
                                            className="hidden sm:flex flex-row text-[0.789rem] font-semibold leading-6 rounded bg-juniper-2 text-juniper-11 shadow-md ring-1 ring-inset ring-juniper-9 items-center group px-3 space-x-2"
                                        >
                                            <span className="flex py-3 cursor-default">Quickstart with</span>
                                            <div className="flex flex-row overflow-hidden flex-grow items-center justify-center">
                                                {providers.map((p) => (
                                                    <a
                                                        key={p.key}
                                                        href={`https://app.deepsource.com/login?provider=${p.key}`}
                                                        aria-label={`Quickstart with ${p.name}`}
                                                        className="flex flex-grow flex-row items-center justify-center space-x-1.5 font-medium text-juniper-12 py-2.5 hover:bg-juniper-3 overflow-hidden"
                                                    >
                                                        <img alt={p.name} className="h-6 w-6" src={p.icon} />
                                                    </a>
                                                ))}
                                            </div>
                                        </div>

                                        {/* Quickstart button — Mobile */}
                                        <button className="sm:hidden flex flex-row text-[0.789rem] font-semibold leading-6 rounded bg-juniper-2 text-juniper-11 shadow-md ring-1 ring-inset ring-juniper-9 items-center justify-center group px-3 py-3 space-x-2 w-full">
                                            <span className="flex cursor-default">Quickstart with</span>
                                            <div className="flex flex-row items-center justify-center space-x-1.5">
                                                {providers.map((p) => (
                                                    <img key={p.key} alt={p.name} className="h-6 w-6" src={p.icon} />
                                                ))}
                                            </div>
                                        </button>

                                        <span className="font-sans text-[0.676rem] block pt-3 text-gray-12 leading-none text-center sm:text-left">
                                            14-day free trial, no credit card needed
                                        </span>
                                    </div>

                                    {/* Contact Sales */}
                                    <div className="flex flex-col space-y-3 items-stretch sm:items-start">
                                        <button className="flex flex-row text-[0.789rem] font-semibold leading-6 rounded bg-juniper-1 text-gray-11 hover:text-gray-12 shadow ring-1 ring-inset ring-gray-6 items-center justify-center sm:justify-start group px-3 py-3 space-x-2 transition-colors duration-150 w-full sm:w-auto">
                                            <svg
                                                xmlns="http://www.w3.org/2000/svg"
                                                viewBox="0 0 20 20"
                                                fill="currentColor"
                                                className="h-4 w-4 text-gray-11"
                                            >
                                                <path
                                                    fillRule="evenodd"
                                                    d="M3.43 2.524A41.29 41.29 0 0 1 10 2c2.236 0 4.43.18 6.57.524 1.437.231 2.43 1.49 2.43 2.902v5.148c0 1.413-.993 2.67-2.43 2.902a41.102 41.102 0 0 1-3.55.414c-.28.02-.521.18-.643.413l-1.712 3.293a.75.75 0 0 1-1.33 0l-1.713-3.293a.783.783 0 0 0-.642-.413 41.108 41.108 0 0 1-3.55-.414C1.993 13.245 1 11.986 1 10.574V5.426c0-1.413.993-2.67 2.43-2.902Z"
                                                    clipRule="evenodd"
                                                />
                                            </svg>
                                            <span>Contact Sales</span>
                                        </button>
                                        <span className="block sm:hidden text-[0.789rem] text-gray-12 leading-none text-center">
                                            For growing teams and enterprises
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </section>
                </div>
            </div>

            {/* Spacer */}
            <div
                style={{ '--spacer-mobile': '2rem', '--spacer-desktop': '3rem', height: 'var(--spacer-mobile)' }}
                aria-hidden="true"
            />
        </div>
    );
}
