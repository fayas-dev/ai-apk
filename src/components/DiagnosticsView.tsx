import React, { useState, useEffect } from 'react';
import { RelayStatus, LogEntry } from '../types';
import {
  Activity,
  Server,
  Wifi,
  Cpu,
  Terminal,
  QrCode,
  CheckCircle,
  AlertCircle,
  Copy,
  Trash2,
  RefreshCw,
} from 'lucide-react';

interface DiagnosticsViewProps {
  relayStatus: RelayStatus | null;
  logs: LogEntry[];
  onClearLogs: () => void;
  onRefreshStatus: () => void;
}

export const DiagnosticsView: React.FC<DiagnosticsViewProps> = ({
  relayStatus,
  logs,
  onClearLogs,
  onRefreshStatus,
}) => {
  const [latency, setLatency] = useState<number | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const measureLatency = async () => {
    const start = performance.now();
    try {
      await fetch('/api/health');
      const roundTrip = Math.round(performance.now() - start);
      setLatency(roundTrip);
    } catch {
      setLatency(null);
    }
  };

  useEffect(() => {
    measureLatency();
    const interval = setInterval(measureLatency, 5000);
    return () => clearInterval(interval);
  }, []);

  const copyConnectionUrl = () => {
    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/jarvis`;
    navigator.clipboard.writeText(wsUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-4 w-full flex flex-col gap-4">
      {/* System Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Status Card 1: Server Status */}
        <div className="bg-[#0B1424] border border-cyan-500/30 rounded-2xl p-4 shadow">
          <div className="flex items-center justify-between text-xs font-mono text-cyan-300/70 mb-2">
            <span>RELAY SERVER</span>
            <Server className="w-4 h-4 text-[#00E5FF]" />
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-lg font-bold font-orbitron text-white">ONLINE</span>
          </div>
          <p className="text-[11px] font-mono text-gray-400 mt-1">Port 3000 • Node/Express</p>
        </div>

        {/* Status Card 2: Device Connections */}
        <div className="bg-[#0B1424] border border-cyan-500/30 rounded-2xl p-4 shadow">
          <div className="flex items-center justify-between text-xs font-mono text-cyan-300/70 mb-2">
            <span>CONNECTED CLIENTS</span>
            <Wifi className="w-4 h-4 text-[#00FF88]" />
          </div>
          <div className="flex items-center gap-3">
            <span className="text-lg font-bold font-orbitron text-[#00FF88]">
              {relayStatus ? relayStatus.activePcClients + relayStatus.activeMobileClients : 0}
            </span>
            <span className="text-xs font-mono text-cyan-200">
              ({relayStatus?.activePcClients || 0} PC, {relayStatus?.activeMobileClients || 0} Mobile)
            </span>
          </div>
          <p className="text-[11px] font-mono text-gray-400 mt-1">WebSocket: /ws/jarvis</p>
        </div>

        {/* Status Card 3: Neural AI Engine */}
        <div className="bg-[#0B1424] border border-cyan-500/30 rounded-2xl p-4 shadow">
          <div className="flex items-center justify-between text-xs font-mono text-cyan-300/70 mb-2">
            <span>AI NEURAL ENGINE</span>
            <Cpu className="w-4 h-4 text-[#BD00FF]" />
          </div>
          <div className="text-sm font-bold font-orbitron text-purple-300 truncate">
            {relayStatus?.hasGemini
              ? 'GEMINI 2.5 FLASH'
              : relayStatus?.hasOpenRouter
              ? 'OPENROUTER AI'
              : 'MARK VII CORE'}
          </div>
          <p className="text-[11px] font-mono text-gray-400 mt-1">
            {relayStatus?.hasGemini || relayStatus?.hasOpenRouter ? 'Cloud LLM Active' : 'Zero-Latency Engine'}
          </p>
        </div>

        {/* Status Card 4: WebSocket Latency */}
        <div className="bg-[#0B1424] border border-cyan-500/30 rounded-2xl p-4 shadow">
          <div className="flex items-center justify-between text-xs font-mono text-cyan-300/70 mb-2">
            <span>NETWORK LATENCY</span>
            <Activity className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-lg font-bold font-orbitron text-cyan-300">
            {latency !== null ? `${latency} ms` : 'Testing...'}
          </div>
          <p className="text-[11px] font-mono text-gray-400 mt-1">
            {latency && latency < 60 ? 'Optimal Response' : 'Normal Relay Range'}
          </p>
        </div>
      </div>

      {/* Device Pairing Section */}
      <div className="bg-[#0B1424] border border-cyan-500/30 rounded-2xl p-4 md:p-5">
        <div className="flex items-center justify-between border-b border-cyan-500/20 pb-3 mb-4">
          <div className="flex items-center gap-2">
            <QrCode className="w-5 h-5 text-[#00E5FF]" />
            <h3 className="text-sm font-bold font-orbitron text-cyan-300 tracking-wider">
              DEVICE PAIRING & RELAY LINK
            </h3>
          </div>
          <button
            onClick={onRefreshStatus}
            className="p-1.5 rounded-lg bg-cyan-950/40 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 text-xs flex items-center gap-1 cursor-pointer font-mono"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
          {/* QR Code */}
          <div className="flex flex-col items-center justify-center p-3 bg-[#070D18] rounded-xl border border-cyan-500/20">
            <div className="w-40 h-40 bg-white p-2 rounded-lg flex items-center justify-center shadow-md">
              <img
                src="/pairing_qr.png"
                alt="Device Pairing QR"
                className="w-full h-full object-contain"
                onError={(e) => {
                  (e.target as HTMLElement).style.display = 'none';
                  const parent = (e.target as HTMLElement).parentElement;
                  if (parent) {
                    parent.innerHTML = `
                      <div class="text-center p-2 text-gray-900 font-mono text-xs">
                        <div class="font-bold mb-1">JARVIS RELAY</div>
                        <div class="text-[10px] break-all">ws://${window.location.host}/ws/jarvis</div>
                      </div>
                    `;
                  }
                }}
              />
            </div>
            <span className="text-[10px] font-mono text-cyan-300/60 mt-2">Scan with Jarvis Mobile Client</span>
          </div>

          {/* Connection URL & Instructions */}
          <div className="md:col-span-2 flex flex-col gap-3 font-mono">
            <div>
              <label className="text-xs text-cyan-300 font-bold">Relay WebSocket URL:</label>
              <div className="flex items-center gap-2 mt-1 bg-[#070D18] p-2 rounded-xl border border-cyan-500/30">
                <code className="text-xs text-[#00E5FF] truncate flex-1">
                  {`${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/jarvis`}
                </code>
                <button
                  onClick={copyConnectionUrl}
                  className="px-2.5 py-1 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 text-xs flex items-center gap-1 cursor-pointer"
                >
                  <Copy className="w-3 h-3" />
                  <span>{copied ? 'Copied!' : 'Copy'}</span>
                </button>
              </div>
            </div>

            <div className="text-xs text-gray-300 space-y-1 bg-[#070D18]/60 p-3 rounded-xl border border-white/5">
              <p className="text-cyan-400 font-bold">How device relay functions:</p>
              <p>1. PC Client or APK connects to the WebSocket endpoint above.</p>
              <p>2. Voice or trackpad commands from this web console are broadcasted instantly to paired PC clients.</p>
              <p>3. If no physical PC is connected, the built-in Mark VII virtual desktop simulator handles commands seamlessly.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Live Diagnostic Terminal Event Log */}
      <div className="bg-[#0B1424] border border-cyan-500/30 rounded-2xl p-4">
        <div className="flex items-center justify-between border-b border-cyan-500/20 pb-2.5 mb-3">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-[#00E5FF]" />
            <span className="text-xs font-mono font-bold text-cyan-300 tracking-wider">
              REAL-TIME DIAGNOSTIC EVENT LOG
            </span>
          </div>
          <button
            onClick={onClearLogs}
            className="p-1 rounded text-gray-400 hover:text-red-400 text-xs flex items-center gap-1 font-mono cursor-pointer"
            title="Clear logs"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear</span>
          </button>
        </div>

        <div className="bg-[#050A14] rounded-xl p-3 h-48 overflow-y-auto font-mono text-xs space-y-1.5 border border-cyan-500/20">
          {logs.length === 0 ? (
            <p className="text-gray-500 italic">No events recorded yet. Ready to capture telemetry...</p>
          ) : (
            logs.map((log) => (
              <div key={log.id} className="flex items-start gap-2 leading-tight">
                <span className="text-cyan-400/50 shrink-0 text-[10px]">[{log.timestamp}]</span>
                <span
                  className={`text-[10px] uppercase font-bold shrink-0 ${
                    log.type === 'command'
                      ? 'text-[#00FF88]'
                      : log.type === 'response'
                      ? 'text-[#00E5FF]'
                      : log.type === 'relay'
                      ? 'text-[#BD00FF]'
                      : log.type === 'error'
                      ? 'text-[#FF3366]'
                      : 'text-gray-400'
                  }`}
                >
                  [{log.type}]
                </span>
                <span className="text-gray-200 break-all">{log.message}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
