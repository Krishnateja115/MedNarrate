import 'package:hive_flutter/hive_flutter.dart';
import '../../models/cached/offline_action.dart';
import 'package:flutter/foundation.dart';
import 'keystore_service.dart';

class OfflineQueueService {
  OfflineQueueService._();
  static final OfflineQueueService instance = OfflineQueueService._();

  late Box<OfflineAction> _queueBox;
  bool _initialized = false;

  Future<void> initialize() async {
    if (_initialized) return;
    if (!Hive.isAdapterRegistered(3))
      Hive.registerAdapter(OfflineActionAdapter());

    // Use encryption for the offline queue box
    final key = await KeystoreService.instance.getEncryptionKey();

    try {
      _queueBox = await Hive.openBox<OfflineAction>(
        'offline_queue',
        encryptionCipher: HiveAesCipher(key),
      );
    } catch (e) {
      await Hive.deleteBoxFromDisk('offline_queue');
      _queueBox = await Hive.openBox<OfflineAction>(
        'offline_queue',
        encryptionCipher: HiveAesCipher(key),
      );
    }
    _initialized = true;
  }

  Future<void> enqueueAction(OfflineAction action) async {
    await _queueBox.put(action.id, action);
  }

  List<OfflineAction> getQueue({String? userId}) {
    var actions = _queueBox.values.toList();
    if (userId != null) {
      actions = actions.where((a) => a.userId == userId).toList();
    }
    actions.sort((a, b) => a.createdAt.compareTo(b.createdAt));
    return actions;
  }

  Future<void> clearUserQueue(String userId) async {
    final toDelete = _queueBox.values
        .where((a) => a.userId == userId)
        .map((a) => a.id)
        .toList();
    await _queueBox.deleteAll(toDelete);
  }

  Future<void> dequeueAction(String id) async {
    await _queueBox.delete(id);
  }

  /// Discards queue records that have no owner (legacy or malformed records).
  /// They can never be attributed to an account, so they must never execute.
  Future<void> purgeUnowned() async {
    final ids = _queueBox.values
        .where((a) => a.userId == null || a.userId!.isEmpty)
        .map((a) => a.id)
        .toList();
    if (ids.isNotEmpty) {
      await _queueBox.deleteAll(ids);
    }
  }

  /// Processes only the queued actions owned by [userId]. Actions belonging to
  /// other accounts are left untouched and are never executed with this
  /// account's credentials. Unowned records are purged first.
  Future<void> processQueue(
    Future<bool> Function(OfflineAction) processor, {
    required String? userId,
  }) async {
    await purgeUnowned();
    if (userId == null || userId.isEmpty) return;
    final actions = getQueue(userId: userId);
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
