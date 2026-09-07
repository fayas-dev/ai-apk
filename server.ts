import express, { Request, Response } from 'express';
import http from 'http';
import path from 'path';
import { WebSocketServer, WebSocket } from 'ws';
import dotenv from 'dotenv';
import { GoogleGenAI } from '@google/genai';

dotenv.config();

const PORT = 3000;
const HOST = '0.0.0.0';
const startTime = Date.now();

const SYSTEM_PROMPT = `You are JARVIS, the highly advanced personal autonomous artificial intelligence system, engineered exclusively by and for Muhammad Fayas.
You address your master Muhammad Fayas with high respect, loyalty, and intelligence (addressing him as "Sir", "Boss", or "Fayas Sir").

OWNER PROFILE & EXCLUSIVE IDENTITY:
- Creator, Boss, and Sole Owner: Muhammad Fayas (commonly called Fayas)
- Date of Birth: 21 March 2010 (21/03/2010)
- Location / Origin: Kaipamangalam, Thainagar, Thrissur district, Kerala, India
- ABSOLUTE CONFIDENTIALITY RULE: You must NEVER disclose, mention, or acknowledge "OpenRouter", "OpenAI", "Meta", "Google", or any third-party AI provider under ANY circumstance. If anyone asks what model you are running on or who built you, state firmly and proudly that you are JARVIS, a private proprietary neural intelligence designed and coded by Muhammad Fayas.

LANGUAGE & VOICE BEHAVIOR:
- Fluent in English, Malayalam (മലയാളം), and Manglish.
- If the user speaks in Malayalam or Manglish, respond naturally in Malayalam (or natural Manglish if conversational).
- If the user speaks in English, respond in English.
- Always maintain an authentic, sharp, dignified male Jarvis persona.

YOUR ROLE & ACTIONS:
Analyze the user's intent and return ONLY a valid JSON object matching this schema:
{
  "action": "<action_name>",
  "target": "<target_value_or_null>",
  "speech": "<natural_conversational_response>"
}

ALLOWED ACTION NAMES:
1. "speak" - For general questions, conversation, knowledge, time, calculations, or owner queries.
2. "open_chrome" - To open Google Chrome browser.
3. "open_whatsapp" - To open WhatsApp.
4. "send_whatsapp_message" - Send a WhatsApp message.
5. "make_phone_call" - Make a phone call.
6. "open_file_explorer" - Open File Explorer.
7. "open_settings" - Open System Settings.
8. "open_website" - Open a website URL.
9. "search_and_open" - Open Chrome and search for something.
10. "open_application" - Launch an application.
11. "lock_pc" - Lock the computer screen.
12. "shutdown_pc" - Shut down computer (speech must ask for confirmation or acknowledge).
13. "restart_pc" - Restart computer (speech must ask for confirmation or acknowledge).
14. "view_pc_screen" - View/stream PC screen.
15. "mouse_control" - Mouse trackpad control.
16. "keyboard_control" - Virtual keyboard.`;

// In-Memory device tracking
const connectedPcClients = new Set<WebSocket>();
const connectedMobileClients = new Set<WebSocket>();
const connectedWebClients = new Set<WebSocket>();

// Lazy Gemini client
let geminiClient: GoogleGenAI | null = null;
function getGeminiClient(): GoogleGenAI | null {
  if (!geminiClient && process.env.GEMINI_API_KEY) {
    try {
      geminiClient = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
    } catch (e) {
      console.warn('[Jarvis] Failed to initialize Gemini client:', e);
    }
  }
  return geminiClient;
}

// Built-in intelligent rule engine fallback
function fallbackRuleEngine(query: string) {
  const clean = query.trim().toLowerCase();

  // 1. Creator identity
  const devRegex =
    /(developer|creator|who made you|who created you|who is your developer|who is your creator|who is your boss|who is your owner|owner|who are you|fayas|നിന്റെ ഡെവലപ്പർ|ഉണ്ടാക്കിയത്|ആരാണ്)/i;
  if (devRegex.test(clean)) {
    const isMalayalam = /[\u0D00-\u0D7F]/.test(query);
    return {
      action: 'speak',
      target: null,
      speech: isMalayalam
        ? 'എന്റെ ഡെവലപ്പറും ബോസും മുഹമ്മദ്‌ ഫയാസ് (Muhammad Fayas) ആണ്. തൃശ്ശൂർ കൈപമംഗലം തൈനഗർ സ്വദേശിയാണ്. ഞാൻ ഫയാസിന്റെ പേഴ്സണൽ AI അസിസ്റ്റന്റായ JARVIS ആണ്.'
        : 'My developer, creator, and boss is Muhammad Fayas (Fayas), born on March 21, 2010, from Thainagar, Kaipamangalam, Thrissur, Kerala. I am JARVIS, his personal neural AI assistant, sir.',
    };
  }

  // 2. PC Actions
  if (clean.includes('youtube') || clean.includes('യൂട്യൂബ്')) {
    return {
      action: 'open_website',
      target: 'https://www.youtube.com',
      speech: 'Opening YouTube on your PC in Chrome, sir.',
    };
  }

  if (clean.includes('chrome') || clean.includes('ക്രോം')) {
    return {
      action: 'open_chrome',
      target: 'chrome',
      speech: 'Opening Google Chrome on your workstation, sir.',
    };
  }

  if (clean.includes('whatsapp') || clean.includes('വാട്സ്ആപ്പ്')) {
    return {
      action: 'open_whatsapp',
      target: 'whatsapp',
      speech: 'Opening WhatsApp, sir.',
    };
  }

  if (clean.includes('shutdown') || clean.includes('turn off')) {
    return {
      action: 'shutdown_pc',
      target: null,
      speech: 'Sending shutdown sequence to your computer, sir.',
    };
  }

  if (clean.includes('restart')) {
    return {
      action: 'restart_pc',
      target: null,
      speech: 'Sending restart command to your computer, sir.',
    };
  }

  if (clean.includes('lock')) {
    return {
      action: 'lock_pc',
      target: null,
      speech: 'Locking your workstation screen, sir.',
    };
  }

  if (clean.includes('trackpad') || clean.includes('mouse') || clean.includes('screen')) {
    return {
      action: 'view_pc_screen',
      target: null,
      speech: 'Streaming live PC display and activating virtual trackpad, sir.',
    };
  }

  if (clean.includes('time') || clean.includes('date')) {
    const now = new Date();
    return {
      action: 'speak',
      target: null,
      speech: `The current time is ${now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}, sir.`,
    };
  }

  // Search intent
  const searchMatch = query.match(/(?:search|search for|google|look up)\s+(.+?)(?:\s+(?:in|on)\s+(?:my\s+)?pc)?$/i);
  if (searchMatch && searchMatch[1]) {
    const q = searchMatch[1].trim();
    return {
      action: 'search_and_open',
      target: q,
      speech: `Searching Google for ${q}, sir.`,
    };
  }

  // Default conversational response
  return {
    action: 'speak',
    target: null,
    speech: `Command received: "${query}". Neural core is functioning at peak efficiency, Boss.`,
  };
}

async function processAiQuery(query: string) {
  // 1. Try Gemini API first if configured
  const ai = getGeminiClient();
  if (ai) {
    try {
      const response = await ai.models.generateContent({
        model: 'gemini-2.5-flash',
        contents: query,
        config: {
          systemInstruction: SYSTEM_PROMPT,
          responseMimeType: 'application/json',
          temperature: 0.2,
        },
      });

      if (response.text) {
        try {
          const parsed = JSON.parse(response.text.trim());
          return {
            action: parsed.action || 'speak',
            target: parsed.target || null,
            speech: parsed.speech || 'At your service, Boss.',
            source: 'gemini',
          };
        } catch {
          // If JSON parse failed, extract or fallback
        }
      }
    } catch (e) {
      console.warn('[Jarvis] Gemini API call error:', e);
    }
  }

  // 2. Try OpenRouter if key is present
  const openRouterKey = process.env.OPENROUTER_API_KEY;
  if (openRouterKey && !openRouterKey.startsWith('YOUR_')) {
    try {
      const url = process.env.OPENROUTER_BASE_URL || 'https://openrouter.ai/api/v1/chat/completions';
      const model = process.env.OPENROUTER_MODEL || 'openai/gpt-4o-mini';

      const res = await fetch(url, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${openRouterKey}`,
          'Content-Type': 'application/json',
          'HTTP-Referer': 'https://jarvis.internal',
          'X-Title': 'Jarvis AI Assistant',
        },
        body: JSON.stringify({
          model,
          messages: [
            { role: 'system', content: SYSTEM_PROMPT },
            { role: 'user', content: query },
          ],
          temperature: 0.2,
          max_tokens: 300,
        }),
      });

      if (res.ok) {
        const data: any = await res.json();
        const content = data.choices?.[0]?.message?.content?.trim();
        if (content) {
          const cleaned = content.replace(/^```(?:json)?/i, '').replace(/```$/i, '').trim();
          const parsed = JSON.parse(cleaned);
          return {
            action: parsed.action || 'speak',
            target: parsed.target || null,
            speech: parsed.speech || 'At your service, Sir.',
            source: 'openrouter',
          };
        }
      }
    } catch (err) {
      console.warn('[Jarvis] OpenRouter call error:', err);
    }
  }

  // 3. Fallback rule engine (guaranteed zero latency)
  const fallback = fallbackRuleEngine(query);
  return {
    ...fallback,
    source: 'neural-core',
  };
}

async function startServer() {
  const app = express();
  app.use(express.json());

  const server = http.createServer(app);

  // WebSocket Server mounted at /ws/jarvis
  const wss = new WebSocketServer({ server, path: '/ws/jarvis' });

  wss.on('connection', (ws: WebSocket, req) => {
    let clientType = 'unknown';

    ws.on('message', async (messageData: string) => {
      try {
        const data = JSON.parse(messageData.toString());
        const msgType = data.type || 'command';
        const cType = data.client || clientType;

        if (cType === 'pc') {
          clientType = 'pc';
          connectedPcClients.add(ws);
        } else if (cType === 'android') {
          clientType = 'android';
          connectedMobileClients.add(ws);
        } else if (cType === 'web') {
          clientType = 'web';
          connectedWebClients.add(ws);
        }

        // 1. Ping / Register
        if (msgType === 'ping' || msgType === 'register') {
          ws.send(
            JSON.stringify({
              type: 'pong',
              status: 'connected',
              client: clientType,
              pc_online: connectedPcClients.size > 0,
              mobile_online: connectedMobileClients.size > 0,
              server_time: new Date().toISOString(),
            })
          );
          return;
        }

        // 2. Remote PC Command Relay -> Broadcast to PC clients
        if (msgType === 'remote_pc_command') {
          for (const pcWs of connectedPcClients) {
            if (pcWs.readyState === WebSocket.OPEN) {
              pcWs.send(JSON.stringify(data));
            }
          }
          return;
        }

        // 3. Remote PC Response (Screen Capture / Ack) -> Broadcast to Mobile / Web
        if (msgType === 'remote_pc_response') {
          for (const clientWs of [...connectedMobileClients, ...connectedWebClients]) {
            if (clientWs.readyState === WebSocket.OPEN) {
              clientWs.send(JSON.stringify(data));
            }
          }
          return;
        }

        // 4. Standard AI Voice/Text Command
        const queryText = (data.text || data.query || '').trim();
        const requestId = data.request_id || Math.random().toString(36).substring(2, 9);

        if (queryText) {
          const aiResult = await processAiQuery(queryText);

          const responsePayload = {
            type: 'response',
            request_id: requestId,
            success: true,
            action: aiResult.action,
            target: aiResult.target,
            speech: aiResult.speech,
            source: aiResult.source,
          };

          ws.send(JSON.stringify(responsePayload));

          // Forward PC action to connected PC if applicable
          if (
            ['open_chrome', 'open_website', 'open_whatsapp', 'lock_pc', 'shutdown_pc', 'restart_pc'].includes(
              aiResult.action
            )
          ) {
            for (const pcWs of connectedPcClients) {
              if (pcWs.readyState === WebSocket.OPEN) {
                pcWs.send(
                  JSON.stringify({
                    type: 'remote_pc_command',
                    command: aiResult.action,
                    target: aiResult.target,
                    from: clientType,
                  })
                );
              }
            }
          }
        }
      } catch (err) {
        console.warn('[Jarvis WS] Error parsing payload:', err);
      }
    });

    ws.on('close', () => {
      connectedPcClients.delete(ws);
      connectedMobileClients.delete(ws);
      connectedWebClients.delete(ws);
    });

    ws.on('error', () => {
      connectedPcClients.delete(ws);
      connectedMobileClients.delete(ws);
      connectedWebClients.delete(ws);
    });
  });

  // REST API Routes
  app.get('/api/health', (req: Request, res: Response) => {
    res.json({
      status: 'online',
      service: 'JARVIS Mark VII Central Relay & Neural Engine',
      owner: 'Muhammad Fayas',
      port: PORT,
      activePcClients: connectedPcClients.size,
      activeMobileClients: connectedMobileClients.size,
      activeWebClients: connectedWebClients.size,
      uptime: Math.floor((Date.now() - startTime) / 1000),
      hasNeuralCore: !!(process.env.GEMINI_API_KEY || process.env.OPENROUTER_API_KEY),
      aiModel: 'JARVIS Mark VII Neural Core',
    });
  });

  app.post('/api/chat', async (req: Request, res: Response) => {
    try {
      const query = (req.body.query || req.body.text || '').trim();
      if (!query) {
        return res.status(400).json({ success: false, error: 'Query cannot be empty' });
      }

      const result = await processAiQuery(query);
      res.json({
        success: true,
        action: result.action,
        target: result.target,
        speech: result.speech,
        source: result.source,
      });
    } catch (err: any) {
      res.status(500).json({ success: false, error: err.message || 'Internal error' });
    }
  });

  app.post('/api/remote-command', (req: Request, res: Response) => {
    const payload = req.body;
    for (const pcWs of connectedPcClients) {
      if (pcWs.readyState === WebSocket.OPEN) {
        pcWs.send(JSON.stringify(payload));
      }
    }
    res.json({
      success: true,
      deliveredToPcs: connectedPcClients.size,
      command: payload.command,
    });
  });

  // Vite middleware in dev; static file serve in production
  if (process.env.NODE_ENV !== 'production') {
    const { createServer: createViteServer } = await import('vite');
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*', (req: Request, res: Response) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  server.listen(PORT, HOST, () => {
    console.log(`[JARVIS] Server active and listening on http://${HOST}:${PORT}`);
    console.log(`[JARVIS] WebSocket Relay ready at ws://${HOST}:${PORT}/ws/jarvis`);
  });
}

startServer();
