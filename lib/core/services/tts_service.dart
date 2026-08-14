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
    if (kIsWeb) return; // TTS limited on web
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
    if (kIsWeb) return;
    await _tts.stop();
    await _tts.speak(text);
  }

  Future<void> pause() async {
    if (kIsWeb) return;
    await _tts.pause();
    _state = TtsState.paused;
    stateNotifier.value = TtsState.paused;
  }

  Future<void> stop() async {
    if (kIsWeb) return;
    await _tts.stop();
    _state = TtsState.stopped;
    stateNotifier.value = TtsState.stopped;
  }

  Future<void> resume() async {
    if (kIsWeb) return;
    if (_state == TtsState.paused) {
      await _tts.speak(''); // flutter_tts doesn't have resume; re-speak is needed at higher level
    }
  }
}
