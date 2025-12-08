import React from 'react';

export const FooterColumn = (props) => {
  return (
    <div
      className={`text-[13px] box-border caret-transparent tracking-[-0.13px] leading-[19.5px] outline-transparent w-full ${props.variant || "pl-0 pr-6 md:pl-6"}`}
    >
      <h3 className="font-[510] box-border caret-transparent outline-transparent mb-4 md:mb-6">
        {props.title}
      </h3>
      <ul className="box-border caret-transparent gap-x-0.5 flex flex-col list-none outline-transparent gap-y-0.5 pl-0">
        {props.links.map((link, index) => (
          <li
            key={index}
            className="box-border caret-transparent outline-transparent"
          >
            <a
              href={link.href}
              className="text-neutral-400 items-center box-border caret-transparent flex min-h-7 outline-transparent text-wrap w-full md:text-nowrap"
            >
              {link.shortText ? (
                <>
                  <span className="box-border caret-transparent hidden min-h-0 min-w-0 outline-transparent text-wrap md:block md:min-h-auto md:min-w-auto md:text-nowrap">
                    {link.text}
                  </span>
                  <span className="box-border caret-transparent block min-h-auto min-w-auto outline-transparent text-wrap md:hidden md:min-h-0 md:min-w-0 md:text-nowrap">
                    {link.shortText}
                  </span>
                </>
              ) : (
                link.text
              )}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
};