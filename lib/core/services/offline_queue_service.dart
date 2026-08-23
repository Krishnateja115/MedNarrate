import 'package:hive_flutter/hive_flutter.dart';
import '../../models/cached/offline_action.dart';
import 'package:flutter/foundation.dart';

class OfflineQueueService {
  OfflineQueueService._();
  static final OfflineQueueService instance = OfflineQueueService._();
  
  late Box<OfflineAction> _queueBox;
  bool _initialized = false;

  Future<void> initialize() async {
    if (_initialized) return;
    if (!Hive.isAdapterRegistered(3)) Hive.registerAdapter(OfflineActionAdapter());
    _queueBox = await Hive.openBox<OfflineAction>('offline_queue');
    _initialized = true;
  }

  Future<void> enqueueAction(OfflineAction action) async {
    await _queueBox.put(action.id, action);
  }

  List<OfflineAction> getQueue() {
    final actions = _queueBox.values.toList();
    actions.sort((a, b) => a.createdAt.compareTo(b.createdAt));
    return actions;
  }

  Future<void> dequeueAction(String id) async {
    await _queueBox.delete(id);
  }

  Future<void> processQueue(Future<bool> Function(OfflineAction) processor) async {
    final actions = getQueue();
    for (final action in actions) {
      try {
        final success = await processor(action);
        if (success) {
          await dequeueAction(action.id);
        } else {
          // Stop processing if one fails to keep order
          break;
        }
      } catch (e) {
        debugPrint("Error processing queue action: $e");
        break;
      }
    }
  }
}
