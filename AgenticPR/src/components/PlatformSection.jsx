import PRReview from './PRReview';
import Autofix from './Autofix';
import PRGates from './PRGates';
import PRReportCard from './PRReportCard';

export default function PlatformSection() {
    return (
        <>
            {/* Divider */}
            <div className="relative w-screen left-1/2 -translate-x-1/2">
                <hr className="border-t border-gray-5" aria-hidden="true" />
            </div>
            <div className="w-full h-12 sm:h-24" />

            <section className="mx-auto max-w-7xl px-6 lg:mx-[7.44rem]">
                {/* Platform Header */}
                <div>
                    <h3 className="text-[0.902rem] text-gray-12 uppercase font-semibold inline-flex items-center tracking-wide">
                        <span className="bg-juniper-9 rounded-sm w-5 h-5 inline-block" />
                        <span className="px-3 py-1 leading-4">Platform</span>
                    </h3>
                    <div className="w-full h-4 sm:h-5" />
                    <div className="max-w-5xl">
                        <h2 className="text-[1.353rem] sm:text-[1.691rem] font-semibold tracking-tight text-juniper-11">
                            Deep code review with hybrid static analysis and AI agents.{' '}
                            <span className="sm:block text-gray-10 font-[550] leading-snug">
                                High-signal, low false-positive issues and structured feedback across security,
                                quality, complexity, and coverage.
                            </span>
                        </h2>
                    </div>
                </div>

                <div className="h-8 sm:h-16 w-full" />

                {/* Bento Grid */}
                <div className="space-y-12 sm:space-y-24">
                    <PRReview />
                    <Autofix />
                    <PRGates />
                    <PRReportCard />
                </div>
            </section>
        </>
    );
}
