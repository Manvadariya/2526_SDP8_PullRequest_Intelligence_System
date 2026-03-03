import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import useRepoStats from '../hooks/useRepoStats';

export default function Settings() {
  const { repoName } = useParams();
  const { stats } = useRepoStats();
  const [activeTab, setActiveTab] = useState('General');

  // Derive repo info from real data if available
  const totalReviews = stats?.total_reviews || 0;
  const languages = stats?.languages || [];

  const tabs = [
    'General',
    'Code Review',
    'Code Formatters',
    'Code Coverage',
    'Quality gates',
    'Badges'
  ];

  return (
    <div className="flex bg-[#0E1116] h-[calc(100vh-130px)]">
      {/* Sidebar Navigation */}
      <div className="w-[240px] shrink-0 border-r border-[#30363D] py-4">
        <nav className="flex flex-col gap-[2px] px-3">
          {tabs.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`w-full text-left px-3 py-1.5 rounded-md text-[13px] font-medium transition-colors ${
                activeTab === tab
                  ? 'bg-[#161B22] text-[#E6EDF3] border-l-2 border-[#3fb950] -ml-px pl-[11px]'
                  : 'text-[#8B949E] hover:text-[#E6EDF3] hover:bg-[#161B22]'
              }`}
            >
              {tab}
            </button>
          ))}
        </nav>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 p-8 overflow-y-auto">
        <div className="max-w-[760px] w-full">
          
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-xl font-semibold text-[#E6EDF3] mb-1">{activeTab}</h1>
            <p className="text-[14px] text-[#8B949E]">
              Manage your repository settings.
            </p>
          </div>

          {/* Form Actions (Only showing General for now based on screenshot) */}
          {activeTab === 'General' && (
             <div className="space-y-8">
                
                {/* Default Branch */}
                <div>
                   <div className="flex justify-between items-start mb-4">
                      <div>
                         <h3 className="text-[14px] font-medium text-[#E6EDF3] mb-1">Default branch</h3>
                         <p className="text-[13px] text-[#8B949E] leading-relaxed max-w-[500px]">
                            We use this branch to track issues and metrics for the repository and as a baseline for all merge request analyses.
                         </p>
                      </div>
                      <div className="w-[240px]">
                         <input 
                            type="text" 
                            defaultValue="main" 
                            className="w-full bg-[#0E1116] border border-[#30363D] rounded-md py-1.5 px-3 text-[13px] text-[#E6EDF3] focus:outline-none focus:border-[#58a6ff] focus:ring-1 focus:ring-[#58a6ff]"
                         />
                      </div>
                   </div>
                   
                   <div className="bg-[#1C2128] border border-[#444C56] rounded-md p-3 flex items-start gap-3 mt-4">
                      <div className="w-4 h-4 rounded-full bg-[#1F6FEB] flex items-center justify-center text-white font-bold text-[10px] shrink-0 mt-0.5">!</div>
                      <p className="text-[13px] text-[#58a6ff] leading-relaxed">
                         We recommend keeping this identical to the default branch on GitHub.
                      </p>
                   </div>
                </div>

                <div className="h-px bg-[#30363D] w-full"></div>

                {/* Git Submodules */}
                <div>
                   <div className="flex justify-between items-start">
                      <div>
                         <h3 className="text-[14px] font-medium text-[#E6EDF3] mb-1">Use Git submodules</h3>
                         <p className="text-[13px] text-[#8B949E] leading-relaxed max-w-[500px]">
                            Enable this if the repository depends on code inside submodules. If the submodules are private, ensure that DeepSource has access to them via the SSH key.
                         </p>
                      </div>
                      <div className="pt-1">
                         <div className="w-9 h-5 bg-[#21262D] rounded-full relative cursor-pointer border border-[#30363D]">
                            <div className="absolute left-0.5 top-0.5 w-3.5 h-3.5 bg-[#8B949E] rounded-full transition-transform"></div>
                         </div>
                      </div>
                   </div>
                </div>

                <div className="h-px bg-[#30363D] w-full"></div>

                {/* Analysis Result Diffing */}
                <div>
                  <h3 className="text-[14px] font-medium text-[#E6EDF3] mb-1">Analysis result diffing</h3>
                  <p className="text-[13px] text-[#8B949E] leading-relaxed max-w-[500px] mb-4">
                      Control the scope of analysis results shown on pull request analysis runs. We recommend you keep this set to <span className="font-semibold text-[#E6EDF3]">Baseline</span>.
                  </p>

                  <div className="space-y-4">
                     <label className="flex items-start gap-3 cursor-pointer group">
                        <div className="w-3.5 h-3.5 rounded-full border border-[#3fb950] bg-[#161B22] flex items-center justify-center shrink-0 mt-[3px]">
                           <div className="w-1.5 h-1.5 rounded-full bg-[#3fb950]"></div>
                        </div>
                        <div>
                           <div className="text-[13px] font-medium text-[#E6EDF3] mb-0.5 uppercase tracking-wide">BASELINE</div>
                           <p className="text-[13px] text-[#8B949E] leading-relaxed">
                              Report issues only for modified lines in changed files in the pull request compared to the default branch.
                           </p>
                        </div>
                     </label>

                     <label className="flex items-start gap-3 cursor-pointer group">
                        <div className="w-3.5 h-3.5 rounded-full border border-[#8B949E] bg-[#161B22] flex items-center justify-center shrink-0 mt-[3px] group-hover:border-[#E6EDF3] transition-colors">
                        </div>
                        <div>
                           <div className="text-[13px] font-medium text-[#8B949E] group-hover:text-[#E6EDF3] mb-0.5 uppercase tracking-wide transition-colors">BROAD</div>
                           <p className="text-[13px] text-[#8B949E] leading-relaxed">
                              Report all issues in all the changed files in the pull request. We do not recommend this as it can get noisy.
                           </p>
                        </div>
                     </label>
                  </div>
                </div>

             </div>
          )}

          {activeTab === 'Code Review' && (
             <div className="space-y-8">
                <div>
                   <h2 className="text-[16px] font-semibold text-[#E6EDF3] mb-1">Code Review</h2>
                   <p className="text-[13px] text-[#8B949E] leading-relaxed max-w-[650px] mb-6">
                      Configure the settings for code quality and security review. You can enable as many analyzers you need and adjust individual properties for each to suit your development environment.
                   </p>

                   <div className="bg-[#161B22] border border-[#30363D] rounded-md p-5 mb-8">
                      <div className="flex justify-between items-start mb-6">
                         <div>
                            <h3 className="text-[14px] font-medium text-[#E6EDF3] mb-2">Enable code review</h3>
                            <p className="text-[13px] text-[#8B949E] leading-relaxed max-w-[500px]">
                               DeepSource will automatically review every pull request to identify bugs, security vulnerabilities, anti-patterns, and performance issues using a hybrid static analysis and AI code review agent.
                            </p>
                         </div>
                         <div className="pt-1">
                            <div className="w-9 h-5 bg-[#3fb950] rounded-full relative cursor-pointer border border-[#3fb950] transition-colors">
                               <div className="absolute right-0.5 top-0.5 w-3.5 h-3.5 bg-white rounded-full transition-transform"></div>
                            </div>
                         </div>
                      </div>

                      <div className="h-px bg-[#30363D] w-full mb-6"></div>

                      <label className="flex items-start gap-3 cursor-pointer">
                         <div className="mt-1">
                            <div className="w-3.5 h-3.5 rounded-[3px] bg-[#1F6FEB] border border-[#1F6FEB] flex items-center justify-center">
                               <svg width="10" height="10" viewBox="0 0 16 16" fill="white"><path fillRule="evenodd" d="M13.78 4.22a.75.75 0 010 1.06l-7.25 7.25a.75.75 0 01-1.06 0L2.22 9.28a.75.75 0 011.06-1.06L6 10.94l6.72-6.72a.75.75 0 011.06 0z"></path></svg>
                            </div>
                         </div>
                         <div>
                            <div className="flex items-center gap-2 mb-1">
                               <h3 className="text-[13px] font-medium text-[#E6EDF3]">Enable secrets detection</h3>
                               <span className="text-[10px] font-semibold tracking-wider text-[#58a6ff] bg-[#1F6FEB]/10 px-1.5 py-0.5 rounded uppercase">RECOMMENDED</span>
                            </div>
                            <p className="text-[13px] text-[#8B949E] leading-relaxed max-w-[500px]">
                               Scan code and configuration files to find accidentally exposed sensitive data like API keys, passwords, and tokens. Pull request checks will fail automatically if a secret is detected.
                            </p>
                         </div>
                      </label>
                   </div>

                   <h3 className="text-[14px] font-semibold text-[#E6EDF3] mb-4">Analyzers</h3>
                   
                   <div className="relative mb-4">
                      <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8B949E]" viewBox="0 0 16 16" fill="currentColor"><path fillRule="evenodd" d="M11.5 7a4.499 4.499 0 11-8.998 0A4.499 4.499 0 0111.5 7zm-.82 4.74a6 6 0 111.06-1.06l3.04 3.04a.75.75 0 11-1.06 1.06l-3.04-3.04z"></path></svg>
                      <input 
                         type="text" 
                         placeholder="Search analyzers by name or framework..." 
                         className="w-full bg-[#0E1116] border border-[#30363D] rounded-md py-2 pl-9 pr-3 text-[13px] text-[#E6EDF3] placeholder-[#8B949E] focus:outline-none focus:border-[#58a6ff] focus:ring-1 focus:ring-[#58a6ff]"
                      />
                   </div>

                   <div className="border border-[#30363D] rounded-md divide-y divide-[#30363D] overflow-hidden">
                      {(languages.length > 0 ? languages : ['JavaScript', 'Python']).map(lang => {
                         const langColorMap = {
                           JavaScript: { bg: '#f1e05a', text: 'black', border: ' border border-yellow-400' },
                           TypeScript: { bg: '#3178c6', text: 'white', border: '' },
                           Python: { bg: '#3572A5', text: 'white', border: '' },
                           Java: { bg: '#b07219', text: 'white', border: '' },
                           Go: { bg: '#00add8', text: 'black', border: '' },
                           Rust: { bg: '#dea584', text: 'black', border: '' },
                           C: { bg: '#555555', text: 'white', border: '' },
                           'C++': { bg: '#f34b7d', text: 'white', border: '' },
                           Ruby: { bg: '#701516', text: 'white', border: '' },
                           PHP: { bg: '#4F5D95', text: 'white', border: '' },
                           Shell: { bg: '#89e051', text: 'black', border: '' },
                         };
                         const lc = langColorMap[lang] || { bg: '#30363D', text: 'white', border: '' };
                         return (
                         <div key={lang} className="flex justify-between items-center px-4 py-3 bg-[#161B22] hover:bg-[#21262D] cursor-pointer transition-colors group">
                            <div className="flex items-center gap-3">
                               <div className={`w-5 h-5 rounded flex items-center justify-center text-[10px] font-bold${lc.border}`}
                                 style={{ backgroundColor: lc.bg, color: lc.text }}>
                                  {lang.charAt(0)}
                               </div>
                               <span className="text-[13px] font-medium text-[#E6EDF3]">{lang}</span>
                            </div>
                            <svg className="w-4 h-4 text-[#8B949E] group-hover:text-[#E6EDF3] transition-colors" viewBox="0 0 16 16" fill="currentColor"><path fillRule="evenodd" d="M6.22 3.22a.75.75 0 011.06 0l4.25 4.25a.75.75 0 010 1.06l-4.25 4.25a.75.75 0 01-1.06-1.06L9.94 8 6.22 4.28a.75.75 0 010-1.06z"></path></svg>
                         </div>
                         );
                      })}
                   </div>
                </div>
             </div>
          )}

          {activeTab === 'Code Formatters' && (
             <div className="space-y-8">
                <div>
                   <h2 className="text-[16px] font-semibold text-[#E6EDF3] mb-1">Code Formatters</h2>
                   <p className="text-[13px] text-[#8B949E] leading-relaxed max-w-[650px] mb-6">
                      Automated code formatting that doesn't break your build.
                   </p>

                   <div className="bg-[#161B22] border border-[#30363D] rounded-md p-5 mb-6">
                      <div className="flex justify-between items-start mb-4">
                         <div>
                            <h3 className="text-[14px] font-medium text-[#E6EDF3] mb-2">Autofix</h3>
                            <p className="text-[13px] text-[#8B949E] leading-relaxed max-w-[500px]">
                               To use Autofix on this repository, DeepSource needs the necessary permissions to automatically create pull-requests. <a href="#" className="text-[#58a6ff] hover:underline">Learn more →</a>
                            </p>
                         </div>
                         <button className="flex items-center gap-2 px-3 py-1.5 bg-[#238636] hover:bg-[#2ea043] rounded-md text-[13px] font-medium text-white transition-colors border border-[rgba(240,246,252,0.1)]">
                            <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path fillRule="evenodd" d="M7.646 1.146a.5.5 0 01.708 0l2 2a.5.5 0 01-.708.708L8.5 2.707V11.5a.5.5 0 01-1 0V2.707L6.354 3.854a.5.5 0 11-.708-.708l2-2zM3 13.5A1.5 1.5 0 014.5 12h7a1.5 1.5 0 011.5 1.5v.5A1.5 1.5 0 0111.5 15h-7A1.5 1.5 0 013 14v-.5z"></path></svg>
                            Install Autofix app
                         </button>
                      </div>
                      
                      <div className="bg-[#1C2128] border border-[#444C56] rounded-md p-3 flex items-start gap-2">
                         <div className="w-1.5 h-1.5 rounded-full bg-[#1F6FEB] shrink-0 mt-[7px]"></div>
                         <p className="text-[13px] text-[#E6EDF3] leading-relaxed">
                            The Autofix app has not been installed yet.
                         </p>
                      </div>
                   </div>

                   <div className="bg-[#161B22] border border-[#30363D] rounded-md p-5 mb-8">
                      <div className="flex justify-between items-start">
                         <div>
                            <h3 className="text-[14px] font-medium text-[#E6EDF3] mb-2">Enable code formatting on pull requests</h3>
                            <p className="text-[13px] text-[#8B949E] leading-relaxed max-w-[500px]">
                               DeepSource will run code formatters on every commit on every pull request. If the code needs formatting, it'll automatically add a new commit with the changes on top of the last commit.
                            </p>
                         </div>
                         <div className="pt-1">
                            <div className="w-9 h-5 bg-[#21262D] rounded-full relative cursor-pointer border border-[#30363D]">
                               <div className="absolute left-0.5 top-0.5 w-3.5 h-3.5 bg-[#8B949E] rounded-full transition-transform"></div>
                            </div>
                         </div>
                      </div>
                   </div>

                   <h3 className="text-[14px] font-semibold text-[#E6EDF3] mb-4">Code Formatters</h3>
                   
                   <div className="border border-[#30363D] border-dashed rounded-md p-8 flex flex-col items-center justify-center text-center bg-transparent">
                      <h4 className="text-[14px] font-semibold text-[#E6EDF3] mb-2">No formatters enabled</h4>
                      <p className="text-[13px] text-[#8B949E] max-w-[400px]">
                         Search for formatters and add them to automatically format your code on pull requests.
                      </p>
                   </div>
                </div>
             </div>
          )}

          {activeTab === 'Code Coverage' && (
             <div className="space-y-8">
                <div>
                   <h2 className="text-[16px] font-semibold text-[#E6EDF3] mb-1">Code Coverage</h2>
                   <p className="text-[13px] text-[#8B949E] leading-relaxed max-w-[650px] mb-6">
                      Manage how you track the code coverage of this repository.
                   </p>

                   <div className="bg-[#161B22] border border-[#30363D] rounded-md p-5 mb-6">
                      <h3 className="text-[14px] font-medium text-[#58a6ff] mb-2">How does it work?</h3>
                      <p className="text-[13px] text-[#8B949E] leading-relaxed max-w-[650px] mb-3">
                         Code Coverage is automatically enabled when we receive a coverage report for your repository. Send a coverage report to DeepSource directly using the CLI or integrate coverage reporting in your CI pipeline.
                      </p>
                      <a href="#" className="flex items-center gap-1.5 text-[13px] text-[#58a6ff] hover:underline font-medium">
                         Learn more
                         <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path fillRule="evenodd" d="M10.604 1h4.146a.25.25 0 01.25.25v4.146a.25.25 0 01-.427.177L13.03 4.03 9.28 7.78a.75.75 0 01-1.06-1.06l3.75-3.75-1.543-1.543A.25.25 0 0110.604 1zM3.75 2A1.75 1.75 0 002 3.75v8.5c0 .966.784 1.75 1.75 1.75h8.5A1.75 1.75 0 0014 12.25v-3.5a.75.75 0 00-1.5 0v3.5a.25.25 0 01-.25.25h-8.5a.25.25 0 01-.25-.25v-8.5a.25.25 0 01.25-.25h3.5a.75.75 0 000-1.5h-3.5z"></path></svg>
                      </a>
                   </div>

                   <div className="border border-[#30363D] rounded-md overflow-hidden bg-[#161B22] mb-8">
                      <div className="flex justify-between items-start p-5 border-b border-[#30363D]">
                         <div>
                            <h3 className="text-[14px] font-medium text-[#E6EDF3] mb-2">Code Coverage</h3>
                            <p className="text-[13px] text-[#8B949E] leading-relaxed max-w-[500px]">
                               When active, DeepSource will report code coverage issues and metrics.
                            </p>
                         </div>
                         <div className="flex items-center gap-1.5 px-3 py-1 bg-[#21262D] rounded-full border border-[#30363D] text-[10px] font-bold text-[#8B949E] tracking-wider uppercase">
                            <div className="w-1.5 h-1.5 rounded-full bg-[#8B949E]"></div>
                            REPORTING INACTIVE
                         </div>
                      </div>
                      <div className="px-5 py-3 hover:bg-[#21262D] cursor-pointer transition-colors flex items-center gap-2 group">
                         <svg className="w-3.5 h-3.5 text-[#8B949E] group-hover:text-[#E6EDF3] transition-colors" viewBox="0 0 16 16" fill="currentColor"><path fillRule="evenodd" d="M6.22 3.22a.75.75 0 011.06 0l4.25 4.25a.75.75 0 010 1.06l-4.25 4.25a.75.75 0 01-1.06-1.06L9.94 8 6.22 4.28a.75.75 0 010-1.06z"></path></svg>
                         <h3 className="text-[13px] font-medium text-[#E6EDF3]">How to send coverage reports to DeepSource?</h3>
                      </div>
                   </div>

                   <h3 className="text-[14px] font-semibold text-[#E6EDF3] mb-4">Preferences</h3>
                   
                   <div className="bg-[#161B22] border border-[#30363D] rounded-md p-5 flex justify-between items-start">
                      <div>
                         <h3 className="text-[14px] font-medium text-[#E6EDF3] mb-1">Enable report inference on the default branch</h3>
                         <p className="text-[13px] text-[#8B949E] leading-relaxed max-w-[500px]">
                            Ask DeepSource to re-use coverage reports from pull-requests after a merge. Turn this on if you don't run tests on your default branch commits.
                         </p>
                      </div>
                      <div className="pt-1">
                         <div className="w-9 h-5 bg-[#21262D] rounded-full relative cursor-pointer border border-[#30363D]">
                            <div className="absolute left-0.5 top-0.5 w-3.5 h-3.5 bg-[#8B949E] rounded-full transition-transform"></div>
                         </div>
                      </div>
                   </div>
                </div>
             </div>
          )}

          {activeTab === 'Quality gates' && (
             <div className="space-y-8">
                <div>
                   <h2 className="text-[16px] font-semibold text-[#E6EDF3] mb-1">Quality Gates</h2>
                   <p className="text-[13px] text-[#8B949E] leading-relaxed max-w-[650px] mb-6">
                      Configure quality gates for your repository.
                   </p>

                   <div className="bg-[#161B22] border border-[#30363D] rounded-md p-5 mb-8 flex flex-col gap-6">
                      <div className="flex justify-between items-start">
                         <div>
                            <h3 className="text-[14px] font-medium text-[#E6EDF3] mb-2">Pull Request Comments</h3>
                            <p className="text-[13px] text-[#8B949E] leading-relaxed max-w-[500px]">
                               DeepSource will comment on the pull request with a summary of the analysis.
                            </p>
                         </div>
                         <div className="pt-1">
                            <div className="w-9 h-5 bg-[#3fb950] rounded-full relative cursor-pointer border border-[#3fb950] transition-colors">
                               <div className="absolute right-0.5 top-0.5 w-3.5 h-3.5 bg-white rounded-full transition-transform"></div>
                            </div>
                         </div>
                      </div>
                      
                      <div className="h-px bg-[#30363D] w-full"></div>

                      <div className="flex justify-between items-start">
                         <div>
                            <h3 className="text-[14px] font-medium text-[#E6EDF3] mb-2">Post issues as inline PR comments</h3>
                            <p className="text-[13px] text-[#8B949E] leading-relaxed max-w-[500px]">
                               When enabled, DeepSource will post issues as inline comments on pull requests.
                            </p>
                         </div>
                         <div className="pt-1">
                            <div className="w-9 h-5 bg-[#3fb950] rounded-full relative cursor-pointer border border-[#3fb950] transition-colors">
                               <div className="absolute right-0.5 top-0.5 w-3.5 h-3.5 bg-white rounded-full transition-transform"></div>
                            </div>
                         </div>
                      </div>
                   </div>

                   <h3 className="text-[14px] font-semibold text-[#E6EDF3] mb-1">Issues</h3>
                   <p className="text-[13px] text-[#8B949E] leading-relaxed max-w-[650px] mb-6">
                      Configure the category and priority of issues that are reported and mark analysis runs as failed for blocking pull requests on GitHub.
                   </p>
                   
                   <div className="w-full">
                      <div className="grid grid-cols-3 mb-2 px-4 py-2">
                         <div className="text-[11px] font-semibold text-[#8B949E] tracking-wider uppercase">ISSUE CATEGORY</div>
                         <div className="text-[11px] font-semibold text-[#8B949E] tracking-wider uppercase text-center">REPORT ISSUE</div>
                         <div className="text-[11px] font-semibold text-[#8B949E] tracking-wider uppercase text-center">MARK RUN AS FAILED</div>
                      </div>
                      
                      <div className="border border-[#30363D] rounded-md divide-y divide-[#30363D] bg-[#161B22] overflow-hidden">
                         {['Bug risk', 'Anti-pattern', 'Performance', 'Security', 'Type check', 'Coverage', 'Secrets', 'Style'].map((category, idx) => (
                            <div key={idx} className="grid grid-cols-3 items-center px-4 py-3 hover:bg-[#21262D] transition-colors">
                               <div className="text-[13px] font-medium text-[#E6EDF3]">{category}</div>
                               <div className="flex justify-center flex-col items-center">
                                  {category === 'Style' ? (
                                      <div className="w-4 h-4 rounded-[3px] border border-[#8B949E] bg-[#0E1116] cursor-pointer hover:border-[#E6EDF3] transition-colors"></div>
                                  ) : (
                                      <div className="w-4 h-4 rounded-[3px] bg-[#3fb950] flex items-center justify-center cursor-pointer">
                                        <svg width="12" height="12" viewBox="0 0 16 16" fill="white"><path fillRule="evenodd" d="M13.78 4.22a.75.75 0 010 1.06l-7.25 7.25a.75.75 0 01-1.06 0L2.22 9.28a.75.75 0 011.06-1.06L6 10.94l6.72-6.72a.75.75 0 011.06 0z"></path></svg>
                                      </div>
                                  )}
                               </div>
                               <div className="flex justify-center flex-col items-center">
                                  {category === 'Style' ? (
                                      <div className="w-4 h-4 rounded-[3px] border border-[#8B949E] bg-[#0E1116] cursor-pointer hover:border-[#E6EDF3] transition-colors"></div>
                                  ) : (
                                      <div className="w-4 h-4 rounded-[3px] bg-[#3fb950] flex items-center justify-center cursor-pointer">
                                        <svg width="12" height="12" viewBox="0 0 16 16" fill="white"><path fillRule="evenodd" d="M13.78 4.22a.75.75 0 010 1.06l-7.25 7.25a.75.75 0 01-1.06 0L2.22 9.28a.75.75 0 011.06-1.06L6 10.94l6.72-6.72a.75.75 0 011.06 0z"></path></svg>
                                      </div>
                                  )}
                               </div>
                            </div>
                         ))}
                      </div>
                   </div>
                </div>
             </div>
          )}

          {activeTab === 'Badges' && (
             <div className="space-y-8">
                <div>
                   <h2 className="text-[16px] font-semibold text-[#E6EDF3] mb-1">Badges</h2>
                   <p className="text-[13px] text-[#8B949E] leading-relaxed max-w-[650px] mb-6">
                      Embeddable badges that can be used to link to the DeepSource dashboard for this project. Add these badges in the project's README, wiki or the website.
                   </p>

                   <div className="bg-[#161B22] border border-[#30363D] rounded-md p-6 max-w-[600px]">
                      
                      <div className="bg-[#0E1116] border border-[#30363D] rounded-md h-[120px] flex items-center justify-center mb-6">
                         <div className="flex items-center rounded overflow-hidden">
                             <div className="flex items-center gap-1.5 bg-[#444c56] px-2 py-1 text-[11px] font-bold text-white tracking-wider">
                                <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path fillRule="evenodd" d="M2.75 2.5a.25.25 0 00-.25.25v2.5a.75.75 0 01-1.5 0v-2.5A1.75 1.75 0 012.75 1h10.5c.966 0 1.75.784 1.75 1.75v10.5A1.75 1.75 0 0113.25 15H2.75A1.75 1.75 0 011 13.25v-2.5a.75.75 0 011.5 0v2.5c0 .138.112.25.25.25h10.5a.25.25 0 00.25-.25V2.75a.25.25 0 00-.25-.25H2.75zM8 4a1 1 0 100 2 1 1 0 000-2zM6.5 5a1.5 1.5 0 113 0 1.5 1.5 0 01-3 0zm-2 5.5a1 1 0 100 2 1 1 0 000-2zM3 10.5a1.5 1.5 0 113 0 1.5 1.5 0 01-3 0zm8.5-2.5a1 1 0 100 2 1 1 0 000-2zM10 9a1.5 1.5 0 113 0 1.5 1.5 0 01-3 0z"></path></svg>
                                code coverage
                             </div>
                             <div className="bg-[#21262D] px-2 py-1 text-[11px] font-bold text-[#E6EDF3] tracking-wider">
                                unreported
                             </div>
                         </div>
                      </div>

                      <div className="flex items-center gap-2 mb-8">
                         <input 
                            readOnly
                            type="text" 
                            defaultValue={`[![AgenticPR](https://img.shields.io/badge/AgenticPR-${repoName || 'repo'}-blue)]`} 
                            className="flex-1 bg-[#0E1116] border border-[#30363D] rounded-l-md rounded-r-none py-1.5 px-3 text-[13px] text-[#E6EDF3] focus:outline-none"
                         />
                         <button className="flex items-center gap-1.5 px-3 py-1.5 bg-[#21262D] hover:bg-[#30363D] border border-[#30363D] border-l-0 rounded-r-md rounded-l-none text-[13px] font-medium text-[#E6EDF3] transition-colors h-[34px] -ml-2 shrink-0 relative z-10">
                            <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path fillRule="evenodd" d="M0 6.75C0 5.784.784 5 1.75 5h1.5a.75.75 0 010 1.5h-1.5a.25.25 0 00-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 00.25-.25v-1.5a.75.75 0 011.5 0v1.5A1.75 1.75 0 019.25 16h-7.5A1.75 1.75 0 010 14.25v-7.5z"></path><path fillRule="evenodd" d="M5 1.75C5 .784 5.784 0 6.75 0h7.5C15.216 0 16 .784 16 1.75v7.5A1.75 1.75 0 0114.25 11h-7.5A1.75 1.75 0 015 9.25v-7.5zm1.75-.25a.25.25 0 00-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 00.25-.25v-7.5a.25.25 0 00-.25-.25h-7.5z"></path></svg>
                            Copy
                         </button>
                      </div>

                      <div className="space-y-6">
                         <div className="flex justify-between items-center">
                            <h3 className="text-[14px] font-medium text-[#E6EDF3]">Badge type</h3>
                            <select className="bg-[#21262D] border border-[#30363D] rounded-md py-1.5 px-3 text-[13px] text-[#E6EDF3] focus:outline-none w-[180px] cursor-pointer hover:bg-[#30363D] transition-colors appearance-none">
                               <option>Code coverage</option>
                               <option>Code Quality</option>
                            </select>
                         </div>

                         <div className="h-px bg-[#30363D] w-full"></div>

                         <div className="flex justify-between items-start">
                            <div>
                               <h3 className="text-[14px] font-medium text-[#E6EDF3] mb-1">Show trend</h3>
                               <p className="text-[13px] text-[#8B949E] leading-relaxed max-w-[400px]">
                                  Add a trendline showing how the value of this metric has varied in the last 6 months.
                               </p>
                            </div>
                            <div className="pt-1">
                               <div className="w-9 h-5 bg-[#3fb950] rounded-full relative cursor-pointer border border-[#3fb950] transition-colors">
                                  <div className="absolute right-0.5 top-0.5 w-3.5 h-3.5 bg-white rounded-full transition-transform"></div>
                               </div>
                            </div>
                         </div>
                         
                         <div className="h-px bg-[#30363D] w-full"></div>

                         <div className="flex justify-between items-center pb-2">
                            <h3 className="text-[14px] font-medium text-[#E6EDF3]">Format</h3>
                            <select className="bg-[#21262D] border border-[#30363D] rounded-md py-1.5 px-3 text-[13px] text-[#E6EDF3] focus:outline-none w-[180px] cursor-pointer hover:bg-[#30363D] transition-colors appearance-none">
                               <option>Markdown</option>
                               <option>HTML</option>
                            </select>
                         </div>
                      </div>

                   </div>
                </div>
             </div>
          )}
          
        </div>
      </div>
    </div>
  );
}
