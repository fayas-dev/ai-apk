import React, { useState, useEffect } from 'react';
import { VoiceSettings } from '../types';
import { Settings, Volume2, Globe, User, Shield, Check, Play } from 'lucide-react';

interface SettingsViewProps {
  settings: VoiceSettings;
  onUpdateSettings: (newSettings: Partial<VoiceSettings>) => void;
  onTestVoice: () => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({
  settings,
  onUpdateSettings,
  onTestVoice,
}) => {
  const [availableVoices, setAvailableVoices] = useState<SpeechSynthesisVoice[]>([]);

  useEffect(() => {
    const loadVoices = () => {
      if (typeof window !== 'undefined' && window.speechSynthesis) {
        setAvailableVoices(window.speechSynthesis.getVoices());
      }
    };
    loadVoices();
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }
  }, []);

  return (
    <div className="max-w-4xl mx-auto px-4 py-4 w-full flex flex-col gap-4">
      {/* Speech & Voice Synthesis Settings */}
      <div className="bg-[#0B1424] border border-cyan-500/30 rounded-2xl p-4 md:p-5">
        <div className="flex items-center gap-2 border-b border-cyan-500/20 pb-2.5 mb-4">
          <Volume2 className="w-5 h-5 text-[#00E5FF]" />
          <h3 className="text-sm font-bold font-orbitron text-cyan-300 tracking-wider">
            SPEECH SYNTHESIS & VOICE CONFIGURATION
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Voice Selector */}
          <div>
            <label className="block text-xs font-mono text-cyan-200 mb-1">
              Assistant Voice Model:
            </label>
            <select
              value={settings.voiceURI}
              onChange={(e) => onUpdateSettings({ voiceURI: e.target.value })}
              className="w-full bg-[#070D18] border border-cyan-500/30 rounded-xl px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-cyan-400"
            >
              <option value="">Default Jarvis Neural Voice</option>
              {availableVoices.map((voice) => (
                <option key={voice.voiceURI} value={voice.voiceURI}>
                  {voice.name} ({voice.lang})
                </option>
              ))}
            </select>
          </div>

          {/* Language Selection */}
          <div>
            <label className="block text-xs font-mono text-cyan-200 mb-1">
              Primary Dialog Language:
            </label>
            <select
              value={settings.language}
              onChange={(e) => onUpdateSettings({ language: e.target.value as any })}
              className="w-full bg-[#070D18] border border-cyan-500/30 rounded-xl px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-cyan-400"
            >
              <option value="en">English (US / UK / Global)</option>
              <option value="ml">Malayalam (മലയാളം - India)</option>
              <option value="auto">Auto-Detect Multilingual</option>
            </select>
          </div>

          {/* Speech Rate Slider */}
          <div>
            <div className="flex justify-between text-xs font-mono text-cyan-200 mb-1">
              <span>Speech Speed Rate:</span>
              <span className="text-[#00E5FF]">{settings.rate}x</span>
            </div>
            <input
              type="range"
              min="0.6"
              max="1.6"
              step="0.05"
              value={settings.rate}
              onChange={(e) => onUpdateSettings({ rate: parseFloat(e.target.value) })}
              className="w-full accent-cyan-400 cursor-pointer"
            />
          </div>

          {/* Speech Pitch Slider */}
          <div>
            <div className="flex justify-between text-xs font-mono text-cyan-200 mb-1">
              <span>Speech Pitch Tone:</span>
              <span className="text-[#00E5FF]">{settings.pitch}</span>
            </div>
            <input
              type="range"
              min="0.5"
              max="1.5"
              step="0.05"
              value={settings.pitch}
              onChange={(e) => onUpdateSettings({ pitch: parseFloat(e.target.value) })}
              className="w-full accent-cyan-400 cursor-pointer"
            />
          </div>
        </div>

        <div className="mt-4 pt-3 border-t border-cyan-500/20 flex flex-wrap items-center justify-between gap-3">
          {/* Continuous Mode Toggle */}
          <label className="flex items-center gap-2 text-xs font-mono text-gray-300 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={settings.autoListen}
              onChange={(e) => onUpdateSettings({ autoListen: e.target.checked })}
              className="w-4 h-4 rounded border-cyan-400 accent-cyan-400"
            />
            <span>Continuous Conversation (Auto-relisten after reply)</span>
          </label>

          <button
            onClick={onTestVoice}
            className="px-4 py-2 rounded-xl bg-cyan-500/20 hover:bg-cyan-500/30 text-[#00E5FF] border border-cyan-400 font-mono text-xs font-bold flex items-center gap-1.5 cursor-pointer shadow-[0_0_10px_rgba(0,229,255,0.2)]"
          >
            <Play className="w-3.5 h-3.5" />
            <span>Test Jarvis Voice</span>
          </button>
        </div>
      </div>

      {/* Creator & Identity Profile */}
      <div className="bg-[#0B1424] border border-cyan-500/30 rounded-2xl p-4 md:p-5">
        <div className="flex items-center gap-2 border-b border-cyan-500/20 pb-2.5 mb-4">
          <User className="w-5 h-5 text-[#00FF88]" />
          <h3 className="text-sm font-bold font-orbitron text-emerald-300 tracking-wider">
            CREATOR & IDENTITY MATRIX
          </h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 font-mono text-xs">
          <div className="p-3 rounded-xl bg-[#070D18] border border-cyan-500/20">
            <span className="text-cyan-400/60 block text-[10px] uppercase">Owner & Creator</span>
            <span className="text-white font-bold text-sm">Muhammad Fayas (Fayas)</span>
          </div>

          <div className="p-3 rounded-xl bg-[#070D18] border border-cyan-500/20">
            <span className="text-cyan-400/60 block text-[10px] uppercase">Origin Location</span>
            <span className="text-white font-bold text-sm">Kaipamangalam, Thrissur, Kerala</span>
          </div>

          <div className="p-3 rounded-xl bg-[#070D18] border border-cyan-500/20">
            <span className="text-cyan-400/60 block text-[10px] uppercase">Date of Birth</span>
            <span className="text-white font-bold text-sm">21 March 2010</span>
          </div>

          <div className="p-3 rounded-xl bg-[#070D18] border border-cyan-500/20">
            <span className="text-cyan-400/60 block text-[10px] uppercase">System Architecture</span>
            <span className="text-white font-bold text-sm">JARVIS Mark VII Neural Core</span>
          </div>

          <div className="p-3 rounded-xl bg-[#070D18] border border-cyan-500/20">
            <span className="text-cyan-400/60 block text-[10px] uppercase">Languages Supported</span>
            <span className="text-white font-bold text-sm">English, Malayalam, Manglish</span>
          </div>

          <div className="p-3 rounded-xl bg-[#070D18] border border-cyan-500/20">
            <span className="text-cyan-400/60 block text-[10px] uppercase">Device Protocols</span>
            <span className="text-white font-bold text-sm">WebSocket Relay & STT/TTS</span>
          </div>
        </div>
      </div>
    </div>
  );
};
