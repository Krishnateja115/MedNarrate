import 'package:health/health.dart';

class HealthService {
  HealthService._();
  static final HealthService instance = HealthService._();

  final Health _health = Health();

  final List<HealthDataType> _dataTypes = [
    HealthDataType.STEPS,
    HealthDataType.HEART_RATE,
    HealthDataType.SLEEP_ASLEEP,
  ];

  Future<bool> requestAuthorization() async {
    try {
      final hasPermissions = await _health.hasPermissions(_dataTypes) ?? false;
      if (hasPermissions) return true;

      return await _health.requestAuthorization(_dataTypes);
    } catch (e) {
      print("Health authorization error: $e");
      return false;
    }
  }

  Future<List<HealthDataPoint>> getHealthData(DateTime start, DateTime end) async {
    try {
      bool authorized = await requestAuthorization();
      if (!authorized) return [];

      List<HealthDataPoint> healthData = await _health.getHealthDataFromTypes(
        startTime: start,
        endTime: end,
        types: _dataTypes,
      );

      // Clean duplicates
      return Health().removeDuplicates(healthData);
    } catch (e) {
      print("Error fetching health data: $e");
      return [];
    }
  }

  Future<int> getStepsToday() async {
    try {
      bool authorized = await requestAuthorization();
      if (!authorized) return 0;
      
      final now = DateTime.now();
      final midnight = DateTime(now.year, now.month, now.day);
      int? steps = await _health.getTotalStepsInInterval(midnight, now);
      return steps ?? 0;
    } catch (e) {
      print("Error fetching steps: $e");
      return 0;
    }
  }
}
