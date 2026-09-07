import 'package:flutter_tts/flutter_tts.dart';

class JarvisTtsService {
  final FlutterTts _flutterTts = FlutterTts();
  bool _isSpeaking = false;
  bool get isSpeaking => _isSpeaking;

  double _pitch = 0.80; // Deep, confident masculine Jarvis pitch
  double _rate = 0.48;  // Authoritative, clear conversational rate
  Map<String, String>? _maleVoice;
  String _currentLang = '';

  double get pitch => _pitch;
  double get rate => _rate;

  Future<void> initialize() async {
    try {
      // Without this, speak() resolves as soon as playback STARTS (not
      // finishes) on Android, so the app would re-open the microphone while
      // Jarvis is still talking and pick up its own voice as a new command.
      await _flutterTts.awaitSpeakCompletion(true);
      await _flutterTts.setLanguage('en-US');
      _currentLang = 'en-US';
      await _flutterTts.setSpeechRate(_rate);
      await _flutterTts.setVolume(1.0);
      await _flutterTts.setPitch(_pitch);

      await _findAndSetMaleVoice();

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

  Future<void> _findAndSetMaleVoice() async {
    try {
      final voices = await _flutterTts.getVoices;
      if (voices is List) {
        // Priority 1: Check explicitly male gender or name containing male
        for (final v in voices) {
          if (v is Map) {
            final name = (v['name'] ?? '').toString().toLowerCase();
            final locale = (v['locale'] ?? '').toString().toLowerCase();
            final gender = (v['gender'] ?? '').toString().toLowerCase();

            final isEnglish = locale.contains('en-us') ||
                locale.contains('en-gb') ||
                locale.contains('en-in') ||
                locale.contains('en');

            if (isEnglish) {
              if (gender == 'male' ||
                  name.contains('male') ||
                  name.contains('#male') ||
                  name.contains('-male') ||
                  name.contains('david') ||
                  name.contains('george') ||
                  name.contains('guy') ||
                  name.contains('en-us-x-sfg') ||
                  name.contains('en-us-x-iom') ||
                  name.contains('en-us-x-iol') ||
                  name.contains('en-in-x-cxx') ||
                  name.contains('en-gb-x-rjs')) {
                _maleVoice = {
                  'name': v['name'].toString(),
                  'locale': v['locale'].toString()
                };
                await _flutterTts.setVoice(_maleVoice!);
                return;
              }
            }
          }
        }

        // Priority 2: Any English voice that does NOT say female
        for (final v in voices) {
          if (v is Map) {
            final name = (v['name'] ?? '').toString().toLowerCase();
            final locale = (v['locale'] ?? '').toString().toLowerCase();
            final gender = (v['gender'] ?? '').toString().toLowerCase();
            if (locale.contains('en') &&
                gender != 'female' &&
                !name.contains('female') &&
                !name.contains('#female')) {
              _maleVoice = {
                'name': v['name'].toString(),
                'locale': v['locale'].toString()
              };
              await _flutterTts.setVoice(_maleVoice!);
              return;
            }
          }
        }
      }
    } catch (_) {}
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
      final hasMalayalam = RegExp(r'[\u0D00-\u0D7F]').hasMatch(text);
      final targetLang = hasMalayalam ? 'ml-IN' : 'en-US';

      if (_currentLang != targetLang) {
        await _flutterTts.setLanguage(targetLang);
        _currentLang = targetLang;
      }

      // Re-apply male voice
      if (!hasMalayalam) {
        if (_maleVoice == null) {
          await _findAndSetMaleVoice();
        }
        if (_maleVoice != null) {
          try {
            await _flutterTts.setVoice(_maleVoice!);
          } catch (_) {}
        }
      }

      await _flutterTts.setPitch(_pitch);
      await _flutterTts.setSpeechRate(_rate);
      await _flutterTts.setVolume(1.0);
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
