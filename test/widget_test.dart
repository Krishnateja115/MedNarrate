import 'package:flutter_test/flutter_test.dart';
import 'package:mednarrate/main.dart';

void main() {
  testWidgets('MedNarrate app loads successfully',
      (WidgetTester tester) async {

    await tester.pumpWidget(const MedNarrateApp());

    expect(find.text('MedNarrate'), findsOneWidget);
  });
}