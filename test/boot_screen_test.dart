import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mednarrate/boot_screen.dart';

void main() {
  testWidgets('boot screen shows the brand and the status text',
      (tester) async {
    await tester.pumpWidget(
      const MaterialApp(home: BootScreen(status: 'Getting things ready...')),
    );
    // The screen animates forever (progress line, glow), so never settle.
    await tester.pump(const Duration(milliseconds: 1200));

    expect(find.text('MedNarrate'), findsOneWidget);
    expect(find.text('AI Medical Report Assistant'), findsOneWidget);
    expect(find.text('Getting things ready...'), findsOneWidget);
    expect(find.byType(LinearProgressIndicator), findsOneWidget);
    expect(find.byType(Image), findsOneWidget);
  });

  testWidgets('boot screen stays black like the native launch screen',
      (tester) async {
    await tester.pumpWidget(
      const MaterialApp(home: BootScreen(status: 'x')),
    );
    final scaffold = tester.widget<Scaffold>(find.byType(Scaffold));
    expect(scaffold.backgroundColor, Colors.black);
  });
}
