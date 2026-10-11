import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mednarrate/core/services/api_models.dart';
import 'package:mednarrate/features/reports/widgets/lab_result_row.dart';

void main() {
  test('lab model preserves provisional source metadata', () {
    final lab = LabValue.fromMap({
      'test_name': 'Monocytes',
      'original_name': 'Monocytes',
      'value': 9,
      'unit': '%',
      'ref_low': 2,
      'ref_high': 8,
      'flag': 'high',
      'reference_source': 'general_provisional',
      'reference_source_url': 'https://medlineplus.gov/ency/article/003657.htm',
    });

    expect(lab.referenceSource, 'general_provisional');
    expect(lab.referenceSourceUrl, contains('medlineplus.gov'));
  });

  testWidgets('provisional result is visibly labeled', (tester) async {
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: LabResultRow(
          parameter: 'Monocytes',
          unit: '%',
          value: 9,
          minRange: 2,
          maxRange: 8,
          flag: 'high',
          isProvisional: true,
          onTap: () {},
        ),
      ),
    ));

    expect(find.textContaining('PROVISIONAL'), findsOneWidget);
    expect(find.textContaining('(general)'), findsOneWidget);
  });
}
