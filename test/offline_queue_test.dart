import 'dart:io';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:mednarrate/core/services/offline_queue_service.dart';
import 'package:mednarrate/models/cached/offline_action.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  late Directory tempDir;

  const owner = 'user-a';

  OfflineAction buildAction(String id, DateTime createdAt,
          {String? userId = owner}) =>
      OfflineAction(
        id: id,
        endpoint: '/api/v1/reports',
        method: 'POST',
        body: {'note': 'action $id'},
        createdAt: createdAt,
        userId: userId,
      );

  setUpAll(() async {
    TestWidgetsFlutterBinding.ensureInitialized();
    SharedPreferences.setMockInitialValues({});
    FlutterSecureStorage.setMockInitialValues({});
    tempDir = await Directory.systemTemp.createTemp('offline_queue_test_');
    Hive.init(tempDir.path);
    await OfflineQueueService.instance.initialize();
  });

  tearDownAll(() async {
    await Hive.close();
    if (await tempDir.exists()) {
      await tempDir.delete(recursive: true);
    }
  });

  setUp(() async {
    // Drain the queue through the public API so every test starts empty,
    // without depending on internal fields or re-running initialize().
    for (final action in OfflineQueueService.instance.getQueue()) {
      await OfflineQueueService.instance.dequeueAction(action.id);
    }
  });

  test('enqueueAction + getQueue returns actions ordered oldest-first',
      () async {
    final newer = buildAction('action-2', DateTime(2026, 1, 2));
    final older = buildAction('action-1', DateTime(2026, 1, 1));

    // Enqueue out of chronological order to prove getQueue sorts, not just echoes insertion order.
    await OfflineQueueService.instance.enqueueAction(newer);
    await OfflineQueueService.instance.enqueueAction(older);

    final queue = OfflineQueueService.instance.getQueue();
    expect(queue.length, 2);
    expect(queue.first.id, 'action-1',
        reason:
            'getQueue must return the oldest queued action first so retries are processed in order');
    expect(queue.last.id, 'action-2');
  });

  test('dequeueAction removes exactly the requested action', () async {
    await OfflineQueueService.instance
        .enqueueAction(buildAction('keep', DateTime(2026, 1, 1)));
    await OfflineQueueService.instance
        .enqueueAction(buildAction('remove', DateTime(2026, 1, 2)));

    await OfflineQueueService.instance.dequeueAction('remove');

    final remaining = OfflineQueueService.instance.getQueue();
    expect(remaining.length, 1);
    expect(remaining.single.id, 'keep');
  });

  test(
      'processQueue dequeues successful actions and stops at the first failure to preserve order',
      () async {
    await OfflineQueueService.instance
        .enqueueAction(buildAction('a', DateTime(2026, 1, 1)));
    await OfflineQueueService.instance
        .enqueueAction(buildAction('b', DateTime(2026, 1, 2)));
    await OfflineQueueService.instance
        .enqueueAction(buildAction('c', DateTime(2026, 1, 3)));

    final processedIds = <String>[];
    await OfflineQueueService.instance.processQueue((action) async {
      processedIds.add(action.id);
      return action.id !=
          'b'; // succeed for 'a', fail for 'b', 'c' should never be attempted
    }, userId: owner);

    expect(processedIds, ['a', 'b'],
        reason:
            'processQueue must stop at the first failed action instead of skipping ahead');

    final remainingIds =
        OfflineQueueService.instance.getQueue().map((a) => a.id).toList();
    expect(remainingIds, ['b', 'c'],
        reason:
            'the successfully processed action ("a") must be dequeued; the failed one and anything after it must remain');
  });

  test('processQueue leaves the queue untouched when every action succeeds',
      () async {
    await OfflineQueueService.instance
        .enqueueAction(buildAction('x', DateTime(2026, 1, 1)));
    await OfflineQueueService.instance
        .enqueueAction(buildAction('y', DateTime(2026, 1, 2)));

    await OfflineQueueService.instance
        .processQueue((action) async => true, userId: owner);

    expect(OfflineQueueService.instance.getQueue(), isEmpty);
  });

  test('processQueue never executes another account\'s actions', () async {
    await OfflineQueueService.instance
        .enqueueAction(buildAction('mine', DateTime(2026, 1, 1)));
    await OfflineQueueService.instance.enqueueAction(
        buildAction('theirs', DateTime(2026, 1, 2), userId: 'user-b'));

    final processedIds = <String>[];
    await OfflineQueueService.instance.processQueue((action) async {
      processedIds.add(action.id);
      return true;
    }, userId: owner);

    expect(processedIds, ['mine']);
    final left =
        OfflineQueueService.instance.getQueue().map((a) => a.id).toList();
    expect(left, ['theirs'],
        reason: 'the other account\'s action must remain untouched');
  });

  test('legacy/unowned records are purged and never executed', () async {
    await OfflineQueueService.instance.enqueueAction(
        buildAction('legacy', DateTime(2026, 1, 1), userId: null));

    final processedIds = <String>[];
    await OfflineQueueService.instance.processQueue((action) async {
      processedIds.add(action.id);
      return true;
    }, userId: owner);

    expect(processedIds, isEmpty);
    expect(OfflineQueueService.instance.getQueue(), isEmpty);
  });

  test('processQueue does nothing when no user is signed in', () async {
    await OfflineQueueService.instance
        .enqueueAction(buildAction('a', DateTime(2026, 1, 1)));
    final processedIds = <String>[];
    await OfflineQueueService.instance.processQueue((action) async {
      processedIds.add(action.id);
      return true;
    }, userId: null);
    expect(processedIds, isEmpty);
    expect(OfflineQueueService.instance.getQueue().length, 1);
  });

  test('clearUserQueue removes only that user\'s actions', () async {
    await OfflineQueueService.instance
        .enqueueAction(buildAction('a1', DateTime(2026, 1, 1)));
    await OfflineQueueService.instance.enqueueAction(
        buildAction('b1', DateTime(2026, 1, 2), userId: 'user-b'));

    await OfflineQueueService.instance.clearUserQueue(owner);

    expect(OfflineQueueService.instance.getQueue().map((a) => a.id).toList(),
        ['b1']);
  });
}
