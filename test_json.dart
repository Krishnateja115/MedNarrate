import 'dart:convert';
void main() {
  final str = '{"findings_json": [{"k": "v"}], "medications_json": [], "ui_labels": {}}';
  final map = jsonDecode(str) as Map<String, dynamic>;
  try {
    final l = List<Map<String, dynamic>>.from(map['findings_json'] ?? []);
    print('SUCCESS FINDINGS');
    final l2 = List<Map<String, dynamic>>.from(map['medications_json'] ?? []);
    print('SUCCESS MEDS');
    final rawLabels = map['ui_labels'] as Map<String, dynamic>? ?? {};
    final labels = rawLabels.map((k, v) => MapEntry(k, v?.toString() ?? ''));
    print('SUCCESS LABELS');
  } catch (e) {
    print('ERROR: $e');
  }
}
