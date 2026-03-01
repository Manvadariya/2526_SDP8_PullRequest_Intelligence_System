import React from 'react';
import { Settings as SettingsIcon, Shield, Bell, Key } from 'lucide-react';

const SettingSection = ({ title, icon: Icon, children }) => (
    <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-6 mb-8">
        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-[#30363d]">
            <div className="p-2 bg-[#1f2937] rounded-md">
                <Icon size={20} className="text-gray-400" />
            </div>
            <h2 className="text-lg font-semibold text-white">{title}</h2>
        </div>
        {children}
    </div>
);

const Toggle = ({ label, description, defaultChecked }) => (
    <div className="flex items-center justify-between py-4">
        <div>
            <div className="text-sm font-medium text-white">{label}</div>
            <div className="text-xs text-gray-500">{description}</div>
        </div>
        <input type="checkbox" defaultChecked={defaultChecked} className="w-10 h-5 bg-[#30363d] rounded-full appearance-none cursor-pointer checked:bg-[#238636] transition-colors relative after:content-[''] after:absolute after:top-1 after:left-1 after:w-3 after:h-3 after:bg-white after:rounded-full after:transition-transform checked:after:translate-x-5" />
    </div>
);

export default function Settings() {
  return (
    <div className="flex-1 bg-[#0d1117] p-8 overflow-y-auto">
        <div className="max-w-3xl mx-auto">
            <h1 className="text-2xl font-semibold text-white mb-8">Settings</h1>
            
            <SettingSection title="General" icon={SettingsIcon}>
                <div className="space-y-4">
                    <div className="flex flex-col gap-2">
                        <label className="text-sm font-medium text-gray-300">Project Name</label>
                        <input type="text" defaultValue="AgenticPR" className="bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-2 text-white focus:border-[#1f6feb] outline-none transition-colors" />
                    </div>
                     <div className="flex flex-col gap-2">
                        <label className="text-sm font-medium text-gray-300">Repository URL</label>
                        <input type="text" defaultValue="https://github.com/agentic/pr-system" disabled className="bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-2 text-gray-500 cursor-not-allowed" />
                    </div>
                </div>
            </SettingSection>

            <SettingSection title="Notifications" icon={Bell}>
                <div className="divide-y divide-[#30363d]">
                    <Toggle label="Email Notifications" description="Receive emails about scan results" defaultChecked />
                    <Toggle label="Slack Integration" description="Post alerts to #dev-ops channel" />
                    <Toggle label="Browser Push" description="Get notified when a scan completes" defaultChecked />
                </div>
            </SettingSection>

            <div className="flex justify-end gap-4 mt-8">
                <button className="px-4 py-2 rounded-md text-sm font-medium text-gray-400 hover:text-white hover:bg-[#1f2937] transition-colors">Cancel</button>
                <button className="bg-[#238636] hover:bg-[#2ea043] text-white px-6 py-2 rounded-md text-sm font-medium transition-colors">Save Changes</button>
            </div>
        </div>
    </div>
  );
}
