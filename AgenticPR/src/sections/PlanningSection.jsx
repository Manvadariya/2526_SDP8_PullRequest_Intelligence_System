import { SectionHeader } from "@/components/SectionHeader";
import { ProjectManagement } from "@/sections/PlanningSection/components/ProjectManagement";
import { DocumentEditor } from "@/sections/PlanningSection/components/DocumentEditor";
import { FeatureGrid } from "@/components/FeatureGrid";

export const PlanningSection = () => {
  return (
    <section className="bg-[linear-gradient(rgba(255,255,255,0.05),rgba(0,0,0,0)_20%)] box-border caret-transparent isolate outline-transparent overflow-x-hidden overflow-y-auto py-12 md:py-40">
      <div className="box-border caret-transparent max-w-screen-lg outline-transparent w-full mx-auto px-6">
        <SectionHeader
          variant="grid [grid-template-areas:'a_a_a_a''b_b_b_b'] grid-cols-[repeat(4,minmax(0px,1fr))] outline-transparent gap-y-8 md:[grid-template-areas:'a_a_a_a_a_a_a_a_._._._._.''b_b_b_b_b_._._._._._._._.'] md:grid-cols-[repeat(12,minmax(0px,1fr))]"
          badge={{
            iconClassName: "bg-green-400",
            text: "Project and long-term planning",
            iconSrc: "https://c.animaapp.com/miwyuqyvUsUdBR/assets/icon-31.svg",
          }}
          title="Set the product direction"
          titleLink="/plan"
          description={
            <>
              <span className="text-stone-50">
                Align your team around a unified product timeline.
              </span>{" "}
              Plan, manage, and track all product initiatives with Linear's
              visual planning tools.
            </>
          }
        />
      </div>
      <div className="relative items-center box-border caret-transparent flex flex-col justify-center outline-transparent pointer-events-none before:accent-auto before:box-border before:caret-transparent before:text-stone-50 before:block before:text-base before:not-italic before:normal-nums before:font-normal before:tracking-[normal] before:leading-6 before:list-outside before:list-disc before:pointer-events-none before:text-start before:indent-[0px] before:normal-case before:visible before:mt-0 before:border-separate before:font-inter_variable before:md:mt-[-8%] after:accent-auto after:box-border after:caret-transparent after:text-stone-50 after:block after:text-base after:not-italic after:normal-nums after:font-normal after:tracking-[normal] after:leading-6 after:list-outside after:list-disc after:mb-[-3%] after:pointer-events-none after:text-start after:indent-[0px] after:normal-case after:visible after:border-separate after:font-inter_variable">
        <img
          alt="A screenshot of a roadmap view in Linear showing two projects that are currently in progress"
          src="https://c.animaapp.com/miwyuqyvUsUdBR/assets/f=auto,dpr=2,q=95,fit=scale-down,metadata=none.webp"
          className="[mask-image:radial-gradient(90%_50%,rgb(217,217,217)_0%,rgba(115,115,115,0)_100%)] text-transparent aspect-[auto_3200_/_1620] box-border shrink-0 max-w-none w-[937.5px] ml-[150px] md:[mask-image:radial-gradient(57%_57%_at_50%_35%,rgb(217,217,217)_0%,rgba(115,115,115,0)_100%)] md:max-w-[1600px] md:w-[3200px] md:ml-0"
        />
      </div>
      <div className="box-border caret-transparent max-w-screen-lg outline-transparent w-full mx-auto px-6">
        <ProjectManagement />
        <div className="box-border caret-transparent h-px min-h-px min-w-px outline-transparent w-px -ml-px mt-[55px]"></div>
        <DocumentEditor />
        <div className="bg-white/10 box-border caret-transparent shrink-0 h-px outline-transparent w-full my-12 rounded-full"></div>
        <FeatureGrid
          features={[
            {
              iconUrl:
                "https://c.animaapp.com/miwyuqyvUsUdBR/assets/icon-55.svg",
              title: "Initiatives",
              description: "Coordinate strategic product efforts.",
            },
            {
              iconUrl:
                "https://c.animaapp.com/miwyuqyvUsUdBR/assets/icon-56.svg",
              title: "Cross-team projects",
              description: "Collaborate across teams and departments.",
            },
            {
              iconUrl:
                "https://c.animaapp.com/miwyuqyvUsUdBR/assets/icon-57.svg",
              iconClassName: "text-slate-300",
              title: "Milestones",
              description: "Break projects down into concrete phases.",
            },
            {
              iconUrl:
                "https://c.animaapp.com/miwyuqyvUsUdBR/assets/icon-58.svg",
              title: "Progress insights",
              description: "Track scope, velocity, and progress over time.",
            },
          ]}
        />
      </div>
    </section>
  );
};