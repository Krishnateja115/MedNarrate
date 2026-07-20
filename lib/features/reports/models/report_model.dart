class ReportModel {
  final String id;
  final String title;
  final String hospital;
  final DateTime reportDate;
  final String fileName;
  final String filePath;
  final String fileType;
  final String reportType;
  final String extractedText;
  final bool isFavourite;
  final DateTime uploadedAt;

  const ReportModel({
    required this.id,
    required this.title,
    required this.hospital,
    required this.reportDate,
    required this.fileName,
    required this.filePath,
    required this.fileType,
    required this.reportType,
    required this.extractedText,
    required this.isFavourite,
    required this.uploadedAt,
  });

  ReportModel copyWith({
    String? id,
    String? title,
    String? hospital,
    DateTime? reportDate,
    String? fileName,
    String? filePath,
    String? fileType,
    String? reportType,
    String? extractedText,
    bool? isFavourite,
    DateTime? uploadedAt,
  }) {
    return ReportModel(
      id: id ?? this.id,
      title: title ?? this.title,
      hospital: hospital ?? this.hospital,
      reportDate: reportDate ?? this.reportDate,
      fileName: fileName ?? this.fileName,
      filePath: filePath ?? this.filePath,
      fileType: fileType ?? this.fileType,
      reportType: reportType ?? this.reportType,
      extractedText: extractedText ?? this.extractedText,
      isFavourite: isFavourite ?? this.isFavourite,
      uploadedAt: uploadedAt ?? this.uploadedAt,
    );
  }

  Map<String, dynamic> toMap() {
    return {
      "id": id,
      "title": title,
      "hospital": hospital,
      "reportDate": reportDate.toIso8601String(),
      "fileName": fileName,
      "filePath": filePath,
      "fileType": fileType,
      "reportType": reportType,
      "extractedText": extractedText,
      "isFavourite": isFavourite,
      "uploadedAt": uploadedAt.toIso8601String(),
    };
  }

  factory ReportModel.fromMap(
    Map<String, dynamic> map,
  ) {
    return ReportModel(
      id: map["id"],
      title: map["title"],
      hospital: map["hospital"],
      reportDate: DateTime.parse(
        map["reportDate"],
      ),
      fileName: map["fileName"],
      filePath: map["filePath"],
      fileType: map["fileType"],
      reportType: map["reportType"],
      extractedText:
          map["extractedText"] ?? "",
      isFavourite:
          map["isFavourite"] ?? false,
      uploadedAt: DateTime.parse(
        map["uploadedAt"],
      ),
    );
  }

  @override
  String toString() {
    return "ReportModel(title: $title)";
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        other is ReportModel &&
            runtimeType == other.runtimeType &&
            id == other.id;
  }

  @override
  int get hashCode => id.hashCode;
}