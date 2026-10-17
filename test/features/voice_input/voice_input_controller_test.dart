import 'dart:async';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:mednarrate/core/services/api_exception.dart';
import 'package:mednarrate/core/services/api_models.dart';
import 'package:mednarrate/features/voice_input/voice_input_controller.dart';
import 'package:mednarrate/features/voice_input/voice_recorder.dart';
import 'package:shared_preferences/shared_preferences.dart';

class _FakeRecorder implements VoiceRecorder {
  VoiceStartResult startResult = VoiceStartResult.started;
  String? stopPath;
  int cancelCount = 0;
  bool disposed = false;
  final StreamController<double> _levels = StreamController<double>.broadcast();

  @override
  Stream<double> get levels => _levels.stream;

  @override
  Future<VoiceStartResult> start() async => startResult;

  @override
  Future<String?> stop() async => stopPath;

  @override
  Future<void> cancel() async => cancelCount++;

  @override
  Future<void> dispose() async {
    disposed = true;
  }
}

const _enabled = SpeechStatus(
  enabled: true,
  languages: ['en', 'hi', 'ta'],
  maxSeconds: 120,
);

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late _FakeRecorder recorder;
  late Directory tmp;

  setUp(() {
    SharedPreferences.setMockInitialValues({});
    recorder = _FakeRecorder();
    tmp = Directory.systemTemp.createTempSync('voice_test');
  });

  tearDown(() {
    if (tmp.existsSync()) tmp.deleteSync(recursive: true);
  });

  String clip() {
    final f = File('${tmp.path}/clip.m4a')..writeAsBytesSync([1, 2, 3]);
    recorder.stopPath = f.path;
    return f.path;
  }

  VoiceInputController make({
    SpeechStatus status = _enabled,
    Future<SpeechResult> Function(String, {String? language})? transcribe,
  }) {
    return VoiceInputController(
      recorder: recorder,
      loadStatus: () async => status,
      transcribe: transcribe ??
          (path, {language}) async =>
              const SpeechResult(text: 'my head hurts', noSpeech: false),
    );
  }

  test('stays unavailable when the server has voice input switched off',
      () async {
    final c = make(status: const SpeechStatus.disabled());
    await c.init(defaultLanguage: 'en');
    expect(c.available, isFalse);
    expect(c.state, VoiceState.unavailable);
    c.dispose();
  });

  test('uses the app language when supported, otherwise English', () async {
    final hindi = make();
    await hindi.init(defaultLanguage: 'hi');
    expect(hindi.language, 'hi');
    hindi.dispose();

    final french = make();
    await french.init(defaultLanguage: 'fr');
    expect(french.language, 'en');
    french.dispose();
  });

  test('remembers the chosen language', () async {
    final first = make();
    await first.init(defaultLanguage: 'en');
    await first.setLanguage('ta');
    first.dispose();

    final second = make();
    await second.init(defaultLanguage: 'en');
    expect(second.language, 'ta');
    second.dispose();
  });

  test('record, finish and get the text back; the clip is deleted', () async {
    String? sentLanguage;
    final c = make(transcribe: (path, {language}) async {
      sentLanguage = language;
      return const SpeechResult(text: 'my head hurts', noSpeech: false);
    });
    await c.init(defaultLanguage: 'hi');
    final path = clip();

    await c.start();
    expect(c.state, VoiceState.recording);
    await Future<void>.delayed(const Duration(milliseconds: 900));
    final text = await c.finish();

    expect(text, 'my head hurts');
    expect(sentLanguage, 'hi');
    expect(c.state, VoiceState.idle);
    expect(File(path).existsSync(), isFalse);
    expect(c.takeError(), isNull);
    c.dispose();
  });

  test('a very short recording is rejected without calling the server',
      () async {
    var called = false;
    final c = make(transcribe: (path, {language}) async {
      called = true;
      return const SpeechResult(text: 'x', noSpeech: false);
    });
    await c.init(defaultLanguage: 'en');
    clip();
    await c.start();
    final text = await c.finish();
    expect(text, isNull);
    expect(called, isFalse);
    expect(c.takeError(), contains('too short'));
    expect(c.state, VoiceState.idle);
    c.dispose();
  });

  test('silence gives a friendly message and no text', () async {
    final c = make(
      transcribe: (path, {language}) async =>
          const SpeechResult(text: '', noSpeech: true),
    );
    await c.init(defaultLanguage: 'en');
    clip();
    await c.start();
    await Future<void>.delayed(const Duration(milliseconds: 900));
    expect(await c.finish(), isNull);
    expect(c.takeError(), contains("Couldn't hear"));
    expect(c.state, VoiceState.idle);
    c.dispose();
  });

  test('microphone permission denied explains how to fix it', () async {
    recorder.startResult = VoiceStartResult.permissionDenied;
    final c = make();
    await c.init(defaultLanguage: 'en');
    await c.start();
    expect(c.state, VoiceState.idle);
    expect(c.takeError(), contains('Microphone access'));
    c.dispose();
  });

  test('a server error is reported and the box is usable again', () async {
    final c = make(
      transcribe: (path, {language}) async =>
          throw const ApiException(503, 'Voice input is busy right now.'),
    );
    await c.init(defaultLanguage: 'en');
    clip();
    await c.start();
    await Future<void>.delayed(const Duration(milliseconds: 900));
    expect(await c.finish(), isNull);
    expect(c.takeError(), 'Voice input is busy right now.');
    expect(c.state, VoiceState.idle);
    c.dispose();
  });

  test('a 404 means the server turned voice input off', () async {
    final c = make(
      transcribe: (path, {language}) async =>
          throw const ApiException(404, 'Voice input is not enabled.'),
    );
    await c.init(defaultLanguage: 'en');
    clip();
    await c.start();
    await Future<void>.delayed(const Duration(milliseconds: 900));
    await c.finish();
    expect(c.state, VoiceState.unavailable);
    c.dispose();
  });

  test('cancel while recording discards the clip', () async {
    final c = make();
    await c.init(defaultLanguage: 'en');
    await c.start();
    await c.cancel();
    expect(c.state, VoiceState.idle);
    expect(recorder.cancelCount, 1);
    c.dispose();
  });

  test('cancel while converting ignores the late answer', () async {
    final gate = Completer<SpeechResult>();
    final c = make(transcribe: (path, {language}) => gate.future);
    await c.init(defaultLanguage: 'en');
    clip();
    await c.start();
    await Future<void>.delayed(const Duration(milliseconds: 900));
    final pending = c.finish();
    await Future<void>.delayed(const Duration(milliseconds: 50));
    expect(c.state, VoiceState.transcribing);

    await c.cancel();
    gate.complete(const SpeechResult(text: 'late', noSpeech: false));
    expect(await pending, isNull);
    expect(c.state, VoiceState.idle);
    c.dispose();
  });
}
