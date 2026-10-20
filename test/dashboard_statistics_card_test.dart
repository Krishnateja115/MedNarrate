import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mednarrate/features/dashboard/widgets/dashboard_statistics_card.dart';

void main() {
  Widget host(DashboardStatisticsCard card) =>
      MaterialApp(home: Scaffold(body: Row(children: [card])));

  testWidgets('tapping the card runs onTap and shows the arrow', (tester) async {
    var taps = 0;
    await tester.pumpWidget(host(DashboardStatisticsCard(
      title: 'Reports',
      value: '2',
      icon: Icons.description_outlined,
      color: Colors.teal,
      onTap: () => taps++,
    )));

    expect(find.byIcon(Icons.chevron_right_rounded), findsOneWidget);
    await tester.tap(find.text('Reports'));
    expect(taps, 1);
  });

  testWidgets('without onTap there is no arrow', (tester) async {
    await tester.pumpWidget(host(const DashboardStatisticsCard(
      title: 'Reports',
      value: '2',
      icon: Icons.description_outlined,
      color: Colors.teal,
    )));

    expect(find.byIcon(Icons.chevron_right_rounded), findsNothing);
  });
}
