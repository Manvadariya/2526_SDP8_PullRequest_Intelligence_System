import { useState } from 'react';

const navLinks = [
    { label: 'Benchmarks', href: '/benchmarks' },
    { label: 'Customers', href: '/customers' },
    { label: 'Pricing', href: '/pricing' },
    { label: 'Docs', href: 'https://docs.deepsource.com', external: true },
];

const resourceLinks = [
    { label: 'Blog', href: 'https://deepsource.com/blog' },
    { label: 'Changelog', href: 'https://deepsource.com/changelog' },
    { label: 'Learning Center', href: 'https://deepsource.com/learn' },
];

export default function Navbar() {
    const [mobileOpen, setMobileOpen] = useState(false);
    const [resourcesOpen, setResourcesOpen] = useState(false);

    return (
        <header className="fixed top-0 z-50 w-full">
            {/* Progressive blur background */}
            <div className="progressive-blur pointer-events-none absolute inset-0">
                <div className="blur-layer blur-layer-1" />
                <div className="blur-layer blur-layer-2" />
                <div className="blur-layer blur-layer-3" />
                <div className="blur-layer blur-layer-4" />
            </div>

            <nav
                className="text-gray-12 relative mx-auto flex max-w-7xl space-x-[1.583rem] xl:space-x-[2.11rem] items-center justify-between p-[1.583rem] lg:mx-[7.44rem]"
                aria-label="Global"
            >
                {/* Logo */}
                <div className="flex flex-shrink-0">
                    <a href="/" className="-m-1.5 p-1.5">
                        <span className="sr-only">DeepSource</span>
                        <img
                            className="h-[1.583rem] w-auto flex-shrink-0"
                            src="https://deepsource.com/_nuxt/wordmark-light.CU2fWIAi.svg"
                            alt="DeepSource"
                        />
                    </a>
                </div>

                {/* Mobile menu button */}
                <div className="flex lg:hidden">
                    <button
                        type="button"
                        className="-m-2.5 inline-flex items-center justify-center rounded-md p-2.5"
                        onClick={() => setMobileOpen(!mobileOpen)}
                    >
                        <span className="sr-only">Open main menu</span>
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            fill="none"
                            viewBox="0 0 24 24"
                            strokeWidth="1.5"
                            stroke="currentColor"
                            aria-hidden="true"
                            className="h-6 w-6 stroke-2"
                            data-slot="icon"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5"
                            />
                        </svg>
                    </button>
                </div>

                {/* Desktop nav links */}
                <div className="hidden lg:flex gap-x-[1.583rem] xl:gap-x-[2.11rem] translate-y-[1.84px]">
                    {navLinks.map((link) => (
                        <a
                            key={link.label}
                            href={link.href}
                            className="text-[0.923rem] font-medium leading-5"
                            {...(link.external ? { rel: 'noopener noreferrer' } : {})}
                        >
                            {link.label}
                        </a>
                    ))}

                    {/* Resources dropdown */}
                    <div className="relative">
                        <button
                            className="flex items-center gap-x-1 text-[0.923rem] font-medium leading-5 outline-none"
                            type="button"
                            aria-expanded={resourcesOpen}
                            onClick={() => setResourcesOpen(!resourcesOpen)}
                        >
                            Resources
                            <svg
                                xmlns="http://www.w3.org/2000/svg"
                                viewBox="0 0 20 20"
                                fill="currentColor"
                                aria-hidden="true"
                                className={`h-[1.318rem] w-[1.318rem] flex-none transition-transform ${resourcesOpen ? 'rotate-180' : ''}`}
                                data-slot="icon"
                            >
                                <path
                                    fillRule="evenodd"
                                    d="M5.22 8.22a.75.75 0 0 1 1.06 0L10 11.94l3.72-3.72a.75.75 0 1 1 1.06 1.06l-4.25 4.25a.75.75 0 0 1-1.06 0L5.22 9.28a.75.75 0 0 1 0-1.06Z"
                                    clipRule="evenodd"
                                />
                            </svg>
                        </button>
                        {resourcesOpen && (
                            <div className="absolute top-full left-0 mt-2 w-48 rounded-md bg-gray-1 shadow-lg ring-1 ring-gray-4 p-2 z-50">
                                {resourceLinks.map((link) => (
                                    <a
                                        key={link.label}
                                        href={link.href}
                                        className="block px-[0.791rem] py-[0.528rem] text-[0.923rem] font-medium text-gray-11 hover:text-gray-12 hover:bg-gray-2 rounded"
                                    >
                                        {link.label}
                                    </a>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Invisible screen reader div from snippet */}
                <div
                    hidden=""
                    style={{
                        position: 'fixed',
                        top: 1,
                        left: 1,
                        width: 1,
                        height: 0,
                        padding: 0,
                        margin: -1,
                        overflow: 'hidden',
                        clip: 'rect(0, 0, 0, 0)',
                        whiteSpace: 'nowrap',
                        borderWidth: 0,
                        display: 'none',
                    }}
                ></div>

                {/* Desktop CTA buttons */}
                <div className="hidden lg:flex lg:flex-1 lg:justify-end gap-x-[1.055rem]">
                    <a
                        href="https://app.deepsource.com/login"
                        className="text-[0.923rem] font-medium leading-5 mr-[0.528rem]"
                    >
                        Log in
                    </a>
                    <a
                        href="https://app.deepsource.com/signup"
                        className="bg-juniper-1 hover:bg-gray-2 ring-gray-6 text-[0.923rem] font-medium leading-5 rounded px-[0.659rem] py-[0.263rem] -my-[0.263rem] shadow-sm ring-1 ring-inset"
                    >
                        Sign up
                    </a>
                    <a
                        href="/contact/sales"
                        className="text-[0.923rem] font-semibold leading-5 rounded px-[0.659rem] py-[0.263rem] -my-[0.27rem] shadow-sm ring-1 ring-inset bg-juniper-2 hover:bg-juniper-3 ring-juniper-7 text-juniper-11"
                    >
                        Contact Sales
                    </a>
                </div>
            </nav>

            {/* Invisible screen reader div from snippet */}
            <div
                hidden=""
                style={{
                    position: 'fixed',
                    top: 1,
                    left: 1,
                    width: 1,
                    height: 0,
                    padding: 0,
                    margin: -1,
                    overflow: 'hidden',
                    clip: 'rect(0, 0, 0, 0)',
                    whiteSpace: 'nowrap',
                    borderWidth: 0,
                    display: 'none',
                }}
            ></div>

            {/* Mobile menu */}
            {mobileOpen && (
                <div className="lg:hidden bg-gray-1 border-t border-gray-4 px-[1.583rem] py-[1.055rem] space-y-[1.055rem]">
                    {navLinks.map((link) => (
                        <a
                            key={link.label}
                            href={link.href}
                            className="block text-[0.923rem] font-medium leading-5"
                        >
                            {link.label}
                        </a>
                    ))}
                    <div className="pt-[1.055rem] border-t border-gray-4 flex flex-col gap-[0.791rem]">
                        <a href="https://app.deepsource.com/login" className="text-[0.923rem] font-medium">
                            Log in
                        </a>
                        <a
                            href="https://app.deepsource.com/signup"
                            className="text-[0.923rem] font-medium text-center bg-juniper-1 ring-gray-6 rounded px-[0.659rem] py-[0.528rem] shadow-sm ring-1 ring-inset"
                        >
                            Sign up
                        </a>
                        <a
                            href="/contact/sales"
                            className="text-[0.923rem] font-semibold text-center rounded px-[0.659rem] py-[0.528rem] shadow-sm ring-1 ring-inset bg-juniper-2 ring-juniper-9 text-juniper-11"
                        >
                            Contact Sales
                        </a>
                    </div>
                </div>
            )}
        </header>
    );
}
