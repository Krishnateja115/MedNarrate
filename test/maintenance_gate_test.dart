import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mednarrate/core/services/maintenance_controller.dart';
import 'package:mednarrate/features/maintenance/screens/maintenance_screen.dart';

void main() {
  testWidgets('full-screen maintenance state blocks until the server clears it',
      (tester) async {
    var response = <String, dynamic>{
      'is_enabled': true,
      'scope': 'all',
      'message': 'System upgrade in progress',
    };
    final controller = MaintenanceController(loadStatus: () async => response);
    await controller.refresh();
    expect(controller.blocksApp, isTrue);

    await tester.pumpWidget(MaterialApp(
      home: MaintenanceScreen(controller: controller),
    ));
    expect(find.text('MedNarrate is under maintenance'), findsOneWidget);
    expect(find.text('System upgrade in progress'), findsOneWidget);
    expect(find.byType(PopScope), findsOneWidget);
    expect(tester.widget<PopScope>(find.byType(PopScope)).canPop, isFalse);

    response = {'is_enabled': false, 'scope': null, 'message': null};
    await tester.tap(find.text('Check again'));
    await tester.pump();
    expect(controller.blocksApp, isFalse);
    controller.dispose();
  });

  test('unknown availability blocks cached screens; scoped work does not',
      () async {
    var unavailable = true;
    final controller = MaintenanceController(loadStatus: () async {
      if (unavailable) throw Exception('offline');
      return {'is_enabled': true, 'scope': 'chat', 'message': 'Chat is paused'};
    });
    expect(controller.blocksApp, isTrue);
    await controller.refresh();
    expect(controller.availability, MaintenanceAvailability.unavailable);
    expect(controller.blocksApp, isTrue);
    unavailable = false;
    await controller.refresh();
    expect(controller.availability, MaintenanceAvailability.available);
    expect(controller.blocksApp, isFalse);
    controller.dispose();
  });
}
