export default function PRDashboard() {
    return (
        <section className="relative overflow-hidden min-h-[500px] sm:min-h-0 max-w-7xl mx-auto px-6 lg:mx-[5.8rem]">
            <div className="relative">
                <img
                    src="https://deepsource.com/img/illustration/pr-dashboard.svg"
                    alt="DeepSource PR dashboard"
                    width="1200"
                    height="800"
                    loading="lazy"
                    decoding="async"
                    className="w-full h-auto min-w-[900px] sm:min-w-0"
                />
            </div>
            {/* Mobile fade-out on right */}
            <div className="absolute inset-y-0 right-0 w-24 pointer-events-none bg-gradient-to-l from-ink-400 to-transparent sm:hidden" />
        </section>
    );
}
