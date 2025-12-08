import { AISection } from "../sections/AISection";
import { Hero } from "../sections/Hero";
import { IssueTrackingSection } from "../sections/IssueTrackingSection";
import { PlanningSection } from "../sections/PlanningSection";

export const Main = () => {
  return (
    <main className="box-border caret-transparent flex basis-[0%] flex-col grow min-h-[1000px] outline-transparent pt-16">
      <div className="box-border caret-transparent outline-transparent"></div>
      {/* <Hero/> */}
      <div className="box-border caret-transparent hidden h-px mt-[-65px] min-h-px min-w-px outline-transparent w-px -ml-px md:block"></div>
      <div className="box-border caret-transparent block h-px mt-[-33px] min-h-px min-w-px outline-transparent w-px -ml-px md:hidden"></div>
      {/* <ProductDemo /> */}
      {/*<LogoCloud />
      <ProductTeamsSection />*/}
       <AISection />
      <PlanningSection />
      <IssueTrackingSection />
      {/* <IntegrationsSection />
      <FoundationsSection />
      <CTASection /> */}
    </main>
  );
};
