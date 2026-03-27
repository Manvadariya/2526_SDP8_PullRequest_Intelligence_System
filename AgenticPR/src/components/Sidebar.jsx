import React, { useState } from 'react';
import { NavLink, Link } from 'react-router-dom';
import { Home, FolderOpen, FileText, BookOpen, HelpCircle, ChevronRight, LogOut, Plus } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import ActivateRepoModal from './ActivateRepoModal';

export default function Sidebar() {
  const { user, logout } = useAuth();
  const [showActivateModal, setShowActivateModal] = useState(false);

  // Use profile data if auth works, otherwise fallback
  const username = user?.username || "Manvadariya";
  const avatarUrl = user?.avatar_url || "https://github.com/Manvadariya.png";
  const displayName = user?.name || "Man Vadariya";

  const mainNav = [
    { name: 'Home', icon: Home, path: '/home' },
    // { name: 'Repositories', icon: FolderOpen, path: '/repositories' },
  ];

  return (
    <div className="w-[260px] h-screen bg-[#0E1116] border-r border-[#30363D] flex flex-col shrink-0">

      <div className="pt-4 pb-2 px-3">
        {/* User Dropdown trigger */}
        <a href={`https://github.com/${username}`} target="_blank" rel="noopener noreferrer" className="w-full flex items-center justify-between p-2 rounded-md hover:bg-[#161B22] transition-colors group mb-3 cursor-pointer">
          <div className="flex items-center gap-2 overflow-hidden">
            <img
              src={avatarUrl}
              alt={username}
              className="w-6 h-6 rounded-md object-cover"
            />
            <span className="text-[#E6EDF3] text-[14px] font-medium truncate">{username}</span>
          </div>
          <ChevronRight size={14} className="text-[#8B949E] group-hover:text-[#E6EDF3] transition-colors" />
        </a>

        {/* Action Button */}
        <button
          onClick={() => setShowActivateModal(true)}
          className="w-full flex items-center gap-2 p-2 rounded-md text-[#8B949E] hover:text-[#E6EDF3] hover:bg-[#161B22] transition-colors mb-2"
        >
          <Plus size={16} />
          <span className="text-[13px] font-medium">Activate new repository</span>
        </button>
      </div>

      <ActivateRepoModal
        isOpen={showActivateModal}
        onClose={() => setShowActivateModal(false)}
      />

      {/* Main Navigation */}
      <nav className="flex-1 px-3 py-2 space-y-0.5 mt-2">
        {mainNav.map((item) => (
          <NavLink
            key={item.name}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-md text-[13px] font-medium transition-colors ${isActive
                ? 'bg-[#161B22] text-[#E6EDF3]'
                : 'text-[#8B949E] hover:bg-[#161B22] hover:text-[#E6EDF3]'
              }`
            }
          >
            <item.icon size={16} />
            {item.name}
          </NavLink>
        ))}
      </nav>

      {/* Footer Navigation */}
      <div className="px-3 py-4 border-t border-[#30363D]">
        {/* <nav className="space-y-0.5 mb-4">
          <a href="#" className="flex items-center gap-3 px-3 py-2 rounded-md text-[13px] text-[#8B949E] hover:bg-[#161B22] hover:text-[#E6EDF3] transition-colors">
            <BookOpen size={16} />
            Read documentation
          </a>
          <a href="#" className="flex items-center gap-3 px-3 py-2 rounded-md text-[13px] text-[#8B949E] hover:bg-[#161B22] hover:text-[#E6EDF3] transition-colors">
            <HelpCircle size={16} />
            Contact support
          </a>
        </nav> */}

        {/* User Profile Mini Footer */}
        <div className="flex items-center justify-between px-3 mt-4">
          <a href={`https://github.com/${username}`} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 overflow-hidden hover:opacity-80 transition-opacity">
            <img
              src={avatarUrl}
              alt={username}
              className="w-5 h-5 rounded-full object-cover"
            />
            <span className="text-[#8B949E] text-[13px] truncate">{displayName}</span>
          </a>

          <button
            onClick={logout}
            className="text-[#8B949E] hover:text-[#f85149] transition-colors p-1 flex-shrink-0"
            title="Log out"
          >
            <LogOut size={14} />
          </button>
        </div>

        <div className="px-3 mt-6 text-[11px] text-[#8B949E]">
          © 2026 AgenticPR
        </div>
      </div>
    </div>
  );
}
