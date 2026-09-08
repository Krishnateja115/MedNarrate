import 'package:flutter_test/flutter_test.dart';
import 'package:mednarrate/core/services/health_tip_service.dart';
import 'package:mednarrate/core/services/health_tips.dart';

void main() {
  final service = HealthTipService.instance;

  group('HealthTipService', () {
    test('has exactly 366 tips', () {
      expect(kHealthTips.length, equals(366));
    });

    test('same date always returns the same tip', () {
      final date = DateTime(2024, 9, 8);
      expect(service.getTipForDate(date), equals(service.getTipForDate(date)));
    });

    test('consecutive dates return different tips', () {
      final date1 = DateTime(2024, 1, 1);
      final date2 = DateTime(2024, 1, 2);
      expect(service.getTipForDate(date1), isNot(service.getTipForDate(date2)));
    });

    test('all 366 consecutive days produce 366 unique tips', () {
      final startDate = DateTime(2024, 1, 1); // 2024 is a leap year
      final tips = <String>{};
      for (int i = 0; i < 366; i++) {
        final date = startDate.add(Duration(days: i));
        tips.add(service.getTipForDate(date));
      }
      expect(tips.length, equals(366),
          reason: 'Every day in a leap year should show a unique tip');
    });

    test('all 365 consecutive days in a normal year produce 365 unique tips', () {
      final startDate = DateTime(2023, 1, 1); // 2023 is not a leap year
      final tips = <String>{};
      for (int i = 0; i < 365; i++) {
        final date = startDate.add(Duration(days: i));
        tips.add(service.getTipForDate(date));
      }
      expect(tips.length, equals(365),
          reason: 'Every day in a normal year should show a unique tip');
    });

    test('February 28 and February 29 return different tips in a leap year', () {
      final feb28 = DateTime(2024, 2, 28);
      final feb29 = DateTime(2024, 2, 29);
      expect(service.getTipForDate(feb28), isNot(service.getTipForDate(feb29)));
    });

    test('February 29 and March 1 return different tips in a leap year', () {
      final feb29 = DateTime(2024, 2, 29);
      final mar1 = DateTime(2024, 3, 1);
      expect(service.getTipForDate(feb29), isNot(service.getTipForDate(mar1)));
    });

    test('day 366 (after full cycle) is different from day 365', () {
      final day365 = DateTime(2024, 1, 1).add(const Duration(days: 364));
      final day366 = DateTime(2024, 1, 1).add(const Duration(days: 365));
      // After 366 unique tips, tip 366 wraps to tip[0] — different from tip[365].
      expect(service.getTipForDate(day365), isNot(service.getTipForDate(day366)));
    });

    test('time-of-day does not affect the tip', () {
      final morning = DateTime(2024, 6, 15, 8, 0, 0);
      final evening = DateTime(2024, 6, 15, 20, 30, 0);
      expect(service.getTipForDate(morning), equals(service.getTipForDate(evening)));
    });

    test('tip index wraps after the full 366-tip cycle', () {
      final referenceDate = DateTime(2000, 1, 1);
      final after366 = referenceDate.add(const Duration(days: 366));
      expect(
        service.getTipForDate(referenceDate),
        equals(service.getTipForDate(after366)),
        reason: 'After one full 366-day cycle the tips should restart',
      );
    });

    test('no individual tip string is empty', () {
      for (final tip in kHealthTips) {
        expect(tip.trim().isNotEmpty, isTrue,
            reason: 'Tip "$tip" should not be empty');
      }
    });

    test('all 366 tip strings are unique', () {
      final unique = kHealthTips.toSet();
      expect(unique.length, equals(kHealthTips.length),
          reason: 'Every tip string in kHealthTips must be unique');
    });

    test('tipCount returns 366', () {
      expect(service.tipCount, equals(366));
    });
  });
}
