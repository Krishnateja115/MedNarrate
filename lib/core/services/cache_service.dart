import 'package:hive_flutter/hive_flutter.dart';
import '../../features/reports/models/report_model.dart';
import '../../models/cached/cached_report.dart';
import '../../models/cached/cached_lab_value.dart';
import '../../models/cached/cached_chat_message.dart';

class CacheService {
  CacheService._();
  static final CacheService instance = CacheService._();

  late Box<CachedReport> _reportsBox;
  late Box<CachedLabValue> _labValuesBox;
  late Box<CachedChatMessage> _chatMessagesBox;
  late Box<dynamic> _metadataBox;

  bool _initialized = false;

  Future<void> initialize() async {
    if (_initialized) return;

    await Hive.initFlutter();
    
    // Register Adapters
    if (!Hive.isAdapterRegistered(0)) Hive.registerAdapter(CachedReportAdapter());
    if (!Hive.isAdapterRegistered(1)) Hive.registerAdapter(CachedLabValueAdapter());
    if (!Hive.isAdapterRegistered(2)) Hive.registerAdapter(CachedChatMessageAdapter());

    // Open boxes
    _reportsBox = await Hive.openBox<CachedReport>('reports');
    _labValuesBox = await Hive.openBox<CachedLabValue>('lab_values');
    _chatMessagesBox = await Hive.openBox<CachedChatMessage>('chat_messages');
    _metadataBox = await Hive.openBox<dynamic>('metadata');

    _initialized = true;
  }

  Future<void> saveReports(List<ReportModel> reports) async {
    final Map<String, CachedReport> entries = {};
    for (var r in reports) {
      entries[r.id] = CachedReport(
        id: r.id,
        userId: 'current', // Note: proper user isolation would need the user ID
        title: r.title,
        reportType: r.reportType,
        uploadedAt: r.uploadedAt ?? DateTime.now(),
        status: r.extractedText != null ? 'completed' : 'pending',
        summaryText: r.extractedText ?? '',
        reportDate: r.reportDate,
      );
    }
    await _reportsBox.putAll(entries);
    await _metadataBox.put('reports_cached_at', DateTime.now().toIso8601String());
  }

  List<ReportModel> getCachedReports() {
    final list = _reportsBox.values.toList()
      ..sort((a, b) => b.uploadedAt.compareTo(a.uploadedAt));
    
    return list.map((c) => ReportModel(
      id: c.id,
      title: c.title,
      hospital: '',
      reportDate: c.reportDate,
      fileName: '',
      filePath: '',
      fileType: '',
      reportType: c.reportType,
      extractedText: c.summaryText,
      processingStatus: 'completed',
      isFavourite: false,
      uploadedAt: c.uploadedAt,
    )).toList();
  }

  bool isReportCacheStale() {
    final cachedAtStr = _metadataBox.get('reports_cached_at') as String?;
    if (cachedAtStr == null) return true;
    final cachedAt = DateTime.parse(cachedAtStr);
    return DateTime.now().difference(cachedAt).inMinutes > 30;
  }

  Future<void> saveLabValues(String reportId, List<dynamic> labValues) async {
    // For brevity, skipping full lab value conversion here.
    // Similar to saveReports.
  }

  List<dynamic> getCachedLabValues(String reportId) {
    return _labValuesBox.values.where((c) => c.reportId == reportId).toList();
  }

  Future<void> saveChatMessages(String sessionId, List<dynamic> messages) async {
    // Similar to saveReports
  }

  List<dynamic> getCachedChatMessages(String sessionId) {
    return _chatMessagesBox.values
        .where((m) => m.sessionId == sessionId)
        .toList()
        ..sort((a, b) => a.timestamp.compareTo(b.timestamp));
  }

  Future<void> clearAll() async {
    await _reportsBox.clear();
    await _labValuesBox.clear();
    await _chatMessagesBox.clear();
    await _metadataBox.clear();
  }

  int getCacheSizeBytes() {
    // Approximate by string length of JSON equivalent or file size.
    // For now, return a placeholder.
    return 1024 * 1024; // 1 MB
  }
}
