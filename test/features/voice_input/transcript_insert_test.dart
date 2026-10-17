import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mednarrate/features/voice_input/transcript_insert.dart';

TextEditingController _box(String text, {int? start, int? end}) {
  final c = TextEditingController(text: text);
  c.selection = TextSelection(
    baseOffset: start ?? text.length,
    extentOffset: end ?? start ?? text.length,
  );
  return c;
}

void main() {
  test('fills an empty box', () {
    final c = _box('');
    final r = insertTranscript(c, '  my head hurts  ');
    expect(c.text, 'my head hurts');
    expect(r.inserted, isTrue);
    expect(r.truncated, isFalse);
    expect(c.selection.baseOffset, 13);
  });

  test('appends after existing text with a space', () {
    final c = _box('Hello');
    insertTranscript(c, 'doctor');
    expect(c.text, 'Hello doctor');
  });

  test('inserts at the cursor and keeps the rest', () {
    final c = _box('Hello world', start: 5);
    insertTranscript(c, 'big');
    expect(c.text, 'Hello big world');
    expect(c.selection.baseOffset, 'Hello big'.length);
  });

  test('replaces the selected text', () {
    final c = _box('one two three', start: 4, end: 7);
    insertTranscript(c, 'TWO');
    expect(c.text, 'one TWO three');
  });

  test('works with Indian scripts', () {
    final c = _box('');
    insertTranscript(c, 'எனக்கு தலைவலி');
    expect(c.text, 'எனக்கு தலைவலி');
  });

  test('shortens to the limit between words', () {
    final c = _box('abc');
    final r = insertTranscript(c, 'one two three four five', maxLength: 15);
    expect(r.truncated, isTrue);
    expect(r.inserted, isTrue);
    expect(c.text.length, lessThanOrEqualTo(15));
    expect(c.text, 'abc one two');
  });

  test('does nothing when the box is full', () {
    final c = _box('x' * 10);
    final r = insertTranscript(c, 'more', maxLength: 10);
    expect(r.inserted, isFalse);
    expect(c.text, 'x' * 10);
  });

  test('ignores an empty transcript', () {
    final c = _box('keep');
    final r = insertTranscript(c, '   ');
    expect(r.inserted, isFalse);
    expect(c.text, 'keep');
  });

  test('handles an invalid selection by appending', () {
    final c = TextEditingController(text: 'abc'); // selection is -1
    insertTranscript(c, 'def');
    expect(c.text, 'abc def');
  });
}
