export type AssistantState =
  | 'disconnected'
  | 'connecting'
  | 'connected'
  | 'listening'
  | 'processing'
  | 'speaking'
  | 'error';

export interface JarvisResponse {
  action: string;
  target?: string | null;
  speech: string;
  success: boolean;
  requestId?: string;
  source?: 'gemini' | 'openrouter' | 'neural-core';
}

export type ActiveTab = 'arc-reactor' | 'remote-control' | 'diagnostics' | 'settings';

export interface RelayStatus {
  status: string;
  service: string;
  owner: string;
  port: number;
  activePcClients: number;
  activeMobileClients: number;
  uptime: number;
  hasGemini: boolean;
  hasOpenRouter: boolean;
  aiModel: string;
}

export interface LogEntry {
  id: string;
  timestamp: string;
  type: 'info' | 'command' | 'response' | 'error' | 'relay';
  message: string;
  payload?: any;
}

export interface VoiceSettings {
  pitch: number;
  rate: number;
  autoListen: boolean;
  language: 'en' | 'ml' | 'auto';
  voiceURI: string;
}
