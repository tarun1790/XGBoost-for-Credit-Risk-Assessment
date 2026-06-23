import React from 'react';
import { Layers, CheckCircle2, Circle, PlayCircle, ShieldAlert } from 'lucide-react';

export default function PlanVisualizer({ plan = [], currentStepIndex = 0, status }) {
  return (
    <div className="glass-panel p-6 relative overflow-hidden h-full">
      {/* Corner indicators */}
      <div className="absolute top-1.5 left-1.5 w-2 h-2 border-t border-l border-white" />
      <div className="absolute top-1.5 right-1.5 w-2 h-2 border-t border-r border-white" />
      <div className="absolute bottom-1.5 left-1.5 w-2 h-2 border-b border-l border-white" />
      <div className="absolute bottom-1.5 right-1.5 w-2 h-2 border-b border-r border-white" />

      <div className="flex items-center gap-2 mb-4 border-b border-neutral-900 pb-3">
        <Layers className="w-4 h-4 text-white" />
        <h4 className="text-xs font-bold uppercase tracking-wider text-white">Hierarchical Subgoal Plan Tree</h4>
      </div>

      <div className="space-y-3.5 max-h-[350px] overflow-y-auto pr-1 terminal-scroll">
        {plan.length > 0 ? (
          plan.map((step, idx) => {
            const isCompleted = idx < currentStepIndex;
            const isCurrent = idx === currentStepIndex && status === "EXECUTING";
            const isFailed = idx === currentStepIndex && status === "FAILED";
            const isPending = idx > currentStepIndex || (idx === currentStepIndex && status === "PENDING");

            return (
              <div
                key={step.step}
                className={`p-3.5 border transition-all duration-200 ${
                  isCurrent
                    ? "bg-neutral-950 border-white text-white shadow-[0_0_15px_rgba(255,255,255,0.03)]"
                    : isCompleted
                    ? "bg-black border-neutral-900 text-neutral-500"
                    : isFailed
                    ? "bg-black border-neutral-800 text-neutral-600"
                    : "bg-black border-neutral-900 text-neutral-400"
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5 shrink-0">
                      {isCompleted && <CheckCircle2 className="w-4 h-4 text-neutral-500" />}
                      {isCurrent && <PlayCircle className="w-4 h-4 text-white animate-pulse" />}
                      {isFailed && <ShieldAlert className="w-4 h-4 text-neutral-500" />}
                      {isPending && <Circle className="w-4 h-4 text-neutral-800" />}
                    </div>

                    <div className="space-y-0.5">
                      <span className="text-[9px] font-bold uppercase tracking-wider block">
                        Step {step.step} — {step.agent}
                      </span>
                      <span className="text-xs font-bold block">{step.description}</span>
                      {step.details && Object.keys(step.details).length > 0 && (
                        <span className="text-[9px] font-mono text-neutral-500 block truncate max-w-[280px]">
                          Params: {JSON.stringify(step.details)}
                        </span>
                      )}
                    </div>
                  </div>

                  <span className={`text-[8px] font-bold border px-1.5 py-0.5 uppercase tracking-wider ${
                    isCurrent ? "border-white text-white" : "border-neutral-900 text-neutral-600"
                  }`}>
                    {step.action}
                  </span>
                </div>
              </div>
            );
          })
        ) : (
          <div className="text-center py-12 border border-dashed border-neutral-900">
            <span className="text-[10px] text-neutral-600 uppercase tracking-widest font-mono font-bold block">
              Waiting for agent goal submission...
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
