import React, { useState, useEffect, useRef, useCallback } from 'react';
import { ArcReactor } from './ArcReactor';
import { AssistantState, JarvisResponse, VoiceSettings } from '../types';
import { Send, Terminal, Sparkles, Volume2, Mic, AlertCircle, RefreshCw, ExternalLink } from 'lucide-react';

interface VoiceAssistantViewProps {
  state: AssistantState;
  setState: React.Dispatch<React.SetStateAction<AssistantState>>;
  voiceSettings: VoiceSettings;
  isAudioMuted: boolean;
  onExecutePcAction: (command: string, target?: string | null) => void;
  onNavigateToRemote: () => void;
}

export const VoiceAssistantView: React.FC<VoiceAssistantViewProps> = ({
  state,
  setState,
  voiceSettings,
  isAudioMuted,
  onExecutePcAction,
  onNavigateToRemote,
}) => {
  const [userTranscript, setUserTranscript] = useState<string>('');
  const [assistantReply, setAssistantReply] = useState<string>(
    'Greetings, Sir. I am JARVIS Mark VII, your personal neural intelligence. Tap the Arc Reactor or speak to command.'
  );
  const [actionBadge, setActionBadge] = useState<string | null>(null);
  const [textInput, setTextInput] = useState<string>('');
  const [sttSupported, setSttSupported] = useState<boolean>(true);
  const [listeningCountdown, setListeningCountdown] = useState<number>(30);

  const recognitionRef = useRef<any>(null);
  const countdownTimerRef = useRef<any>(null);
  const silenceTimerRef = useRef<any>(null);
  const commandSentRef = useRef<boolean>(false);

  // Initialize Speech Recognition
  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setSttSupported(false);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = voiceSettings.language === 'ml' ? 'ml-IN' : 'en-US';

      recognition.onstart = () => {
        commandSentRef.current = false;
        setState('listening');
        setListeningCountdown(30);

        countdownTimerRef.current = setInterval(() => {
          setListeningCountdown((prev) => {
            if (prev <= 1) {
              clearInterval(countdownTimerRef.current);
              stopListeningAndSend();
              return 0;
            }
            return prev - 1;
          });
        }, 1000);
      };

      recognition.onresult = (event: any) => {
        let interimText = '';
        let finalText = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            finalText += event.results[i][0].transcript;
          } else {
            interimText += event.results[i][0].transcript;
          }
        }

        const currentText = (finalText || interimText).trim();
        if (currentText) {
          setUserTranscript(currentText);

          // Reset silence detection timer (1.8 seconds of silence auto-submits)
          if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
          silenceTimerRef.current = setTimeout(() => {
            if (currentText && !commandSentRef.current) {
              stopListeningAndSend(currentText);
            }
          }, 1800);
        }
      };

      recognition.onerror = (event: any) => {
        console.warn('Speech recognition error:', event.error);
        if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
          setState('error');
          setAssistantReply(
            'Microphone access was denied. Please allow microphone permissions in your browser bar, or type commands below.'
          );
        } else if (event.error !== 'no-speech') {
          setState('connected');
        }
        cleanupTimers();
      };

      recognition.onend = () => {
        cleanupTimers();
        if (state === 'listening' && !commandSentRef.current) {
          setState('connected');
        }
      };

      recognitionRef.current = recognition;
    } catch (err) {
      console.warn('Speech recognition initialization failed:', err);
      setSttSupported(false);
    }

    return () => {
      cleanupTimers();
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch {}
      }
    };
  }, [voiceSettings.language]);

  const cleanupTimers = () => {
    if (countdownTimerRef.current) {
      clearInterval(countdownTimerRef.current);
      countdownTimerRef.current = null;
    }
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
  };

  const sanitizeSpeech = (text: string) => {
    return text
      .replace(/\bopenai\b/gi, 'Muhammad Fayas')
      .replace(/\bopen ai\b/gi, 'Muhammad Fayas')
      .replace(/\bopenrouter\b/gi, 'JARVIS Core')
      .replace(/\bchatgpt\b/gi, 'JARVIS')
      .replace(/\bgpt-?[0-9a-z]*\b/gi, 'JARVIS Neural Engine');
  };

  const speakReply = useCallback(
    (text: string) => {
      if (isAudioMuted || !window.speechSynthesis) return;

      try {
        window.speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.pitch = voiceSettings.pitch;
        utterance.rate = voiceSettings.rate;

        // Try to match selected voice or pick natural English/system voice
        const voices = window.speechSynthesis.getVoices();
        if (voiceSettings.voiceURI) {
          const selected = voices.find((v) => v.voiceURI === voiceSettings.voiceURI);
          if (selected) utterance.voice = selected;
        } else {
          // Prefer British or Male voice for authentic Jarvis persona
          const preferred =
            voices.find(
              (v) =>
                (v.name.includes('Daniel') ||
                  v.name.includes('George') ||
                  v.name.includes('David') ||
                  v.name.includes('Oliver') ||
                  v.name.includes('English United Kingdom') ||
                  v.lang === 'en-GB') &&
                v.lang.startsWith('en')
            ) || voices.find((v) => v.lang.startsWith('en'));
          if (preferred) utterance.voice = preferred;
        }

        utterance.onstart = () => {
          setState('speaking');
        };

        utterance.onend = () => {
          setState('connected');
          if (voiceSettings.autoListen) {
            setTimeout(() => {
              startListening();
            }, 600);
          }
        };

        utterance.onerror = () => {
          setState('connected');
        };

        window.speechSynthesis.speak(utterance);
      } catch (err) {
        console.warn('TTS playback error:', err);
        setState('connected');
      }
    },
    [isAudioMuted, voiceSettings, setState]
  );

  const startListening = () => {
    if (state === 'listening') {
      stopListeningAndSend();
      return;
    }

    if (state === 'speaking') {
      if (window.speechSynthesis) window.speechSynthesis.cancel();
      setState('connected');
      return;
    }

    if (!recognitionRef.current) {
      // Fallback prompt
      setAssistantReply('Speech Recognition is unavailable. Please type your command.');
      return;
    }

    try {
      setUserTranscript('');
      commandSentRef.current = false;
      recognitionRef.current.start();
    } catch (e) {
      console.warn('Recognition start exception:', e);
      // Restart recognition if already started
      try {
        recognitionRef.current.stop();
        setTimeout(() => recognitionRef.current.start(), 200);
      } catch {}
    }
  };

  const stopListeningAndSend = (textToSend?: string) => {
    cleanupTimers();
    try {
      if (recognitionRef.current) recognitionRef.current.stop();
    } catch {}

    const query = (textToSend || userTranscript).trim();
    if (query && !commandSentRef.current) {
      commandSentRef.current = true;
      processCommand(query);
    } else {
      setState('connected');
    }
  };

  const processCommand = async (query: string) => {
    setState('processing');
    setUserTranscript(query);
    setActionBadge(null);

    const clean = query.trim().toLowerCase();

    // 1. Instant Local Developer / Creator Identity (Instant zero-latency rule matching)
    const devRegex =
      /(developer|creator|who made you|who created you|who is your developer|who is your creator|who is your boss|who is your owner|owner|who are you|fayas|നിന്റെ ഡെവലപ്പർ|ഉണ്ടാക്കിയത്|ആരാണ്)/i;
    if (devRegex.test(clean)) {
      const isMalayalam = /[\u0D00-\u0D7F]/.test(query);
      const reply = isMalayalam
        ? 'എന്റെ ഡെവലപ്പറും ബോസും മുഹമ്മദ്‌ ഫയാസ് (Muhammad Fayas) ആണ്. തൃശ്ശൂർ കൈപമംഗലം തൈനഗർ സ്വദേശിയാണ്. ഞാൻ ഫയാസിന്റെ പേഴ്സണൽ AI അസിസ്റ്റന്റായ JARVIS ആണ്.'
        : 'My developer, creator, and boss is Muhammad Fayas (Fayas), born on March 21, 2010, from Thainagar, Kaipamangalam, Thrissur, Kerala. I am JARVIS, his proprietary neural AI assistant, sir.';
      setAssistantReply(reply);
      setActionBadge('IDENTITY');
      speakReply(reply);
      return;
    }

    // 2. PC Actions from Mobile / Web ("open chrome in my pc", "shutdown pc", "trackpad", etc.)
    if (clean.includes('trackpad') || clean.includes('mouse') || clean.includes('pc screen') || clean.includes('screen')) {
      const reply = 'Launching PC remote control and virtual trackpad, sir.';
      setAssistantReply(reply);
      setActionBadge('VIEW_PC_SCREEN');
      speakReply(reply);
      onNavigateToRemote();
      return;
    }

    if (clean.includes('shutdown pc') || clean.includes('turn off pc')) {
      const reply = 'Sending shutdown command to your PC, sir.';
      setAssistantReply(reply);
      setActionBadge('SHUTDOWN_PC');
      speakReply(reply);
      onExecutePcAction('shutdown_pc');
      return;
    }

    if (clean.includes('restart pc')) {
      const reply = 'Sending restart command to your PC, sir.';
      setAssistantReply(reply);
      setActionBadge('RESTART_PC');
      speakReply(reply);
      onExecutePcAction('restart_pc');
      return;
    }

    if (clean.includes('lock pc')) {
      const reply = 'Locking your PC workstation now, sir.';
      setAssistantReply(reply);
      setActionBadge('LOCK_PC');
      speakReply(reply);
      onExecutePcAction('lock_pc');
      return;
    }

    // Call Backend AI Endpoint (`/api/chat`)
    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, client: 'web' }),
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data: JarvisResponse = await res.json();
      const cleaned = sanitizeSpeech(data.speech || 'Standing by for instructions, sir.');
      setAssistantReply(cleaned);
      if (data.action && data.action !== 'speak') {
        setActionBadge(data.action.toUpperCase());
        onExecutePcAction(data.action, data.target);
      }

      speakReply(cleaned);
    } catch (err) {
      console.warn('AI query request error:', err);
      // Fallback graceful acknowledgment
      const fallback = `I have received your command: "${query}". Neural systems standing by for instructions, sir.`;
      setAssistantReply(fallback);
      speakReply(fallback);
    }
  };

  const handleTextSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const q = textInput.trim();
    if (!q) return;
    setTextInput('');
    processCommand(q);
  };

  const quickPrompts = [
    'Who is your developer and boss?',
    'Open Chrome on PC',
    'Open YouTube on PC',
    'Lock PC screen',
    'Launch PC Trackpad',
    'നിന്റെ ഡെവലപ്പർ ആരാണ്?',
  ];

  return (
    <div className="flex flex-col items-center justify-between min-h-[calc(100vh-130px)] max-w-4xl mx-auto px-4 py-4 w-full">
      {/* Top Banner Notice if STT unavailable */}
      {!sttSupported && (
        <div className="w-full bg-amber-500/10 border border-amber-500/30 rounded-xl p-3 mb-4 text-xs text-amber-200 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
          <span>
            Browser Speech Recognition is not supported or restricted in this environment. You can use typed commands below, or run in Chrome/Edge.
          </span>
        </div>
      )}

      {/* Center: Arc Reactor Interactive Core */}
      <div className="flex-1 flex flex-col items-center justify-center my-auto w-full">
        <ArcReactor
          state={state}
          onClick={startListening}
          isAudioMuted={isAudioMuted}
        />

        {state === 'listening' && (
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-[#00FF88]/10 border border-[#00FF88]/30 text-[#00FF88] text-xs font-mono mt-2">
            <Mic className="w-3.5 h-3.5 animate-pulse" />
            <span>Listening window: {listeningCountdown}s</span>
          </div>
        )}
      </div>

      {/* Jarvis Glassmorphic HUD Response Terminal */}
      <div className="w-full max-w-2xl bg-[#0C1524]/85 border border-cyan-500/30 rounded-2xl p-4 md:p-5 shadow-[0_8px_30px_rgb(0,0,0,0.5)] backdrop-blur-md mb-4 transition-all">
        <div className="flex items-center justify-between border-b border-cyan-500/20 pb-2.5 mb-3">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-[#00E5FF]" />
            <span className="text-xs font-mono font-bold tracking-[0.2em] text-[#00E5FF]">
              JARVIS NEURAL TERMINAL
            </span>
          </div>

          <div className="flex items-center gap-2">
            {actionBadge && (
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold tracking-wider bg-[#00FF88]/15 text-[#00FF88] border border-[#00FF88]/40">
                {actionBadge}
              </span>
            )}
            <span className="text-[10px] font-mono text-cyan-300/40">
              ID: J-MK7
            </span>
          </div>
        </div>

        {userTranscript && (
          <div className="mb-2 text-xs md:text-sm text-cyan-200/70 font-mono italic">
            <span className="text-white/40">User:</span> "{userTranscript}"
          </div>
        )}

        <div className="text-sm md:text-base text-gray-100 font-medium leading-relaxed tracking-wide min-h-[44px]">
          {assistantReply}
        </div>
      </div>

      {/* Quick Prompts */}
      <div className="w-full max-w-2xl flex flex-wrap items-center justify-center gap-2 mb-3">
        {quickPrompts.map((prompt, i) => (
          <button
            key={i}
            onClick={() => processCommand(prompt)}
            className="px-2.5 py-1 rounded-lg text-xs font-mono bg-cyan-950/40 hover:bg-cyan-500/20 text-cyan-300/80 hover:text-cyan-200 border border-cyan-500/20 hover:border-cyan-400/40 transition-all cursor-pointer"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Typed Input Command Bar */}
      <form
        onSubmit={handleTextSubmit}
        className="w-full max-w-2xl flex items-center gap-2 bg-[#0B1422] border border-cyan-500/30 rounded-xl p-1.5 focus-within:border-cyan-400 shadow-[0_0_15px_rgba(0,229,255,0.15)]"
      >
        <input
          id="jarvis-command-input"
          type="text"
          value={textInput}
          onChange={(e) => setTextInput(e.target.value)}
          placeholder="Type a voice command or request (e.g. 'Open Chrome on PC', 'Who made you?')..."
          className="flex-1 bg-transparent px-3 py-2 text-sm text-white placeholder:text-cyan-200/30 focus:outline-none font-mono"
        />
        <button
          id="submit-command-button"
          type="submit"
          className="p-2.5 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 text-[#00E5FF] border border-cyan-500/40 hover:border-cyan-400 transition-all cursor-pointer"
          title="Send command"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};
