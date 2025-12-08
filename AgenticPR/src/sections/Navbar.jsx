import React from 'react';

export const NavbarLogo = () => {
  return (
    <li className="box-border caret-transparent flex basis-[0%] grow justify-start outline-transparent text-nowrap">
      <span className="box-border caret-transparent flex outline-transparent text-nowrap">
        <a
          aria-label="Navigate to home"
          href="/homepage"
          className="items-center box-border caret-transparent flex h-8 justify-start outline-transparent text-nowrap -ml-2 px-2 rounded-md"
        >
          <img
            src="https://c.animaapp.com/miwyuqyvUsUdBR/assets/icon-1.svg"
            alt="Icon"
            className="box-border caret-transparent shrink-0 h-5 outline-transparent text-nowrap"
          />
        </a>
      </span>
    </li>
  );
};

export const MobileMenuButton = () => {
  return (
    <li className="box-border caret-transparent block min-h-[auto] min-w-[auto] outline-transparent text-nowrap -ml-4 md:hidden md:min-h-0 md:min-w-0">
      <button
        type="button"
        className="items-center aspect-square bg-transparent caret-transparent flex h-16 justify-center text-center text-nowrap bg-[position:0px_0px] -mr-6 p-0"
      >
        <img
          src="https://c.animaapp.com/miwyuqyvUsUdBR/assets/icon-2.svg"
          alt="Icon"
          className="box-border caret-transparent shrink-0 h-4 outline-transparent text-nowrap w-4"
        />
      </button>
    </li>
  );
};

export const DesktopMenu = () => {
  return (
    <ul
      aria-label="Site navigation"
      className="items-center box-border caret-transparent gap-x-4 flex justify-start list-none min-h-16 outline-transparent gap-y-4 pl-0 md:gap-x-2 md:justify-normal md:gap-y-2"
    >
      <NavbarLogo />
      <li className="box-border caret-transparent hidden min-h-0 min-w-0 outline-transparent text-nowrap md:list-item md:min-h-[auto] md:min-w-[auto]">
        <button className="relative text-neutral-400 text-[13px] font-[510] items-center bg-transparent caret-transparent flex h-8 isolate justify-center leading-[19.5px] outline-transparent text-center text-nowrap bg-[position:0px_0px] px-3 py-0 rounded-lg before:accent-auto before:box-border before:caret-transparent before:text-neutral-400 before:block before:text-[13px] before:not-italic before:normal-nums before:font-[510] before:tracking-[normal] before:leading-[19.5px] before:list-outside before:list-none before:pointer-events-auto before:absolute before:text-center before:indent-[0px] before:normal-case before:text-nowrap before:visible before:z-0 before:border-separate before:-inset-x-2 before:inset-y-0 before:font-inter_variable">
          Product
        </button>
        <a
          href="/features"
          className="relative text-neutral-400 text-[13px] font-[510] items-center box-border caret-transparent hidden h-8 isolate justify-center leading-[19.5px] outline-transparent text-nowrap bg-[position:0px_0px] px-3 rounded-lg before:accent-auto before:box-border before:caret-transparent before:text-neutral-400 before:block before:text-[13px] before:not-italic before:normal-nums before:font-[510] before:tracking-[normal] before:leading-[19.5px] before:list-outside before:list-none before:pointer-events-auto before:absolute before:text-start before:indent-[0px] before:normal-case before:text-nowrap before:visible before:z-0 before:border-separate before:-inset-x-2 before:inset-y-0 before:font-inter_variable"
        >
          Product
        </a>
      </li>
      <li className="box-border caret-transparent hidden min-h-0 min-w-0 outline-transparent text-nowrap md:list-item md:min-h-[auto] md:min-w-[auto]">
        <button className="relative text-neutral-400 text-[13px] font-[510] items-center bg-transparent caret-transparent flex h-8 isolate justify-center leading-[19.5px] outline-transparent text-center text-nowrap bg-[position:0px_0px] px-3 py-0 rounded-lg before:accent-auto before:box-border before:caret-transparent before:text-neutral-400 before:block before:text-[13px] before:not-italic before:normal-nums before:font-[510] before:tracking-[normal] before:leading-[19.5px] before:list-outside before:list-none before:pointer-events-auto before:absolute before:text-center before:indent-[0px] before:normal-case before:text-nowrap before:visible before:z-0 before:border-separate before:-inset-x-2 before:inset-y-0 before:font-inter_variable">
          Resources
        </button>
        <a
          href="/about"
          className="relative text-neutral-400 text-[13px] font-[510] items-center box-border caret-transparent hidden h-8 isolate justify-center leading-[19.5px] outline-transparent text-nowrap bg-[position:0px_0px] px-3 rounded-lg before:accent-auto before:box-border before:caret-transparent before:text-neutral-400 before:block before:text-[13px] before:not-italic before:normal-nums before:font-[510] before:tracking-[normal] before:leading-[19.5px] before:list-outside before:list-none before:pointer-events-auto before:absolute before:text-start before:indent-[0px] before:normal-case before:text-nowrap before:visible before:z-0 before:border-separate before:-inset-x-2 before:inset-y-0 before:font-inter_variable"
        >
          Resources
        </a>
      </li>
      <li className="box-border caret-transparent hidden min-h-0 min-w-0 outline-transparent text-nowrap md:list-item md:min-h-[auto] md:min-w-[auto]">
        <a
          href="/pricing"
          className="relative text-neutral-400 text-[13px] font-[510] items-center box-border caret-transparent flex h-8 justify-center leading-[19.5px] outline-transparent text-nowrap bg-[position:0px_0px] px-3 rounded-lg"
        >
          Pricing
        </a>
      </li>
      <li className="box-border caret-transparent hidden min-h-0 min-w-0 outline-transparent text-nowrap md:list-item md:min-h-[auto] md:min-w-[auto]">
        <a
          href="/customers"
          className="relative text-neutral-400 text-[13px] font-[510] items-center box-border caret-transparent flex h-8 justify-center leading-[19.5px] outline-transparent text-nowrap bg-[position:0px_0px] px-3 rounded-lg"
        >
          Customers
        </a>
      </li>
      <li className="box-border caret-transparent hidden min-h-0 min-w-0 outline-transparent text-nowrap md:list-item md:min-h-[auto] md:min-w-[auto]">
        <a
          href="/now"
          className="relative text-neutral-400 text-[13px] font-[510] items-center box-border caret-transparent flex h-8 justify-center leading-[19.5px] outline-transparent text-nowrap bg-[position:0px_0px] px-3 rounded-lg"
        >
          Now
        </a>
      </li>
      <li className="box-border caret-transparent hidden min-h-0 min-w-0 outline-transparent text-nowrap md:list-item md:min-h-[auto] md:min-w-[auto]">
        <a
          href="/contact"
          className="relative text-neutral-400 text-[13px] font-[510] items-center box-border caret-transparent flex h-8 justify-center leading-[19.5px] outline-transparent text-nowrap bg-[position:0px_0px] px-3 rounded-lg"
        >
          Contact
        </a>
      </li>
      <div className="box-border caret-transparent gap-x-2 flex basis-[0%] grow justify-end outline-transparent gap-y-2">
        <li className="items-center box-border caret-transparent hidden justify-center outline-transparent text-nowrap">
          <a
            href="/docs"
            className="relative text-neutral-400 text-[13px] font-[510] items-center box-border caret-transparent flex h-8 justify-center leading-[19.5px] outline-transparent text-nowrap w-full bg-[position:0px_0px] px-3 rounded-lg"
          >
            Docs
          </a>
        </li>
        <li className="items-center box-border caret-transparent hidden justify-center outline-transparent text-nowrap">
          <span className="box-border caret-transparent outline-transparent text-nowrap w-full">
            <a
              type="button"
              href="/login"
              className="relative text-zinc-950 text-[13px] font-[510] items-center bg-neutral-200 shadow-[rgba(0,0,0,0)_0px_8px_2px_0px,rgba(0,0,0,0.01)_0px_5px_2px_0px,rgba(0,0,0,0.04)_0px_3px_2px_0px,rgba(0,0,0,0.07)_0px_1px_1px_0px,rgba(0,0,0,0.08)_0px_0px_1px_0px] box-border caret-transparent gap-x-2 inline-flex shrink-0 h-8 justify-center leading-8 max-w-full outline-transparent gap-y-2 text-nowrap w-full border border-neutral-200 px-3 rounded-lg border-solid"
            >
              Open app
            </a>
          </span>
        </li>
        <li className="items-center box-border caret-transparent flex justify-center outline-transparent text-nowrap">
          <span className="box-border caret-transparent block outline-transparent text-nowrap w-full">
            <a
              href="/login"
              className="relative text-neutral-400 text-[13px] font-[510] items-center box-border caret-transparent flex h-8 justify-center leading-[19.5px] outline-transparent text-nowrap w-full bg-[position:0px_0px] px-3 rounded-lg"
            >
              Log in
            </a>
          </span>
        </li>
        <li className="items-center box-border caret-transparent flex justify-center outline-transparent text-nowrap">
          <a
            type="button"
            href="/signup"
            className="relative text-zinc-950 text-[13px] font-[510] items-center bg-neutral-200 shadow-[rgba(0,0,0,0)_0px_8px_2px_0px,rgba(0,0,0,0.01)_0px_5px_2px_0px,rgba(0,0,0,0.04)_0px_3px_2px_0px,rgba(0,0,0,0.07)_0px_1px_1px_0px,rgba(0,0,0,0.08)_0px_0px_1px_0px] box-border caret-transparent gap-x-2 flex shrink-0 h-8 justify-center leading-8 max-w-full outline-transparent gap-y-2 text-nowrap w-full border border-neutral-200 px-3 rounded-lg border-solid"
          >
            Sign up
          </a>
        </li>
      </div>
      <MobileMenuButton />
    </ul>
  );
};

export const Navbar = () => {
  return (
    <div className="relative items-center box-border caret-transparent flex h-16 max-w-screen-lg outline-transparent w-full mx-auto px-6">
      <div className="relative box-border caret-transparent outline-transparent w-full">
        <DesktopMenu />
      </div>
    </div>
  );
};