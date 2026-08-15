import 'package:hive/hive.dart';

part 'cached_report.g.dart';

@HiveType(typeId: 0)
class CachedReport extends HiveObject {
  @HiveField(0)
  final String id;

  @HiveField(1)
  final String userId;

  @HiveField(2)
  final String title;

  @HiveField(3)
  final String reportType;

  @HiveField(4)
  final DateTime uploadedAt;

  @HiveField(5)
  final String status;

  @HiveField(6)
  final String summaryText;

  @HiveField(7)
  final DateTime reportDate;

  CachedReport({
    required this.id,
    required this.userId,
    required this.title,
    required this.reportType,
    required this.uploadedAt,
    required this.status,
    required this.summaryText,
    required this.reportDate,
  });
}
