import 'package:flutter/foundation.dart';
import 'package:flutter_tts/flutter_tts.dart';

enum TtsState { stopped, playing, paused }

/// TTSService — singleton wrapper around flutter_tts.
/// Call [speak] with any text, [pause], [stop] as needed.
class TTSService {
  TTSService._();
  static final TTSService instance = TTSService._();

  final FlutterTts _tts = FlutterTts();
  TtsState _state = TtsState.stopped;
  TtsState get state => _state;

  final ValueNotifier<TtsState> stateNotifier = ValueNotifier(TtsState.stopped);

  Future<void> init() async {
    // kIsWeb check removed to allow web TTS
    await _tts.setLanguage('en-US');
    await _tts.setSpeechRate(0.5);
    await _tts.setVolume(1.0);
    await _tts.setPitch(1.0);

    _tts.setStartHandler(() {
      _state = TtsState.playing;
      stateNotifier.value = TtsState.playing;
    });
    _tts.setCompletionHandler(() {
      _state = TtsState.stopped;
      stateNotifier.value = TtsState.stopped;
    });
    _tts.setCancelHandler(() {
      _state = TtsState.stopped;
      stateNotifier.value = TtsState.stopped;
    });
    _tts.setErrorHandler((_) {
      _state = TtsState.stopped;
      stateNotifier.value = TtsState.stopped;
    });
  }

  Future<void> speak(String text) async {
    await _tts.stop();
    // Strip common markdown characters for cleaner TTS
    final cleanText = text.replaceAll(RegExp(r'[\*\#\_]'), '').replaceAll(RegExp(r'\n+'), '. ');
    await _tts.speak(cleanText);
  }

  Future<void> pause() async {
    await _tts.pause();
    _state = TtsState.paused;
    stateNotifier.value = TtsState.paused;
  }

  Future<void> stop() async {
    await _tts.stop();
    _state = TtsState.stopped;
    stateNotifier.value = TtsState.stopped;
  }

  Future<void> resume() async {
    if (_state == TtsState.paused) {
      await _tts.speak(''); // flutter_tts doesn't have resume; re-speak is needed at higher level
    }
  }
}
