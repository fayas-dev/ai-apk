import React from 'react';
import { ActiveTab, AssistantState } from '../types';
import { Radio, Laptop, Activity, Settings, Volume2, VolumeX, ShieldCheck } from 'lucide-react';

interface NavbarProps {
  currentTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
  state: AssistantState;
  isAudioMuted: boolean;
  onToggleMute: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  onTabChange,
  state,
  isAudioMuted,
  onToggleMute,
}) => {
  const getBadgeStyle = () => {
    switch (state) {
      case 'connected':
        return 'text-[#00E5FF] border-[#00E5FF]/40 bg-[#00E5FF]/10 shadow-[0_0_12px_rgba(0,229,255,0.25)]';
      case 'listening':
        return 'text-[#00FF88] border-[#00FF88]/40 bg-[#00FF88]/10 shadow-[0_0_12px_rgba(0,255,136,0.3)] animate-pulse';
      case 'processing':
        return 'text-[#BD00FF] border-[#BD00FF]/40 bg-[#BD00FF]/10 shadow-[0_0_12px_rgba(189,0,255,0.3)] animate-pulse';
      case 'speaking':
        return 'text-[#00B0FF] border-[#00B0FF]/40 bg-[#00B0FF]/10 shadow-[0_0_12px_rgba(0,176,255,0.3)]';
      case 'connecting':
        return 'text-[#FFB300] border-[#FFB300]/40 bg-[#FFB300]/10 shadow-[0_0_12px_rgba(255,179,0,0.2)]';
      default:
        return 'text-[#FF3366] border-[#FF3366]/40 bg-[#FF3366]/10 shadow-[0_0_12px_rgba(255,51,102,0.2)]';
    }
  };

  const getBadgeText = () => {
    switch (state) {
      case 'connected':
        return '● ONLINE';
      case 'listening':
        return '◉ LISTENING';
      case 'processing':
        return '◎ THINKING';
      case 'speaking':
        return '▶ SPEAKING';
      case 'connecting':
        return '○ CONNECTING';
      default:
        return '● OFFLINE';
    }
  };

  return (
    <header className="border-b border-cyan-500/20 bg-[#070D18]/90 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-3">
        {/* Brand & Mark */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-950/40 border border-cyan-400/30 flex items-center justify-center p-1.5 shadow-[0_0_15px_rgba(0,229,255,0.2)]">
            <img src="/logo.png" alt="JARVIS" className="w-full h-full object-contain" onError={(e) => { (e.target as HTMLElement).style.display = 'none'; }} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl md:text-2xl font-black tracking-[0.2em] font-orbitron text-transparent bg-clip-text bg-gradient-to-r from-[#00E5FF] via-cyan-200 to-white drop-shadow-[0_0_12px_rgba(0,229,255,0.4)]">
                JARVIS
              </h1>
              <span className="hidden sm:inline-block px-1.5 py-0.5 rounded text-[10px] font-mono tracking-wider font-semibold bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">
                MARK VII
              </span>
            </div>
            <p className="text-[10px] font-mono tracking-widest text-cyan-300/60 uppercase">
              Neural Assistant & PC Relay // Fayas Edition
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 bg-[#0B1524] p-1 rounded-xl border border-cyan-500/20">
          <button
            id="nav-arc-reactor"
            onClick={() => onTabChange('arc-reactor')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wider transition-all duration-200 cursor-pointer ${
              currentTab === 'arc-reactor'
                ? 'bg-cyan-500/20 text-[#00E5FF] border border-cyan-400/40 shadow-[0_0_10px_rgba(0,229,255,0.2)]'
                : 'text-gray-400 hover:text-cyan-200 hover:bg-white/5'
            }`}
          >
            <Radio className="w-3.5 h-3.5" />
            <span className="hidden md:inline">ARC REACTOR</span>
            <span className="md:hidden">AI</span>
          </button>

          <button
            id="nav-remote-control"
            onClick={() => onTabChange('remote-control')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wider transition-all duration-200 cursor-pointer ${
              currentTab === 'remote-control'
                ? 'bg-cyan-500/20 text-[#00E5FF] border border-cyan-400/40 shadow-[0_0_10px_rgba(0,229,255,0.2)]'
                : 'text-gray-400 hover:text-cyan-200 hover:bg-white/5'
            }`}
          >
            <Laptop className="w-3.5 h-3.5" />
            <span className="hidden md:inline">PC REMOTE</span>
            <span className="md:hidden">REMOTE</span>
          </button>

          <button
            id="nav-diagnostics"
            onClick={() => onTabChange('diagnostics')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wider transition-all duration-200 cursor-pointer ${
              currentTab === 'diagnostics'
                ? 'bg-cyan-500/20 text-[#00E5FF] border border-cyan-400/40 shadow-[0_0_10px_rgba(0,229,255,0.2)]'
                : 'text-gray-400 hover:text-cyan-200 hover:bg-white/5'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            <span className="hidden md:inline">DIAGNOSTICS</span>
            <span className="md:hidden">STATUS</span>
          </button>

          <button
            id="nav-settings"
            onClick={() => onTabChange('settings')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wider transition-all duration-200 cursor-pointer ${
              currentTab === 'settings'
                ? 'bg-cyan-500/20 text-[#00E5FF] border border-cyan-400/40 shadow-[0_0_10px_rgba(0,229,255,0.2)]'
                : 'text-gray-400 hover:text-cyan-200 hover:bg-white/5'
            }`}
          >
            <Settings className="w-3.5 h-3.5" />
            <span className="hidden md:inline">SETTINGS</span>
            <span className="md:hidden">CONFIG</span>
          </button>
        </nav>

        {/* Status Badge & Audio Toggle */}
        <div className="flex items-center gap-2">
          <button
            id="toggle-audio-mute"
            onClick={onToggleMute}
            aria-label={isAudioMuted ? 'Unmute voice output' : 'Mute voice output'}
            className={`p-2 rounded-lg border transition-all cursor-pointer ${
              isAudioMuted
                ? 'bg-red-500/10 border-red-500/30 text-red-400'
                : 'bg-cyan-500/10 border-cyan-500/30 text-cyan-300 hover:bg-cyan-500/20'
            }`}
            title={isAudioMuted ? 'Voice output muted' : 'Voice output active'}
          >
            {isAudioMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
          </button>

          <div
            id="status-badge"
            className={`px-2.5 py-1 rounded-full text-[11px] font-mono font-bold tracking-widest border ${getBadgeStyle()}`}
          >
            {getBadgeText()}
          </div>
        </div>
      </div>
    </header>
  );
};
