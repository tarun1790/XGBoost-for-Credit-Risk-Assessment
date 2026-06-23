import React, { useState, useEffect } from 'react';
import { Shield, ListRestart, HelpCircle, FileText, CheckCircle, AlertOctagon, Maximize2, X } from 'lucide-react';
import { taskAPI } from './services/api';
import LiveMonitor from './components/LiveMonitor';
import PlanVisualizer from './components/PlanVisualizer';
import LogExplorer from './components/LogExplorer';

export default function App() {
  const [tasks, setTasks] = useState([]);
  const [activeTask, setActiveTask] = useState(null);
  const [plan, setPlan] = useState([]);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [lastScreenshot, setLastScreenshot] = useState(null);
  const [status, setStatus] = useState("STANDBY");
  const [logs, setLogs] = useState([]);
  
  // Audits and logs
  const [audits, setAudits] = useState([]);
  const [selectedScreenshot, setSelectedScreenshot] = useState(null);

  // Load task list on bootup
  const loadTasks = async () => {
    try {
      const data = await taskAPI.list();
      setTasks(data);
      if (data.length > 0 && !activeTask) {
        // Select latest task as active by default
        await selectTask(data[0].id);
      }
    } catch (err) {
      console.error("Error loading tasks:", err);
    }
  };

  const selectTask = async (taskId) => {
    try {
      const task = await taskAPI.getDetails(taskId);
      setActiveTask(task);
      setPlan(task.plan?.step_tree || []);
      setCurrentStepIndex(task.plan?.current_step || 0);
      setStatus(task.status);
      setLogs(task.action_logs || []);
      
      // Determine last screenshot from logs
      if (task.action_logs && task.action_logs.length > 0) {
        const lastWithImg = [...task.action_logs].reverse().find(l => l.screenshot_path);
        setLastScreenshot(lastWithImg ? lastWithImg.screenshot_path : null);
      } else {
        setLastScreenshot(null);
      }
    } catch (err) {
      console.error("Error loading task details:", err);
    }
  };

  // Sync audit trail logs
  const loadAudits = async () => {
    try {
      const data = await taskAPI.getAudits();
      setAudits(data);
    } catch (err) {
      console.log(err);
    }
  };

  // Connect to live WebSocket telemetry stream
  useEffect(() => {
    loadTasks();
    loadAudits();
    
    let ws = null;
    let reconnectTimeout = null;

    const connectWebSocket = () => {
      ws = taskAPI.getWebSocketStream();
      
      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        console.log("Telemetry Frame received:", msg);
        
        // Update states based on event context
        if (msg.plan) setPlan(msg.plan);
        if (msg.current_step !== undefined) setCurrentStepIndex(msg.current_step);
        if (msg.screenshot) setLastScreenshot(msg.screenshot);
        
        if (msg.event === "PLAN_GENERATED") {
          setStatus("EXECUTING");
        } else if (msg.event === "EXECUTING_STEP") {
          setStatus("EXECUTING");
        } else if (msg.event === "STEP_COMPLETED") {
          // Refresh logs immediately
          if (activeTask && msg.task_id === activeTask.id) {
            selectTask(activeTask.id);
          }
        } else if (msg.event === "TASK_FINISHED") {
          setStatus(msg.status);
          loadTasks();
          loadAudits();
        } else if (msg.event === "HEALING_RECOVERY") {
          // Log alert event in audits
          loadAudits();
        }
      };

      ws.onclose = () => {
        console.log("WebSocket disconnected. Retrying in 3s...");
        reconnectTimeout = setTimeout(connectWebSocket, 3000);
      };
      
      ws.onerror = (err) => {
        console.error("WebSocket error:", err);
        ws.close();
      };
    };

    connectWebSocket();

    return () => {
      if (ws) ws.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
    };
  }, [activeTask?.id]);

  const handleNewTask = (task) => {
    loadTasks();
    selectTask(task.id);
  };

  return (
    <div className="flex h-screen bg-black overflow-hidden font-mono text-neutral-300">
      
      {/* Sidebar Task List */}
      <aside className="w-80 bg-black border-r border-neutral-900 flex flex-col shrink-0">
        <div className="p-6 border-b border-neutral-900 flex items-center gap-3">
          <div className="p-1.5 border border-white text-white shrink-0">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <h1 className="font-extrabold text-white text-sm tracking-wider uppercase leading-none">Autonomous Agent</h1>
            <span className="text-[9px] text-neutral-500 font-bold uppercase tracking-widest mt-1 block">Computer Use HUD</span>
          </div>
        </div>

        {/* Scrollable list */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2.5 terminal-scroll">
          <span className="text-[9px] text-neutral-500 font-bold uppercase tracking-wider block px-2 mb-1">
            Submitted Goal Runs ({tasks.length})
          </span>
          {tasks.map((task) => {
            const isActive = activeTask?.id === task.id;
            return (
              <button
                key={task.id}
                onClick={() => selectTask(task.id)}
                className={`w-full text-left p-3.5 border transition-all duration-150 rounded-none ${
                  isActive
                    ? "bg-neutral-950 border-white text-white"
                    : "bg-black border-neutral-900 text-neutral-400 hover:text-white hover:border-neutral-700"
                }`}
              >
                <span className="text-[8px] font-mono text-neutral-500 block truncate">{task.id}</span>
                <span className="text-xs font-bold block truncate mt-0.5">"{task.goal}"</span>
                <div className="flex items-center gap-2 mt-2">
                  <span className={`text-[8px] font-bold border px-1.5 py-0.5 uppercase tracking-wider ${
                    task.status === "SUCCESS"
                      ? "border-neutral-800 text-neutral-500"
                      : task.status === "FAILED"
                      ? "border-neutral-800 text-neutral-600"
                      : "border-neutral-800 text-white animate-pulse"
                  }`}>
                    {task.status}
                  </span>
                  <span className="text-[8px] text-neutral-600">
                    {new Date(task.created_at).toLocaleTimeString()}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      </aside>

      {/* Main Panel Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Upper Header */}
        <header className="bg-black border-b border-neutral-900 px-6 py-4 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">
              Control Dashboard Console
            </h2>
            <span className="h-1.5 w-1.5 rounded-full bg-white animate-ping" />
          </div>
          <div className="flex items-center gap-4 text-[10px]">
            <span className="text-neutral-500 uppercase font-bold tracking-wider">
              Status: <span className="text-white">{status}</span>
            </span>
          </div>
        </header>

        {/* Scrollable Container */}
        <main className="flex-1 overflow-y-auto p-6 space-y-6 bg-black terminal-scroll">
          <LiveMonitor
            activeTask={activeTask}
            currentStep={plan[currentStepIndex]}
            lastScreenshot={lastScreenshot}
            status={status}
            onSubmitTask={handleNewTask}
          />
          
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <LogExplorer logs={logs} onSelectScreenshot={setSelectedScreenshot} />
            </div>
            <div>
              <PlanVisualizer plan={plan} currentStepIndex={currentStepIndex} status={status} />
            </div>
          </div>
        </main>
      </div>

      {/* Image Modal Preview Overlay */}
      {selectedScreenshot && (
        <div className="fixed inset-0 bg-black/90 backdrop-blur-md flex items-center justify-center p-4 z-50 animate-fadeIn">
          <div className="glass-panel p-6 relative max-w-4xl w-full flex flex-col">
            <div className="absolute top-1.5 left-1.5 w-2 h-2 border-t border-l border-white" />
            <div className="absolute top-1.5 right-1.5 w-2 h-2 border-t border-r border-white" />
            <div className="absolute bottom-1.5 left-1.5 w-2 h-2 border-b border-l border-white" />
            <div className="absolute bottom-1.5 right-1.5 w-2 h-2 border-b border-r border-white" />

            <div className="flex items-center justify-between border-b border-neutral-900 pb-3 mb-4">
              <span className="text-xs font-bold uppercase tracking-wider text-white">Evidence Screenshot Capture</span>
              <button
                onClick={() => setSelectedScreenshot(null)}
                className="text-neutral-500 hover:text-white p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="flex-1 overflow-hidden flex items-center justify-center border border-neutral-900 bg-neutral-950 p-2 min-h-[300px]">
              <img
                src={`http://localhost:8000${selectedScreenshot}`}
                alt="Audit Evidence Full"
                className="max-h-[70vh] object-contain"
              />
            </div>

            <div className="mt-4 pt-3 border-t border-neutral-900 text-[10px] text-neutral-500 flex justify-between font-mono">
              <span>Path: {selectedScreenshot}</span>
              <span className="text-white">Evidence Validated</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
