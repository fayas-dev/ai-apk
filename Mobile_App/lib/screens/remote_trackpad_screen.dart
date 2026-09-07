import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import '../services/websocket_service.dart';

class RemoteTrackpadScreen extends StatefulWidget {
  final JarvisWebSocketService wsService;

  const RemoteTrackpadScreen({super.key, required this.wsService});

  @override
  State<RemoteTrackpadScreen> createState() => _RemoteTrackpadScreenState();
}

class _RemoteTrackpadScreenState extends State<RemoteTrackpadScreen> {
  String? _screenBase64;
  StreamSubscription? _screenSubscription;
  bool _isAutoRefresh = false;
  Timer? _autoRefreshTimer;
  final TextEditingController _keyboardController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _screenSubscription = widget.wsService.screenDataStream.listen((b64) {
      if (mounted) {
        setState(() {
          _screenBase64 = b64;
        });
      }
    });

    // Automatically enable live screen stream with visible pointer (600ms refresh)
    _toggleAutoRefresh(true);
  }

  @override
  void dispose() {
    _autoRefreshTimer?.cancel();
    _screenSubscription?.cancel();
    _keyboardController.dispose();
    super.dispose();
  }

  void _toggleAutoRefresh(bool enable) {
    setState(() {
      _isAutoRefresh = enable;
    });
    _autoRefreshTimer?.cancel();
    if (enable) {
      widget.wsService.requestPcScreen();
      _autoRefreshTimer = Timer.periodic(const Duration(milliseconds: 600), (_) {
        if (mounted) {
          widget.wsService.requestPcScreen();
        }
      });
    }
  }

  void _sendTextToPc() {
    final text = _keyboardController.text;
    if (text.isNotEmpty) {
      widget.wsService.sendKeyType(text);
      _keyboardController.clear();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Typed text to PC'),
          duration: Duration(milliseconds: 800),
          backgroundColor: Color(0xFF0F1B2B),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF070B12),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0B131E),
        title: const Text(
          'PC REMOTE CONTROL',
          style: TextStyle(
            color: Color(0xFF00E5FF),
            fontWeight: FontWeight.bold,
            letterSpacing: 2,
            fontSize: 16,
          ),
        ),
        iconTheme: const IconThemeData(color: Color(0xFF00E5FF)),
        actions: [
          IconButton(
            tooltip: 'Refresh Screen Snapshot',
            icon: const Icon(Icons.refresh_rounded, color: Color(0xFF00E5FF)),
            onPressed: () => widget.wsService.requestPcScreen(),
          ),
          IconButton(
            tooltip: _isAutoRefresh ? 'Disable Live Stream' : 'Enable Live Stream (2s)',
            icon: Icon(
              _isAutoRefresh ? Icons.videocam_rounded : Icons.videocam_off_rounded,
              color: _isAutoRefresh ? const Color(0xFF00FF88) : Colors.white54,
            ),
            onPressed: () => _toggleAutoRefresh(!_isAutoRefresh),
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            // 1. PC Screen Preview Box
            Container(
              height: 180,
              width: double.infinity,
              margin: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: const Color(0xFF0D1826),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFF00E5FF).withOpacity(0.3)),
              ),
              clipBehavior: Clip.antiAlias,
              child: _screenBase64 != null
                  ? Image.memory(
                      base64Decode(_screenBase64!),
                      fit: BoxFit.contain,
                      gaplessPlayback: true,
                    )
                  : Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: const [
                          Icon(Icons.desktop_windows_rounded, color: Colors.white24, size: 40),
                          SizedBox(height: 8),
                          Text(
                            'Requesting PC Screen Stream...',
                            style: TextStyle(color: Colors.white54, fontSize: 12),
                          ),
                        ],
                      ),
                    ),
            ),

            // 2. Quick PC Action Bar
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: [
                    _buildShortcutBtn(
                      icon: Icons.power_settings_new,
                      label: 'Shutdown',
                      color: const Color(0xFFFF3366),
                      onTap: () => _confirmAction('Shutdown PC', () => widget.wsService.shutdownPc()),
                    ),
                    _buildShortcutBtn(
                      icon: Icons.restart_alt,
                      label: 'Restart',
                      color: const Color(0xFFFF9100),
                      onTap: () => _confirmAction('Restart PC', () => widget.wsService.restartPc()),
                    ),
                    _buildShortcutBtn(
                      icon: Icons.lock_outline,
                      label: 'Lock',
                      color: const Color(0xFF00E5FF),
                      onTap: () => widget.wsService.lockPc(),
                    ),
                    _buildShortcutBtn(
                      icon: Icons.web,
                      label: 'Chrome',
                      color: const Color(0xFF00E5FF),
                      onTap: () => widget.wsService.openChromeOnPc(),
                    ),
                    _buildShortcutBtn(
                      icon: Icons.chat_bubble_outline,
                      label: 'WhatsApp',
                      color: const Color(0xFF00FF88),
                      onTap: () => widget.wsService.openWhatsAppOnPc(),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 10),

            // 3. Virtual Trackpad Area
            Expanded(
              child: Container(
                margin: const EdgeInsets.symmetric(horizontal: 12),
                decoration: BoxDecoration(
                  color: const Color(0xFF0E1624),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: const Color(0xFF00E5FF).withOpacity(0.2)),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.5),
                      blurRadius: 10,
                    ),
                  ],
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(16),
                  child: GestureDetector(
                    behavior: HitTestBehavior.opaque,
                    onPanUpdate: (details) {
                      widget.wsService.sendMouseMove(
                        details.delta.dx,
                        details.delta.dy,
                        sensitivity: 1.8,
                      );
                    },
                    onTap: () {
                      widget.wsService.sendMouseClick('left');
                    },
                    onDoubleTap: () {
                      widget.wsService.sendMouseDoubleClick();
                    },
                    child: Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: const [
                          Icon(Icons.touch_app_rounded, color: Color(0xFF00E5FF), size: 48),
                          SizedBox(height: 8),
                          Text(
                            'VIRTUAL TRACKPAD',
                            style: TextStyle(
                              color: Color(0xFF00E5FF),
                              letterSpacing: 2,
                              fontWeight: FontWeight.bold,
                              fontSize: 14,
                            ),
                          ),
                          SizedBox(height: 4),
                          Text(
                            'Drag finger to move mouse  |  Tap for Left Click',
                            style: TextStyle(color: Colors.white38, fontSize: 11),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ),

            const SizedBox(height: 10),

            // 4. Mouse Buttons Bar (Left Click, Scroll Up, Scroll Down, Right Click)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: Row(
                children: [
                  Expanded(
                    flex: 2,
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF142438),
                        foregroundColor: const Color(0xFF00E5FF),
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                      onPressed: () => widget.wsService.sendMouseClick('left'),
                      child: const Text('LEFT CLICK', style: TextStyle(fontWeight: FontWeight.bold)),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton(
                    style: IconButton.styleFrom(backgroundColor: const Color(0xFF142438)),
                    icon: const Icon(Icons.arrow_upward_rounded, color: Color(0xFF00E5FF)),
                    onPressed: () => widget.wsService.sendMouseScroll(250),
                  ),
                  const SizedBox(width: 4),
                  IconButton(
                    style: IconButton.styleFrom(backgroundColor: const Color(0xFF142438)),
                    icon: const Icon(Icons.arrow_downward_rounded, color: Color(0xFF00E5FF)),
                    onPressed: () => widget.wsService.sendMouseScroll(-250),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    flex: 2,
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF142438),
                        foregroundColor: const Color(0xFF00E5FF),
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                      onPressed: () => widget.wsService.sendMouseClick('right'),
                      child: const Text('RIGHT CLICK', style: TextStyle(fontWeight: FontWeight.bold)),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 10),

            // 5. Virtual Keyboard Input Bar
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              child: Container(
                decoration: BoxDecoration(
                  color: const Color(0xFF0E1624),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: Colors.white12),
                ),
                child: Row(
                  children: [
                    const SizedBox(width: 10),
                    Expanded(
                      child: TextField(
                        controller: _keyboardController,
                        style: const TextStyle(color: Colors.white, fontSize: 13),
                        decoration: const InputDecoration(
                          hintText: 'Type text to send to PC...',
                          hintStyle: TextStyle(color: Colors.white38, fontSize: 12),
                          border: InputBorder.none,
                        ),
                        onSubmitted: (_) => _sendTextToPc(),
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.send_rounded, color: Color(0xFF00E5FF), size: 18),
                      onPressed: _sendTextToPc,
                    ),
                    IconButton(
                      icon: const Icon(Icons.keyboard_return, color: Colors.white70, size: 18),
                      tooltip: 'Enter',
                      onPressed: () => widget.wsService.sendKeyPress('enter'),
                    ),
                    IconButton(
                      icon: const Icon(Icons.backspace_outlined, color: Colors.white70, size: 18),
                      tooltip: 'Backspace',
                      onPressed: () => widget.wsService.sendKeyPress('backspace'),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildShortcutBtn({
    required IconData icon,
    required String label,
    required Color color,
    required VoidCallback onTap,
  }) {
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(
            color: color.withOpacity(0.12),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: color.withOpacity(0.4)),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, color: color, size: 14),
              const SizedBox(width: 6),
              Text(
                label,
                style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.bold),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _confirmAction(String title, VoidCallback onConfirm) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF0E1624),
        title: Text(title, style: const TextStyle(color: Colors.white)),
        content: Text(
          'Are you sure you want to execute $title on your PC?',
          style: const TextStyle(color: Colors.white70),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel', style: TextStyle(color: Colors.white54)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFFFF3366)),
            onPressed: () {
              Navigator.pop(ctx);
              onConfirm();
            },
            child: const Text('Execute', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }
}
