import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:mednarrate/core/services/cache_service.dart';
import 'package:mednarrate/features/reports/models/report_model.dart';
import 'package:path_provider_platform_interface/path_provider_platform_interface.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Points Hive's `initFlutter()` at a real temp directory instead of asking
/// the (unavailable in tests) platform channel for the app documents folder.
class _FakePathProviderPlatform extends PathProviderPlatform {
  _FakePathProviderPlatform(this._path);
  final String _path;

  @override
  Future<String?> getApplicationDocumentsPath() async => _path;
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late Directory tempDir;

  ReportModel buildReport(String id, DateTime uploadedAt) => ReportModel(
        id: id,
        title: 'Report $id',
        hospital: 'General Hospital',
        reportDate: uploadedAt,
        fileName: '$id.pdf',
        filePath: '/mock/$id.pdf',
        fileType: 'application/pdf',
        reportType: 'CBC',
        extractedText: 'extracted text for $id',
        processingStatus: 'completed',
        isFavourite: false,
        uploadedAt: uploadedAt,
      );

  setUpAll(() async {
    tempDir = await Directory.systemTemp.createTemp('cache_service_test_');
    PathProviderPlatform.instance = _FakePathProviderPlatform(tempDir.path);
    SharedPreferences.setMockInitialValues({});
    await CacheService.instance.initialize(userId: 'test-user');
  });

  tearDownAll(() async {
    await Hive.close();
    if (await tempDir.exists()) {
      await tempDir.delete(recursive: true);
    }
  });

  setUp(() async {
    // Reset through the public API so every test starts from a clean cache.
    await CacheService.instance.clearAll();
  });

  test('saveReports + getCachedReports round-trips and returns newest report first', () async {
    final older = buildReport('r1', DateTime(2026, 1, 1));
    final newer = buildReport('r2', DateTime(2026, 2, 1));

    await CacheService.instance.saveReports([older, newer]);

    final cached = CacheService.instance.getCachedReports();
    expect(cached.length, 2);
    expect(cached.first.id, 'r2',
        reason: 'getCachedReports must return the most recently uploaded report first');
    expect(cached.last.id, 'r1');
    expect(cached.first.extractedText, 'extracted text for r2');
  });

  test('saveReports replaces the previous cache instead of accumulating deleted reports', () async {
    await CacheService.instance.saveReports([buildReport('r1', DateTime(2026, 1, 1))]);
    await CacheService.instance.saveReports([buildReport('r2', DateTime(2026, 1, 2))]);

    final cached = CacheService.instance.getCachedReports();
    expect(cached.length, 1,
        reason: 'a fresh saveReports call must clear stale entries, not just add to them');
    expect(cached.single.id, 'r2');
  });

  test('isReportCacheStale is true with no cache and false right after saving', () async {
    expect(CacheService.instance.isReportCacheStale(), isTrue,
        reason: 'an empty cache must always be considered stale');

    await CacheService.instance.saveReports([buildReport('r1', DateTime.now())]);

    expect(CacheService.instance.isReportCacheStale(), isFalse,
        reason: 'a cache written moments ago must not be considered stale');
  });

  test('clearAll empties the cache', () async {
    await CacheService.instance.saveReports([buildReport('r1', DateTime.now())]);
    expect(CacheService.instance.getCachedReports(), isNotEmpty);

    await CacheService.instance.clearAll();

    expect(CacheService.instance.getCachedReports(), isEmpty);
    expect(CacheService.instance.isReportCacheStale(), isTrue);
  });
}
