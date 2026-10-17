import 'dart:async';
import 'dart:io';

import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';

/// How a recording attempt began.
enum VoiceStartResult { started, permissionDenied, failed }

/// Records short voice clips to a temporary file. The chat code talks to this
/// interface, so the `record` plugin lives in exactly one place.
abstract class VoiceRecorder {
  /// Asks for the microphone (first time only) and starts recording.
  Future<VoiceStartResult> start();

  /// Loudness 0..1, about ten times a second while recording.
  Stream<double> get levels;

  /// Stops and returns the file path, or null when nothing was recorded.
  Future<String?> stop();

  /// Stops and throws the recording away.
  Future<void> cancel();

  Future<void> dispose();
}

/// [VoiceRecorder] backed by the `record` package (Android, iOS, macOS,
/// Windows and Linux). AAC in an .m4a container is used because every phone
/// can produce it and the files are small; WAV is the fallback.
class RecordVoiceRecorder implements VoiceRecorder {
  AudioRecorder? _recorder;
  final StreamController<double> _levels = StreamController<double>.broadcast();
  StreamSubscription<Amplitude>? _amplitudeSub;

  AudioRecorder get _rec => _recorder ??= AudioRecorder();

  @override
  Stream<double> get levels => _levels.stream;

  @override
  Future<VoiceStartResult> start() async {
    try {
      final rec = _rec;
      if (!await rec.hasPermission()) {
        return VoiceStartResult.permissionDenied;
      }

      final useAac = await rec.isEncoderSupported(AudioEncoder.aacLc);
      final encoder = useAac ? AudioEncoder.aacLc : AudioEncoder.wav;
      final extension = useAac ? 'm4a' : 'wav';
      final dir = await getTemporaryDirectory();
      final path =
          '${dir.path}${Platform.pathSeparator}mednarrate_voice_${DateTime.now().millisecondsSinceEpoch}.$extension';

      await rec.start(
        RecordConfig(
          encoder: encoder,
          sampleRate: 16000,
          numChannels: 1,
          bitRate: 64000,
        ),
        path: path,
      );

      await _amplitudeSub?.cancel();
      _amplitudeSub = rec
          .onAmplitudeChanged(const Duration(milliseconds: 90))
          .listen((amp) {
        // dBFS: about -45 is a quiet room, 0 is the loudest possible.
        final level = ((amp.current + 45) / 45).clamp(0.0, 1.0);
        if (!_levels.isClosed) _levels.add(level);
      });
      return VoiceStartResult.started;
    } catch (_) {
      return VoiceStartResult.failed;
    }
  }

  @override
  Future<String?> stop() async {
    await _amplitudeSub?.cancel();
    _amplitudeSub = null;
    try {
      return await _recorder?.stop();
    } catch (_) {
      return null;
    }
  }

  @override
  Future<void> cancel() async {
    await _amplitudeSub?.cancel();
    _amplitudeSub = null;
    try {
      await _recorder?.cancel();
    } catch (_) {}
  }

  @override
  Future<void> dispose() async {
    await _amplitudeSub?.cancel();
    _amplitudeSub = null;
    try {
      await _recorder?.dispose();
    } catch (_) {}
    _recorder = null;
    await _levels.close();
  }
}
