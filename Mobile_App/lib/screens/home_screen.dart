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
  String _assistantReply = 'Greetings. Tap my Arc Reactor to speak.';
  String? _actionBadge;

  StreamSubscription? _wsStateSubscription;
  StreamSubscription? _speechStateSubscription;

  final TextEditingController _textController = TextEditingController();

  @override
  void initState() {
    super.initState();

    // Pulse animation for glowing Arc Reactor / logo
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
            _statusMessage = 'VPS Connected (45.131.64.32:2004)';
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
      if (status == SpeechStateStatus.permissionDenied) {
        setState(() {
          _state = AssistantState.error;
          _statusMessage = 'Microphone permission denied';
          _assistantReply =
              'Please grant microphone permission in device settings.';
        });
      } else if (status == SpeechStateStatus.unavailable) {
        setState(() {
          _state = AssistantState.error;
          _statusMessage = 'Speech recognition unavailable';
        });
      }
    });
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _wsStateSubscription?.cancel();
    _speechStateSubscription?.cancel();
    _conversationTimer?.cancel();
    _wsService.dispose();
    _speechService.dispose();
    _ttsService.dispose();
    _textController.dispose();
    super.dispose();
  }

  Timer? _conversationTimer;

  Future<void> _handleJarvisTap() async {
    if (_state == AssistantState.listening) {
      // User tapped while listening -> cancel or send
      _conversationTimer?.cancel();
      await _speechService.stopListening();
      if (_userTranscript.trim().isNotEmpty) {
        _sendQueryToJarvis(_userTranscript);
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
    if (!mounted) return;

    setState(() {
      _state = AssistantState.listening;
      _statusMessage = 'Active conversation (30s)... Speak freely';
      _userTranscript = '';
    });

    // 30 second conversational timer - if user says nothing within 30s, turn off mic
    _conversationTimer = Timer(const Duration(seconds: 30), () async {
      await _speechService.stopListening();
      if (!mounted) return;
      setState(() {
        _state = _wsService.currentStatus == ConnectionStateStatus.connected
            ? AssistantState.connected
            : AssistantState.disconnected;
        _statusMessage = 'Session closed (30s timeout). Tap Arc Reactor to speak';
      });
    });

    _speechService.startListening(
      onResult: (text, isFinal) {
        if (!mounted) return;
        setState(() {
          _userTranscript = text;
        });
        if (isFinal && text.trim().isNotEmpty) {
          _conversationTimer?.cancel();
          _sendQueryToJarvis(text);
        }
      },
    );
  }

  Future<void> _sendQueryToJarvis(String query) async {
    if (query.trim().isEmpty) return;
    _conversationTimer?.cancel();

    setState(() {
      _state = AssistantState.processing;
      _statusMessage = 'Jarvis AI is thinking...';
      _userTranscript = query;
      _actionBadge = null;
    });

    try {
      final JarvisResponse response = await _wsService.sendCommand(query);

      if (!mounted) return;

      if (response.success) {
        setState(() {
          _state = AssistantState.speaking;
          _statusMessage = 'Responding...';
          _assistantReply = response.speech;
          _actionBadge = response.action != 'speak' ? response.action : null;
        });

        await _ttsService.speak(response.speech);

        // Execute native mobile actions if applicable
        if (response.action == 'open_whatsapp') {
          MobileActionsService.openWhatsApp();
        } else if (response.action == 'send_whatsapp_message') {
          MobileActionsService.openWhatsApp(phone: response.target, message: response.speech);
        } else if (response.action == 'make_phone_call' && response.target != null) {
          MobileActionsService.makePhoneCall(response.target!);
        } else if (response.action == 'open_chrome') {
          MobileActionsService.openChrome();
        } else if (response.action == 'view_pc_screen' || response.action == 'mouse_control') {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => RemoteTrackpadScreen(wsService: _wsService),
            ),
          );
        }

        if (mounted) {
          // Keep microphone active for up to 30s for continuous conversation
          _start30SecondListeningSession();
        }
      } else {
        setState(() {
          _state = AssistantState.error;
          _statusMessage = response.error ?? 'Request failed';
          _assistantReply = response.speech;
        });
      }
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _state = AssistantState.error;
        _statusMessage = 'Error connecting to Jarvis VPS';
        _assistantReply = 'Communication failed. Please check network connection.';
      });
    }
  }

  Color _getStatusColor() {
    switch (_state) {
      case AssistantState.connected:
        return const Color(0xFF00E5FF); // Neon Cyan
      case AssistantState.connecting:
        return const Color(0xFFFFB300); // Amber
      case AssistantState.listening:
        return const Color(0xFF00FF88); // Neon Green
      case AssistantState.processing:
        return const Color(0xFFBD00FF); // Futuristic Purple
      case AssistantState.speaking:
        return const Color(0xFF00B0FF); // Light Blue
      case AssistantState.disconnected:
      case AssistantState.error:
        return const Color(0xFFFF3366); // Neon Red/Pink
    }
  }

  String _getStateLabel() {
    switch (_state) {
      case AssistantState.connected:
        return '● VPS Connected';
      case AssistantState.connecting:
        return '○ Connecting to VPS...';
      case AssistantState.listening:
        return '● Listening...';
      case AssistantState.processing:
        return '● Processing...';
      case AssistantState.speaking:
        return '● Speaking...';
      case AssistantState.disconnected:
        return '○ VPS Disconnected';
      case AssistantState.error:
        return '● Error';
    }
  }

  @override
  Widget build(BuildContext context) {
    final statusColor = _getStatusColor();

    return Scaffold(
      backgroundColor: const Color(0xFF070B12),
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
              // Top Header
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
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
                            fontSize: 26,
                            fontWeight: FontWeight.w900,
                            letterSpacing: 4.0,
                          ),
                        ),
                        Text(
                          'MARK VII // NEURAL AI OS',
                          style: TextStyle(
                            color: Colors.white38,
                            fontSize: 10,
                            fontWeight: FontWeight.w600,
                            letterSpacing: 1.5,
                          ),
                        ),
                      ],
                    ),
                    Row(
                      children: [
                        // Remote PC Trackpad Button
                        IconButton(
                          icon: const Icon(Icons.laptop_chromebook_rounded, color: Color(0xFF00E5FF), size: 22),
                          tooltip: 'PC Remote Control',
                          onPressed: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (_) => RemoteTrackpadScreen(wsService: _wsService),
                              ),
                            );
                          },
                        ),
                        // Settings Button
                        IconButton(
                          icon: const Icon(Icons.settings_rounded, color: Color(0xFF00E5FF), size: 22),
                          tooltip: 'Jarvis Settings',
                          onPressed: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (_) => SettingsScreen(
                                  wsService: _wsService,
                                  ttsService: _ttsService,
                                ),
                              ),
                            );
                          },
                        ),
                        const SizedBox(width: 4),
                        // VPS Status Badge
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                          decoration: BoxDecoration(
                            color: statusColor.withOpacity(0.12),
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(
                              color: statusColor.withOpacity(0.5),
                              width: 1,
                            ),
                            boxShadow: [
                              BoxShadow(
                                color: statusColor.withOpacity(0.25),
                                blurRadius: 10,
                                spreadRadius: 1,
                              ),
                            ],
                          ),
                          child: Text(
                            _getStateLabel(),
                            style: TextStyle(
                              color: statusColor,
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                              letterSpacing: 0.5,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),

              const Spacer(),

              // Glowing Central Jarvis Button / Arc Reactor
              GestureDetector(
                onTap: _handleJarvisTap,
                child: AnimatedBuilder(
                  animation: _pulseAnimation,
                  builder: (context, child) {
                    final pulseValue = _pulseAnimation.value;
                    final activeGlow = _state == AssistantState.listening ||
                        _state == AssistantState.processing ||
                        _state == AssistantState.speaking;
                    final glowRadius = activeGlow ? 40.0 + (pulseValue * 25.0) : 20.0 + (pulseValue * 10.0);

                    return Stack(
                      alignment: Alignment.center,
                      children: [
                        // Outer Pulsing Neon Rings
                        Container(
                          width: 240 + (pulseValue * 15),
                          height: 240 + (pulseValue * 15),
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            border: Border.all(
                              color: statusColor.withValues(alpha: 0.15 + (pulseValue * 0.2)),
                              width: 1.5,
                            ),
                          ),
                        ),
                        Container(
                          width: 210,
                          height: 210,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            border: Border.all(
                              color: statusColor.withOpacity(0.4),
                              width: 2.0,
                            ),
                            boxShadow: [
                              BoxShadow(
                                color: statusColor.withValues(alpha: activeGlow ? 0.6 : 0.25),
                                blurRadius: glowRadius,
                                spreadRadius: activeGlow ? 4 : 1,
                              ),
                            ],
                          ),
                        ),
                        // Inner Button Container with Jarvis Logo
                        Container(
                          width: 175,
                          height: 175,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            gradient: RadialGradient(
                              colors: [
                                statusColor.withOpacity(0.3),
                                const Color(0xFF0F1B2B),
                                const Color(0xFF060B12),
                              ],
                            ),
                            border: Border.all(
                              color: statusColor.withOpacity(0.8),
                              width: 3.0,
                            ),
                            boxShadow: [
                              BoxShadow(
                                color: statusColor.withOpacity(0.5),
                                blurRadius: 20,
                              ),
                            ],
                          ),
                          child: ClipOval(
                            child: Padding(
                              padding: const EdgeInsets.all(22.0),
                              child: Image.asset(
                                'images/logo.png',
                                fit: BoxFit.contain,
                                errorBuilder: (context, error, stackTrace) {
                                  return Icon(
                                    Icons.mic,
                                    size: 60,
                                    color: statusColor,
                                  );
                                },
                              ),
                            ),
                          ),
                        ),
                      ],
                    );
                  },
                ),
              ),

              const SizedBox(height: 28),

              // Tap Prompt / Status Label
              Text(
                _state == AssistantState.listening
                    ? 'Listening... Tap to send'
                    : (_state == AssistantState.speaking
                        ? 'Jarvis is speaking... Tap to stop'
                        : 'Tap to Speak'),
                style: TextStyle(
                  color: statusColor,
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 1.5,
                ),
              ),

              const SizedBox(height: 8),

              Text(
                _statusMessage,
                style: const TextStyle(
                  color: Colors.white54,
                  fontSize: 12,
                ),
              ),

              const Spacer(),

              // Glassmorphic Response Panel
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: Container(
                  width: double.infinity,
                  constraints: const BoxConstraints(minHeight: 120),
                  padding: const EdgeInsets.all(18),
                  decoration: BoxDecoration(
                    color: const Color(0xFF101926).withOpacity(0.85),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(
                      color: const Color(0xFF00E5FF).withOpacity(0.25),
                      width: 1,
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.6),
                        blurRadius: 15,
                        offset: const Offset(0, 6),
                      ),
                    ],
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Row(
                            children: const [
                              Icon(Icons.terminal, color: Color(0xFF00E5FF), size: 16),
                              SizedBox(width: 8),
                              Text(
                                'NEURAL FEEDBACK',
                                style: TextStyle(
                                  color: Color(0xFF00E5FF),
                                  fontSize: 11,
                                  fontWeight: FontWeight.bold,
                                  letterSpacing: 1.5,
                                ),
                              ),
                            ],
                          ),
                          if (_actionBadge != null)
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                              decoration: BoxDecoration(
                                color: const Color(0xFF00E5FF).withOpacity(0.15),
                                borderRadius: BorderRadius.circular(8),
                                border: Border.all(
                                  color: const Color(0xFF00E5FF).withOpacity(0.4),
                                ),
                              ),
                              child: Text(
                                _actionBadge!.toUpperCase(),
                                style: const TextStyle(
                                  color: Color(0xFF00E5FF),
                                  fontSize: 10,
                                  fontWeight: FontWeight.bold,
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
                            color: Colors.white70,
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
                          fontSize: 15,
                          height: 1.4,
                          fontWeight: FontWeight.w400,
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 16),

              // Manual Text Input Fallback Bar
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                child: Container(
                  decoration: BoxDecoration(
                    color: const Color(0xFF0B121C),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: Colors.white12,
                    ),
                  ),
                  child: Row(
                    children: [
                      const SizedBox(width: 14),
                      Expanded(
                        child: TextField(
                          controller: _textController,
                          style: const TextStyle(color: Colors.white, fontSize: 14),
                          decoration: const InputDecoration(
                            hintText: 'Type a command (e.g. open chrome)...',
                            hintStyle: TextStyle(color: Colors.white30, fontSize: 13),
                            border: InputBorder.none,
                          ),
                          onSubmitted: (value) {
                            if (value.trim().isNotEmpty) {
                              _sendQueryToJarvis(value.trim());
                              _textController.clear();
                            }
                          },
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.send_rounded, color: Color(0xFF00E5FF), size: 20),
                        onPressed: () {
                          if (_textController.text.trim().isNotEmpty) {
                            _sendQueryToJarvis(_textController.text.trim());
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
