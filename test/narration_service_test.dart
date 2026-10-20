import 'package:flutter_test/flutter_test.dart';
import 'package:mednarrate/core/services/narration_service.dart';

void main() {
  group('NarrationService.toSpeakable', () {
    test('drops markdown marks and ends every line like a sentence', () {
      const input =
          '## Summary\n**Hemoglobin** is *normal*\n- Take rest\n- Drink water.';
      expect(
        NarrationService.toSpeakable(input),
        'Summary. Hemoglobin is normal. Take rest. Drink water.',
      );
    });

    test('keeps link text and drops the address', () {
      expect(
        NarrationService.toSpeakable('See [your report](https://example.com) today'),
        'See your report today.',
      );
    });

    test('reads a table row as a sentence, without pipes or dashes', () {
      const input = '| Test | Your Result | Flag |\n'
          '|------|-------------|------|\n'
          '| Hemoglobin | **12.5 g/dL** | Low |';
      expect(
        NarrationService.toSpeakable(input),
        'Hemoglobin — Your Result: 12.5 g/dL, Flag: Low.',
      );
    });

    test('empty and symbol-only text has nothing to read', () {
      expect(NarrationService.toSpeakable('   \n  '), '');
      expect(NarrationService.chunkForSpeech(''), isEmpty);
    });
  });

  group('NarrationService.chunkForSpeech', () {
    test('splits at sentence ends and loses nothing', () {
      final text =
          List.generate(50, (i) => 'Sentence number $i is here.').join(' ');
      final chunks = NarrationService.chunkForSpeech(text, maxChars: 100);

      expect(chunks.length, greaterThan(1));
      expect(chunks.every((c) => c.length <= 100), isTrue);
      expect(chunks.join(' '), text);
    });

    test('cuts one very long sentence into pieces of the allowed size', () {
      final text = List.filled(250, 'a').join();
      final chunks = NarrationService.chunkForSpeech(text, maxChars: 100);

      expect(chunks.map((c) => c.length), [100, 100, 50]);
      expect(chunks.join(), text);
    });
  });
}
