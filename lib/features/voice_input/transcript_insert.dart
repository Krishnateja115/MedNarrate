import 'package:flutter/widgets.dart';

/// Puts [transcript] into [controller] at the cursor (or replaces the selected
/// text), adding a space on either side when needed. The text is never sent:
/// the user reads it, edits it if they like, and presses send themselves.
///
/// Returns `inserted: false` when the box is already full, and
/// `truncated: true` when the transcript had to be shortened to fit
/// [maxLength].
({bool inserted, bool truncated}) insertTranscript(
  TextEditingController controller,
  String transcript, {
  int maxLength = 500,
}) {
  final spoken = transcript.trim();
  if (spoken.isEmpty) return (inserted: false, truncated: false);

  final value = controller.value;
  final text = value.text;
  var start = value.selection.start;
  var end = value.selection.end;
  if (start < 0 || end < 0 || start > text.length || end > text.length) {
    start = text.length;
    end = text.length;
  }
  if (start > end) {
    final swap = start;
    start = end;
    end = swap;
  }

  final before = text.substring(0, start);
  final after = text.substring(end);
  final lead = before.isNotEmpty && !RegExp(r'\s$').hasMatch(before) ? ' ' : '';
  final trail = after.isNotEmpty && !RegExp(r'^\s').hasMatch(after) ? ' ' : '';

  final room = maxLength - before.length - after.length;
  var piece = spoken;
  var truncated = false;
  final needed = lead.length + piece.length + trail.length;
  if (needed > room) {
    truncated = true;
    final allowed = room - lead.length - trail.length;
    if (allowed <= 0) return (inserted: false, truncated: true);
    piece = piece.substring(0, allowed);
    // Prefer to stop between words rather than in the middle of one.
    final lastSpace = piece.lastIndexOf(RegExp(r'\s'));
    if (lastSpace > allowed ~/ 2) piece = piece.substring(0, lastSpace);
    piece = piece.trimRight();
    if (piece.isEmpty) return (inserted: false, truncated: true);
  }

  final inserted = '$lead$piece$trail';
  final newText = '$before$inserted$after';
  final caret = before.length + lead.length + piece.length + trail.length;
  controller.value = TextEditingValue(
    text: newText,
    selection: TextSelection.collapsed(offset: caret),
  );
  return (inserted: true, truncated: truncated);
}
