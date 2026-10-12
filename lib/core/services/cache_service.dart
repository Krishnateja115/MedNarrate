import 'dart:convert';
import 'package:hive_flutter/hive_flutter.dart';
import '../../features/reports/models/report_model.dart';
import '../../models/cached/cached_report.dart';
import '../../models/cached/cached_lab_value.dart';
import '../../models/cached/cached_chat_message.dart';
import 'keystore_service.dart';

class CacheService {
  CacheService._();
  static final CacheService instance = CacheService._();

  late Box<CachedReport> _reportsBox;
  late Box<CachedLabValue> _labValuesBox;
  late Box<CachedChatMessage> _chatMessagesBox;
  late Box<dynamic> _metadataBox;

  bool _initialized = false;
  String _currentUserId = 'default';

  Future<void> initialize({String userId = 'default'}) async {
    if (_initialized && _currentUserId == userId) return;

    _currentUserId = userId;
    await Hive.initFlutter();
    
    final encryptionKey = await KeystoreService.instance.getEncryptionKey();
    final cipher = HiveAesCipher(encryptionKey);
    
    // Register Adapters
    if (!Hive.isAdapterRegistered(0)) Hive.registerAdapter(CachedReportAdapter());
    if (!Hive.isAdapterRegistered(1)) Hive.registerAdapter(CachedLabValueAdapter());
    if (!Hive.isAdapterRegistered(2)) Hive.registerAdapter(CachedChatMessageAdapter());

    // Open boxes with scoped names and encryption
    _reportsBox = await _openBoxSafely<CachedReport>('reports_$_currentUserId', cipher);
    _labValuesBox = await _openBoxSafely<CachedLabValue>('lab_values_$_currentUserId', cipher);
    _chatMessagesBox = await _openBoxSafely<CachedChatMessage>('chat_messages_$_currentUserId', cipher);
    _metadataBox = await _openBoxSafely<dynamic>('metadata_$_currentUserId', cipher);

    _initialized = true;
  }

  Future<Box<T>> _openBoxSafely<T>(String name, HiveAesCipher cipher) async {
    try {
      return await Hive.openBox<T>(name, encryptionCipher: cipher);
    } catch (e) {
      await Hive.deleteBoxFromDisk(name);
      return await Hive.openBox<T>(name, encryptionCipher: cipher);
    }
  }

  Future<void> saveReports(List<ReportModel> reports) async {
    final Map<String, CachedReport> entries = {};
    for (var r in reports) {
      entries[r.id] = CachedReport(
        id: r.id,
        userId: _currentUserId,
        title: r.title,
        reportType: r.reportType,
        uploadedAt: r.uploadedAt,
        status: 'completed',
        summaryText: r.extractedText,
        reportDate: r.reportDate,
      );
    }
    await _reportsBox.clear(); // Clear existing to remove deleted reports
    await _reportsBox.putAll(entries);
    await _metadataBox.put(
      'report_details',
      jsonEncode({for (final report in reports) report.id: report.toMap()}),
    );
    await _metadataBox.put('reports_cached_at', DateTime.now().toIso8601String());
  }

  List<ReportModel> getCachedReports() {
    final list = _reportsBox.values.toList()
      ..sort((a, b) => b.uploadedAt.compareTo(a.uploadedAt));
    
    final details = _readMap('report_details');
    return list.map((c) {
      final detail = details[c.id];
      if (detail is Map) {
        return ReportModel.fromMap(Map<String, dynamic>.from(detail));
      }
      return ReportModel(
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
      );
    }).toList();
  }

  ReportModel? getCachedReport(String reportId) {
    final detail = _readMap('report_details')[reportId];
    if (detail is Map) {
      return ReportModel.fromMap(Map<String, dynamic>.from(detail));
    }
    for (final report in getCachedReports()) {
      if (report.id == reportId) return report;
    }
    return null;
  }

  Future<void> saveReport(ReportModel report) async {
    final details = _readMap('report_details');
    details[report.id] = report.toMap();
    await _metadataBox.put('report_details', jsonEncode(details));
    await _reportsBox.put(
      report.id,
      CachedReport(
        id: report.id,
        userId: _currentUserId,
        title: report.title,
        reportType: report.reportType,
        uploadedAt: report.uploadedAt,
        status: report.processingStatus,
        summaryText: report.extractedText,
        reportDate: report.reportDate,
      ),
    );
  }

  bool isReportCacheStale() {
    final cachedAtStr = _metadataBox.get('reports_cached_at') as String?;
    if (cachedAtStr == null) return true;
    final cachedAt = DateTime.parse(cachedAtStr);
    return DateTime.now().difference(cachedAt).inMinutes > 30;
  }

  Future<void> saveLabValues(String reportId, List<dynamic> labValues) async {
    await _metadataBox.put('lab_values:$reportId', jsonEncode(labValues));
  }

  List<dynamic> getCachedLabValues(String reportId) {
    return _readList('lab_values:$reportId');
  }

  Future<void> saveChatMessages(String sessionId, List<dynamic> messages) async {
    await _metadataBox.put('chat_messages:$sessionId', jsonEncode(messages));
  }

  List<dynamic> getCachedChatMessages(String sessionId) {
    return _readList('chat_messages:$sessionId');
  }

  Future<void> saveChatSessions(List<dynamic> sessions) async {
    await _metadataBox.put('chat_sessions', jsonEncode(sessions));
  }

  List<dynamic> getCachedChatSessions() => _readList('chat_sessions');

  Future<void> saveAnalysis(String reportId, Map<String, dynamic> analysis) async {
    await _metadataBox.put('analysis:$reportId', jsonEncode(analysis));
    final values = analysis['structured_lab_values'];
    if (values is List) await saveLabValues(reportId, values);
  }

  Map<String, dynamic>? getCachedAnalysis(String reportId) {
    final data = _metadataBox.get('analysis:$reportId');
    if (data is! String) return null;
    try {
      return Map<String, dynamic>.from(jsonDecode(data) as Map);
    } catch (_) {
      return null;
    }
  }

  Map<String, dynamic> _readMap(String key) {
    final data = _metadataBox.get(key);
    if (data is! String) return {};
    try {
      return Map<String, dynamic>.from(jsonDecode(data) as Map);
    } catch (_) {
      return {};
    }
  }

  List<dynamic> _readList(String key) {
    final data = _metadataBox.get(key);
    if (data is! String) return [];
    try {
      return List<dynamic>.from(jsonDecode(data) as List);
    } catch (_) {
      return [];
    }
  }

  Future<void> clearAll() async {
    await _reportsBox.clear();
    await _labValuesBox.clear();
    await _chatMessagesBox.clear();
    await _metadataBox.clear();
  }

  int getCacheSizeBytes() {
    return [..._reportsBox.values, ..._metadataBox.values]
        .fold<int>(0, (size, value) => size + utf8.encode(value.toString()).length);
  }
}
