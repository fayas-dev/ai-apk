import React from 'react';
import { AssistantState } from '../types';
import { Mic, MicOff, Volume2, Sparkles, Cpu, AlertTriangle } from 'lucide-react';

interface ArcReactorProps {
  state: AssistantState;
  onClick: () => void;
  isAudioMuted?: boolean;
}

export const ArcReactor: React.FC<ArcReactorProps> = ({ state, onClick, isAudioMuted }) => {
  const getThemeColors = () => {
    switch (state) {
      case 'listening':
        return {
          primary: '#00FF88',
          ring: 'rgba(0, 255, 136, 0.4)',
          glow: 'rgba(0, 255, 136, 0.25)',
          shadow: '0 0 45px rgba(0, 255, 136, 0.6), inset 0 0 25px rgba(0, 255, 136, 0.3)',
          label: 'LISTENING',
        };
      case 'processing':
        return {
          primary: '#BD00FF',
          ring: 'rgba(189, 0, 255, 0.45)',
          glow: 'rgba(189, 0, 255, 0.25)',
          shadow: '0 0 45px rgba(189, 0, 255, 0.6), inset 0 0 25px rgba(189, 0, 255, 0.3)',
          label: 'PROCESSING',
        };
      case 'speaking':
        return {
          primary: '#00B0FF',
          ring: 'rgba(0, 176, 255, 0.45)',
          glow: 'rgba(0, 176, 255, 0.25)',
          shadow: '0 0 45px rgba(0, 176, 255, 0.6), inset 0 0 25px rgba(0, 176, 255, 0.3)',
          label: 'SPEAKING',
        };
      case 'connecting':
        return {
          primary: '#FFB300',
          ring: 'rgba(255, 179, 0, 0.4)',
          glow: 'rgba(255, 179, 0, 0.2)',
          shadow: '0 0 35px rgba(255, 179, 0, 0.5), inset 0 0 20px rgba(255, 179, 0, 0.2)',
          label: 'CONNECTING',
        };
      case 'error':
      case 'disconnected':
        return {
          primary: '#FF3366',
          ring: 'rgba(255, 51, 102, 0.35)',
          glow: 'rgba(255, 51, 102, 0.15)',
          shadow: '0 0 35px rgba(255, 51, 102, 0.4), inset 0 0 20px rgba(255, 51, 102, 0.2)',
          label: 'OFFLINE',
        };
      case 'connected':
      default:
        return {
          primary: '#00E5FF',
          ring: 'rgba(0, 229, 255, 0.35)',
          glow: 'rgba(0, 229, 255, 0.2)',
          shadow: '0 0 40px rgba(0, 229, 255, 0.45), inset 0 0 25px rgba(0, 229, 255, 0.25)',
          label: 'ONLINE',
        };
    }
  };

  const theme = getThemeColors();
  const isActive = state === 'listening' || state === 'processing' || state === 'speaking';

  return (
    <div className="relative flex flex-col items-center justify-center select-none my-4">
      {/* Outer Pulse Wave Rings */}
      <button
        id="arc-reactor-button"
        onClick={onClick}
        aria-label="Toggle Jarvis Arc Reactor Voice Assistant"
        className="relative group focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 rounded-full transition-transform active:scale-95 cursor-pointer"
      >
        {/* Outermost Pulsing Halo Ring */}
        <div
          className={`absolute -inset-8 rounded-full border transition-all duration-700 pointer-events-none ${
            isActive ? 'animate-arc-pulse scale-105' : 'opacity-20 group-hover:opacity-40'
          }`}
          style={{
            borderColor: theme.ring,
            boxShadow: isActive ? `0 0 30px ${theme.glow}` : 'none',
          }}
        />

        {/* Rotating Tech HUD Ring */}
        <div
          className="absolute -inset-4 rounded-full border border-dashed animate-arc-rotate pointer-events-none opacity-40 group-hover:opacity-75 transition-opacity"
          style={{ borderColor: theme.primary }}
        />

        {/* Reverse Rotating Segment Ring */}
        <div
          className="absolute -inset-2 rounded-full border border-dotted animate-arc-rotate-rev pointer-events-none opacity-30 group-hover:opacity-60 transition-opacity"
          style={{ borderColor: theme.primary }}
        />

        {/* Main Arc Reactor Outer Housing */}
        <div
          className="relative w-52 h-52 md:w-60 md:h-60 rounded-full flex items-center justify-center p-3 transition-all duration-500 bg-radial from-[#0e1c2e] via-[#09111c] to-[#04060a] border-2"
          style={{
            borderColor: theme.primary,
            boxShadow: theme.shadow,
          }}
        >
          {/* Segmented Arc Slots */}
          <div className="absolute inset-0 rounded-full pointer-events-none overflow-hidden opacity-40">
            {[...Array(12)].map((_, i) => (
              <div
                key={i}
                className="absolute top-0 left-1/2 -ml-[1px] w-[2px] h-full origin-center"
                style={{
                  transform: `rotate(${i * 30}deg)`,
                  background: `linear-gradient(to bottom, ${theme.primary} 0%, transparent 25%, transparent 75%, ${theme.primary} 100%)`,
                }}
              />
            ))}
          </div>

          {/* Inner Glowing Reactor Core */}
          <div
            className="relative w-36 h-36 md:w-44 md:h-44 rounded-full flex flex-col items-center justify-center border-2 overflow-hidden transition-all duration-300 bg-gradient-to-b from-[#132338] via-[#0b1523] to-[#040810]"
            style={{
              borderColor: `${theme.primary}99`,
              boxShadow: `inset 0 0 20px ${theme.glow}`,
            }}
          >
            {/* Logo Image or Fallback Iconic Symbol */}
            <div className="relative z-10 flex flex-col items-center justify-center">
              <img
                src="/logo.png"
                alt="JARVIS Core"
                className={`w-20 h-20 md:w-24 md:h-24 object-contain filter drop-shadow transition-all duration-500 ${
                  isActive ? 'scale-110 drop-shadow-[0_0_15px_rgba(0,229,255,0.8)]' : 'opacity-85 group-hover:opacity-100'
                }`}
                onError={(e) => {
                  // If image fails to load, gracefully hide and show icon fallback
                  (e.target as HTMLElement).style.display = 'none';
                }}
              />

              {/* Status Icon Badge */}
              <div className="mt-1 flex items-center gap-1">
                {state === 'listening' ? (
                  <Mic className="w-5 h-5 text-[#00FF88] animate-bounce" />
                ) : state === 'speaking' ? (
                  <Volume2 className="w-5 h-5 text-[#00B0FF] animate-pulse" />
                ) : state === 'processing' ? (
                  <Sparkles className="w-5 h-5 text-[#BD00FF] animate-spin" />
                ) : state === 'error' || state === 'disconnected' ? (
                  <AlertTriangle className="w-5 h-5 text-[#FF3366]" />
                ) : (
                  <Cpu className="w-5 h-5 text-[#00E5FF] opacity-70 group-hover:opacity-100" />
                )}
              </div>
            </div>

            {/* Core Energy Flow Lines */}
            <div
              className={`absolute inset-0 bg-radial from-transparent via-${theme.primary}/10 to-transparent pointer-events-none ${
                isActive ? 'animate-pulse' : ''
              }`}
            />
          </div>
        </div>
      </button>

      {/* Voice Prompt Guidance */}
      <div className="mt-6 text-center">
        <p
          className="text-base md:text-lg font-semibold tracking-wider font-orbitron transition-colors duration-300"
          style={{ color: theme.primary }}
        >
          {state === 'listening'
            ? 'LISTENING... (TAP TO SEND)'
            : state === 'speaking'
            ? 'SPEAKING... (TAP TO INTERRUPT)'
            : state === 'processing'
            ? 'NEURAL CORE THINKING...'
            : 'TAP ARC REACTOR TO SPEAK'}
        </p>
        <p className="text-xs text-cyan-200/50 mt-1 uppercase tracking-widest font-mono">
          {state === 'listening'
            ? 'Web Speech Engine Active • 30s Window'
            : isAudioMuted
            ? 'Voice output muted (Text only)'
            : 'Microphone & Continuous Dialog Ready'}
        </p>
      </div>
    </div>
  );
};
