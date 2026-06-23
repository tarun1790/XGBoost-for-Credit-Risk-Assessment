import React, { useState } from 'react';
import { Terminal, Shield, Play, Loader, AlertTriangle, CheckCircle } from 'lucide-react';
import { taskAPI } from '../services/api';

export default function LiveMonitor({ activeTask, currentStep, lastScreenshot, status, onSubmitTask }) {
  const [goal, setGoal] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!goal.trim()) return;
    setLoading(true);
    try {
      const task = await taskAPI.submit(goal);
      onSubmitTask(task);
      setGoal("");
    } catch (err) {
      console.error(err);
      alert("Failed to initiate agent goal run.");
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case "EXECUTING": return "text-white border-white";
      case "SUCCESS": return "text-neutral-400 border-neutral-600";
      case "FAILED": return "text-neutral-500 border-neutral-800";
      default: return "text-neutral-600 border-neutral-900";
    }
  };

  return (
    <div className="space-y-6">
      {/* Target Goal Input Console */}
      <div className="glass-panel p-6 relative overflow-hidden">
        {/* FUI Corner indicators */}
        <div className="absolute top-1.5 left-1.5 w-2 h-2 border-t border-l border-white" />
        <div className="absolute top-1.5 right-1.5 w-2 h-2 border-t border-r border-white" />
        <div className="absolute bottom-1.5 left-1.5 w-2 h-2 border-b border-l border-white" />
        <div className="absolute bottom-1.5 right-1.5 w-2 h-2 border-b border-r border-white" />

        <div className="flex items-center gap-2 mb-3 border-b border-neutral-900 pb-2">
          <Terminal className="w-4 h-4 text-white" />
          <h4 className="text-xs font-bold uppercase tracking-wider text-white">Agent Target Goal Console</h4>
        </div>

        <form onSubmit={handleSubmit} className="flex gap-4">
          <input
            type="text"
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            placeholder="Enter goal (e.g. 'Open dashboard, go to borrowers, extract table data...')"
            disabled={loading}
            className="flex-1 bg-black border border-neutral-800 hover:border-neutral-600 focus:border-white px-4 py-3 text-xs focus:outline-none transition-colors"
          />
          <button
            type="submit"
            disabled={loading || !goal.trim()}
            className="px-6 py-3 bg-white hover:bg-neutral-200 text-black text-xs font-black uppercase flex items-center gap-2 transition-colors disabled:opacity-50"
          >
            {loading ? (
              <Loader className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4 fill-current" />
            )}
            Deploy Agent
          </button>
        </form>
      </div>

      {/* Screen Frame Capture */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 columns: Screen frame */}
        <div className="lg:col-span-2 glass-panel p-6 relative flex flex-col justify-between min-h-[380px] overflow-hidden">
          <div className="absolute top-1.5 left-1.5 w-2 h-2 border-t border-l border-white" />
          <div className="absolute top-1.5 right-1.5 w-2 h-2 border-t border-r border-white" />
          <div className="absolute bottom-1.5 left-1.5 w-2 h-2 border-b border-l border-white" />
          <div className="absolute bottom-1.5 right-1.5 w-2 h-2 border-b border-r border-white" />

          <div className="flex items-center justify-between border-b border-neutral-900 pb-3 mb-4">
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-white animate-pulse" />
              <h4 className="text-xs font-bold uppercase tracking-wider text-white">Live Screen Frame Capture</h4>
            </div>
            {status === "EXECUTING" && (
              <span className="flex items-center gap-1.5 text-[10px] text-white border border-white px-2 py-0.5 animate-pulse uppercase font-bold">
                ● Live Scanners
              </span>
            )}
          </div>

          <div className="flex-1 border border-neutral-900 bg-neutral-950 flex items-center justify-center relative overflow-hidden min-h-[250px]">
            {lastScreenshot ? (
              <img
                src={`http://localhost:8000${lastScreenshot}`}
                alt="Agent Screen Audits"
                className="max-h-[320px] max-w-full object-contain"
                onError={(e) => {
                  e.target.style.display = 'none';
                }}
              />
            ) : (
              <div className="text-center p-6">
                <Loader className={`w-8 h-8 mx-auto mb-2 text-neutral-700 ${status === "EXECUTING" ? "animate-spin text-white" : ""}`} />
                <span className="text-[10px] text-neutral-600 uppercase tracking-widest font-mono font-bold">
                  {status === "EXECUTING" ? "Acquiring telemetry capture..." : "No active screenshot capture feed"}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Right column: Action telemetry metrics */}
        <div className="glass-panel p-6 relative flex flex-col justify-between overflow-hidden">
          <div className="absolute top-1.5 left-1.5 w-2 h-2 border-t border-l border-white" />
          <div className="absolute top-1.5 right-1.5 w-2 h-2 border-t border-r border-white" />
          <div className="absolute bottom-1.5 left-1.5 w-2 h-2 border-b border-l border-white" />
          <div className="absolute bottom-1.5 right-1.5 w-2 h-2 border-b border-r border-white" />

          <div>
            <div className="border-b border-neutral-900 pb-3 mb-4">
              <h4 className="text-xs font-bold uppercase tracking-wider text-white">Execution Logs Telemetry</h4>
            </div>

            <div className="space-y-4">
              <div className="bg-black border border-neutral-900 p-4">
                <span className="text-neutral-500 text-[9px] font-bold uppercase tracking-wider block">Agent Deployment Status</span>
                <span className="text-xs text-neutral-300 font-bold uppercase block mt-1">
                  {status || "STANDBY"}
                </span>
              </div>

              {activeTask && (
                <div className="bg-black border border-neutral-900 p-4 space-y-1">
                  <span className="text-neutral-500 text-[9px] font-bold uppercase tracking-wider block">Active Goal ID</span>
                  <span className="text-[10px] text-white font-mono break-all block">{activeTask.id}</span>
                  <span className="text-[10px] text-neutral-400 block truncate mt-1">Goal: "{activeTask.goal}"</span>
                </div>
              )}

              {currentStep && (
                <div className="bg-black border border-neutral-900 p-4 space-y-1">
                  <span className="text-neutral-500 text-[9px] font-bold uppercase tracking-wider block">Active Step Operation</span>
                  <span className="text-xs text-white font-bold uppercase block">
                    [{currentStep.agent}] {currentStep.action}
                  </span>
                  <p className="text-[10px] text-neutral-400 leading-normal block mt-1">
                    Description: {currentStep.description}
                  </p>
                </div>
              )}
            </div>
          </div>

          <div className="pt-4 border-t border-neutral-900 mt-4 text-[9px] text-neutral-600 font-bold uppercase">
            <span>Platform scale: Windows 11 x64</span>
          </div>
        </div>
      </div>
    </div>
  );
}
