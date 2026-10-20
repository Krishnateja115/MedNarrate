import 'package:flutter/foundation.dart';
import 'package:flutter_tts/flutter_tts.dart';

import '../utils/markdown_tables.dart';

/// How a read-aloud request ended.
enum NarrationResult {
  /// The whole text was read.
  finished,

  /// The person (or a new request) stopped it part-way.
  stopped,

  /// The phone has no voice installed for the language.
  voiceMissing,

  /// There was no readable text.
  nothingToRead,

  /// The voice engine failed or is not available on this device.
  failed,
}

/// Reads report summaries aloud with the phone's own text-to-speech voice.
///
/// Everything runs on the device: no extra account, no cost, and the text of a
/// medical report is never sent anywhere for this feature. The voice engine is
/// created on first use, so screens that only show the button never touch the
/// platform plugin.
class NarrationService {
  NarrationService._();

  static final NarrationService instance = NarrationService._();

  /// Voice locale for each language the app supports.
  static const Map<String, String> _voiceLocales = {
    'en': 'en-IN',
    'hi': 'hi-IN',
    'ta': 'ta-IN',
    'te': 'te-IN',
    'kn': 'kn-IN',
    'ml': 'ml-IN',
    'mr': 'mr-IN',
    'bn': 'bn-IN',
  };

  /// Android refuses a single utterance of about 4000 characters or more.
  static const int _maxChunkChars = 3000;

  FlutterTts? _tts;
  bool _configured = false;

  /// Bumped by [stop] and by every new request so an older read-aloud knows to quit.
  int _session = 0;

  /// True while something is being read.
  final ValueNotifier<bool> isSpeaking = ValueNotifier<bool>(false);

  FlutterTts _engine() => _tts ??= FlutterTts();

  /// Reads [text] in [languageCode] (e.g. `hi`). Completes when reading ends.
  Future<NarrationResult> speak(String text, String languageCode) async {
    final chunks = chunkForSpeech(toSpeakable(text));
    if (chunks.isEmpty) return NarrationResult.nothingToRead;

    final session = ++_session;
    try {
      final tts = _engine();
      await tts.stop();
      if (!_configured) {
        await tts.awaitSpeakCompletion(true);
        await tts.setSpeechRate(0.45);
        await tts.setVolume(1.0);
        await tts.setPitch(1.0);
        _configured = true;
      }
      if (!await _selectVoice(tts, languageCode)) {
        return NarrationResult.voiceMissing;
      }
      if (session != _session) return NarrationResult.stopped;

      isSpeaking.value = true;
      for (final chunk in chunks) {
        if (session != _session) return NarrationResult.stopped;
        await tts.speak(chunk);
      }
      return session == _session
          ? NarrationResult.finished
          : NarrationResult.stopped;
    } catch (error) {
      debugPrint('Read aloud failed: $error');
      return NarrationResult.failed;
    } finally {
      if (session == _session) isSpeaking.value = false;
    }
  }

  /// Stops reading right away. Safe to call when nothing is playing.
  Future<void> stop() async {
    _session++;
    isSpeaking.value = false;
    try {
      await _tts?.stop();
    } catch (error) {
      debugPrint('Stopping read aloud failed: $error');
    }
  }

  Future<bool> _selectVoice(FlutterTts tts, String languageCode) async {
    final primary = _voiceLocales[languageCode] ?? languageCode;
    final candidates = <String>[primary, if (languageCode == 'en') 'en-US'];
    for (final locale in candidates) {
      final available = await tts.isLanguageAvailable(locale);
      if (available == true || available == 1) {
        await tts.setLanguage(locale);
        return true;
      }
    }
    return false;
  }

  /// Plain sentences from the markdown-style summary text: heading marks,
  /// bullets and emphasis are dropped and every line ends like a sentence so the
  /// voice pauses between items instead of running them together.
  @visibleForTesting
  static String toSpeakable(String text) {
    final cleaned = flattenMarkdownTables(text)
        .replaceAllMapped(
            RegExp(r'\[([^\]]*)\]\([^)]*\)'), (m) => m.group(1) ?? '')
        .replaceAll(RegExp(r'^\s{0,3}#{1,6}\s*', multiLine: true), '')
        .replaceAll(RegExp(r'^\s*[-*•]\s+', multiLine: true), '')
        .replaceAll(RegExp(r'[*_`>#|]+'), ' ');
    final lines = cleaned
        .split(RegExp(r'[\r\n]+'))
        .map((line) => line.trim())
        .where((line) => line.isNotEmpty)
        .map((line) => RegExp(r'[.!?।:;]$').hasMatch(line) ? line : '$line.');
    return lines
        .join(' ')
        .replaceAll(RegExp(r'\s{2,}'), ' ')
        .replaceAllMapped(RegExp(r'\s+([,.;:!?])'), (m) => m.group(1)!)
        .trim();
  }

  /// Splits [text] at sentence ends into pieces of at most [maxChars].
  @visibleForTesting
  static List<String> chunkForSpeech(String text,
      {int maxChars = _maxChunkChars}) {
    final clean = text.trim();
    if (clean.isEmpty) return const [];

    final chunks = <String>[];
    var current = StringBuffer();
    void flush() {
      if (current.isNotEmpty) {
        chunks.add(current.toString().trim());
        current = StringBuffer();
      }
    }

    for (final sentence in clean.split(RegExp(r'(?<=[.!?।])\s+'))) {
      if (sentence.length > maxChars) {
        flush();
        for (var start = 0; start < sentence.length; start += maxChars) {
          final end = start + maxChars > sentence.length
              ? sentence.length
              : start + maxChars;
          chunks.add(sentence.substring(start, end));
        }
        continue;
      }
      if (current.length + sentence.length + 1 > maxChars) flush();
      if (current.isNotEmpty) current.write(' ');
      current.write(sentence);
    }
    flush();
    return chunks;
  }
}
