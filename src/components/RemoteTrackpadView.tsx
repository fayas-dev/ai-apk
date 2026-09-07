import React, { useState, useRef, useEffect } from 'react';
import {
  Laptop,
  Power,
  RotateCcw,
  Lock,
  Globe,
  Youtube,
  MessageSquare,
  Folder,
  Sliders,
  Activity,
  Volume2,
  VolumeX,
  RefreshCw,
  Video,
  VideoOff,
  Keyboard,
  Send,
  MousePointer,
  ChevronUp,
  ChevronDown,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';

interface RemoteTrackpadViewProps {
  onExecuteAction: (command: string, target?: string | null) => void;
}

export const RemoteTrackpadView: React.FC<RemoteTrackpadViewProps> = ({ onExecuteAction }) => {
  const [isLiveStreaming, setIsLiveStreaming] = useState<boolean>(false);
  const [lastActionStatus, setLastActionStatus] = useState<string | null>(null);
  const [keyboardText, setKeyboardText] = useState<string>('');
  const [trackpadSensitivity, setTrackpadSensitivity] = useState<number>(1.2);
  const [confirmDialog, setConfirmDialog] = useState<{
    isOpen: boolean;
    title: string;
    action: () => void;
  } | null>(null);

  // Simulated live PC desktop monitor state
  const [pcStats, setPcStats] = useState({
    cpu: 28,
    ram: 45,
    activeWindow: 'Google Chrome - JARVIS Dev',
    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  });

  const trackpadRef = useRef<HTMLDivElement>(null);
  const lastTouchRef = useRef<{ x: number; y: number } | null>(null);

  // Update simulated PC clock and stats
  useEffect(() => {
    const timer = setInterval(() => {
      setPcStats((prev) => ({
        ...prev,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        cpu: Math.floor(20 + Math.random() * 25),
      }));
    }, 3000);
    return () => clearInterval(timer);
  }, []);

  const triggerAction = (command: string, target?: string | null, feedback?: string) => {
    onExecuteAction(command, target);
    setLastActionStatus(feedback || `Dispatched: ${command}`);
    setTimeout(() => {
      setLastActionStatus(null);
    }, 2500);
  };

  const handlePointerDown = (e: React.PointerEvent) => {
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
    lastTouchRef.current = { x: e.clientX, y: e.clientY };
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!lastTouchRef.current) return;
    const dx = (e.clientX - lastTouchRef.current.x) * trackpadSensitivity;
    const dy = (e.clientY - lastTouchRef.current.y) * trackpadSensitivity;
    lastTouchRef.current = { x: e.clientX, y: e.clientY };

    // Send mouse move delta to backend/connected PC
    onExecuteAction('mouse_move', JSON.stringify({ dx: Math.round(dx), dy: Math.round(dy) }));
  };

  const handlePointerUp = (e: React.PointerEvent) => {
    try {
      (e.target as HTMLElement).releasePointerCapture(e.pointerId);
    } catch {}
    lastTouchRef.current = null;
  };

  const handleKeyboardSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!keyboardText.trim()) return;
    triggerAction('key_type', keyboardText, `Typed "${keyboardText}" to PC`);
    setKeyboardText('');
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-4 w-full flex flex-col gap-4">
      {/* Action Notification Toast */}
      {lastActionStatus && (
        <div className="fixed top-18 right-6 z-50 bg-[#0A1828] border border-cyan-400 text-cyan-200 px-4 py-2 rounded-xl text-xs font-mono shadow-[0_0_20px_rgba(0,229,255,0.4)] flex items-center gap-2 animate-bounce">
          <CheckCircle2 className="w-4 h-4 text-[#00FF88]" />
          <span>{lastActionStatus}</span>
        </div>
      )}

      {/* Confirmation Modal */}
      {confirmDialog?.isOpen && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0D1826] border border-red-500/40 rounded-2xl max-w-sm w-full p-6 text-center shadow-2xl">
            <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-3" />
            <h3 className="text-lg font-bold font-orbitron text-white mb-2">{confirmDialog.title}</h3>
            <p className="text-xs text-gray-300 mb-6 font-mono">
              Are you sure you want to execute this system command on the connected workstation?
            </p>
            <div className="flex gap-3 justify-center">
              <button
                onClick={() => setConfirmDialog(null)}
                className="px-4 py-2 rounded-xl border border-gray-600 text-gray-300 text-xs font-mono hover:bg-white/5 cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  confirmDialog.action();
                  setConfirmDialog(null);
                }}
                className="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-white text-xs font-mono font-bold shadow-[0_0_15px_rgba(255,51,102,0.4)] cursor-pointer"
              >
                Confirm Command
              </button>
            </div>
          </div>
        </div>
      )}

      {/* PC Screen Preview Box */}
      <div className="bg-[#0B1424] border border-cyan-500/30 rounded-2xl p-3 shadow-lg">
        <div className="flex items-center justify-between border-b border-cyan-500/20 pb-2 mb-2">
          <div className="flex items-center gap-2">
            <Laptop className="w-4 h-4 text-[#00E5FF]" />
            <span className="text-xs font-mono font-bold text-cyan-300 tracking-wider">
              PC MONITOR LIVE FEED
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => triggerAction('screen_snapshot', null, 'Captured PC screen frame')}
              className="p-1.5 rounded-lg bg-cyan-950/40 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 text-xs flex items-center gap-1 cursor-pointer"
              title="Refresh Snapshot"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span className="hidden sm:inline font-mono text-[11px]">Snapshot</span>
            </button>
            <button
              onClick={() => {
                const next = !isLiveStreaming;
                setIsLiveStreaming(next);
                triggerAction('toggle_stream', next ? 'start' : 'stop', next ? 'Live PC Stream Enabled' : 'Stream Paused');
              }}
              className={`p-1.5 rounded-lg border text-xs flex items-center gap-1 cursor-pointer ${
                isLiveStreaming
                  ? 'bg-emerald-500/20 border-emerald-400 text-emerald-300 shadow-[0_0_10px_rgba(0,255,136,0.2)]'
                  : 'bg-gray-800/40 border-gray-600 text-gray-400 hover:text-gray-200'
              }`}
            >
              {isLiveStreaming ? <Video className="w-3.5 h-3.5" /> : <VideoOff className="w-3.5 h-3.5" />}
              <span className="hidden sm:inline font-mono text-[11px]">
                {isLiveStreaming ? 'Live (2s)' : 'Stream Off'}
              </span>
            </button>
          </div>
        </div>

        {/* Simulated Display Stream Surface */}
        <div className="relative aspect-video max-h-56 w-full rounded-xl overflow-hidden bg-[#070D18] border border-cyan-500/20 flex flex-col justify-between p-3 select-none">
          {/* Windows Desktop Header/Wallpaper Simulator */}
          <div className="flex items-center justify-between text-[11px] font-mono text-cyan-300/60">
            <div className="flex items-center gap-1.5 bg-black/40 px-2 py-1 rounded">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>DESKTOP-JARVIS-MK7</span>
            </div>
            <div className="flex items-center gap-3 bg-black/40 px-2 py-1 rounded">
              <span>CPU: {pcStats.cpu}%</span>
              <span>RAM: {pcStats.ram}%</span>
            </div>
          </div>

          <div className="text-center my-auto">
            <div className="inline-flex flex-col items-center p-3 rounded-xl bg-cyan-950/30 border border-cyan-500/20 backdrop-blur-sm">
              <Laptop className="w-8 h-8 text-[#00E5FF] mb-1" />
              <p className="text-xs font-mono text-cyan-200">Workstation Connected & Streaming</p>
              <p className="text-[10px] font-mono text-gray-400 mt-0.5">{pcStats.activeWindow}</p>
            </div>
          </div>

          {/* Desktop Taskbar Simulator */}
          <div className="bg-[#050912]/90 border border-white/10 rounded-lg p-1.5 flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded bg-blue-500/30 flex items-center justify-center text-[9px] font-bold text-blue-300">
                W
              </div>
              <span className="text-[10px] font-mono text-gray-300">Windows 11 Neural Relay</span>
            </div>
            <span className="text-[10px] font-mono text-cyan-300">{pcStats.time}</span>
          </div>
        </div>
      </div>

      {/* Quick PC Shortcuts Action Bar */}
      <div className="bg-[#0B1424] border border-cyan-500/30 rounded-2xl p-3">
        <h4 className="text-xs font-mono font-bold text-cyan-300 tracking-wider mb-2.5">
          QUICK PC ACTIONS
        </h4>

        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-2">
          <button
            onClick={() => triggerAction('open_chrome', 'chrome', 'Opening Chrome on PC')}
            className="p-2.5 rounded-xl bg-[#0F1B2B] hover:bg-cyan-500/15 border border-cyan-500/20 hover:border-cyan-400 text-cyan-200 flex flex-col items-center gap-1 transition-all cursor-pointer"
          >
            <Globe className="w-5 h-5 text-[#00E5FF]" />
            <span className="text-[11px] font-mono">Chrome</span>
          </button>

          <button
            onClick={() => triggerAction('open_website', 'https://www.youtube.com', 'Opening YouTube on PC')}
            className="p-2.5 rounded-xl bg-[#0F1B2B] hover:bg-red-500/15 border border-red-500/20 hover:border-red-400 text-red-200 flex flex-col items-center gap-1 transition-all cursor-pointer"
          >
            <Youtube className="w-5 h-5 text-red-400" />
            <span className="text-[11px] font-mono">YouTube</span>
          </button>

          <button
            onClick={() => triggerAction('open_whatsapp', null, 'Opening WhatsApp on PC')}
            className="p-2.5 rounded-xl bg-[#0F1B2B] hover:bg-emerald-500/15 border border-emerald-500/20 hover:border-emerald-400 text-emerald-200 flex flex-col items-center gap-1 transition-all cursor-pointer"
          >
            <MessageSquare className="w-5 h-5 text-[#00FF88]" />
            <span className="text-[11px] font-mono">WhatsApp</span>
          </button>

          <button
            onClick={() => triggerAction('open_file_explorer', 'explorer', 'Opening File Explorer')}
            className="p-2.5 rounded-xl bg-[#0F1B2B] hover:bg-amber-500/15 border border-amber-500/20 hover:border-amber-400 text-amber-200 flex flex-col items-center gap-1 transition-all cursor-pointer"
          >
            <Folder className="w-5 h-5 text-amber-400" />
            <span className="text-[11px] font-mono">Explorer</span>
          </button>

          <button
            onClick={() => triggerAction('open_settings', 'settings', 'Opening PC Settings')}
            className="p-2.5 rounded-xl bg-[#0F1B2B] hover:bg-purple-500/15 border border-purple-500/20 hover:border-purple-400 text-purple-200 flex flex-col items-center gap-1 transition-all cursor-pointer"
          >
            <Sliders className="w-5 h-5 text-[#BD00FF]" />
            <span className="text-[11px] font-mono">Settings</span>
          </button>

          <button
            onClick={() => triggerAction('lock_pc', null, 'Locking PC screen')}
            className="p-2.5 rounded-xl bg-[#0F1B2B] hover:bg-amber-500/15 border border-amber-500/20 hover:border-amber-400 text-amber-300 flex flex-col items-center gap-1 transition-all cursor-pointer"
          >
            <Lock className="w-5 h-5 text-amber-400" />
            <span className="text-[11px] font-mono">Lock PC</span>
          </button>

          <button
            onClick={() => triggerAction('volume_up', null, 'Volume Increased')}
            className="p-2.5 rounded-xl bg-[#0F1B2B] hover:bg-cyan-500/15 border border-cyan-500/20 text-cyan-300 flex flex-col items-center gap-1 transition-all cursor-pointer"
          >
            <Volume2 className="w-5 h-5 text-[#00E5FF]" />
            <span className="text-[11px] font-mono">Vol Up</span>
          </button>

          <button
            onClick={() => triggerAction('volume_down', null, 'Volume Decreased')}
            className="p-2.5 rounded-xl bg-[#0F1B2B] hover:bg-cyan-500/15 border border-cyan-500/20 text-cyan-300 flex flex-col items-center gap-1 transition-all cursor-pointer"
          >
            <VolumeX className="w-5 h-5 text-cyan-300" />
            <span className="text-[11px] font-mono">Vol Down</span>
          </button>

          <button
            onClick={() => triggerAction('open_task_manager', null, 'Opening Task Manager')}
            className="p-2.5 rounded-xl bg-[#0F1B2B] hover:bg-cyan-500/15 border border-cyan-500/20 text-cyan-300 flex flex-col items-center gap-1 transition-all cursor-pointer"
          >
            <Activity className="w-5 h-5 text-cyan-300" />
            <span className="text-[11px] font-mono">Task Mgr</span>
          </button>

          <button
            onClick={() =>
              setConfirmDialog({
                isOpen: true,
                title: 'Restart PC Workstation',
                action: () => triggerAction('restart_pc', null, 'Restart command sent to PC'),
              })
            }
            className="p-2.5 rounded-xl bg-[#0F1B2B] hover:bg-amber-500/15 border border-amber-500/30 text-amber-300 flex flex-col items-center gap-1 transition-all cursor-pointer"
          >
            <RotateCcw className="w-5 h-5 text-amber-400" />
            <span className="text-[11px] font-mono">Restart</span>
          </button>

          <button
            onClick={() =>
              setConfirmDialog({
                isOpen: true,
                title: 'Shutdown PC Workstation',
                action: () => triggerAction('shutdown_pc', null, 'Shutdown command sent to PC'),
              })
            }
            className="p-2.5 rounded-xl bg-[#1A0C14] hover:bg-red-500/20 border border-red-500/30 text-red-300 flex flex-col items-center gap-1 transition-all cursor-pointer"
          >
            <Power className="w-5 h-5 text-[#FF3366]" />
            <span className="text-[11px] font-mono">Shutdown</span>
          </button>
        </div>
      </div>

      {/* Virtual Trackpad Surface */}
      <div className="bg-[#0B1424] border border-cyan-500/30 rounded-2xl p-4 flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MousePointer className="w-4 h-4 text-[#00E5FF]" />
            <span className="text-xs font-mono font-bold text-cyan-300 tracking-wider">
              VIRTUAL TOUCHPAD
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono text-gray-400">Sensitivity:</span>
            <input
              type="range"
              min="0.5"
              max="2.5"
              step="0.1"
              value={trackpadSensitivity}
              onChange={(e) => setTrackpadSensitivity(parseFloat(e.target.value))}
              className="w-20 accent-cyan-400"
            />
          </div>
        </div>

        {/* Touch / Mouse Drag Area */}
        <div
          ref={trackpadRef}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          className="w-full h-44 md:h-52 bg-[#070D18] rounded-xl border-2 border-dashed border-cyan-500/30 flex flex-col items-center justify-center text-center touch-none cursor-crosshair select-none relative overflow-hidden group hover:border-cyan-400/60 transition-colors"
        >
          <MousePointer className="w-7 h-7 text-cyan-400/40 group-hover:text-cyan-400 transition-colors mb-2" />
          <p className="text-xs font-mono text-cyan-200/60">Drag on surface to control PC cursor</p>
          <p className="text-[10px] font-mono text-cyan-400/40 mt-1">Multi-touch & pointer tracking</p>
        </div>

        {/* Mouse Buttons */}
        <div className="grid grid-cols-4 gap-2">
          <button
            onClick={() => triggerAction('mouse_click', 'left', 'Left Click')}
            className="py-3 rounded-xl bg-cyan-950/40 hover:bg-cyan-500/20 border border-cyan-500/30 hover:border-cyan-400 text-cyan-200 font-mono text-xs font-bold active:scale-95 transition-all cursor-pointer"
          >
            Left Click
          </button>
          <button
            onClick={() => triggerAction('mouse_double_click', 'left', 'Double Click')}
            className="py-3 rounded-xl bg-cyan-950/40 hover:bg-cyan-500/20 border border-cyan-500/30 hover:border-cyan-400 text-cyan-200 font-mono text-xs font-bold active:scale-95 transition-all cursor-pointer"
          >
            Double Click
          </button>
          <button
            onClick={() => triggerAction('mouse_click', 'right', 'Right Click')}
            className="py-3 rounded-xl bg-cyan-950/40 hover:bg-cyan-500/20 border border-cyan-500/30 hover:border-cyan-400 text-cyan-200 font-mono text-xs font-bold active:scale-95 transition-all cursor-pointer"
          >
            Right Click
          </button>
          <div className="flex gap-1">
            <button
              onClick={() => triggerAction('mouse_scroll', 'up', 'Scroll Up')}
              className="flex-1 py-3 rounded-xl bg-cyan-950/40 hover:bg-cyan-500/20 border border-cyan-500/30 text-cyan-200 flex items-center justify-center active:scale-95 transition-all cursor-pointer"
              title="Scroll Up"
            >
              <ChevronUp className="w-4 h-4" />
            </button>
            <button
              onClick={() => triggerAction('mouse_scroll', 'down', 'Scroll Down')}
              className="flex-1 py-3 rounded-xl bg-cyan-950/40 hover:bg-cyan-500/20 border border-cyan-500/30 text-cyan-200 flex items-center justify-center active:scale-95 transition-all cursor-pointer"
              title="Scroll Down"
            >
              <ChevronDown className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Remote Keyboard Input Bar */}
      <form
        onSubmit={handleKeyboardSend}
        className="bg-[#0B1424] border border-cyan-500/30 rounded-2xl p-3 flex items-center gap-2"
      >
        <Keyboard className="w-5 h-5 text-cyan-400 ml-2 shrink-0" />
        <input
          type="text"
          value={keyboardText}
          onChange={(e) => setKeyboardText(e.target.value)}
          placeholder="Type text to send directly to PC active window..."
          className="flex-1 bg-transparent px-3 py-2 text-sm text-white placeholder:text-gray-500 focus:outline-none font-mono"
        />
        <button
          type="submit"
          className="px-4 py-2 rounded-xl bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-400 text-cyan-300 font-mono text-xs font-bold flex items-center gap-1.5 cursor-pointer"
        >
          <Send className="w-3.5 h-3.5" />
          <span>Type to PC</span>
        </button>
      </form>
    </div>
  );
};
