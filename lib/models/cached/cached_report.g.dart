// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'cached_report.dart';

// **************************************************************************
// TypeAdapterGenerator
// **************************************************************************

class CachedReportAdapter extends TypeAdapter<CachedReport> {
  @override
  final int typeId = 0;

  @override
  CachedReport read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{
      for (int i = 0; i < numOfFields; i++) reader.readByte(): reader.read(),
    };
    return CachedReport(
      id: fields[0] as String,
      userId: fields[1] as String,
      title: fields[2] as String,
      reportType: fields[3] as String,
      uploadedAt: fields[4] as DateTime,
      status: fields[5] as String,
      summaryText: fields[6] as String,
      reportDate: fields[7] as DateTime,
    );
  }

  @override
  void write(BinaryWriter writer, CachedReport obj) {
    writer
      ..writeByte(8)
      ..writeByte(0)
      ..write(obj.id)
      ..writeByte(1)
      ..write(obj.userId)
      ..writeByte(2)
      ..write(obj.title)
      ..writeByte(3)
      ..write(obj.reportType)
      ..writeByte(4)
      ..write(obj.uploadedAt)
      ..writeByte(5)
      ..write(obj.status)
      ..writeByte(6)
      ..write(obj.summaryText)
      ..writeByte(7)
      ..write(obj.reportDate);
  }

  @override
  int get hashCode => typeId.hashCode;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is CachedReportAdapter &&
          runtimeType == other.runtimeType &&
          typeId == other.typeId;
}
