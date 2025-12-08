import { FooterColumn } from "@/sections/Footer/components/FooterColumn";

export const Footer = () => {
  return (
    <footer className="relative bg-zinc-950 border-b-stone-50 border-l-stone-50 border-r-stone-50 border-t-zinc-800 box-border caret-transparent max-w-full outline-transparent z-50 border-t">
      <div className="items-start box-border caret-transparent gap-x-4 grid grid-cols-[repeat(3,minmax(0px,1fr))] grid-rows-[auto_repeat(3,auto)] justify-items-start max-w-screen-lg outline-transparent gap-y-10 mx-auto py-14 md:gap-x-8 md:grid-cols-[repeat(6,minmax(0px,1fr))] md:grid-rows-none">
        <div className="items-start box-border caret-transparent flex flex-col h-full justify-between outline-transparent">
          <a
            href="/"
            className="box-border caret-transparent flex col-end-[-1] col-start-1 row-end-1 row-start-1 outline-transparent ml-6 md:col-end-auto md:col-start-auto md:row-end-auto md:row-start-auto"
          >
            <img
              src="https://c.animaapp.com/miwyuqyvUsUdBR/assets/icon-74.svg"
              alt="Icon"
              className="box-border caret-transparent shrink-0 h-5 outline-transparent w-5"
            />
          </a>
        </div>
        <FooterColumn
          title="Features"
          links={[
            { href: "/plan", text: "Plan" },
            { href: "/build", text: "Build" },
            { href: "/insights", text: "Insights" },
            { href: "/customer-requests", text: "Customer Requests" },
            { href: "/asks", text: "Linear Asks" },
            { href: "/security", text: "Security" },
            { href: "/mobile", text: "Mobile" },
          ]}
        />
        <FooterColumn
          title="Product"
          links={[
            { href: "/pricing", text: "Pricing" },
            { href: "/method", text: "Method" },
            { href: "/integrations", text: "Integrations" },
            { href: "/changelog", text: "Changelog" },
            { href: "/docs", text: "Documentation", shortText: "Docs" },
            { href: "/download", text: "Download" },
            { href: "/switch", text: "Switch" },
          ]}
        />
        <FooterColumn
          title="Company"
          variant="px-6"
          links={[
            { href: "/about", text: "About" },
            { href: "/customers", text: "Customers" },
            { href: "/careers", text: "Careers" },
            { href: "/now", text: "Now" },
            { href: "/readme", text: "README" },
            { href: "/quality", text: "Quality" },
            { href: "/brand", text: "Brand" },
          ]}
        />
        <FooterColumn
          title="Resources"
          links={[
            { href: "/developers", text: "Developers" },
            { href: "https://linearstatus.com/", text: "Status" },
            { href: "/startups", text: "Startups" },
            { href: "/security/vulnerability", text: "Report vulnerability" },
            { href: "/dpa", text: "DPA" },
            { href: "/privacy", text: "Privacy" },
            { href: "/terms", text: "Terms" },
          ]}
        />
        <FooterColumn
          title="Connect"
          links={[
            { href: "/contact", text: "Contact us" },
            { href: "https://linear.app/join-slack", text: "Community" },
            { href: "https://x.com/linear", text: "X (Twitter)" },
            { href: "https://github.com/linear", text: "GitHub" },
            { href: "https://www.youtube.com/@linear", text: "YouTube" },
          ]}
        />
        <div className="text-[13px] box-border caret-transparent col-end-[-1] col-start-1 tracking-[-0.13px] leading-[19.5px] outline-transparent w-full pl-0 pr-6 md:col-start-2 md:pl-6"></div>
      </div>
    </footer>
  );
};
