import 'package:hive/hive.dart';

part 'offline_action.g.dart';

@HiveType(typeId: 3)
class OfflineAction extends HiveObject {
  @HiveField(0)
  final String id;

  @HiveField(1)
  final String endpoint;

  @HiveField(2)
  final String method;

  @HiveField(3)
  final Map<String, dynamic> body;

  @HiveField(4)
  final DateTime createdAt;

  OfflineAction({
    required this.id,
    required this.endpoint,
    required this.method,
    required this.body,
    required this.createdAt,
  });
}
