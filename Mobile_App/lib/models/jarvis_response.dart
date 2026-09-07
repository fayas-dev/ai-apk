/// Jarvis Response Model
/// Safely parses JSON payloads received from the Jarvis VPS server.
class JarvisResponse {
  final String type;
  final String requestId;
  final bool success;
  final String action;
  final String? target;
  final String speech;
  final String? error;

  JarvisResponse({
    required this.type,
    required this.requestId,
    required this.success,
    this.action = 'speak',
    this.target,
    this.speech = '',
    this.error,
  });

  factory JarvisResponse.fromJson(Map<String, dynamic> json) {
    final type = (json['type'] as String?) ?? 'response';
    final requestId = (json['request_id'] as String?) ?? '';
    final success = (json['success'] as bool?) ?? (type == 'response');
    final action = (json['action'] as String?) ?? 'speak';
    final target = json['target'] as String?;
    final speech = (json['speech'] as String?) ?? '';
    final error = json['error'] as String?;

    return JarvisResponse(
      type: type,
      requestId: requestId,
      success: success,
      action: action,
      target: target,
      speech: speech.isNotEmpty ? speech : (error ?? 'Command processed.'),
      error: error,
    );
  }

  factory JarvisResponse.error({required String requestId, required String message}) {
    return JarvisResponse(
      type: 'error',
      requestId: requestId,
      success: false,
      action: 'speak',
      speech: message,
      error: message,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'type': type,
      'request_id': requestId,
      'success': success,
      'action': action,
      'target': target,
      'speech': speech,
      if (error != null) 'error': error,
    };
  }

  @override
  String toString() {
    return 'JarvisResponse(action: $action, speech: "$speech", success: $success)';
  }
}
