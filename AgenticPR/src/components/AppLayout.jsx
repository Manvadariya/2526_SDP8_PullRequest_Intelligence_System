import React from 'react';
import Sidebar from '../components/Sidebar';
import { Outlet } from 'react-router-dom';

export default function AppLayout() {
  return (
    <div className="flex h-screen bg-[#0d1117] text-[#c9d1d9] font-sans antialiased overflow-hidden">
      <Sidebar />
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
          <Outlet />
      </div>
    </div>
  );
}
