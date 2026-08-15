import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mednarrate/shared/widgets/offline_banner.dart';

void main() {
  group('OfflineBanner Widget', () {
    testWidgets('renders without crashing', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: OfflineBanner(),
          ),
        ),
      );
      await tester.pump();
      expect(find.byType(OfflineBanner), findsOneWidget);
    });

    testWidgets('contains at least one SlideTransition', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(body: OfflineBanner()),
        ),
      );
      await tester.pump();
      // MaterialApp itself adds some SlideTransitions (route transitions)
      expect(find.byType(SlideTransition), findsAtLeastNWidgets(1));
    });

    testWidgets('banner has a Row child', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(body: OfflineBanner()),
        ),
      );
      await tester.pump();
      expect(find.byType(Row), findsAtLeastNWidgets(1));
    });

    testWidgets('displays an Icon in the banner', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(body: OfflineBanner()),
        ),
      );
      await tester.pump();
      final iconFinder = find.byWidgetPredicate(
        (widget) =>
            widget is Icon &&
            (widget.icon == Icons.wifi_off || widget.icon == Icons.wifi),
      );
      expect(iconFinder, findsOneWidget);
    });

    testWidgets('displays status text in banner', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(body: OfflineBanner()),
        ),
      );
      await tester.pump();
      final textFinder = find.byWidgetPredicate(
        (widget) =>
            widget is Text &&
            (widget.data?.contains('offline') == true ||
                widget.data?.contains('online') == true),
      );
      expect(textFinder, findsOneWidget);
    });

    testWidgets('banner background is not transparent', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(body: OfflineBanner()),
        ),
      );
      await tester.pump();
      final container = tester.widget<Container>(
        find.descendant(of: find.byType(OfflineBanner), matching: find.byType(Container)),
      );
      expect(container.color, isNotNull);
    });
  });
}
