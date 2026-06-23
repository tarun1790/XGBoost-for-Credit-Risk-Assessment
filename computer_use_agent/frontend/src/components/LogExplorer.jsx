import React from 'react';
import { Terminal, ExternalLink, ShieldCheck, ShieldAlert } from 'lucide-react';

export default function LogExplorer({ logs = [], onSelectScreenshot }) {
  return (
    <div className="glass-panel p-6 relative overflow-hidden">
      {/* Corner indicators */}
      <div className="absolute top-1.5 left-1.5 w-2 h-2 border-t border-l border-white" />
      <div className="absolute top-1.5 right-1.5 w-2 h-2 border-t border-r border-white" />
      <div className="absolute bottom-1.5 left-1.5 w-2 h-2 border-b border-l border-white" />
      <div className="absolute bottom-1.5 right-1.5 w-2 h-2 border-b border-r border-white" />

      <div className="flex items-center gap-2 mb-4 border-b border-neutral-900 pb-3">
        <Terminal className="w-4 h-4 text-white" />
        <h4 className="text-xs font-bold uppercase tracking-wider text-white">Action Execution Logs & Audit Trail</h4>
      </div>

      <div className="overflow-x-auto">
        {logs.length > 0 ? (
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-neutral-950 text-neutral-500 font-semibold border-b border-neutral-900 uppercase tracking-wider text-[9px]">
                <th className="px-4 py-3">Agent</th>
                <th className="px-4 py-3">Action</th>
                <th className="px-4 py-3">Description</th>
                <th className="px-4 py-3">Audit Details</th>
                <th className="px-4 py-3">Evidence Capture</th>
                <th className="px-4 py-3 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-900">
              {logs.map((log, index) => (
                <tr key={log.id || index} className="hover:bg-neutral-950 transition-colors">
                  <td className="px-4 py-3 font-bold text-white uppercase text-[10px]">
                    {log.agent_type}
                  </td>
                  <td className="px-4 py-3 text-neutral-300 uppercase text-[10px]">
                    {log.action_type}
                  </td>
                  <td className="px-4 py-3 text-neutral-300 font-bold max-w-[200px] truncate">
                    {log.step_name}
                  </td>
                  <td className="px-4 py-3 text-neutral-450 font-mono text-[9px] max-w-[240px] truncate">
                    {log.action_details ? JSON.stringify(log.action_details) : "—"}
                  </td>
                  <td className="px-4 py-3">
                    {log.screenshot_path ? (
                      <button
                        onClick={() => onSelectScreenshot(log.screenshot_path)}
                        className="text-white hover:underline flex items-center gap-1 text-[10px] font-bold uppercase"
                      >
                        Screenshot <ExternalLink className="w-3 h-3" />
                      </button>
                    ) : (
                      <span className="text-neutral-700">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 border text-[9px] font-bold uppercase ${
                      log.is_success
                        ? "border-neutral-800 text-neutral-400"
                        : "border-neutral-800 text-neutral-500"
                    }`}>
                      {log.is_success ? (
                        <>
                          <ShieldCheck className="w-3 h-3 text-neutral-500" /> Success
                        </>
                      ) : (
                        <>
                          <ShieldAlert className="w-3 h-3 text-neutral-600" /> Failure
                        </>
                      )}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="text-center py-12 border border-dashed border-neutral-900">
            <span className="text-[10px] text-neutral-600 uppercase tracking-widest font-mono font-bold">
              No actions executed in this session yet.
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
