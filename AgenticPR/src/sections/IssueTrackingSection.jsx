import { SectionHeader } from "@/components/SectionHeader";
import { CyclesView } from "@/sections/IssueTrackingSection/components/CyclesView";
import { InsightsSection } from "@/sections/IssueTrackingSection/components/InsightsSection";
import { FeatureGrid } from "@/components/FeatureGrid";

export const IssueTrackingSection = () => {
  return (
    <section className="bg-[linear-gradient(rgba(255,255,255,0.05),rgba(0,0,0,0)_20%)] box-border caret-transparent isolate outline-transparent overflow-x-hidden overflow-y-auto py-12 md:py-40">
      <div className="box-border caret-transparent max-w-screen-lg outline-transparent w-full mx-auto px-6">
        <SectionHeader
          variant="grid [grid-template-areas:'a_a_a_a''b_b_b_b'] grid-cols-[repeat(4,minmax(0px,1fr))] outline-transparent gap-y-8 md:[grid-template-areas:'a_a_a_a_a_a_a_a_._._._._.''b_b_b_b_b_._._._._._._._.'] md:grid-cols-[repeat(12,minmax(0px,1fr))]"
          badge={{
            iconClassName: "bg-orange-400",
            text: "Task tracking and sprint planning",
            iconSrc: "https://c.animaapp.com/miwyuqyvUsUdBR/assets/icon-31.svg",
          }}
          title="Issue tracking you'll enjoy using"
          titleLink="/build"
          description={
            <>
              <span className="text-stone-50">
                Optimized for speed and efficiency.
              </span>{" "}
              Create tasks in seconds, discuss issues in context, and breeze
              through your work in views tailored to you and your team.
            </>
          }
        />
      </div>
      <div className="relative items-center box-border caret-transparent flex flex-col justify-center outline-transparent pointer-events-none before:accent-auto before:box-border before:caret-transparent before:text-stone-50 before:block before:text-base before:not-italic before:normal-nums before:font-normal before:tracking-[normal] before:leading-6 before:list-outside before:list-disc before:mt-[-4%] before:pointer-events-none before:text-start before:indent-[0px] before:normal-case before:visible before:border-separate before:font-inter_variable after:accent-auto after:box-border after:caret-transparent after:text-stone-50 after:block after:text-base after:not-italic after:normal-nums after:font-normal after:tracking-[normal] after:leading-6 after:list-outside after:list-disc after:mb-[-20%] after:pointer-events-none after:text-start after:indent-[0px] after:normal-case after:visible after:border-separate after:font-inter_variable after:md:mb-[-6%]">
        <img
          alt="A screenshot of an issue board view in Linear showing three high-priority tasks"
          src="https://c.animaapp.com/miwyuqyvUsUdBR/assets/f=auto,dpr=2,q=95,fit=scale-down,metadata=none-1.webp"
          className="[mask-image:radial-gradient(83.83%_83.84%_at_50%_16.17%,rgb(217,217,217)_0%,rgba(115,115,115,0)_80%)] text-transparent aspect-[auto_3200_/_1620] box-border shrink-0 max-w-none w-[937.5px] ml-[112.5px] md:max-w-[1600px] md:w-[3200px] md:ml-0"
        />
      </div>
      <div className="box-border caret-transparent max-w-screen-lg outline-transparent w-full mx-auto px-6">
        <CyclesView />
        <div className="box-border caret-transparent h-px min-h-px min-w-px outline-transparent w-px -ml-px mt-[31px]"></div>
        <InsightsSection />
        <div className="bg-white/10 box-border caret-transparent shrink-0 h-px outline-transparent w-full my-6 rounded-full"></div>
        <FeatureGrid
          features={[
            {
              iconUrl:
                "https://c.animaapp.com/miwyuqyvUsUdBR/assets/icon-63.svg",
              title: "Tailored workflows",
              description:
                "Track progress across custom issue flows for your team.",
            },
            {
              iconUrl:
                "https://c.animaapp.com/miwyuqyvUsUdBR/assets/icon-64.svg",
              title: "Custom views",
              description:
                "Switch between list and board. Group issues with swimlanes.",
            },
            {
              iconUrl:
                "https://c.animaapp.com/miwyuqyvUsUdBR/assets/icon-65.svg",
              title: "Filters",
              description:
                "Refine issue lists down to what's most relevant to you.",
            },
            {
              iconUrl:
                "https://c.animaapp.com/miwyuqyvUsUdBR/assets/icon-66.svg",
              title: "SLAs",
              description:
                "Automatically apply deadlines to time-sensitive tasks.",
            },
          ]}
        />
      </div>
    </section>
  );
};