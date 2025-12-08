export const DocumentEditor = () => {
  return (
    <div className="box-border caret-transparent gap-x-8 grid [grid-template-areas:'a_a_a_a''b_b_b_b'] grid-cols-[repeat(4,minmax(0px,1fr))] outline-transparent gap-y-8 md:[grid-template-areas:'a_a_a_a_b_b_b_b_b_b_b_b'] md:grid-cols-[repeat(12,minmax(0px,1fr))]">
      <div className="box-border caret-transparent col-end-[a] col-start-[a] row-end-[a] row-start-[a] outline-transparent">
        <div className="box-border caret-transparent h-px min-h-px min-w-px outline-transparent w-px -ml-px mt-[63px]"></div>
        <h3 className="text-2xl font-[510] box-border caret-transparent tracking-[-0.288px] leading-[31.92px] outline-transparent">
          Ideate and specify what to build next
        </h3>
        <div className="box-border caret-transparent h-px min-h-px min-w-px outline-transparent w-px -ml-px mt-[23px]"></div>
        <div
          role="group"
          className="box-border caret-transparent gap-x-2 flex flex-col gap-y-2"
        >
          <button
            type="button"
            role="radio"
            className="text-[17px] font-[510] bg-transparent caret-transparent gap-x-3 flex justify-start tracking-[-0.22px] leading-[25px] outline-transparent gap-y-3 text-center bg-[position:0px_0px] p-0"
          >
            <div className="bg-green-400 box-border caret-transparent h-6 outline-transparent w-1 rounded-full"></div>
            Collaborative documents
          </button>
          <button
            type="button"
            role="radio"
            className="text-neutral-500 text-[17px] font-[510] bg-transparent caret-transparent gap-x-3 flex justify-start tracking-[-0.22px] leading-[25px] outline-transparent gap-y-3 text-center bg-[position:0px_0px] p-0"
          >
            <div className="bg-neutral-800 box-border caret-transparent h-6 outline-transparent w-1 rounded-full"></div>
            Inline comments
          </button>
          <button
            type="button"
            role="radio"
            className="text-neutral-500 text-[17px] font-[510] bg-transparent caret-transparent gap-x-3 flex justify-start tracking-[-0.22px] leading-[25px] outline-transparent gap-y-3 text-center bg-[position:0px_0px] p-0"
          >
            <div className="bg-neutral-800 box-border caret-transparent h-6 outline-transparent w-1 rounded-full"></div>
            Text-to-issue commands
          </button>
        </div>
      </div>
      <div className="box-border caret-transparent col-end-[b] col-start-[b] row-end-[b] row-start-[b] outline-transparent">
        <div
          aria-label="Linear document titled 'Collaborate on ideas' with two people editing, Zoe and Quinn. The document contains: 'Write down product ideas and work together on feature specs in realtime, multiplayer documents. Add style and structure with rich-text formatting options.'"
          className="relative box-border caret-transparent outline-transparent w-fit overflow-hidden mx-auto px-0 md:mr-0 md:px-6 after:accent-auto after:bg-[linear-gradient(rgba(0,0,0,0)_80%,rgb(8,9,10)_97%)] after:box-border after:caret-transparent after:text-stone-50 after:block after:text-base after:not-italic after:normal-nums after:font-normal after:tracking-[normal] after:leading-6 after:list-outside after:list-disc after:pointer-events-none after:absolute after:text-start after:indent-[0px] after:normal-case after:visible after:border-separate after:inset-0 after:font-inter_variable"
        >
          <img
            src="https://c.animaapp.com/miwyuqyvUsUdBR/assets/icon-52.svg"
            alt="Icon"
            className="box-border caret-transparent shrink-0 h-[482px] outline-transparent w-[532px]"
          />
          <div className="absolute box-border caret-transparent max-w-[262.5px] outline-transparent ml-16 mr-auto top-[100px] inset-x-0 md:max-w-[360px] md:ml-auto">
            <div className="text-green-400 items-center bg-neutral-800/50 box-border caret-transparent flex h-9 justify-center outline-transparent w-9 rounded-lg">
              <img
                src="https://c.animaapp.com/miwyuqyvUsUdBR/assets/icon-53.svg"
                alt="Icon"
                className="box-border caret-transparent shrink-0 h-[22px] outline-transparent w-[22px]"
              />
            </div>
            <div className="box-border caret-transparent h-px min-h-px min-w-px outline-transparent w-px -ml-px mt-[31px]"></div>
            <span className="text-[17px] font-[510] box-border caret-transparent tracking-[-0.204px] leading-[23.8px] outline-transparent">
              <span className="relative bg-green-400/20 box-border caret-transparent outline-transparent pointer-events-none border border-lime-700 -mx-0.5 px-0.5 rounded-r-[1px] rounded-bl rounded-tl border-solid">
                Collaborate on
              </span>
              <span className="relative box-border caret-transparent outline-transparent pointer-events-none before:accent-auto before:bg-lime-700 before:box-border before:caret-transparent before:text-stone-50 before:block before:text-[17px] before:not-italic before:normal-nums before:font-[510] before:tracking-[-0.204px] before:leading-[23.8px] before:list-outside before:list-disc before:pointer-events-none before:absolute before:text-start before:indent-[0px] before:normal-case before:visible before:w-0.5 before:rounded-full before:border-separate before:left-0 before:-inset-y-px before:font-inter_variable">
                <span className="absolute box-border caret-transparent block outline-transparent left-0 -top-3.5">
                  <span className="text-white text-[10px] bg-lime-700 box-border caret-transparent block h-3.5 leading-[14px] outline-transparent text-center text-nowrap px-1 rounded-r-sm rounded-tl-sm before:accent-auto before:shadow-[rgb(44,144,28)_0px_-2px_0px_0px] before:box-border before:caret-transparent before:text-white before:block before:text-[10px] before:not-italic before:normal-nums before:font-[510] before:h-1 before:tracking-[-0.204px] before:leading-[14px] before:list-outside before:list-disc before:pointer-events-none before:absolute before:text-center before:indent-[0px] before:normal-case before:text-nowrap before:visible before:w-0.5 before:rounded-tl-sm before:border-separate before:left-0.5 before:-bottom-1 before:font-inter_variable">
                    zoe
                  </span>
                </span>
              </span>
              ideas
            </span>
            <div className="box-border caret-transparent h-px min-h-px min-w-px outline-transparent w-px -ml-px mt-[11px]"></div>
            <span className="text-neutral-400 text-[15px] box-border caret-transparent tracking-[-0.165px] outline-transparent">
              Write down product ideas and work together on feature specs in
              realtime, multiplayer project
              <span className="relative box-border caret-transparent outline-transparent pointer-events-none before:accent-auto before:bg-indigo-500 before:box-border before:caret-transparent before:text-neutral-400 before:block before:text-[15px] before:not-italic before:normal-nums before:font-normal before:tracking-[-0.165px] before:leading-6 before:list-outside before:list-disc before:pointer-events-none before:absolute before:text-start before:indent-[0px] before:normal-case before:visible before:w-0.5 before:rounded-full before:border-separate before:left-0 before:-inset-y-px before:font-inter_variable">
                <span className="absolute box-border caret-transparent block outline-transparent left-0 -top-3.5">
                  <span className="text-white text-[10px] bg-indigo-500 box-border caret-transparent block h-3.5 leading-[14px] outline-transparent text-center text-nowrap px-1 rounded-r-sm rounded-tl-sm before:accent-auto before:shadow-[rgb(94,106,210)_0px_-2px_0px_0px] before:box-border before:caret-transparent before:text-white before:block before:text-[10px] before:not-italic before:normal-nums before:font-normal before:h-1 before:tracking-[-0.165px] before:leading-[14px] before:list-outside before:list-disc before:pointer-events-none before:absolute before:text-center before:indent-[0px] before:normal-case before:text-nowrap before:visible before:w-0.5 before:rounded-tl-sm before:border-separate before:left-0.5 before:-bottom-1 before:font-inter_variable">
                    quinn
                  </span>
                </span>
              </span>
              documents. Add{" "}
              <span className="text-neutral-500 box-border caret-transparent outline-transparent">
                **
              </span>
              style
              <span className="text-neutral-500 box-border caret-transparent outline-transparent">
                **
              </span>
              and
              <span className="text-neutral-500 box-border caret-transparent outline-transparent">
                ##
              </span>
              structure with rich-text formatting options.
            </span>
            <div className="box-border caret-transparent h-px min-h-px min-w-px outline-transparent w-px -ml-px mt-[23px]"></div>
            <img
              src="https://c.animaapp.com/miwyuqyvUsUdBR/assets/icon-54.svg"
              alt="Icon"
              className="box-border caret-transparent shrink-0 h-[165px] outline-transparent w-[333px]"
            />
          </div>
        </div>
      </div>
    </div>
  );
};
