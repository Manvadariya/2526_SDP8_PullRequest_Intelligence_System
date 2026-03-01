import React, { useState } from "react";
import { Link } from "react-router-dom";

export default function Signup() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  return (
    <section className="bg-[linear-gradient(rgba(255,255,255,0.03),rgba(0,0,0,0)_40%)] box-border caret-transparent isolate outline-transparent overflow-x-hidden overflow-y-auto py-12 md:py-40">
      <div className="box-border caret-transparent max-w-[420px] outline-transparent w-full mx-auto px-6">
        {/* Header */}
        <div className="box-border caret-transparent outline-transparent text-center mb-10">
          <div className="items-center box-border caret-transparent gap-x-2 flex justify-center outline-transparent gap-y-2 mb-6">
            <svg className="box-border caret-transparent shrink-0 h-8 outline-transparent w-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" />
            </svg>
            <span className="text-[21px] font-[510] box-border caret-transparent tracking-[-0.37px] leading-7 outline-transparent">
              AgenticPR
            </span>
          </div>
          <h1 className="text-[40px] font-[538] box-border caret-transparent tracking-[-0.6px] leading-[44px] outline-transparent mb-3">
            Create account
          </h1>
          <p className="text-neutral-400 text-[15px] box-border caret-transparent tracking-[-0.165px] outline-transparent">
            Get started with AI-powered code reviews
          </p>
        </div>

        {/* GitHub OAuth Button */}
        <div className="box-border caret-transparent outline-transparent mb-6">
          <button
            type="button"
            className="relative text-stone-50 text-[13px] font-[510] items-center bg-zinc-800 box-border caret-transparent gap-x-2 flex shrink-0 h-10 justify-center leading-8 max-w-full outline-transparent gap-y-2 text-nowrap w-full border border-zinc-700 px-3 rounded-lg border-solid"
          >
            <svg className="box-border caret-transparent shrink-0 h-5 outline-transparent w-5" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
            </svg>
            Sign up with GitHub
          </button>
        </div>

        {/* Divider */}
        <div className="items-center box-border caret-transparent flex outline-transparent gap-x-4 mb-6">
          <div className="bg-white/10 box-border caret-transparent shrink-0 h-px outline-transparent grow rounded-full"></div>
          <span className="text-neutral-500 text-[13px] box-border caret-transparent block tracking-[-0.13px] leading-[19.5px] outline-transparent">
            or
          </span>
          <div className="bg-white/10 box-border caret-transparent shrink-0 h-px outline-transparent grow rounded-full"></div>
        </div>

        {/* Form */}
        <form className="box-border caret-transparent outline-transparent" onSubmit={(e) => e.preventDefault()}>
          <div className="box-border caret-transparent outline-transparent mb-4">
            <label className="text-slate-300 text-[13px] font-[510] box-border caret-transparent block tracking-[-0.13px] leading-[19.5px] outline-transparent mb-2">
              Full name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Your name"
              className="text-stone-50 text-[15px] items-center bg-zinc-900 box-border caret-stone-50 flex h-10 outline-transparent w-full border border-zinc-700 px-3 rounded-lg border-solid placeholder:text-neutral-500 focus:border-indigo-500 focus:outline-none"
            />
          </div>

          <div className="box-border caret-transparent outline-transparent mb-4">
            <label className="text-slate-300 text-[13px] font-[510] box-border caret-transparent block tracking-[-0.13px] leading-[19.5px] outline-transparent mb-2">
              Email address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              className="text-stone-50 text-[15px] items-center bg-zinc-900 box-border caret-stone-50 flex h-10 outline-transparent w-full border border-zinc-700 px-3 rounded-lg border-solid placeholder:text-neutral-500 focus:border-indigo-500 focus:outline-none"
            />
          </div>

          <div className="box-border caret-transparent outline-transparent mb-6">
            <label className="text-slate-300 text-[13px] font-[510] box-border caret-transparent block tracking-[-0.13px] leading-[19.5px] outline-transparent mb-2">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="text-stone-50 text-[15px] items-center bg-zinc-900 box-border caret-stone-50 flex h-10 outline-transparent w-full border border-zinc-700 px-3 rounded-lg border-solid placeholder:text-neutral-500 focus:border-indigo-500 focus:outline-none"
            />
            <p className="text-neutral-500 text-[12px] box-border caret-transparent tracking-[-0.12px] leading-[18px] outline-transparent mt-2">
              Must be at least 8 characters
            </p>
          </div>

          <button
            type="submit"
            className="relative text-zinc-950 text-[13px] font-[510] items-center bg-neutral-200 shadow-[rgba(0,0,0,0)_0px_8px_2px_0px,rgba(0,0,0,0.01)_0px_5px_2px_0px,rgba(0,0,0,0.04)_0px_3px_2px_0px,rgba(0,0,0,0.07)_0px_1px_1px_0px,rgba(0,0,0,0.08)_0px_0px_1px_0px] box-border caret-transparent gap-x-2 flex shrink-0 h-10 justify-center leading-8 max-w-full outline-transparent gap-y-2 text-nowrap w-full border border-neutral-200 px-3 rounded-lg border-solid"
          >
            Create account
          </button>
        </form>

        {/* Terms */}
        <p className="text-neutral-500 text-[12px] box-border caret-transparent tracking-[-0.12px] leading-[18px] outline-transparent text-center mt-4">
          By signing up, you agree to our Terms of Service and Privacy Policy
        </p>

        {/* Footer */}
        <div className="box-border caret-transparent outline-transparent text-center mt-8">
          <span className="text-neutral-400 text-[13px] box-border caret-transparent tracking-[-0.13px] leading-[19.5px] outline-transparent">
            Already have an account?{" "}
            <Link to="/login" className="text-stone-50 font-[510] box-border caret-transparent outline-transparent hover:text-indigo-400">
              Log in
            </Link>
          </span>
        </div>
      </div>
    </section>
  );
};
