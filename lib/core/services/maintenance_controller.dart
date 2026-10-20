import 'dart:async';

import 'package:flutter/foundation.dart';

import 'api_service.dart';

enum MaintenanceAvailability { checking, available, active, unavailable }

/// The server is authoritative. An unknown status blocks navigation until
/// availability can be verified, so cached screens cannot bypass maintenance.
class MaintenanceController extends ChangeNotifier {
  MaintenanceController({Future<Map<String, dynamic>> Function()? loadStatus})
      : _loadStatus = loadStatus ?? ApiService.instance.getMaintenanceStatus;

  static final MaintenanceController instance = MaintenanceController();

  final Future<Map<String, dynamic>> Function() _loadStatus;
  Timer? _timer;
  Future<void>? _inFlight;

  MaintenanceAvailability availability = MaintenanceAvailability.checking;
  String message = 'MedNarrate is temporarily under maintenance. Please try again shortly.';

  bool get blocksApp => availability != MaintenanceAvailability.available;

  Future<void> start() async {
    _timer ??= Timer.periodic(const Duration(seconds: 15), (_) => refresh());
    await refresh();
  }

  Future<void> refresh() {
    return _inFlight ??= _check().whenComplete(() => _inFlight = null);
  }

  Future<void> _check() async {
    try {
      final status = await _loadStatus().timeout(const Duration(seconds: 5));
      if (status['is_enabled'] == true && status['scope'] == 'all') {
        final notice = status['message'];
        message = notice is String && notice.trim().isNotEmpty
            ? notice.trim()
            : 'MedNarrate is temporarily under maintenance. Please try again shortly.';
        availability = MaintenanceAvailability.active;
      } else {
        availability = MaintenanceAvailability.available;
      }
    } catch (_) {
      // A network error cannot prove that maintenance has ended.
      availability = availability == MaintenanceAvailability.active
          ? MaintenanceAvailability.active
          : MaintenanceAvailability.unavailable;
    }
    notifyListeners();
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }
}
