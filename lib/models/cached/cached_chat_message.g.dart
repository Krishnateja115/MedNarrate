// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'cached_chat_message.dart';

// **************************************************************************
// TypeAdapterGenerator
// **************************************************************************

class CachedChatMessageAdapter extends TypeAdapter<CachedChatMessage> {
  @override
  final int typeId = 2;

  @override
  CachedChatMessage read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{
      for (int i = 0; i < numOfFields; i++) reader.readByte(): reader.read(),
    };
    return CachedChatMessage(
      id: fields[0] as String,
      sessionId: fields[1] as String,
      role: fields[2] as String,
      content: fields[3] as String,
      timestamp: fields[4] as DateTime,
    );
  }

  @override
  void write(BinaryWriter writer, CachedChatMessage obj) {
    writer
      ..writeByte(5)
      ..writeByte(0)
      ..write(obj.id)
      ..writeByte(1)
      ..write(obj.sessionId)
      ..writeByte(2)
      ..write(obj.role)
      ..writeByte(3)
      ..write(obj.content)
      ..writeByte(4)
      ..write(obj.timestamp);
  }

  @override
  int get hashCode => typeId.hashCode;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is CachedChatMessageAdapter &&
          runtimeType == other.runtimeType &&
          typeId == other.typeId;
}
