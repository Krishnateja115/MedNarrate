/// Turns markdown tables into plain bullet lines.
///
/// The AI summary sometimes comes back with a table (`| Test | Result |`).
/// The report screen has no table view, so the raw pipes would show up on
/// screen and be read out loud. Each data row becomes one bullet, e.g.
/// `- Hemoglobin — Your Result: 12.5 g/dL, Reference Range: 13.0–17.0 g/dL, Flag: Low`.
String flattenMarkdownTables(String text) {
  if (!text.contains('|')) return text;

  final output = <String>[];
  final block = <List<String>>[];

  bool isTableLine(String line) {
    final t = line.trim();
    return t.startsWith('|') && '|'.allMatches(t).length >= 2;
  }

  List<String> cellsOf(String line) {
    final cells = line.trim().split('|').map((c) => c.trim()).toList();
    if (cells.isNotEmpty && cells.first.isEmpty) cells.removeAt(0);
    if (cells.isNotEmpty && cells.last.isEmpty) cells.removeLast();
    return cells;
  }

  bool isSeparator(List<String> cells) =>
      cells.isNotEmpty && cells.every((c) => RegExp(r'^:?-{2,}:?$').hasMatch(c));

  void flushBlock() {
    if (block.isEmpty) return;
    List<String>? header;
    var rows = block;
    if (block.length >= 2 && isSeparator(block[1])) {
      header = block.first;
      rows = block.sublist(2);
    }
    for (final cells in rows) {
      if (isSeparator(cells)) continue;
      final values = cells.where((c) => c.isNotEmpty).toList();
      if (values.isEmpty) continue;
      if (cells.length < 2) {
        output.add('- ${cells.first}');
        continue;
      }
      final parts = <String>[];
      for (var i = 1; i < cells.length; i++) {
        if (cells[i].isEmpty) continue;
        final label = (header != null && i < header.length) ? header[i] : '';
        parts.add(label.isEmpty ? cells[i] : '$label: ${cells[i]}');
      }
      final name = cells.first;
      output.add(parts.isEmpty
          ? '- $name'
          : '- ${name.isEmpty ? '' : '$name — '}${parts.join(', ')}');
    }
    block.clear();
  }

  for (final line in text.split('\n')) {
    if (isTableLine(line)) {
      block.add(cellsOf(line));
    } else {
      flushBlock();
      output.add(line);
    }
  }
  flushBlock();
  return output.join('\n');
}
