import 'package:flutter_tts/flutter_tts.dart';

class JarvisTtsService {
  final FlutterTts _flutterTts = FlutterTts();
  bool _isSpeaking = false;
  bool get isSpeaking => _isSpeaking;

  double _pitch = 0.70; // Low pitch for deep male Jarvis persona
  double _rate = 0.50;  // Standard measured speech rate
  Map<String, String>? _maleVoice;

  double get pitch => _pitch;
  double get rate => _rate;

  Future<void> initialize() async {
    try {
      await _flutterTts.setLanguage('en-US');
      await _flutterTts.setSpeechRate(_rate);
      await _flutterTts.setVolume(1.0);
      await _flutterTts.setPitch(_pitch);

      // Attempt to pick a male voice if available on Android
      try {
        final voices = await _flutterTts.getVoices;
        if (voices is List) {
          for (final v in voices) {
            if (v is Map) {
              final name = (v['name'] ?? '').toString().toLowerCase();
              final locale = (v['locale'] ?? '').toString().toLowerCase();
              final gender = (v['gender'] ?? '').toString().toLowerCase();
              if ((locale.contains('en-us') || locale.contains('en-gb') || locale.contains('en-in')) &&
                  (gender == 'male' ||
                   name.contains('male') ||
                   name.contains('en-us-x-sfg') ||
                   name.contains('en-us-x-iol') ||
                   name.contains('en-gb-x-rjs') ||
                   name.contains('david') ||
                   name.contains('george') ||
                   name.contains('guy'))) {
                _maleVoice = {'name': v['name'].toString(), 'locale': v['locale'].toString()};
                await _flutterTts.setVoice(_maleVoice!);
                break;
              }
            }
          }
        }
      } catch (_) {}

      _flutterTts.setStartHandler(() {
        _isSpeaking = true;
      });

      _flutterTts.setCompletionHandler(() {
        _isSpeaking = false;
      });

      _flutterTts.setErrorHandler((msg) {
        _isSpeaking = false;
      });
    } catch (e) {
      // Ignored TTS setup error
    }
  }

  Future<void> setVoicePitch(double pitch) async {
    _pitch = pitch;
    await _flutterTts.setPitch(pitch);
  }

  Future<void> setVoiceRate(double rate) async {
    _rate = rate;
    await _flutterTts.setSpeechRate(rate);
  }

  Future<void> speak(String text) async {
    if (text.trim().isEmpty) return;
    try {
      await stop();
      // Check if text contains Malayalam characters (U+0D00 to U+0D7F)
      final hasMalayalam = RegExp(r'[\u0D00-\u0D7F]').hasMatch(text);
      if (hasMalayalam) {
        await _flutterTts.setLanguage('ml-IN');
      } else {
        await _flutterTts.setLanguage('en-US');
        if (_maleVoice != null) {
          try {
            await _flutterTts.setVoice(_maleVoice!);
          } catch (_) {}
        }
      }
      await _flutterTts.setPitch(_pitch);
      await _flutterTts.setSpeechRate(_rate);
      await _flutterTts.speak(text);
    } catch (e) {
      _isSpeaking = false;
    }
  }

  Future<void> stop() async {
    try {
      await _flutterTts.stop();
      _isSpeaking = false;
    } catch (e) {
      // Ignored
    }
  }

  void dispose() {
    _flutterTts.stop();
  }
}
