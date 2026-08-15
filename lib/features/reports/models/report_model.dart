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
  final String processingStatus;
  final bool isFavourite;
  final DateTime uploadedAt;
  final List<Map<String, dynamic>> metrics;
  final String? clinicalSummary;
  final String? aiSummary;

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
    required this.processingStatus,
    required this.isFavourite,
    required this.uploadedAt,
    this.metrics = const [],
    this.clinicalSummary,
    this.aiSummary,
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
    String? processingStatus,
    bool? isFavourite,
    DateTime? uploadedAt,
    List<Map<String, dynamic>>? metrics,
    String? clinicalSummary,
    String? aiSummary,
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
      processingStatus: processingStatus ?? this.processingStatus,
      isFavourite: isFavourite ?? this.isFavourite,
      uploadedAt: uploadedAt ?? this.uploadedAt,
      metrics: metrics ?? this.metrics,
      clinicalSummary: clinicalSummary ?? this.clinicalSummary,
      aiSummary: aiSummary ?? this.aiSummary,
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
      "processingStatus": processingStatus,
      "isFavourite": isFavourite,
      "uploadedAt": uploadedAt.toIso8601String(),
      "metrics": metrics,
      "clinicalSummary": clinicalSummary,
      "aiSummary": aiSummary,
    };
  }

  factory ReportModel.fromMap(
    Map<String, dynamic> map,
  ) {
    return ReportModel(
      id: map["id"]?.toString() ?? "",
      title: map["title"]?.toString() ?? "Untitled Report",
      hospital: map["hospital"]?.toString() ?? "Unknown Hospital",
      reportDate: map["reportDate"] != null 
          ? DateTime.tryParse(map["reportDate"].toString()) ?? DateTime.now() 
          : DateTime.now(),
      fileName: map["fileName"]?.toString() ?? "",
      filePath: map["filePath"]?.toString() ?? "",
      fileType: map["fileType"]?.toString() ?? "unknown",
      reportType: map["reportType"]?.toString() ?? "other",
      extractedText: map["extractedText"]?.toString() ?? "",
      processingStatus: map["processingStatus"]?.toString() ?? "uploaded",
      isFavourite: map["isFavourite"] as bool? ?? false,
      uploadedAt: map["uploadedAt"] != null 
          ? DateTime.tryParse(map["uploadedAt"].toString()) ?? DateTime.now() 
          : DateTime.now(),
      metrics: List<Map<String, dynamic>>.from(map["metrics"] ?? []),
      clinicalSummary: map["clinicalSummary"]?.toString(),
      aiSummary: map["aiSummary"]?.toString(),
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