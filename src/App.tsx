import React, { useState, useEffect, useRef } from 'react';
import { Navbar } from './components/Navbar';
import { VoiceAssistantView } from './components/VoiceAssistantView';
import { RemoteTrackpadView } from './components/RemoteTrackpadView';
import { DiagnosticsView } from './components/DiagnosticsView';
import { SettingsView } from './components/SettingsView';
import { ActiveTab, AssistantState, RelayStatus, LogEntry, VoiceSettings } from './types';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<ActiveTab>('arc-reactor');
  const [assistantState, setAssistantState] = useState<AssistantState>('connecting');
  const [isAudioMuted, setIsAudioMuted] = useState<boolean>(false);
  const [relayStatus, setRelayStatus] = useState<RelayStatus | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [voiceSettings, setVoiceSettings] = useState<VoiceSettings>({
    pitch: 1.0,
    rate: 1.05,
    autoListen: false,
    language: 'en',
    voiceURI: '',
  });

  const wsRef = useRef<WebSocket | null>(null);

  const addLog = (type: LogEntry['type'], message: string, payload?: any) => {
    const newEntry: LogEntry = {
      id: Math.random().toString(36).substring(2, 9),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      type,
      message,
      payload,
    };
    setLogs((prev) => [newEntry, ...prev.slice(0, 49)]);
  };

  // Fetch initial relay health status
  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/health');
      if (res.ok) {
        const data = await res.json();
        setRelayStatus(data);
        if (assistantState === 'connecting' || assistantState === 'disconnected') {
          setAssistantState('connected');
        }
      }
    } catch (err) {
      console.warn('Health check failed:', err);
    }
  };

  // Setup WebSocket connection to server (/ws/jarvis)
  useEffect(() => {
    fetchStatus();

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/jarvis`;
    let ws: WebSocket;
    let reconnectTimer: any;

    const connectWs = () => {
      try {
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          setAssistantState('connected');
          addLog('info', 'WebSocket connected to /ws/jarvis');
          ws.send(JSON.stringify({ type: 'register', client: 'web' }));
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'pong') {
              setRelayStatus((prev) =>
                prev
                  ? {
                      ...prev,
                      activePcClients: data.pc_online ? 1 : 0,
                      activeMobileClients: data.mobile_online ? 1 : 0,
                    }
                  : null
              );
            } else if (data.type === 'remote_pc_command') {
              addLog('relay', `Remote command dispatched: ${data.command}`, data);
            } else if (data.type === 'response') {
              addLog('response', `AI Response: ${data.speech}`, data);
            }
          } catch (e) {
            console.warn('Failed to parse incoming WS message:', e);
          }
        };

        ws.onclose = () => {
          addLog('error', 'WebSocket disconnected. Reconnecting in 3s...');
          reconnectTimer = setTimeout(connectWs, 3000);
        };

        ws.onerror = () => {
          ws.close();
        };

        wsRef.current = ws;
      } catch (err) {
        reconnectTimer = setTimeout(connectWs, 3000);
      }
    };

    connectWs();

    return () => {
      clearTimeout(reconnectTimer);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  // Action dispatcher to relay commands
  const handleExecutePcAction = async (command: string, target?: string | null) => {
    addLog('command', `Dispatched PC Action: ${command} ${target ? `(Target: ${target})` : ''}`);

    const payload = {
      type: 'remote_pc_command',
      command,
      target: target || null,
      from: 'web_client',
      timestamp: Date.now(),
    };

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(payload));
    } else {
      // Fallback to REST endpoint
      try {
        await fetch('/api/remote-command', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
      } catch (e) {
        console.warn('Failed to send remote command via REST fallback:', e);
      }
    }
  };

  const testVoice = () => {
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      window.speechSynthesis.cancel();
      const testUtterance = new SpeechSynthesisUtterance(
        'Jarvis Mark VII voice synthesis active. All systems operating within normal parameters, Sir.'
      );
      testUtterance.pitch = voiceSettings.pitch;
      testUtterance.rate = voiceSettings.rate;
      if (voiceSettings.voiceURI) {
        const voices = window.speechSynthesis.getVoices();
        const v = voices.find((x) => x.voiceURI === voiceSettings.voiceURI);
        if (v) testUtterance.voice = v;
      }
      window.speechSynthesis.speak(testUtterance);
    }
  };

  return (
    <div className="min-h-screen bg-[#070B12] text-white flex flex-col selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* HUD Navigation Header */}
      <Navbar
        currentTab={currentTab}
        onTabChange={setCurrentTab}
        state={assistantState}
        isAudioMuted={isAudioMuted}
        onToggleMute={() => setIsAudioMuted((prev) => !prev)}
      />

      {/* Main Tab Content */}
      <main className="flex-1 flex flex-col justify-center">
        {currentTab === 'arc-reactor' && (
          <VoiceAssistantView
            state={assistantState}
            setState={setAssistantState}
            voiceSettings={voiceSettings}
            isAudioMuted={isAudioMuted}
            onExecutePcAction={handleExecutePcAction}
            onNavigateToRemote={() => setCurrentTab('remote-control')}
          />
        )}

        {currentTab === 'remote-control' && (
          <RemoteTrackpadView onExecuteAction={handleExecutePcAction} />
        )}

        {currentTab === 'diagnostics' && (
          <DiagnosticsView
            relayStatus={relayStatus}
            logs={logs}
            onClearLogs={() => setLogs([])}
            onRefreshStatus={fetchStatus}
          />
        )}

        {currentTab === 'settings' && (
          <SettingsView
            settings={voiceSettings}
            onUpdateSettings={(newVals) =>
              setVoiceSettings((prev) => ({ ...prev, ...newVals }))
            }
            onTestVoice={testVoice}
          />
        )}
      </main>

      {/* Subdued Footer */}
      <footer className="py-2 px-4 border-t border-cyan-500/10 bg-[#040810] text-center text-[10px] font-mono text-cyan-400/40">
        JARVIS MARK VII // Engineered by Muhammad Fayas • Autonomous Neural AI & Remote Controller
      </footer>
    </div>
  );
};

export default App;
