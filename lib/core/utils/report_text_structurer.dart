/// ReportTextStructurer — presentation-only helper that restores the visual
/// section structure of a patient summary whose line breaks were collapsed
/// (some translated summaries are stored as one continuous paragraph, e.g.
/// "1. Title: body 2. Title: body ...").
///
/// Guarantees:
/// * The stored/translated text is never modified or persisted — this returns
///   a new in-memory string for rendering only.
/// * Only whitespace is replaced by line breaks and markdown markers
///   ("### " for section headings, "• " for list items) are inserted.
///   No words, numbers, units or punctuation are added, removed or reordered.
/// * Text that already contains line breaks (e.g. English, or translations that
///   kept their structure) is returned unchanged.
class ReportTextStructurer {
  ReportTextStructurer._();

  /// ASCII digits plus the native digits of every supported Indic script
  /// (Devanagari, Bengali, Tamil, Telugu, Kannada, Malayalam).
  static const String _digitClass =
      r'0-9\u0966-\u096F\u09E6-\u09EF\u0BE6-\u0BEF\u0C66-\u0C6F\u0CE6-\u0CEF\u0D66-\u0D6F';

  static const List<int> _nativeZeroes = [
    0x0966, 0x09E6, 0x0BE6, 0x0C66, 0x0CE6, 0x0D66,
  ];

  /// Section marker: 1–2 digits + "." + whitespace, at start or after whitespace.
  /// Decimals such as "80.0" never match because no whitespace follows the dot.
  static final RegExp _sectionMarker =
      RegExp('(?:^|(?<=\\s))([$_digitClass]{1,2})\\.\\s+');

  /// Lab-style list item terminator: ")." or ")।" followed by whitespace.
  static final RegExp _itemBoundary = RegExp(r'(?<=\)[.\u0964])\s+');

  /// Inline bullet marker.
  static final RegExp _bulletBoundary = RegExp(r'\s+(?=•\s)');

  static const String _itemSeparator = ' — ';

  /// Converts a run of (possibly native-script) digits to an int, or null.
  static int? parseDigits(String raw) {
    var value = 0;
    for (final rune in raw.runes) {
      int? d;
      if (rune >= 0x30 && rune <= 0x39) {
        d = rune - 0x30;
      } else {
        for (final zero in _nativeZeroes) {
          if (rune >= zero && rune <= zero + 9) {
            d = rune - zero;
            break;
          }
        }
      }
      if (d == null) return null;
      value = value * 10 + d;
    }
    return value;
  }

  /// Returns a render-ready copy of [text] with section structure restored when
  /// the line breaks were lost. Returns [text] unchanged otherwise.
  static String restoreStructure(String text) {
    final trimmed = text.trim();
    if (trimmed.isEmpty || trimmed.contains('\n')) return text;

    final starts = <int>[];
    var expected = 1;
    for (final m in _sectionMarker.allMatches(trimmed)) {
      final n = parseDigits(m.group(1)!);
      if (n == expected) {
        starts.add(m.start);
        expected++;
      }
    }

    // Need at least two sequential numbered sections to be confident that the
    // text follows the numbered report template.
    if (starts.length < 2) return _formatBody(trimmed);

    final out = <String>[];
    final preamble = trimmed.substring(0, starts.first).trim();
    if (preamble.isNotEmpty) out.add(_formatBody(preamble));

    for (var i = 0; i < starts.length; i++) {
      final end = i + 1 < starts.length ? starts[i + 1] : trimmed.length;
      out.add(_formatSection(trimmed.substring(starts[i], end).trim()));
    }
    return out.join('\n\n');
  }

  /// "N. Title: body" → "### N. Title:\nbody-lines". The colon is kept.
  static String _formatSection(String section) {
    final colon = section.indexOf(':');
    // Only treat the leading clause as a heading when it is short.
    if (colon <= 0 || colon > 120) return '### $section';
    final heading = section.substring(0, colon + 1).trim();
    final body = section.substring(colon + 1).trim();
    if (body.isEmpty) return '### $heading';
    return '### $heading\n${_formatBody(body)}';
  }

  /// Splits a section body into list lines when it contains explicit bullets
  /// or lab-style items ("Name: value — status (range)."). Plain prose is left
  /// as a single paragraph.
  static String _formatBody(String body) {
    final hasBullets = body.contains('• ');
    final itemCount = _itemSeparator.allMatches(body).length;
    if (!hasBullets && itemCount < 2) return body;

    final segments = <String>[];
    for (final part in body.split(_bulletBoundary)) {
      if (itemCount >= 2) {
        segments.addAll(part.split(_itemBoundary));
      } else {
        segments.add(part);
      }
    }

    final lines = <String>[];
    for (var seg in segments) {
      seg = seg.trim();
      if (seg.isEmpty) continue;
      final isBullet = seg.startsWith('• ');
      if (isBullet) seg = seg.substring(2).trim();

      final dash = seg.indexOf(_itemSeparator);
      if (dash < 0) {
        lines.add(isBullet ? '• $seg' : seg);
        continue;
      }

      // "Group label: Item: value — ..." → label line + item line.
      final head = seg.substring(0, dash);
      final firstColon = head.indexOf(': ');
      if (firstColon > 0 && head.indexOf(': ', firstColon + 2) > 0) {
        lines.add(seg.substring(0, firstColon + 1).trim());
        seg = seg.substring(firstColon + 1).trim();
      }
      lines.add('• $seg');
    }
    return lines.join('\n');
  }
}
