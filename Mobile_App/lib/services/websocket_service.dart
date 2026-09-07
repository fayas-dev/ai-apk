import 'dart:async';
import 'dart:convert';
import 'dart:math';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../models/jarvis_response.dart';

enum ConnectionStateStatus {
  disconnected,
  connecting,
  connected,
}

class JarvisWebSocketService {
  // Dedicated VPS Server URL (Single source of truth)
  static const String defaultServerUrl = 'ws://45.131.64.32:2004/ws/jarvis';
  static const String defaultPairingToken = 'JARVIS-FAYAS-2010';
  static String activeServerUrl = defaultServerUrl;
  static String activePairingToken = defaultPairingToken;
  static const FlutterSecureStorage _secureStorage = FlutterSecureStorage();

  WebSocketChannel? _channel;
  StreamSubscription? _subscription;
  Timer? _reconnectTimer;

  bool _isDisposed = false;
  int _reconnectAttempts = 0;
  static const int _maxReconnectDelayMs = 30000;
  static const int _baseReconnectDelayMs = 2000;

  final StreamController<ConnectionStateStatus> _connectionStateController =
      StreamController<ConnectionStateStatus>.broadcast();

  Stream<ConnectionStateStatus> get connectionState =>
      _connectionStateController.stream;

  ConnectionStateStatus _currentStatus = ConnectionStateStatus.disconnected;
  ConnectionStateStatus get currentStatus => _currentStatus;

  // Stream for Base64 JPEG PC Screen snapshots
  final StreamController<String> _screenDataController =
      StreamController<String>.broadcast();
  Stream<String> get screenDataStream => _screenDataController.stream;

  // Pending requests: requestId -> Completer<JarvisResponse>
  final Map<String, Completer<JarvisResponse>> _pendingRequests = {};

  Future<void> init() async {
    _isDisposed = false;
    final storedUrl = await _secureStorage.read(key: 'jarvis_secure_endpoint');
    final storedToken = await _secureStorage.read(key: 'jarvis_pairing_token');
    if (storedUrl != null && storedUrl.isNotEmpty) {
      activeServerUrl = storedUrl;
    }
    if (storedToken != null && storedToken.isNotEmpty) {
      activePairingToken = storedToken;
    }
    connect();
  }

  void _setStatus(ConnectionStateStatus status) {
    _currentStatus = status;
    if (!_connectionStateController.isClosed) {
      _connectionStateController.add(status);
    }
  }

  void connect({String? customUrl, String? pairingToken}) {
    if (_isDisposed) return;
    if (customUrl != null && customUrl.isNotEmpty) {
      activeServerUrl = customUrl.trim();
      // Reset channel if URL changes
      if (_channel != null) {
        try {
          _channel!.sink.close();
        } catch (_) {}
      }
      _subscription?.cancel();
      _subscription = null;
      _channel = null;
      _currentStatus = ConnectionStateStatus.disconnected;
    }
    if (pairingToken != null && pairingToken.isNotEmpty) {
      activePairingToken = pairingToken.trim();
    }
    if (customUrl != null && customUrl.isNotEmpty) {
      _secureStorage.write(key: 'jarvis_secure_endpoint', value: activeServerUrl);
      if (pairingToken != null) {
        _secureStorage.write(key: 'jarvis_pairing_token', value: activePairingToken);
      }
    }

    if (_currentStatus == ConnectionStateStatus.connected ||
        _currentStatus == ConnectionStateStatus.connecting) {
      return;
    }

    if (activeServerUrl.isEmpty) {
      _setStatus(ConnectionStateStatus.disconnected);
      return;
    }

    _setStatus(ConnectionStateStatus.connecting);

    try {
      final uri = Uri.parse(activeServerUrl);
      _channel = WebSocketChannel.connect(uri);

      _subscription = _channel!.stream.listen(
        _onMessageReceived,
        onDone: _onDisconnected,
        onError: (error) {
          _onDisconnected();
        },
        cancelOnError: true,
      );

      // Register mobile client. The UI becomes connected only after the relay
      // accepts the pairing token and replies with pong.
      _channel!.sink.add(jsonEncode({
        'type': 'register',
        'client': 'android',
        'device_name': 'Fayas-Mobile',
        'pairing_token': activePairingToken,
      }));
    } catch (e) {
      _onDisconnected();
    }
  }

  void _onMessageReceived(dynamic message) {
    try {
      final Map<String, dynamic> data = jsonDecode(message.toString());
      final msgType = data['type'];

      // 1. Pong = authentication accepted → mark as connected
      if (msgType == 'pong' && data['status'] == 'connected') {
        _setStatus(ConnectionStateStatus.connected);
        _reconnectAttempts = 0;
        return;
      }

      // 2. Screen capture relay from PC
      if (msgType == 'remote_pc_response') {
        if (data['command'] == 'screen_data' && data['screen'] != null) {
          final b64 = data['screen'].toString();
          if (!_screenDataController.isClosed) {
            _screenDataController.add(b64);
          }
        }
        // remote_pc_response is a relay from PC, not a reply to a pending request
        return;
      }

      // 3. Standard AI response (has request_id)
      if (msgType == 'response' || data.containsKey('request_id')) {
        try {
          final response = JarvisResponse.fromJson(data);
          final requestId = response.requestId;
          if (requestId.isNotEmpty && _pendingRequests.containsKey(requestId)) {
            final completer = _pendingRequests.remove(requestId);
            if (completer != null && !completer.isCompleted) {
              completer.complete(response);
            }
          }
        } catch (_) {}
        return;
      }

      // 4. Error responses
      if (msgType == 'error') {
        final requestId = data['request_id']?.toString() ?? '';
        if (requestId.isNotEmpty && _pendingRequests.containsKey(requestId)) {
          final completer = _pendingRequests.remove(requestId);
          if (completer != null && !completer.isCompleted) {
            completer.complete(JarvisResponse.error(
              requestId: requestId,
              message: data['error']?.toString() ?? 'Unknown VPS error.',
            ));
          }
        }
        return;
      }
    } catch (e) {
      // Ignored malformed broadcast
    }
  }

  void _onDisconnected() {
    _subscription?.cancel();
    _subscription = null;
    _channel = null;

    for (final entry in _pendingRequests.entries) {
      if (!entry.value.isCompleted) {
        entry.value.complete(JarvisResponse.error(
          requestId: entry.key,
          message: 'Connection to Jarvis VPS lost.',
        ));
      }
    }
    _pendingRequests.clear();

    _setStatus(ConnectionStateStatus.disconnected);

    if (!_isDisposed) {
      _scheduleReconnect();
    }
  }

  void _scheduleReconnect() {
    _reconnectTimer?.cancel();
    _reconnectAttempts++;

    final delay = min(
      _baseReconnectDelayMs * pow(1.5, _reconnectAttempts).toInt(),
      _maxReconnectDelayMs,
    );

    _reconnectTimer = Timer(Duration(milliseconds: delay), () {
      if (!_isDisposed && _currentStatus == ConnectionStateStatus.disconnected) {
        connect();
      }
    });
  }

  Future<JarvisResponse> sendCommand(String text, {Duration timeout = const Duration(seconds: 25)}) async {
    final requestId = DateTime.now().millisecondsSinceEpoch.toString() +
        '-' +
        Random().nextInt(99999).toString();

    if (_currentStatus != ConnectionStateStatus.connected || _channel == null) {
      connect();
      return JarvisResponse.error(
        requestId: requestId,
        message: 'Jarvis VPS is currently reconnecting. Please try again.',
      );
    }

    final payload = {
      'type': 'command',
      'client': 'android',
      'request_id': requestId,
      'text': text.trim(),
    };

    final completer = Completer<JarvisResponse>();
    _pendingRequests[requestId] = completer;

    try {
      _channel!.sink.add(jsonEncode(payload));
    } catch (e) {
      _pendingRequests.remove(requestId);
      return JarvisResponse.error(
        requestId: requestId,
        message: 'Failed to send command over WebSocket: $e',
      );
    }

    return completer.future.timeout(
      timeout,
      onTimeout: () {
        _pendingRequests.remove(requestId);
        return JarvisResponse.error(
          requestId: requestId,
          message: 'Jarvis VPS server request timed out.',
        );
      },
    );
  }

  // ==========================================
  // Remote PC Control Methods
  // ==========================================

  void sendRemoteCommand(String command, {Map<String, dynamic>? extras}) {
    if (_channel == null || _currentStatus != ConnectionStateStatus.connected) return;
    try {
      final payload = {
        'type': 'remote_pc_command',
        'client': 'android',
        'command': command,
        ...?extras,
      };
      _channel!.sink.add(jsonEncode(payload));
    } catch (_) {}
  }

  void sendMouseMove(double dx, double dy, {double sensitivity = 1.6}) {
    sendRemoteCommand('mouse_move', extras: {'dx': dx, 'dy': dy, 'sensitivity': sensitivity});
  }

  void sendMouseClick(String button) {
    sendRemoteCommand('mouse_click', extras: {'button': button});
  }

  void sendMouseDoubleClick() {
    sendRemoteCommand('mouse_double_click');
  }

  void sendMouseScroll(int amount) {
    sendRemoteCommand('mouse_scroll', extras: {'amount': amount});
  }

  void sendKeyType(String text) {
    sendRemoteCommand('key_type', extras: {'text': text});
  }

  void sendKeyPress(String key) {
    sendRemoteCommand('key_press', extras: {'key': key});
  }

  void requestPcScreen() {
    sendRemoteCommand('get_screen');
  }

  void shutdownPc() {
    sendRemoteCommand('shutdown_pc');
  }

  void restartPc() {
    sendRemoteCommand('restart_pc');
  }

  void lockPc() {
    sendRemoteCommand('lock_pc');
  }

  void openChromeOnPc() {
    sendRemoteCommand('open_chrome');
  }

  void openWhatsAppOnPc() {
    sendRemoteCommand('open_whatsapp');
  }

  /// Search Google in PC Chrome
  void searchWebOnPc(String query) {
    sendRemoteCommand('search_web', extras: {'target': query, 'query': query});
  }

  /// Open a specific URL in PC Chrome
  void openUrlOnPc(String url) {
    sendRemoteCommand('open_url_in_chrome', extras: {'target': url});
  }

  /// Open YouTube on PC Chrome
  void openYoutubeOnPc() {
    sendRemoteCommand('open_url_in_chrome', extras: {'target': 'https://www.youtube.com'});
  }

  /// Search and open any app on PC
  void searchAndOpenAppOnPc(String appName) {
    sendRemoteCommand('search_and_open_app', extras: {'target': appName});
  }

  void dispose() {
    _isDisposed = true;
    _reconnectTimer?.cancel();
    _subscription?.cancel();
    _channel?.sink.close();
    _connectionStateController.close();
    _screenDataController.close();
  }
}
