// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'offline_action.dart';

// **************************************************************************
// TypeAdapterGenerator
// **************************************************************************

class OfflineActionAdapter extends TypeAdapter<OfflineAction> {
  @override
  final int typeId = 3;

  @override
  OfflineAction read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{
      for (int i = 0; i < numOfFields; i++) reader.readByte(): reader.read(),
    };
    return OfflineAction(
      id: fields[0] as String,
      endpoint: fields[1] as String,
      method: fields[2] as String,
      body: (fields[3] as Map).cast<String, dynamic>(),
      createdAt: fields[4] as DateTime,
    );
  }

  @override
  void write(BinaryWriter writer, OfflineAction obj) {
    writer
      ..writeByte(5)
      ..writeByte(0)
      ..write(obj.id)
      ..writeByte(1)
      ..write(obj.endpoint)
      ..writeByte(2)
      ..write(obj.method)
      ..writeByte(3)
      ..write(obj.body)
      ..writeByte(4)
      ..write(obj.createdAt);
  }

  @override
  int get hashCode => typeId.hashCode;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is OfflineActionAdapter &&
          runtimeType == other.runtimeType &&
          typeId == other.typeId;
}
