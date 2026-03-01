import React from 'react';
import { 
  Home, 
  Layers, 
  FileText, 
  Users, 
  Settings, 
  Globe, 
  Lock, 
  ChevronRight,
  Search,
  CheckCircle2, 
  XCircle, 
  GitPullRequest
} from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';

const SidebarItem = ({ icon: Icon, label, path, badge }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const isActive = location.pathname === path;

  return (
    <div 
      onClick={() => navigate(path)}
      className={`flex items-center justify-between px-3 py-2 rounded-md mb-1 cursor-pointer transition-colors ${isActive ? 'bg-[#1f2937] text-white' : 'text-gray-400 hover:bg-[#1f2937] hover:text-white'}`}
    >
      <div className="flex items-center gap-3">
        <Icon size={18} />
        <span className="text-sm font-medium">{label}</span>
      </div>
      {badge && <span className="bg-[#238636] text-white text-xs px-1.5 rounded-full">{badge}</span>}
    </div>
  );
};

const FavoriteItem = ({ label, icon: Icon = Lock, status, onClick }) => {
    return (
      <div onClick={onClick} className={`flex items-center gap-3 px-3 py-2 rounded-md mb-1 cursor-pointer transition-colors text-gray-400 hover:bg-[#1f2937] hover:text-white`}>
        {status === 'success' ? <CheckCircle2 size={16} className="text-[#238636]" /> : 
         status === 'failure' ? <XCircle size={16} className="text-[#da3633]" /> :
         <Icon size={16} className="shrink-0" />}
        <span className="text-sm truncate">{label}</span>
      </div>
    );
};

export default function Sidebar() {
  const navigate = useNavigate();
  
  return (
      <div className="w-64 border-r border-[#30363d] flex flex-col bg-[#0d1117] h-screen shrink-0 sticky top-0">
        {/* Org Selector */}
        <div className="p-4 flex items-center justify-between hover:bg-[#161b22] cursor-pointer transition-colors border-b border-[#30363d] shrink-0">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-blue-500 flex items-center justify-center text-white text-xs font-bold">A</div>
            <span className="font-semibold text-sm">Dashboard</span>
            <ChevronRight size={14} className="rotate-90 text-gray-500" />
          </div>
        </div>

        {/* Main Nav */}
        <div className="flex-1 overflow-y-auto p-3 custom-scrollbar">
          <button className="w-full flex items-center gap-2 border border-[#30363d] rounded-md px-3 py-1.5 text-sm text-gray-300 hover:bg-[#1f2937] hover:border-gray-500 transition-all mb-6">
            <Layers size={16} />
            <span>New Scan</span>
          </button>

          <div className="mb-6">
            <SidebarItem icon={Home} label="Home" path="/" />
            <SidebarItem icon={Layers} label="Repositories" path="/repositories" />
            <SidebarItem icon={FileText} label="Reports" path="/reports" />
            <SidebarItem icon={Users} label="Members" path="/members" />
            <SidebarItem icon={Settings} label="Settings" path="/settings" />
          </div>

          <div className="mb-2 px-3 flex items-center justify-between text-xs font-semibold text-gray-500 uppercase tracking-wider">
            <span>Recent Scans</span>
            <div className="h-[1px] bg-[#30363d] flex-1 ml-3"></div>
          </div>

          <div className="space-y-1">
             {/* Use navigate to /scan which defaults to latest scan. */}
            <FavoriteItem label="Latest Job" onClick={() => navigate('/scan')} status="success" />
          </div>
        </div>
      </div>
  );
}
