import React from 'react';
import { User, Mail, Shield, Trash2, Edit2 } from 'lucide-react';

const MemberRow = ({ name, email, role, avatar }) => (
    <div className="flex items-center justify-between p-4 bg-[#161b22] border border-[#30363d] rounded-lg mb-2 hover:border-gray-500 transition-colors">
        <div className="flex items-center gap-4">
            <div className={`w-10 h-10 rounded-full bg-gradient-to-br ${avatar} flex items-center justify-center text-white text-lg font-bold`}>
                {name.charAt(0)}
            </div>
            <div>
                <h3 className="text-sm font-semibold text-white">{name}</h3>
                <div className="flex items-center gap-2 text-xs text-gray-400">
                    <Mail size={12} />
                    {email}
                </div>
            </div>
        </div>
        <div className="flex items-center gap-4">
            <span className={`px-2 py-1 rounded-full text-xs font-medium border ${role === 'Admin' ? 'bg-purple-900/20 text-purple-400 border-purple-900/50' : 'bg-green-900/20 text-green-400 border-green-900/50'}`}>
                {role}
            </span>
            <div className="flex items-center gap-2">
                <button className="p-1.5 text-gray-400 hover:text-white hover:bg-[#1f2937] rounded-md transition-colors">
                    <Edit2 size={16} />
                </button>
                <button className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-[#1f2937] rounded-md transition-colors">
                    <Trash2 size={16} />
                </button>
            </div>
        </div>
    </div>
);

export default function Members() {
  return (
    <div className="flex-1 bg-[#0d1117] p-8 overflow-y-auto">
        <div className="max-w-4xl mx-auto">
            <div className="flex items-center justify-between mb-8">
                <h1 className="text-2xl font-semibold text-white">Team Members</h1>
                <button className="bg-[#1f6feb] hover:bg-[#1f6feb]/90 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors">
                    Invite Member
                </button>
            </div>
            
            <div className="space-y-4">
                <MemberRow name="Admin User" email="admin@agenticpr.com" role="Admin" avatar="from-blue-500 to-indigo-600" />
                <MemberRow name="Sarah Engineer" email="sarah@corp.com" role="Developer" avatar="from-pink-500 to-rose-600" />
                <MemberRow name="Mike Reviewer" email="mike@corp.com" role="Maintainer" avatar="from-emerald-500 to-teal-600" />
            </div>
        </div>
    </div>
  );
}
