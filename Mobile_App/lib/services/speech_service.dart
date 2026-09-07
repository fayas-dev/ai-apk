import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:speech_to_text/speech_recognition_error.dart';
import 'package:speech_to_text/speech_to_text.dart';

enum SpeechStateStatus {
  uninitialized,
  ready,
  listening,
  done,
  permissionDenied,
  permissionPermanentlyDenied,
  unavailable,
  error,
}

class JarvisSpeechService {
  final SpeechToText _speech = SpeechToText();

  final StreamController<SpeechStateStatus> _statusController =
      StreamController<SpeechStateStatus>.broadcast();
  Stream<SpeechStateStatus> get statusStream => _statusController.stream;

  final StreamController<String> _wordsController =
      StreamController<String>.broadcast();
  Stream<String> get wordsStream => _wordsController.stream;

  SpeechStateStatus _status = SpeechStateStatus.uninitialized;
  SpeechStateStatus get status => _status;

  String _lastRecognizedWords = '';
  String get lastRecognizedWords => _lastRecognizedWords;

  bool _isAvailable = false;
  bool get isAvailable => _isAvailable;

  bool get isListening => _speech.isListening;

  /// Request microphone permission explicitly before initializing STT.
  Future<bool> _requestMicPermission() async {
    try {
      final status = await Permission.microphone.request();
      if (status == PermissionStatus.granted) return true;
      if (status == PermissionStatus.permanentlyDenied) {
        _updateStatus(SpeechStateStatus.permissionPermanentlyDenied);
      } else {
        _updateStatus(SpeechStateStatus.permissionDenied);
      }
      return false;
    } catch (_) {
      return true; // Fallback: let STT handle it
    }
  }

  Future<bool> initialize() async {
    // Explicitly request mic permission first
    final hasPerm = await _requestMicPermission();
    if (!hasPerm) return false;

    try {
      _isAvailable = await _speech.initialize(
        onStatus: _onSpeechStatus,
        onError: _onSpeechError,
        debugLogging: kDebugMode,
      );

      if (_isAvailable) {
        _updateStatus(SpeechStateStatus.ready);
        return true;
      } else {
        if (!_speech.hasPermission) {
          _updateStatus(SpeechStateStatus.permissionDenied);
        } else {
          _updateStatus(SpeechStateStatus.unavailable);
        }
        return false;
      }
    } catch (e) {
      _updateStatus(SpeechStateStatus.error);
      return false;
    }
  }

  void _onSpeechStatus(String status) {
    if (status == 'listening') {
      _updateStatus(SpeechStateStatus.listening);
    } else if (status == 'notListening' || status == 'done') {
      _updateStatus(SpeechStateStatus.done);
    }
  }

  void _onSpeechError(SpeechRecognitionError errorNotification) {
    // Ignore no_match - it just means silence, not a real error
    if (errorNotification.errorMsg.contains('error_no_match') ||
        errorNotification.errorMsg.contains('no_match')) {
      return;
    }
    if (errorNotification.errorMsg.contains('error_permission') ||
        errorNotification.errorMsg.contains('permission')) {
      _updateStatus(SpeechStateStatus.permissionDenied);
    } else if (errorNotification.errorMsg.contains('error_speech_timeout') ||
        errorNotification.errorMsg.contains('speech_timeout')) {
      // Timeout is normal — don't emit error
      _updateStatus(SpeechStateStatus.done);
    } else {
      _updateStatus(SpeechStateStatus.error);
    }
  }

  void _updateStatus(SpeechStateStatus newStatus) {
    _status = newStatus;
    if (!_statusController.isClosed) {
      _statusController.add(newStatus);
    }
  }

  Future<void> startListening({
    required Function(String text, bool isFinal) onResult,
  }) async {
    if (!_isAvailable) {
      final initialized = await initialize();
      if (!initialized) return;
    }

    _lastRecognizedWords = '';

    try {
      await _speech.listen(
        onResult: (result) {
          final words = result.recognizedWords;
          _lastRecognizedWords = words;
          if (!_wordsController.isClosed) {
            _wordsController.add(words);
          }
          // Always call with partial results so the user sees live transcription.
          // isFinal = true when STT confirms the utterance is complete.
          onResult(words, result.finalResult);
        },
        listenFor: const Duration(seconds: 30),
        // pauseFor: how long silence before auto-finalizing (4s is best)
        pauseFor: const Duration(seconds: 4),
        partialResults: true,
        cancelOnError: false,  // Don't cancel on minor errors like no_match
        listenMode: ListenMode.dictation,  // Dictation keeps mic open longer
      );
      _updateStatus(SpeechStateStatus.listening);
    } catch (e) {
      _updateStatus(SpeechStateStatus.error);
    }
  }

  Future<void> stopListening() async {
    try {
      await _speech.stop();
      _updateStatus(SpeechStateStatus.done);
    } catch (e) {
      // Ignored stop error
    }
  }

  Future<void> cancelListening() async {
    try {
      await _speech.cancel();
      _updateStatus(SpeechStateStatus.ready);
    } catch (e) {
      // Ignored cancel error
    }
  }

  void dispose() {
    _speech.stop();
    _statusController.close();
    _wordsController.close();
  }
}
