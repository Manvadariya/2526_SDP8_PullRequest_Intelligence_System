import './index.css';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import PRDashboard from './components/PRDashboard';

import PlatformSection from './components/PlatformSection';
import FeatureCards from './components/FeatureCards';
import Footer from './components/Footer';

function App() {
  return (
    <div className="relative">
      {/* Background gradient at top */}
      {/* Background gradient at top */}
      <div className="absolute top-0 left-0 right-0 h-[420px] opacity-10 bg-gradient-to-b from-juniper-7 to-transparent -z-10 pointer-events-none" />

      <Navbar />

      {/* Spacer for fixed navbar */}
      <div className="h-[28px] sm:h-[48px]" aria-hidden="true" />

      <main className="relative">
        <Hero />
        <PRDashboard />

        {/* Spacer */}
        <div
          style={{ '--spacer-mobile': '2rem', '--spacer-desktop': '3rem', height: 'var(--spacer-mobile)' }}
          aria-hidden="true"
        />

        <PlatformSection />

        {/* Feature Cards Section */}
        <div className="w-full h-12 sm:h-24" />
        <div className="mx-auto max-w-7xl px-6 lg:mx-[7.44rem]">
          <FeatureCards />
        </div>

        {/* Bottom CTA */}
        <div className="w-full h-16 sm:h-32" />
        <section className="mx-auto max-w-7xl px-6 pb-16 sm:pb-24 lg:mx-[7.44rem]">
          <div className="text-center">
            <h2 className="text-[1.691rem] sm:text-[2.165rem] font-semibold tracking-tight text-gray-12">
              Ready to ship with confidence?
            </h2>
            <p className="mt-4 text-[1.014rem] text-gray-10 max-w-2xl mx-auto">
              Join thousands of engineering teams that trust DeepSource to automate code reviews and
              ship production-ready code.
            </p>
            <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
              <a
                href="https://app.deepsource.com/signup"
                className="inline-flex items-center justify-center rounded-md px-6 py-3 text-[0.789rem] font-semibold shadow-md bg-juniper-9 text-white hover:bg-juniper-10 transition-colors"
              >
                Start for free
              </a>
              <a
                href="https://deepsource.com/contact/sales"
                className="inline-flex items-center justify-center rounded-md px-6 py-3 text-[0.789rem] font-semibold shadow ring-1 ring-inset ring-gray-6 text-gray-12 hover:bg-gray-2 transition-colors"
              >
                Contact Sales
              </a>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}

export default App;
