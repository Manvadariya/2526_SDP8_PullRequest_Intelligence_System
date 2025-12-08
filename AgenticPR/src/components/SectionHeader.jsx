import React from "react";

/**
 * @typedef {Object} SectionHeaderProps
 * @property {string} variant
 * @property {Object} [badge]
 * @property {string} badge.iconClassName
 * @property {string} badge.text
 * @property {string} badge.iconSrc
 * @property {string} title
 * @property {string} [titleLink]
 * @property {React.ReactNode} description
 * @property {Object} [ctaButton]
 * @property {string} ctaButton.text
 * @property {string} ctaButton.href
 * @property {string} ctaButton.iconSrc
 * @property {string} [ctaButton.ariaLabel]
 * @property {Array<{title: React.ReactNode, description: string}>} [features]
 * @property {Array<{imageSrc: string, label: string, iconSrc: string}>} [certifications]
 * @property {string} [bottomIconSrc]
 */

/**
 * @param {SectionHeaderProps} props
 */
export const SectionHeader = (props) => {
  const headerContent = (
    <>
      {props.badge && (
        <>
          <div className="items-center box-border caret-transparent gap-x-2 flex outline-transparent gap-y-2">
            <div
              className={`box-border caret-transparent h-2 outline-transparent w-3.5 rounded-full ${props.badge.iconClassName}`}
            ></div>
            <span className="text-slate-300 text-[13px] box-border caret-transparent block tracking-[-0.13px] leading-[19.5px] outline-transparent">
              <div className="items-center box-border caret-transparent gap-x-1.5 flex outline-transparent gap-y-1.5">
                {props.badge.text}
                <img
                  src={props.badge.iconSrc}
                  alt="Icon"
                  className="text-neutral-500 box-border caret-transparent shrink-0 h-[13px] outline-transparent w-[13px]"
                />
              </div>
            </span>
          </div>
          <div className="box-border caret-transparent h-px min-h-px min-w-px outline-transparent w-px -ml-px mt-[15px]"></div>
        </>
      )}
      <h2 className="text-[40px] font-[538] box-border caret-transparent tracking-[-0.6px] leading-[44px] outline-transparent md:text-[56px] md:tracking-[-1.82px] md:leading-[61.6px]">
        {props.title}
      </h2>
    </>
  );

  return (
    <div
      className={`box-border caret-transparent gap-x-8 grid grid-cols-[repeat(4,minmax(0px,1fr))] outline-transparent gap-y-8 md:grid-cols-[repeat(12,minmax(0px,1fr))] ${props.variant}`}
    >
      <div className="box-border caret-transparent col-end-[a] col-start-[a] row-end-[a] row-start-[a] outline-transparent">
        {props.titleLink ? (
          <a
            href={props.titleLink}
            className="box-border caret-transparent outline-transparent"
          >
            {headerContent}
          </a>
        ) : (
          <>
            {headerContent}
            {props.variant ===
              "[grid-template-areas:'a_a_a_a''b_b_b_b''c_c_c_c'] md:[grid-template-areas:'a_a_a_a_a_._._._._._.''b_b_b_b_b_._._._._._.''c_c_c_c_c_._._._._._.']" && (
              <>
                <div className="box-border caret-transparent h-px min-h-px min-w-px outline-transparent w-px -ml-px mt-[23px]"></div>
                <p className="text-neutral-400 text-[15px] box-border caret-transparent tracking-[-0.165px] outline-transparent">
                  {props.description}
                </p>
              </>
            )}
          </>
        )}
      </div>
      <div
        className={`box-border caret-transparent col-end-[b] col-start-[b] row-end-[b] row-start-[b] outline-transparent${props.variant === "[grid-template-areas:'a_a_a_a''b_b_b_b'] md:[grid-template-areas:'a_a_a_a_a_a_b_b_b_b_b_b']" || props.variant === "[grid-template-areas:'a_a_a_a''b_b_b_b'] md:[grid-template-areas:'a_a_a_a_a_a_._b_b_b_b_b']" ? " self-end" : ""}`}
      >
        {props.variant !==
          "[grid-template-areas:'a_a_a_a''b_b_b_b''c_c_c_c'] md:[grid-template-areas:'a_a_a_a_a_._._._._._.''b_b_b_b_b_._._._._._.''c_c_c_c_c_._._._._._.']" && (
          <p
            className={`text-neutral-400 font-[510] box-border caret-transparent outline-transparent ${props.variant === "[grid-template-areas:'a_a_a_a''b_b_b_b'] md:[grid-template-areas:'a_a_a_a_a_a_b_b_b_b_b_b']" || props.variant === "[grid-template-areas:'a_a_a_a''b_b_b_b'] md:[grid-template-areas:'a_a_a_a_a_a_._b_b_b_b_b']" ? "text-[15px] tracking-[-0.165px]" : props.variant === "[grid-template-areas:'a_a_a_a''b_b_b_b'] md:[grid-template-areas:'a_a_a_a_a_a_a_a_a_a_a_._.''b_b_b_b_b_b_b_._._._._._.']" ? "text-[17px] leading-[24.5px] max-w-[400px]" : "text-[17px] leading-[24.5px]"}`}
          >
            {props.description}
          </p>
        )}
        {props.ctaButton && (
          <>
            <div className="box-border caret-transparent h-px min-h-px min-w-px outline-transparent w-px -ml-px mt-[23px]"></div>
            <a
              aria-label={props.ctaButton.ariaLabel}
              href={props.ctaButton.href}
              className="relative text-[13px] font-[510] items-center bg-zinc-800 box-border caret-transparent gap-x-2 inline-flex shrink-0 h-8 justify-center leading-8 max-w-full outline-transparent gap-y-2 text-nowrap border border-zinc-700 px-3 rounded-lg border-solid"
            >
              {props.ctaButton.text}
              <img
                src={props.ctaButton.iconSrc}
                alt="Icon"
                className="box-border caret-transparent shrink-0 h-4 outline-transparent text-nowrap w-4"
              />
            </a>
          </>
        )}
        {props.features && (
          <>
            <div className="box-border caret-transparent h-px min-h-px min-w-px outline-transparent w-px -ml-px mt-[15px]"></div>
            <div className="bg-white/10 box-border caret-transparent shrink-0 h-px outline-transparent w-full rounded-full"></div>
            <div className="box-border caret-transparent h-px min-h-px min-w-px outline-transparent w-px -ml-px mt-[23px]"></div>
            <dl className="box-border caret-transparent gap-x-12 grid grid-cols-[1fr] outline-transparent gap-y-10 md:grid-cols-[auto_minmax(0px,1fr)]">
              {props.features.map((feature, index) => (
                <div
                  key={index}
                  className="box-border caret-transparent gap-x-2 flex flex-col min-h-auto min-w-auto outline-transparent gap-y-2 md:gap-x-normal md:contents md:flex-row md:min-h-0 md:min-w-0 md:gap-y-normal"
                >
                  <dt className="text-sm font-[510] box-border caret-transparent tracking-[-0.18px] leading-[21px] outline-transparent">
                    {feature.title}
                  </dt>
                  <dd className="text-neutral-400 text-sm box-border caret-transparent tracking-[-0.18px] leading-[21px] outline-transparent">
                    {feature.description}
                  </dd>
                </div>
              ))}
            </dl>
          </>
        )}
      </div>
      {props.certifications && (
        <div className="box-border caret-transparent col-end-[c] col-start-[c] row-end-[c] row-start-[c] outline-transparent">
          <div className="box-border caret-transparent h-px min-h-px min-w-px outline-transparent w-px -ml-px mt-[39px]"></div>
          <div className="bg-white/10 box-border caret-transparent shrink-0 h-px outline-transparent w-full rounded-full"></div>
          <div className="box-border caret-transparent gap-x-2 grid grid-cols-[repeat(5,auto)] grid-rows-[repeat(1,auto)] justify-around outline-transparent gap-y-2">
            {props.certifications.map((cert, index) => (
              <React.Fragment key={index}>
                {index > 0 && (
                  <div className="self-stretch bg-white/10 box-border caret-transparent shrink-0 outline-transparent w-px rounded-full"></div>
                )}
                <div className="items-center box-border caret-transparent gap-x-4 flex flex-col outline-transparent gap-y-4 pt-8">
                  <img
                    alt=""
                    src={cert.imageSrc}
                    className="text-transparent aspect-[auto_64_/_64] box-border shrink-0 max-w-full w-16"
                  />
                  <div className="items-center box-border caret-transparent gap-x-1 flex outline-transparent gap-y-1">
                    <span className="text-neutral-500 text-sm box-border caret-transparent block tracking-[-0.182px] leading-[21px] outline-transparent">
                      {cert.label}
                    </span>
                    <img
                      src={cert.iconSrc}
                      alt="Icon"
                      className="box-border caret-transparent shrink-0 h-[18px] outline-transparent w-[18px]"
                    />
                  </div>
                </div>
              </React.Fragment>
            ))}
          </div>
        </div>
      )}
      {props.bottomIconSrc && (
        <div className="absolute box-border caret-transparent hidden outline-transparent pointer-events-none overflow-hidden inset-0 md:block">
          <img
            src={props.bottomIconSrc}
            alt="Icon"
            className="absolute box-border caret-transparent shrink-0 h-[854px] outline-transparent w-[1022px] my-auto left-2/4 inset-y-0"
          />
        </div>
      )}
    </div>
  );
};
