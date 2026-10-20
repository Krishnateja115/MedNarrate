import 'package:flutter_test/flutter_test.dart';
import 'package:mednarrate/core/utils/markdown_tables.dart';

void main() {
  group('flattenMarkdownTables', () {
    test('turns each data row into one bullet and drops header and dashes', () {
      const input = 'Intro\n'
          '| Test | Your Result | Reference Range | Flag |\n'
          '|------|-------------|-----------------|------|\n'
          '| Hemoglobin | 12.5 g/dL | 13.0–17.0 g/dL | Low |\n'
          '| WBC | 9,000 | 4,000–11,000 | Normal |\n'
          'Outro';
      expect(
        flattenMarkdownTables(input),
        'Intro\n'
        '- Hemoglobin — Your Result: 12.5 g/dL, Reference Range: 13.0–17.0 g/dL, Flag: Low\n'
        '- WBC — Your Result: 9,000, Reference Range: 4,000–11,000, Flag: Normal\n'
        'Outro',
      );
    });

    test('leaves text without a table untouched', () {
      const input = 'Plain line\n- a bullet\nA | inside text';
      expect(flattenMarkdownTables(input), input);
    });

    test('handles a table with no header row', () {
      expect(flattenMarkdownTables('| Iron | 80 |'), '- Iron — 80');
    });
  });
}
