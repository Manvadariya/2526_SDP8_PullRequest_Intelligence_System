export const InsightsSection = () => {
  return (
    <div className="box-border caret-transparent gap-x-8 grid [grid-template-areas:'a_a_a_a''b_b_b_b'] grid-cols-[repeat(4,minmax(0px,1fr))] outline-transparent gap-y-8 md:[grid-template-areas:'a_a_a_a_a_a_b_b_b_b_b_b'] md:grid-cols-[repeat(12,minmax(0px,1fr))]">
      <div className="box-border caret-transparent col-end-[span_6] col-start-1 row-end-1 row-start-1 outline-transparent z-[1]">
        <h3 className="text-[21px] font-[510] box-border caret-transparent tracking-[-0.37px] leading-7 outline-transparent">
          Linear Insights
        </h3>
        <div className="box-border caret-transparent h-px min-h-px min-w-px outline-transparent w-px -ml-px mt-[3px]"></div>
        <p className="text-neutral-400 text-[17px] box-border caret-transparent leading-[24.5px] outline-transparent">
          Take the guesswork out of product planning with realtime analytics and
          reporting dashboards.
        </p>
        <div className="box-border caret-transparent h-px min-h-px min-w-px outline-transparent w-px -ml-px mt-[23px]"></div>
        <a
          aria-label="Visit Linear Insights page"
          type="button"
          href="/insights"
          className="relative text-[13px] font-[510] items-center bg-zinc-800 box-border caret-transparent gap-x-2 inline-flex shrink-0 h-8 justify-center leading-8 max-w-full outline-transparent gap-y-2 text-nowrap border border-zinc-700 px-3 rounded-lg border-solid"
        >
          Learn more
          <img
            src="https://c.animaapp.com/miwyuqyvUsUdBR/assets/icon-32.svg"
            alt="Icon"
            className="box-border caret-transparent shrink-0 h-4 outline-transparent text-nowrap w-4"
          />
        </a>
      </div>
      <div className="relative box-border caret-transparent col-end-[-1] col-start-1 row-end-auto row-start-auto outline-transparent pointer-events-none overflow-hidden md:row-end-1 md:row-start-1 after:accent-auto after:bg-[linear-gradient(rgba(0,0,0,0)_70%,rgb(8,9,10)_100%),linear-gradient(to_right,rgb(8,9,10)_0%,rgba(0,0,0,0)_20%,rgba(0,0,0,0)_80%,rgb(8,9,10)_100%),linear-gradient(150deg,rgb(8,9,10)_20%,rgba(0,0,0,0)_30%)] after:bg-[position:0%_0%,0%_0%,0%_0%] after:bg-size-[auto,auto,auto] after:box-border after:caret-transparent after:text-stone-50 after:block after:text-base after:not-italic after:normal-nums after:font-normal after:tracking-[normal] after:leading-6 after:list-outside after:list-disc after:pointer-events-none after:absolute after:text-start after:indent-[0px] after:normal-case after:visible after:border-separate after:inset-0 after:font-inter_variable">
        <img
          alt="A screenshot of a Cycle time chart"
          src="https://c.animaapp.com/miwyuqyvUsUdBR/assets/f=auto,dpr=2,q=95,fit=scale-down,metadata=none.svg"
          className="text-transparent aspect-[auto_1740_/_930] box-border shrink-0 mb-[-25%] ml-[-100%] w-[250%] md:ml-[-15%] md:w-[150%]"
        />
      </div>
    </div>
  );
};
