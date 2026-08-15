import 'package:hive/hive.dart';

part 'cached_lab_value.g.dart';

@HiveType(typeId: 1)
class CachedLabValue extends HiveObject {
  @HiveField(0)
  final String id;

  @HiveField(1)
  final String reportId;

  @HiveField(2)
  final String parameterName;

  @HiveField(3)
  final double value;

  @HiveField(4)
  final String unit;

  @HiveField(5)
  final String status;

  @HiveField(6)
  final String referenceRange;

  CachedLabValue({
    required this.id,
    required this.reportId,
    required this.parameterName,
    required this.value,
    required this.unit,
    required this.status,
    required this.referenceRange,
  });
}
