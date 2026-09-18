import 'dart:async';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'offline_queue_service.dart';
import 'api_service.dart';
import 'api_exception.dart';

class ConnectivityService {
  ConnectivityService._();
  static final ConnectivityService instance = ConnectivityService._();

  final Connectivity _connectivity = Connectivity();
  final StreamController<bool> _controller = StreamController<bool>.broadcast();

  bool _isOnline = true;
  bool get isOnline => _isOnline;
  Stream<bool> get onConnectivityChanged => _controller.stream;

  Future<void> initialize() async {
    final result = await _connectivity.checkConnectivity();
    _updateStatus(result);

    _connectivity.onConnectivityChanged.listen(_updateStatus);
  }

  void _updateStatus(List<ConnectivityResult> results) {
    bool online = false;
    for (var r in results) {
      if (r != ConnectivityResult.none) {
        online = true;
        break;
      }
    }

    if (_isOnline != online) {
      _isOnline = online;
      _controller.add(online);
      if (online) {
        OfflineQueueService.instance.processQueue((action) async {
          try {
            await ApiService.instance.executeOfflineAction(action);
            return true;
          } catch (e) {
            if (e is ApiException) {
              // 4xx errors (except 401/408) are client-side errors that will never succeed.
              // Drop the action to prevent infinite loops.
              if (e.statusCode >= 400 && e.statusCode < 500 && e.statusCode != 401 && e.statusCode != 408) {
                return true;
              }
            }
            return false;
          }
        });
      }
    }
  }
}
