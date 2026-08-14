import 'package:flutter_test/flutter_test.dart';
import 'package:mednarrate/main.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  testWidgets('MedNarrate app loads successfully', (WidgetTester tester) async {
    // Mock shared preferences for tests
    SharedPreferences.setMockInitialValues({});
    
    await tester.pumpWidget(const MedNarrateApp());

    // Give timers (like splash screen) time to run without hanging on infinite animations
    await tester.pump();
    await tester.pump(const Duration(seconds: 3));
    await tester.pump();

    // Verify it navigates successfully
    expect(find.byType(MedNarrateApp), findsOneWidget);
  });
}