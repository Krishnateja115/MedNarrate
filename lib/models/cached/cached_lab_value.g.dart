// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'cached_lab_value.dart';

// **************************************************************************
// TypeAdapterGenerator
// **************************************************************************

class CachedLabValueAdapter extends TypeAdapter<CachedLabValue> {
  @override
  final int typeId = 1;

  @override
  CachedLabValue read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{
      for (int i = 0; i < numOfFields; i++) reader.readByte(): reader.read(),
    };
    return CachedLabValue(
      id: fields[0] as String,
      reportId: fields[1] as String,
      parameterName: fields[2] as String,
      value: fields[3] as double,
      unit: fields[4] as String,
      status: fields[5] as String,
      referenceRange: fields[6] as String,
    );
  }

  @override
  void write(BinaryWriter writer, CachedLabValue obj) {
    writer
      ..writeByte(7)
      ..writeByte(0)
      ..write(obj.id)
      ..writeByte(1)
      ..write(obj.reportId)
      ..writeByte(2)
      ..write(obj.parameterName)
      ..writeByte(3)
      ..write(obj.value)
      ..writeByte(4)
      ..write(obj.unit)
      ..writeByte(5)
      ..write(obj.status)
      ..writeByte(6)
      ..write(obj.referenceRange);
  }

  @override
  int get hashCode => typeId.hashCode;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is CachedLabValueAdapter &&
          runtimeType == other.runtimeType &&
          typeId == other.typeId;
}
