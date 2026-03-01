import React from 'react';
import { FileText, Download } from 'lucide-react';

const ReportCard = ({ title, date, status }) => (
    <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-6 mb-4 cursor-pointer hover:border-gray-500 transition-colors">
        <div className="flex items-center justify-between mb-4">
            <div className={`p-2 rounded-lg bg-green-900/20 text-green-500`}>
                <FileText size={24} />
            </div>
            <span className={`px-2 py-1 rounded text-xs font-bold ${status === 'Ready' ? 'bg-green-900/50 text-green-500' : 'bg-yellow-900/50 text-yellow-500'}`}>
                {status}
            </span>
        </div>
        <h3 className="text-lg font-semibold text-white mb-1">{title}</h3>
        <p className="text-sm text-gray-400 mb-4">Generated on {date}</p>
        <button className="flex items-center gap-2 text-sm text-[#58a6ff] hover:underline">
            <Download size={14} />
            Download PDF
        </button>
    </div>
);

export default function Reports() {
  return (
    <div className="flex-1 bg-[#0d1117] p-8 overflow-y-auto">
        <div className="max-w-7xl mx-auto">
            <h1 className="text-2xl font-semibold text-white mb-6">Reports</h1>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <ReportCard title="Weekly Security Summary" date="Feb 25, 2026" status="Ready" />
                <ReportCard title="Code Quality Analysis" date="Feb 24, 2026" status="Ready" />
                <ReportCard title="Monthly Compliance Report" date="Feb 01, 2026" status="Archived" />
            </div>
        </div>
    </div>
  );
}
