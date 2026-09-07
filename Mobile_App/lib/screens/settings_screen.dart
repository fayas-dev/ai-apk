import 'package:flutter/material.dart';
import '../services/mobile_actions.dart';
import '../services/tts_service.dart';
import '../services/websocket_service.dart';
import 'remote_trackpad_screen.dart';

class SettingsScreen extends StatefulWidget {
  final JarvisWebSocketService wsService;
  final JarvisTtsService ttsService;

  const SettingsScreen({
    super.key,
    required this.wsService,
    required this.ttsService,
  });

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late double _voicePitch;
  late double _voiceRate;
  late TextEditingController _serverController;

  @override
  void initState() {
    super.initState();
    _voicePitch = widget.ttsService.pitch;
    _voiceRate = widget.ttsService.rate;
    _serverController = TextEditingController(text: JarvisWebSocketService.activeServerUrl);
  }

  @override
  void dispose() {
    _serverController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF070B12),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0B131E),
        title: const Text(
          'JARVIS SETTINGS',
          style: TextStyle(
            color: Color(0xFF00E5FF),
            fontWeight: FontWeight.bold,
            letterSpacing: 2,
            fontSize: 16,
          ),
        ),
        iconTheme: const IconThemeData(color: Color(0xFF00E5FF)),
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // 1. Owner Profile Card
            _buildCard(
              title: 'AUTHORIZED OWNER PROFILE',
              icon: Icons.verified_user_rounded,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildProfileRow('Master / Creator', 'Muhammad Fayas'),
                  _buildProfileRow('Date of Birth', '21 / 03 / 2010'),
                  _buildProfileRow('Location', 'Kaipamangalam, Thainagar'),
                  _buildProfileRow('Region', 'Thrissur, Kerala, India'),
                  _buildProfileRow('Language Support', 'English & Malayalam (മലയാളം)'),
                ],
              ),
            ),

            const SizedBox(height: 16),

            // 2. PC Remote Control & Trackpad Shortcut
            _buildCard(
              title: 'PC REMOTE CONTROL & SCREEN',
              icon: Icons.laptop_chromebook_rounded,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Access your computer screen, use virtual mouse trackpad, and execute power commands from mobile.',
                    style: TextStyle(color: Colors.white60, fontSize: 12),
                  ),
                  const SizedBox(height: 14),
                  ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF00E5FF),
                      foregroundColor: Colors.black,
                      minimumSize: const Size(double.infinity, 44),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                    ),
                    icon: const Icon(Icons.touch_app_rounded, size: 20),
                    label: const Text(
                      'OPEN REMOTE TRACKPAD & SCREEN',
                      style: TextStyle(fontWeight: FontWeight.bold, letterSpacing: 1),
                    ),
                    onPressed: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => RemoteTrackpadScreen(wsService: widget.wsService),
                        ),
                      );
                    },
                  ),
                  const SizedBox(height: 10),
                  OutlinedButton.icon(
                    style: OutlinedButton.styleFrom(
                      foregroundColor: const Color(0xFF00E5FF),
                      side: const BorderSide(color: Color(0xFF00E5FF)),
                      minimumSize: const Size(double.infinity, 40),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                    ),
                    icon: const Icon(Icons.qr_code_scanner_rounded, size: 18),
                    label: const Text('PAIR PC VIA QR CODE'),
                    onPressed: () {
                      _showPairingDialog();
                    },
                  ),
                ],
              ),
            ),

            const SizedBox(height: 16),

            // 3. Voice Synthesizer Configuration (Male Voice Tuning)
            _buildCard(
              title: 'VOICE SYNTHESIS (MALE VOICE)',
              icon: Icons.record_voice_over_rounded,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('Voice Pitch (Lower = Deeper Male):', style: TextStyle(color: Colors.white70, fontSize: 12)),
                      Text(_voicePitch.toStringAsFixed(2), style: const TextStyle(color: Color(0xFF00E5FF), fontWeight: FontWeight.bold)),
                    ],
                  ),
                  Slider(
                    value: _voicePitch,
                    min: 0.5,
                    max: 1.5,
                    activeColor: const Color(0xFF00E5FF),
                    inactiveColor: Colors.white12,
                    onChanged: (val) {
                      setState(() => _voicePitch = val);
                      widget.ttsService.setVoicePitch(val);
                    },
                  ),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('Speech Speed:', style: TextStyle(color: Colors.white70, fontSize: 12)),
                      Text(_voiceRate.toStringAsFixed(2), style: const TextStyle(color: Color(0xFF00E5FF), fontWeight: FontWeight.bold)),
                    ],
                  ),
                  Slider(
                    value: _voiceRate,
                    min: 0.3,
                    max: 0.9,
                    activeColor: const Color(0xFF00E5FF),
                    inactiveColor: Colors.white12,
                    onChanged: (val) {
                      setState(() => _voiceRate = val);
                      widget.ttsService.setVoiceRate(val);
                    },
                  ),
                  const SizedBox(height: 6),
                  ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF142438),
                      foregroundColor: const Color(0xFF00E5FF),
                      minimumSize: const Size(double.infinity, 38),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    ),
                    icon: const Icon(Icons.volume_up_rounded, size: 18),
                    label: const Text('Test Jarvis Male Voice'),
                    onPressed: () {
                      widget.ttsService.speak('Neural audio systems calibrated. Standing by for instructions, sir.');
                    },
                  ),
                ],
              ),
            ),

            const SizedBox(height: 16),

            // 4. Quick Mobile Actions (WhatsApp & Calls)
            _buildCard(
              title: 'MOBILE QUICK ACTIONS',
              icon: Icons.apps_rounded,
              child: Column(
                children: [
                  ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: const CircleAvatar(
                      backgroundColor: Color(0xFF00FF88),
                      child: Icon(Icons.chat_rounded, color: Colors.black),
                    ),
                    title: const Text('Open WhatsApp', style: TextStyle(color: Colors.white, fontSize: 14)),
                    subtitle: const Text('Launch WhatsApp or chat with contacts', style: TextStyle(color: Colors.white38, fontSize: 11)),
                    trailing: const Icon(Icons.chevron_right, color: Colors.white38),
                    onTap: () => MobileActionsService.openWhatsApp(),
                  ),
                  const Divider(color: Colors.white10),
                  ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: const CircleAvatar(
                      backgroundColor: Color(0xFF00E5FF),
                      child: Icon(Icons.public, color: Colors.black),
                    ),
                    title: const Text('Open Google Chrome', style: TextStyle(color: Colors.white, fontSize: 14)),
                    subtitle: const Text('Search web on phone', style: TextStyle(color: Colors.white38, fontSize: 11)),
                    trailing: const Icon(Icons.chevron_right, color: Colors.white38),
                    onTap: () => MobileActionsService.openChrome(),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCard({required String title, required IconData icon, required Widget child}) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF0E1624),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFF00E5FF).withValues(alpha: 0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: const Color(0xFF00E5FF), size: 18),
              const SizedBox(width: 8),
              Text(
                title,
                style: const TextStyle(
                  color: Color(0xFF00E5FF),
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1.5,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          child,
        ],
      ),
    );
  }

  Widget _buildProfileRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.white54, fontSize: 12)),
          Text(value, style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }

  void _showPairingDialog() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF0E1624),
        title: const Text('Pair PC via QR / Code', style: TextStyle(color: Color(0xFF00E5FF))),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              '1. On your PC, open Jarvis PC App.\n2. Go to Voice & Settings.\n3. Your PC is already connected to VPS (45.131.64.32:2004).\n4. Mobile and PC pair automatically via the central VPS!',
              style: TextStyle(color: Colors.white70, fontSize: 13, height: 1.4),
            ),
            const SizedBox(height: 14),
            TextField(
              controller: _serverController,
              style: const TextStyle(color: Colors.white, fontSize: 12),
              decoration: const InputDecoration(
                labelText: 'VPS WebSocket Endpoint',
                labelStyle: TextStyle(color: Color(0xFF00E5FF)),
                enabledBorder: UnderlineInputBorder(borderSide: BorderSide(color: Colors.white24)),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel', style: TextStyle(color: Colors.white54)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF00E5FF)),
            onPressed: () {
              widget.wsService.connect(customUrl: _serverController.text.trim());
              Navigator.pop(ctx);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Connected to Jarvis VPS')),
              );
            },
            child: const Text('Connect', style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }
}
