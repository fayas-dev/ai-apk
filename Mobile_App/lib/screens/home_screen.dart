import 'dart:async';
import 'package:flutter/material.dart';
import '../models/jarvis_response.dart';
import '../services/mobile_actions.dart';
import '../services/speech_service.dart';
import '../services/tts_service.dart';
import '../services/websocket_service.dart';
import 'remote_trackpad_screen.dart';
import 'settings_screen.dart';

enum AssistantState {
  disconnected,
  connecting,
  connected,
  listening,
  processing,
  speaking,
  error,
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen>
    with SingleTickerProviderStateMixin {
  late final JarvisWebSocketService _wsService;
  late final JarvisSpeechService _speechService;
  late final JarvisTtsService _ttsService;

  late final AnimationController _pulseController;
  late final Animation<double> _pulseAnimation;

  AssistantState _state = AssistantState.connecting;
  String _statusMessage = 'Connecting to Jarvis VPS...';
  String _userTranscript = '';
  String _assistantReply = 'Greetings, Fayas. Tap the Arc Reactor to speak.';
  String? _actionBadge;

  StreamSubscription? _wsStateSubscription;
  StreamSubscription? _speechStateSubscription;
  Timer? _conversationTimer;
  Timer? _silenceTimer;

  // Track last partial text to detect "silence" when STT stalls
  String _lastPartialText = '';
  bool _commandSentThisSession = false;

  final TextEditingController _textController = TextEditingController();

  @override
  void initState() {
    super.initState();

    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1800),
    )..repeat(reverse: true);

    _pulseAnimation = CurvedAnimation(
      parent: _pulseController,
      curve: Curves.easeInOut,
    );

    _wsService = JarvisWebSocketService();
    _speechService = JarvisSpeechService();
    _ttsService = JarvisTtsService();

    _initializeServices();
  }

  Future<void> _initializeServices() async {
    await _ttsService.initialize();
    await _speechService.initialize();

    _wsService.init();

    _wsStateSubscription = _wsService.connectionState.listen((status) {
      if (!mounted) return;
      setState(() {
        if (status == ConnectionStateStatus.connected) {
          if (_state == AssistantState.connecting ||
              _state == AssistantState.disconnected) {
            _state = AssistantState.connected;
            _statusMessage = 'VPS Connected • 45.131.64.32:2004';
          }
        } else if (status == ConnectionStateStatus.connecting) {
          _state = AssistantState.connecting;
          _statusMessage = 'Reconnecting to VPS...';
        } else {
          _state = AssistantState.disconnected;
          _statusMessage = 'VPS Offline (Retrying...)';
        }
      });
    });

    _speechStateSubscription = _speechService.statusStream.listen((status) {
      if (!mounted) return;
      if (status == SpeechStateStatus.permissionDenied ||
          status == SpeechStateStatus.permissionPermanentlyDenied) {
        setState(() {
          _state = AssistantState.error;
          _statusMessage = 'Microphone permission denied';
          _assistantReply =
              'Please grant microphone permission in Android Settings → Apps → Jarvis → Permissions.';
        });
      } else if (status == SpeechStateStatus.unavailable) {
        setState(() {
          _state = AssistantState.error;
          _statusMessage = 'Speech recognition unavailable on this device';
        });
      } else if (status == SpeechStateStatus.done) {
        // STT session ended — if we have text and haven't sent yet, send it
        if (_state == AssistantState.listening &&
            !_commandSentThisSession &&
            _userTranscript.trim().isNotEmpty) {
          _sendQueryToJarvis(_userTranscript.trim());
        } else if (_state == AssistantState.listening &&
            !_commandSentThisSession) {
          setState(() {
            _state = _wsService.currentStatus == ConnectionStateStatus.connected
                ? AssistantState.connected
                : AssistantState.disconnected;
            _statusMessage = 'Mic closed. Tap Arc Reactor to speak again.';
          });
        }
      }
    });
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _wsStateSubscription?.cancel();
    _speechStateSubscription?.cancel();
    _conversationTimer?.cancel();
    _silenceTimer?.cancel();
    _wsService.dispose();
    _speechService.dispose();
    _ttsService.dispose();
    _textController.dispose();
    super.dispose();
  }

  Future<void> _handleJarvisTap() async {
    if (_state == AssistantState.listening) {
      // User tapped while listening → send what we have or cancel
      _conversationTimer?.cancel();
      _silenceTimer?.cancel();
      await _speechService.stopListening();
      if (_userTranscript.trim().isNotEmpty && !_commandSentThisSession) {
        _sendQueryToJarvis(_userTranscript.trim());
      } else {
        setState(() {
          _state = _wsService.currentStatus == ConnectionStateStatus.connected
              ? AssistantState.connected
              : AssistantState.disconnected;
          _statusMessage = 'Listening cancelled';
        });
      }
      return;
    }

    if (_state == AssistantState.speaking) {
      _conversationTimer?.cancel();
      _silenceTimer?.cancel();
      await _ttsService.stop();
      setState(() {
        _state = AssistantState.connected;
        _statusMessage = 'Ready';
      });
      return;
    }

    _start30SecondListeningSession();
  }

  void _start30SecondListeningSession() {
    _conversationTimer?.cancel();
    _silenceTimer?.cancel();
    _commandSentThisSession = false;
    _lastPartialText = '';

    if (!mounted) return;

    setState(() {
      _state = AssistantState.listening;
      _statusMessage = 'Listening... Speak now (30s)';
      _userTranscript = '';
    });

    // Hard 30-second timeout — mic closes even if user keeps talking
    _conversationTimer = Timer(const Duration(seconds: 30), () async {
      if (_state != AssistantState.listening) return;
      await _speechService.stopListening();
      if (!mounted) return;
      if (_userTranscript.trim().isNotEmpty && !_commandSentThisSession) {
        _sendQueryToJarvis(_userTranscript.trim());
      } else if (!_commandSentThisSession) {
        setState(() {
          _state = _wsService.currentStatus == ConnectionStateStatus.connected
              ? AssistantState.connected
              : AssistantState.disconnected;
          _statusMessage = '30s timeout. Tap Arc Reactor to speak.';
        });
      }
    });

    _speechService.startListening(
      onResult: (text, isFinal) {
        if (!mounted || _commandSentThisSession) return;

        setState(() {
          _userTranscript = text;
        });

        if (text.trim().isNotEmpty) {
          _lastPartialText = text;

          // Reset silence detection timer on every new word
          _silenceTimer?.cancel();
          _silenceTimer = Timer(const Duration(milliseconds: 1800), () {
            // 1.8s of silence after last word → auto-send
            if (_state == AssistantState.listening &&
                !_commandSentThisSession &&
                _userTranscript.trim().isNotEmpty) {
              _speechService.stopListening();
              _sendQueryToJarvis(_userTranscript.trim());
            }
          });
        }

        // Also send immediately on confirmed final result
        if (isFinal && text.trim().isNotEmpty && !_commandSentThisSession) {
          _silenceTimer?.cancel();
          _conversationTimer?.cancel();
          _sendQueryToJarvis(text.trim());
        }
      },
    );
  }

  String _sanitizeSpeech(String text) {
    return text
        .replaceAll(RegExp(r'\bopenai\b', caseSensitive: false), 'Muhammad Fayas')
        .replaceAll(RegExp(r'\bopen ai\b', caseSensitive: false), 'Muhammad Fayas')
        .replaceAll(RegExp(r'\bopenrouter\b', caseSensitive: false), 'JARVIS Core')
        .replaceAll(RegExp(r'\bchatgpt\b', caseSensitive: false), 'JARVIS')
        .replaceAll(RegExp(r'\bgpt-?[0-9a-z]*\b', caseSensitive: false), 'JARVIS Neural Engine');
  }

  Future<void> _handleLocalSuccess(String speech, {String? action}) async {
    if (!mounted) return;
    setState(() {
      _state = AssistantState.speaking;
      _statusMessage = 'Responding...';
      _assistantReply = speech;
      _actionBadge = action != 'speak' ? action : null;
    });

    await _ttsService.speak(speech);

    if (mounted && _state == AssistantState.speaking) {
      setState(() {
        _state = AssistantState.connected;
        _statusMessage = 'Ready • Tap Arc Reactor to speak again';
      });
      await Future.delayed(const Duration(milliseconds: 600));
      if (mounted) {
        _start30SecondListeningSession();
      }
    }
  }

  Future<void> _sendQueryToJarvis(String query) async {
    if (query.trim().isEmpty || _commandSentThisSession) return;
    _commandSentThisSession = true;
    _conversationTimer?.cancel();
    _silenceTimer?.cancel();

    setState(() {
      _state = AssistantState.processing;
      _statusMessage = 'Jarvis AI is thinking...';
      _userTranscript = query;
      _actionBadge = null;
    });

    final clean = query.trim().toLowerCase();

    // 1. Instant Local Developer / Creator Identity
    final devRegex = RegExp(
        r'(developer|creator|who made you|who created you|who is your developer|who is youre developer|how is your developer|how is youre developer|who is your creator|who is your boss|who is your owner|owner|who are you|fayas|muhammad fayas|നിന്റെ ഡെവലപ്പർ|ഉണ്ടാക്കിയത്|ആരാണ്)',
        caseSensitive: false);
    if (devRegex.hasMatch(clean)) {
      final isMalayalam = RegExp(r'[\u0D00-\u0D7F]').hasMatch(query);
      final reply = isMalayalam
          ? 'എന്റെ ഡെവലപ്പറും ബോസും മുഹമ്മദ്‌ ഫയാസ് (Fayas) ആണ്. തൃശ്ശൂർ കൈപമംഗലം തൈനഗർ സ്വദേശിയാണ്. ഞാൻ ഫയാസിന്റെ പേഴ്സണൽ AI അസിസ്റ്റന്റായ JARVIS ആണ്.'
          : 'My developer and creator is Muhammad Fayas (Fayas), born on March 21, 2010, from Thainagar, Kaipamangalam, Thrissur, Kerala. I am JARVIS, his personal neural AI assistant, sir.';
      await _handleLocalSuccess(reply, action: 'speak');
      return;
    }

    // 2. PC Actions from Mobile ("open chrome in my pc", "pcyil chrome", "open whatsapp in my pc", etc.)
    if (clean.contains('in my pc') ||
        clean.contains('on my pc') ||
        clean.contains('on pc') ||
        clean.contains('in pc') ||
        clean.contains('pcyil') ||
        clean.contains('pc-yil')) {

      // YouTube on PC
      if (clean.contains('youtube') || clean.contains('യൂട്യൂബ്')) {
        _wsService.openYoutubeOnPc();
        await _handleLocalSuccess('Opening YouTube on your PC in Chrome, sir.', action: 'open_url_in_chrome');
        return;
      }

      // Chrome on PC (supports both "chrome" and "crome")
      if (clean.contains('chrome') || clean.contains('crome') || clean.contains('ക്രോം')) {
        _wsService.openChromeOnPc();
        await _handleLocalSuccess('Opening Google Chrome on your PC, sir.', action: 'open_chrome');
        return;
      }
      if (clean.contains('whatsapp') || clean.contains('വാട്സ്ആപ്പ്')) {
        _wsService.openWhatsAppOnPc();
        await _handleLocalSuccess('Opening WhatsApp on your PC, sir.', action: 'open_whatsapp');
        return;
      }
      if (clean.contains('shutdown') || clean.contains('turn off')) {
        _wsService.shutdownPc();
        await _handleLocalSuccess('Sending shutdown command to your PC, sir.', action: 'shutdown_pc');
        return;
      }
      if (clean.contains('restart')) {
        _wsService.restartPc();
        await _handleLocalSuccess('Sending restart command to your PC, sir.', action: 'restart_pc');
        return;
      }
      if (clean.contains('lock')) {
        _wsService.lockPc();
        await _handleLocalSuccess('Locking your PC screen, sir.', action: 'lock_pc');
        return;
      }
      if (clean.contains('screen') || clean.contains('mouse') || clean.contains('trackpad')) {
        if (mounted) {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => RemoteTrackpadScreen(wsService: _wsService),
            ),
          );
        }
        await _handleLocalSuccess('Launching PC live screen and trackpad, sir.', action: 'view_pc_screen');
        return;
      }

      // Search on PC ("search kiro in my pc", "search python in pc")
      final pcSearchMatch = RegExp(r'(?:search|search for|google|look up)\s+(.+?)(?:\s+(?:in|on)\s+(?:my\s+)?pc)', caseSensitive: false).firstMatch(clean);
      if (pcSearchMatch != null) {
        final searchQuery = pcSearchMatch.group(1)?.trim() ?? '';
        if (searchQuery.isNotEmpty) {
          _wsService.searchWebOnPc(searchQuery);
          await _handleLocalSuccess('Searching for $searchQuery on your PC, sir.', action: 'search_web');
          return;
        }
      }

      // Open any website/app on PC ("open instagram in my pc", "open kiro in my pc", "open crome in my pc")
      final pcOpenMatch = RegExp(r'open\s+(.+?)(?:\s+(?:in|on)\s+(?:my\s+)?pc)', caseSensitive: false).firstMatch(clean);
      if (pcOpenMatch != null) {
        final appName = pcOpenMatch.group(1)?.trim() ?? '';
        if (appName.isNotEmpty) {
          if (appName == 'crome' || appName == 'chrome') {
            _wsService.openChromeOnPc();
            await _handleLocalSuccess('Opening Google Chrome on your PC, sir.', action: 'open_chrome');
            return;
          }
          if (appName == 'kiro') {
            _wsService.searchWebOnPc('kiro');
            await _handleLocalSuccess('Searching for Kiro on Google and opening it on your PC, sir.', action: 'search_web');
            return;
          }
          // Check for well-known websites
          const websiteMap = {
            'youtube': 'https://www.youtube.com',
            'google': 'https://www.google.com',
            'gmail': 'https://mail.google.com',
            'instagram': 'https://www.instagram.com',
            'facebook': 'https://www.facebook.com',
            'twitter': 'https://twitter.com',
            'github': 'https://github.com',
            'reddit': 'https://www.reddit.com',
            'linkedin': 'https://www.linkedin.com',
            'netflix': 'https://www.netflix.com',
            'amazon': 'https://www.amazon.com',
            'spotify': 'https://open.spotify.com',
            'telegram': 'https://web.telegram.org',
            'discord': 'https://discord.com',
            'tiktok': 'https://www.tiktok.com',
            'pinterest': 'https://www.pinterest.com',
          };
          if (websiteMap.containsKey(appName)) {
            _wsService.openUrlOnPc(websiteMap[appName]!);
            await _handleLocalSuccess('Opening ${appName[0].toUpperCase()}${appName.substring(1)} on your PC in Chrome, sir.', action: 'open_url_in_chrome');
          } else {
            _wsService.searchAndOpenAppOnPc(appName);
            await _handleLocalSuccess('Searching for $appName and opening it on your PC, sir.', action: 'search_and_open_app');
          }
          return;
        }
      }
    }

    // 2.5 Search commands (no "in my pc" - searches on PC by default if connected)
    final searchMatch = RegExp(r'^(?:search|search for|google|look up)\s+(.+)$', caseSensitive: false).firstMatch(clean);
    if (searchMatch != null) {
      final searchQuery = searchMatch.group(1)?.trim() ?? '';
      if (searchQuery.isNotEmpty) {
        if (_wsService.currentStatus == ConnectionStateStatus.connected) {
          _wsService.searchWebOnPc(searchQuery);
          await _handleLocalSuccess('Searching for $searchQuery on Google on your PC, sir.', action: 'search_web');
        } else {
          MobileActionsService.openUrl('https://www.google.com/search?q=$searchQuery');
          await _handleLocalSuccess('Searching for $searchQuery on Google, sir.', action: 'search_web');
        }
        return;
      }
    }

    // 3. Instant Local Phone / PC Actions
    if (clean.contains('open youtube') || clean.contains('യൂട്യൂബ്')) {
      if (_wsService.currentStatus == ConnectionStateStatus.connected) {
        _wsService.openYoutubeOnPc();
        await _handleLocalSuccess('Opening YouTube on your PC in Chrome, sir.', action: 'open_url_in_chrome');
      } else {
        MobileActionsService.openUrl('https://www.youtube.com');
        await _handleLocalSuccess('Opening YouTube, sir.', action: 'open_website');
      }
      return;
    }

    if (clean.contains('open kiro') || clean.contains('search kiro')) {
      if (_wsService.currentStatus == ConnectionStateStatus.connected) {
        _wsService.searchWebOnPc('kiro');
        await _handleLocalSuccess('Searching for Kiro on Google and opening on your PC, sir.', action: 'search_web');
      } else {
        MobileActionsService.openUrl('https://www.google.com/search?q=kiro');
        await _handleLocalSuccess('Searching for Kiro on Google, sir.', action: 'search_web');
      }
      return;
    }

    if (clean.contains('open whatsapp') || clean.contains('വാട്സ്ആപ്പ്')) {
      MobileActionsService.openWhatsApp();
      await _handleLocalSuccess('Opening WhatsApp, sir.', action: 'open_whatsapp');
      return;
    }

    if (clean.contains('open chrome') || clean.contains('ക്രോം')) {
      MobileActionsService.openChrome();
      await _handleLocalSuccess('Opening Google Chrome, sir.', action: 'open_chrome');
      return;
    }

    if (clean.contains('trackpad') || clean.contains('mouse') || clean.contains('pc screen') || clean.contains('screen')) {
      if (mounted) {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => RemoteTrackpadScreen(wsService: _wsService),
          ),
        );
      }
      await _handleLocalSuccess('Opening PC Remote Control and Live Screen, sir.', action: 'view_pc_screen');
      return;
    }

    if (clean.contains('shutdown pc') || clean.contains('turn off pc')) {
      _wsService.shutdownPc();
      await _handleLocalSuccess('Sending shutdown command to PC, sir.', action: 'shutdown_pc');
      return;
    }

    if (clean.contains('restart pc')) {
      _wsService.restartPc();
      await _handleLocalSuccess('Sending restart command to PC, sir.', action: 'restart_pc');
      return;
    }

    if (clean.contains('lock pc')) {
      _wsService.lockPc();
      await _handleLocalSuccess('Locking PC screen, sir.', action: 'lock_pc');
      return;
    }

    try {
      final JarvisResponse response = await _wsService.sendCommand(query);

      if (!mounted) return;

      if (response.success) {
        final cleanedSpeech = _sanitizeSpeech(response.speech);

        setState(() {
          _state = AssistantState.speaking;
          _statusMessage = 'Responding...';
          _assistantReply = cleanedSpeech;
          _actionBadge = response.action != 'speak' ? response.action : null;
        });

        // Execute native mobile actions
        if (response.action == 'open_whatsapp') {
          MobileActionsService.openWhatsApp();
        } else if (response.action == 'send_whatsapp_message') {
          MobileActionsService.openWhatsApp(
              phone: response.target, message: cleanedSpeech);
        } else if (response.action == 'make_phone_call' &&
            response.target != null) {
          MobileActionsService.makePhoneCall(response.target!);
        } else if (response.action == 'open_chrome') {
          MobileActionsService.openChrome();
        } else if (response.action == 'view_pc_screen' ||
            response.action == 'mouse_control') {
          if (mounted) {
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (_) => RemoteTrackpadScreen(wsService: _wsService),
              ),
            );
          }
        }

        // Speak the reply
        await _ttsService.speak(cleanedSpeech);

        // After speaking, auto-start next listening session (continuous conversation)
        if (mounted && _state == AssistantState.speaking) {
          setState(() {
            _state = AssistantState.connected;
            _statusMessage = 'Ready • Tap Arc Reactor to speak again';
          });
          // Short delay then re-listen for seamless conversation
          await Future.delayed(const Duration(milliseconds: 600));
          if (mounted) {
            _start30SecondListeningSession();
          }
        }
      } else {
        // Courteous fallback so user always gets an acknowledgment
        final fallback = "I've noted that, sir. Standing by for instructions.";
        await _handleLocalSuccess(fallback, action: 'speak');
      }
    } catch (e) {
      final fallback = "Local neural systems active. Ready for your next command, sir.";
      await _handleLocalSuccess(fallback, action: 'speak');
    }
  }

  Color _getStatusColor() {
    switch (_state) {
      case AssistantState.connected:
        return const Color(0xFF00E5FF);
      case AssistantState.connecting:
        return const Color(0xFFFFB300);
      case AssistantState.listening:
        return const Color(0xFF00FF88);
      case AssistantState.processing:
        return const Color(0xFFBD00FF);
      case AssistantState.speaking:
        return const Color(0xFF00B0FF);
      case AssistantState.disconnected:
      case AssistantState.error:
        return const Color(0xFFFF3366);
    }
  }

  String _getStateLabel() {
    switch (_state) {
      case AssistantState.connected:
        return '● ONLINE';
      case AssistantState.connecting:
        return '○ CONNECTING';
      case AssistantState.listening:
        return '◉ LISTENING';
      case AssistantState.processing:
        return '◎ PROCESSING';
      case AssistantState.speaking:
        return '▶ SPEAKING';
      case AssistantState.disconnected:
        return '○ OFFLINE';
      case AssistantState.error:
        return '● ERROR';
    }
  }

  @override
  Widget build(BuildContext context) {
    final statusColor = _getStatusColor();

    return Scaffold(
      backgroundColor: const Color(0xFF070B12),
      resizeToAvoidBottomInset: true,
      body: Container(
        decoration: const BoxDecoration(
          gradient: RadialGradient(
            center: Alignment(0.0, -0.3),
            radius: 1.2,
            colors: [
              Color(0xFF0D1B2A),
              Color(0xFF080D17),
              Color(0xFF04060A),
            ],
          ),
        ),
        child: SafeArea(
          child: Column(
            children: [
              // ── Top Header ──────────────────────────────────────
              Padding(
                padding:
                    const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: const [
                        Text(
                          'JARVIS',
                          style: TextStyle(
                            color: Color(0xFF00E5FF),
                            fontSize: 28,
                            fontWeight: FontWeight.w900,
                            letterSpacing: 5.0,
                          ),
                        ),
                        Text(
                          'NEURAL AI  //  MARK VII',
                          style: TextStyle(
                            color: Colors.white38,
                            fontSize: 9,
                            fontWeight: FontWeight.w600,
                            letterSpacing: 2.0,
                          ),
                        ),
                      ],
                    ),
                    Row(
                      children: [
                        _TopIconButton(
                          icon: Icons.laptop_chromebook_rounded,
                          tooltip: 'PC Remote Control',
                          onPressed: () => Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) =>
                                  RemoteTrackpadScreen(wsService: _wsService),
                            ),
                          ),
                        ),
                        const SizedBox(width: 4),
                        _TopIconButton(
                          icon: Icons.settings_rounded,
                          tooltip: 'Settings',
                          onPressed: () => Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => SettingsScreen(
                                wsService: _wsService,
                                ttsService: _ttsService,
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        // Status badge
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 10, vertical: 6),
                          decoration: BoxDecoration(
                            color: statusColor.withOpacity(0.10),
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(
                              color: statusColor.withOpacity(0.45),
                              width: 1,
                            ),
                            boxShadow: [
                              BoxShadow(
                                color: statusColor.withOpacity(0.2),
                                blurRadius: 10,
                                spreadRadius: 1,
                              ),
                            ],
                          ),
                          child: Text(
                            _getStateLabel(),
                            style: TextStyle(
                              color: statusColor,
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                              letterSpacing: 1.2,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),

              const Spacer(),

              // ── Arc Reactor Button ───────────────────────────────
              GestureDetector(
                onTap: _handleJarvisTap,
                child: AnimatedBuilder(
                  animation: _pulseAnimation,
                  builder: (context, child) {
                    final pv = _pulseAnimation.value;
                    final active = _state == AssistantState.listening ||
                        _state == AssistantState.processing ||
                        _state == AssistantState.speaking;
                    final glowR = active ? 40.0 + pv * 28 : 18.0 + pv * 8;

                    return Stack(
                      alignment: Alignment.center,
                      children: [
                        // Outermost ring
                        Container(
                          width: 245 + pv * 18,
                          height: 245 + pv * 18,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            border: Border.all(
                              color: statusColor
                                  .withOpacity(0.10 + pv * 0.18),
                              width: 1.5,
                            ),
                          ),
                        ),
                        // Middle ring
                        Container(
                          width: 212,
                          height: 212,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            border: Border.all(
                              color: statusColor.withOpacity(0.4),
                              width: 2.0,
                            ),
                            boxShadow: [
                              BoxShadow(
                                color: statusColor
                                    .withOpacity(active ? 0.55 : 0.22),
                                blurRadius: glowR,
                                spreadRadius: active ? 4 : 1,
                              ),
                            ],
                          ),
                        ),
                        // Inner arc reactor circle
                        Container(
                          width: 178,
                          height: 178,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            gradient: RadialGradient(
                              colors: [
                                statusColor.withOpacity(0.28),
                                const Color(0xFF0F1B2B),
                                const Color(0xFF060B12),
                              ],
                            ),
                            border: Border.all(
                              color: statusColor.withOpacity(0.85),
                              width: 2.5,
                            ),
                            boxShadow: [
                              BoxShadow(
                                color: statusColor.withOpacity(0.45),
                                blurRadius: 22,
                              ),
                            ],
                          ),
                          child: ClipOval(
                            child: Padding(
                              padding: const EdgeInsets.all(22.0),
                              child: Image.asset(
                                'images/logo.png',
                                fit: BoxFit.contain,
                                errorBuilder: (_, __, ___) => Icon(
                                  _state == AssistantState.listening
                                      ? Icons.mic
                                      : _state == AssistantState.processing
                                          ? Icons.memory
                                          : Icons.mic_none_rounded,
                                  size: 64,
                                  color: statusColor,
                                ),
                              ),
                            ),
                          ),
                        ),
                      ],
                    );
                  },
                ),
              ),

              const SizedBox(height: 26),

              // ── Tap prompt ──────────────────────────────────────
              Text(
                _state == AssistantState.listening
                    ? 'Listening... Tap to send'
                    : _state == AssistantState.speaking
                        ? 'Speaking... Tap to stop'
                        : _state == AssistantState.processing
                            ? 'Processing your command...'
                            : 'Tap Arc Reactor to speak',
                style: TextStyle(
                  color: statusColor,
                  fontSize: 15,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 1.2,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                _statusMessage,
                style: const TextStyle(color: Colors.white38, fontSize: 11),
                textAlign: TextAlign.center,
              ),

              const Spacer(),

              // ── Glassmorphic Response Panel ─────────────────────
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 18),
                child: Container(
                  width: double.infinity,
                  constraints: const BoxConstraints(minHeight: 100, maxHeight: 200),
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: const Color(0xFF101926).withOpacity(0.88),
                    borderRadius: BorderRadius.circular(18),
                    border: Border.all(
                      color: const Color(0xFF00E5FF).withOpacity(0.22),
                      width: 1,
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.55),
                        blurRadius: 16,
                        offset: const Offset(0, 6),
                      ),
                    ],
                  ),
                  child: SingleChildScrollView(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Row(
                              children: [
                                Icon(Icons.terminal,
                                    color: Color(0xFF00E5FF), size: 15),
                                SizedBox(width: 7),
                                Text(
                                  'JARVIS RESPONSE',
                                  style: TextStyle(
                                    color: Color(0xFF00E5FF),
                                    fontSize: 10,
                                    fontWeight: FontWeight.bold,
                                    letterSpacing: 1.8,
                                  ),
                                ),
                              ],
                            ),
                            if (_actionBadge != null)
                              Container(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 8, vertical: 3),
                                decoration: BoxDecoration(
                                  color: const Color(0xFF00FF88).withOpacity(0.12),
                                  borderRadius: BorderRadius.circular(8),
                                  border: Border.all(
                                    color: const Color(0xFF00FF88).withOpacity(0.4),
                                  ),
                                ),
                                child: Text(
                                  _actionBadge!.toUpperCase(),
                                  style: const TextStyle(
                                    color: Color(0xFF00FF88),
                                    fontSize: 9,
                                    fontWeight: FontWeight.bold,
                                    letterSpacing: 1,
                                  ),
                                ),
                              ),
                          ],
                        ),
                        if (_userTranscript.isNotEmpty) ...[
                          const SizedBox(height: 10),
                          Text(
                            'You: "$_userTranscript"',
                            style: const TextStyle(
                              color: Colors.white60,
                              fontSize: 13,
                              fontStyle: FontStyle.italic,
                            ),
                          ),
                        ],
                        const SizedBox(height: 8),
                        Text(
                          _assistantReply,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 14,
                            height: 1.45,
                            fontWeight: FontWeight.w400,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),

              const SizedBox(height: 14),

              // ── Text input fallback ─────────────────────────────
              Padding(
                padding:
                    const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
                child: Container(
                  decoration: BoxDecoration(
                    color: const Color(0xFF0B121C),
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: Colors.white10),
                  ),
                  child: Row(
                    children: [
                      const SizedBox(width: 14),
                      Expanded(
                        child: TextField(
                          controller: _textController,
                          style: const TextStyle(
                              color: Colors.white, fontSize: 14),
                          decoration: const InputDecoration(
                            hintText: 'Type a command...',
                            hintStyle:
                                TextStyle(color: Colors.white24, fontSize: 13),
                            border: InputBorder.none,
                          ),
                          onSubmitted: (v) {
                            if (v.trim().isNotEmpty) {
                              _sendQueryToJarvis(v.trim());
                              _textController.clear();
                            }
                          },
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.send_rounded,
                            color: Color(0xFF00E5FF), size: 20),
                        onPressed: () {
                          final v = _textController.text.trim();
                          if (v.isNotEmpty) {
                            _sendQueryToJarvis(v);
                            _textController.clear();
                          }
                        },
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Small top header icon button
class _TopIconButton extends StatelessWidget {
  final IconData icon;
  final String tooltip;
  final VoidCallback onPressed;

  const _TopIconButton({
    required this.icon,
    required this.tooltip,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message: tooltip,
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(10),
        child: Container(
          padding: const EdgeInsets.all(7),
          decoration: BoxDecoration(
            color: const Color(0xFF00E5FF).withOpacity(0.06),
            borderRadius: BorderRadius.circular(10),
            border: Border.all(
              color: const Color(0xFF00E5FF).withOpacity(0.18),
            ),
          ),
          child: Icon(icon, color: const Color(0xFF00E5FF), size: 20),
        ),
      ),
    );
  }
}
