import React from 'react';
import { Layers, GitPullRequest, Activity } from 'lucide-react';

const StatCard = ({ title, value, icon: Icon, color }) => (
    <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
            <div className={`p-2 rounded-lg ${color}`}>
                <Icon size={24} className="text-white" />
            </div>
            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Last 30 Days</span>
        </div>
        <div className="text-3xl font-bold text-white mb-1">{value}</div>
        <div className="text-sm text-gray-400">{title}</div>
    </div>
);

export default function Home() {
  return (
    <div className="flex-1 bg-[#0d1117] p-8 overflow-y-auto">
        <div className="max-w-7xl mx-auto">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-2xl font-semibold text-white mb-2">Welcome back, Admin</h1>
                    <p className="text-gray-400">Here's what's happening with your projects today.</p>
                </div>
                <button className="bg-[#238636] hover:bg-[#2ea043] text-white px-4 py-2 rounded-md text-sm font-medium transition-colors">
                    + New Project
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <StatCard title="Active Repositories" value="12" icon={Layers} color="bg-blue-600/20" />
                <StatCard title="Pull Requests scanned" value="348" icon={GitPullRequest} color="bg-purple-600/20" />
                <StatCard title="Issues Detected" value="42" icon={Activity} color="bg-red-600/20" />
            </div>

            <div className="bg-[#161b22] border border-[#30363d] rounded-lg overflow-hidden">
                <div className="px-6 py-4 border-b border-[#30363d]">
                    <h2 className="text-lg font-semibold text-white">Recent Activity</h2>
                </div>
                <div className="divide-y divide-[#30363d]">
                    {[1, 2, 3, 4, 5].map((i) => (
                        <div key={i} className="px-6 py-4 flex items-center justify-between hover:bg-[#1f2937] transition-colors cursor-pointer">
                            <div className="flex items-center gap-4">
                                <div className="w-8 h-8 rounded-full bg-[#1f6feb]/20 flex items-center justify-center text-[#58a6ff]">
                                    <GitPullRequest size={16} />
                                </div>
                                <div>
                                    <h3 className="text-sm font-medium text-white">Project AgenticPR updated</h3>
                                    <p className="text-xs text-gray-400">Scan completed with 2 new issues found</p>
                                </div>
                            </div>
                            <span className="text-xs text-gray-500">2h ago</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    </div>
  );
}
