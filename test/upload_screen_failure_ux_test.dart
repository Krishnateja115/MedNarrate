import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mednarrate/features/reports/screens/upload_screen.dart';

void main() {
  testWidgets('UploadScreen renders clean initial state without error card', (WidgetTester tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: UploadScreen(),
      ),
    );

    // Verify Title & Hospital fields are present
    expect(find.text('Report Title *'), findsOneWidget);
    expect(find.text('Hospital / Clinic (optional)'), findsOneWidget);

    // Verify initial file chooser is visible
    expect(find.text('Choose a file to analyze'), findsOneWidget);

    // Verify date picker tile defaults to Auto-detect from document
    expect(find.text('Auto-detect from document'), findsOneWidget);

    // Verify error card and retry actions are not rendered initially
    expect(find.text('AI Analysis Unavailable'), findsNothing);
    expect(find.text('Retry AI Analysis'), findsNothing);
    expect(find.text('Re-upload & Analyze'), findsNothing);

    // Bottom submit button should show Upload & Analyze
    expect(find.text('Upload & Analyze'), findsOneWidget);
  });
}
