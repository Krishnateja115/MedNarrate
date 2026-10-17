import 'dart:async';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../core/l10n/app_l10n.dart';
import '../../core/services/api_exception.dart';
import '../../core/services/api_models.dart';
import '../../core/services/api_service.dart';
import 'voice_languages.dart';
import 'voice_recorder.dart';

enum VoiceState {
  /// The server does not offer voice input (or it is not supported here): no
  /// microphone is shown and the chat box behaves exactly as before.
  unavailable,
  idle,
  recording,
  transcribing,
}

/// Drives the microphone button: record → upload → text.
///
/// It never touches the text box itself; [finish] hands the transcript back to
/// the caller, which decides where it goes.
class VoiceInputController extends ChangeNotifier {
  VoiceInputController({
    VoiceRecorder? recorder,
    Future<SpeechStatus> Function()? loadStatus,
    Future<SpeechResult> Function(String path, {String? language})? transcribe,
  })  : _recorder = recorder ?? RecordVoiceRecorder(),
        _loadStatus = loadStatus ?? ApiService.instance.speechStatus,
        _transcribe = transcribe ??
            ((path, {language}) =>
                ApiService.instance.transcribeAudio(path, language: language));

  static const String _languagePrefKey = 'voice_input_language';
  static const Duration _minimumRecording = Duration(milliseconds: 700);
  static const int _barCount = 32;

  final VoiceRecorder _recorder;
  final Future<SpeechStatus> Function() _loadStatus;
  final Future<SpeechResult> Function(String path, {String? language})
      _transcribe;

  VoiceState _state = VoiceState.unavailable;
  List<String> _languages = const ['en'];
  String _language = 'en';
  int _maxSeconds = 120;
  Duration _elapsed = Duration.zero;
  final List<double> _levels = List<double>.filled(_barCount, 0);
  String? _error;

  // Bumped whenever the current attempt is abandoned, so a slow upload that
  // finishes after the user pressed cancel is ignored.
  int _attempt = 0;
  Timer? _ticker;
  StreamSubscription<double>? _levelSub;
  final Stopwatch _stopwatch = Stopwatch();
  bool _starting = false;
  bool _disposed = false;

  /// Set by the widget: called when the time limit is reached, so it can
  /// finish the recording and use the text like a normal tap on the tick.
  VoidCallback? onTimeLimit;

  VoiceState get state => _state;
  bool get available => _state != VoiceState.unavailable;
  bool get isRecording => _state == VoiceState.recording;
  bool get isTranscribing => _state == VoiceState.transcribing;
  bool get isStarting => _starting;
  bool get isBusy => isRecording || isTranscribing;
  String get language => _language;
  List<String> get languages => _languages;
  Duration get elapsed => _elapsed;
  List<double> get levels => List<double>.unmodifiable(_levels);

  /// Called once when the chat box appears. [defaultLanguage] is the app's
  /// language; it is used until the user picks another one.
  Future<void> init({required String defaultLanguage}) async {
    if (kIsWeb) return;
    final status = await _loadStatus();
    if (_disposed || !status.enabled) return;

    final supported = status.languages
        .where((c) => kVoiceLanguages.any((l) => l.code == c))
        .toList();
    _languages = supported.isEmpty ? const ['en'] : supported;
    _maxSeconds = status.maxSeconds;

    String? saved;
    try {
      saved = (await SharedPreferences.getInstance())
          .getString(_languagePrefKey);
    } catch (_) {}
    if (_disposed) return;
    final wanted = saved ?? defaultLanguage;
    _language = _languages.contains(wanted) ? wanted : _languages.first;
    _state = VoiceState.idle;
    notifyListeners();
  }

  Future<void> setLanguage(String code) async {
    if (!_languages.contains(code) || code == _language) return;
    _language = code;
    notifyListeners();
    try {
      (await SharedPreferences.getInstance())
          .setString(_languagePrefKey, code);
    } catch (_) {}
  }

  /// A message for the user, once; null when there is nothing to report.
  String? takeError() {
    final message = _error;
    _error = null;
    return message;
  }

  Future<void> start() async {
    if (_state != VoiceState.idle || _starting) return;
    final attempt = ++_attempt;
    // Blocks double taps while the permission prompt is on screen.
    _starting = true;
    _elapsed = Duration.zero;
    _levels.fillRange(0, _levels.length, 0);
    notifyListeners();

    final result = await _recorder.start();
    _starting = false;
    if (_disposed) {
      if (result == VoiceStartResult.started) await _recorder.cancel();
      return;
    }
    if (attempt != _attempt) {
      // Cancelled while the permission prompt or the microphone was starting.
      if (result == VoiceStartResult.started) await _recorder.cancel();
      notifyListeners();
      return;
    }

    switch (result) {
      case VoiceStartResult.permissionDenied:
        _fail(
            appL10n.voiceMicOff);
        return;
      case VoiceStartResult.failed:
        _fail(appL10n.voiceCouldNotStart);
        return;
      case VoiceStartResult.started:
        break;
    }

    HapticFeedback.lightImpact().catchError((_) {});
    _state = VoiceState.recording;
    _stopwatch
      ..reset()
      ..start();
    _levelSub = _recorder.levels.listen((level) {
      _levels
        ..removeAt(0)
        ..add(level);
      if (!_disposed) notifyListeners();
    });
    var limitReached = false;
    _ticker = Timer.periodic(const Duration(milliseconds: 250), (_) {
      _elapsed = _stopwatch.elapsed;
      if (!limitReached && _elapsed.inSeconds >= _maxSeconds) {
        // Out of time: use what was said rather than losing it.
        limitReached = true;
        onTimeLimit?.call();
      }
      if (!_disposed) notifyListeners();
    });
    notifyListeners();
  }

  /// Stops recording and returns what was said, or null (nothing heard, too
  /// short, cancelled or failed - [takeError] explains when it matters).
  Future<String?> finish() async {
    if (_state != VoiceState.recording) return null;
    final attempt = _attempt;
    _stopTimers();
    final length = _stopwatch.elapsed;
    _stopwatch.stop();
    _state = VoiceState.transcribing;
    notifyListeners();

    final path = await _recorder.stop();
    if (_disposed) {
      _deleteQuietly(path);
      return null;
    }
    if (attempt != _attempt || path == null) {
      _deleteQuietly(path);
      if (attempt == _attempt) _fail(appL10n.voiceNothingRecorded);
      return null;
    }
    if (length < _minimumRecording) {
      _deleteQuietly(path);
      _fail(appL10n.voiceTooShort);
      return null;
    }

    try {
      final result = await _transcribe(path, language: _language);
      if (_disposed || attempt != _attempt) return null;
      _state = VoiceState.idle;
      if (result.noSpeech) {
        _error = appL10n.voiceNoSpeech;
        notifyListeners();
        return null;
      }
      notifyListeners();
      return result.text;
    } on ApiException catch (e) {
      if (_disposed || attempt != _attempt) return null;
      if (e.statusCode == 404) {
        // Voice input was switched off on the server.
        _state = VoiceState.unavailable;
        _error = appL10n.voiceUnavailableType;
        notifyListeners();
        return null;
      }
      _fail(e.message);
      return null;
    } catch (_) {
      if (_disposed || attempt != _attempt) return null;
      _fail(appL10n.voiceFailed);
      return null;
    } finally {
      _deleteQuietly(path);
    }
  }

  /// Throws the recording away (the ✕ button), or abandons an upload in
  /// progress.
  Future<void> cancel() async {
    if (_state == VoiceState.unavailable || _state == VoiceState.idle) return;
    final wasRecording = _state == VoiceState.recording;
    _attempt++;
    _stopTimers();
    _stopwatch.stop();
    _state = VoiceState.idle;
    notifyListeners();
    if (wasRecording) await _recorder.cancel();
  }

  void _fail(String message) {
    _stopTimers();
    _starting = false;
    _error = message;
    if (_state != VoiceState.unavailable) _state = VoiceState.idle;
    if (!_disposed) notifyListeners();
  }

  void _stopTimers() {
    _ticker?.cancel();
    _ticker = null;
    _levelSub?.cancel();
    _levelSub = null;
  }

  void _deleteQuietly(String? path) {
    if (path == null) return;
    try {
      final file = File(path);
      if (file.existsSync()) file.deleteSync();
    } catch (_) {}
  }

  @override
  void dispose() {
    _disposed = true;
    _attempt++;
    final wasRecording = _state == VoiceState.recording;
    _stopTimers();
    if (wasRecording) {
      unawaited(_recorder.cancel().whenComplete(_recorder.dispose));
    } else {
      unawaited(_recorder.dispose());
    }
    super.dispose();
  }
}
