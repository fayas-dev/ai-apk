import 'dart:async';
import 'dart:convert';
import 'dart:math';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../models/jarvis_response.dart';

enum ConnectionStateStatus {
  disconnected,
  connecting,
  connected,
}

class JarvisWebSocketService {
  // Centralized VPS Server URL - Single source of truth for Mobile App
  static const String serverUrl = 'ws://45.131.64.32:2004/ws/jarvis';

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

  // Pending requests: requestId -> Completer<JarvisResponse>
  final Map<String, Completer<JarvisResponse>> _pendingRequests = {};

  void init() {
    _isDisposed = false;
    connect();
  }

  void _setStatus(ConnectionStateStatus status) {
    _currentStatus = status;
    if (!_connectionStateController.isClosed) {
      _connectionStateController.add(status);
    }
  }

  void connect() {
    if (_isDisposed) return;
    if (_currentStatus == ConnectionStateStatus.connected ||
        _currentStatus == ConnectionStateStatus.connecting) {
      return;
    }

    _setStatus(ConnectionStateStatus.connecting);

    try {
      final uri = Uri.parse(serverUrl);
      _channel = WebSocketChannel.connect(uri);

      _subscription = _channel!.stream.listen(
        _onMessageReceived,
        onDone: _onDisconnected,
        onError: (error) {
          _onDisconnected();
        },
        cancelOnError: true,
      );

      _setStatus(ConnectionStateStatus.connected);
      _reconnectAttempts = 0;
    } catch (e) {
      _onDisconnected();
    }
  }

  void _onMessageReceived(dynamic message) {
    try {
      final Map<String, dynamic> data = jsonDecode(message.toString());
      final response = JarvisResponse.fromJson(data);

      final requestId = response.requestId;
      if (requestId.isNotEmpty && _pendingRequests.containsKey(requestId)) {
        final completer = _pendingRequests.remove(requestId);
        if (completer != null && !completer.isCompleted) {
          completer.complete(response);
        }
      }
    } catch (e) {
      // Ignored malformed broadcast
    }
  }

  void _onDisconnected() {
    _subscription?.cancel();
    _subscription = null;
    _channel = null;

    // Fail all pending requests with error
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

  void dispose() {
    _isDisposed = true;
    _reconnectTimer?.cancel();
    _subscription?.cancel();
    _channel?.sink.close();
    _connectionStateController.close();
  }
}
