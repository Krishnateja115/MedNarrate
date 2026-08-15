import 'package:hive/hive.dart';

part 'cached_chat_message.g.dart';

@HiveType(typeId: 2)
class CachedChatMessage extends HiveObject {
  @HiveField(0)
  final String id;

  @HiveField(1)
  final String sessionId;

  @HiveField(2)
  final String role;

  @HiveField(3)
  final String content;

  @HiveField(4)
  final DateTime timestamp;

  CachedChatMessage({
    required this.id,
    required this.sessionId,
    required this.role,
    required this.content,
    required this.timestamp,
  });
}
