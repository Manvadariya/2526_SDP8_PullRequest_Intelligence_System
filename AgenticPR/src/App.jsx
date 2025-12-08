import { Navbar } from "@/sections/Navbar";
import { Main } from "@/components/Main";
import { Footer } from "@/sections/Footer";

export const App = () => {
  return (
    <body className="text-stone-50 text-base not-italic normal-nums font-normal accent-auto bg-zinc-950 box-border caret-transparent block tracking-[normal] leading-6 list-outside list-disc min-h-[1000px] outline-transparent overflow-x-hidden overflow-y-auto pointer-events-auto text-start indent-[0px] normal-case visible border-separate font-inter_variable">
      <div className="box-border caret-transparent hidden outline-transparent"></div>
      <section
        aria-label="Notifications alt+T"
        className="box-border caret-transparent outline-transparent"
      ></section>
      <div className="box-border caret-transparent flex flex-col h-full outline-transparent w-full">
        <div className="box-border caret-transparent outline-transparent">
          <Navbar />
        </div>
        <Main />
        <Footer />
      </div>
      <img
        src="https://c.animaapp.com/miwyuqyvUsUdBR/assets/icon-75.svg"
        alt="Icon"
        className="box-border caret-transparent hidden shrink-0 outline-transparent"
      />
      <div className="absolute box-border caret-transparent h-0 outline-transparent w-0 overflow-hidden">
        <img
          src="https://c.animaapp.com/miwyuqyvUsUdBR/assets/icon-76.svg"
          alt="Icon"
          className="box-border caret-transparent shrink-0 h-0 outline-transparent w-0"
        />
      </div>
      <div className="absolute box-border caret-transparent h-0 outline-transparent w-0 overflow-hidden">
        <img
          src="https://c.animaapp.com/miwyuqyvUsUdBR/assets/icon-77.svg"
          alt="Icon"
          className="box-border caret-transparent shrink-0 h-0 outline-transparent w-0"
        />
      </div>
      <div className="absolute box-border caret-transparent h-0 outline-transparent w-0 overflow-hidden"></div>
      <div className="absolute box-border caret-transparent block outline-transparent"></div>
      <div className="fixed box-border caret-transparent hidden justify-center outline-transparent w-full z-[10000] left-0 top-14 md:flex"></div>
    </body>
  );
};

export default App;