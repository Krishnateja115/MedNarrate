class LabValuePoint {
  final String reportId;
  final DateTime date;
  final double value;
  final String status;
  final double? changeFromPrevious;

  LabValuePoint({
    required this.reportId,
    required this.date,
    required this.value,
    required this.status,
    this.changeFromPrevious,
  });

  factory LabValuePoint.fromJson(Map<String, dynamic> json) {
    return LabValuePoint(
      reportId: json['report_id'] as String,
      date: DateTime.parse(json['date'] as String),
      value: (json['value'] as num).toDouble(),
      status: json['status'] as String,
      changeFromPrevious: json['change_from_previous'] != null 
          ? (json['change_from_previous'] as num).toDouble() 
          : null,
    );
  }
}

class ParameterComparison {
  final String parameter;
  final String unit;
  final String referenceRange;
  final List<LabValuePoint> values;
  final String trend;
  final String? aiSummary;

  ParameterComparison({
    required this.parameter,
    required this.unit,
    required this.referenceRange,
    required this.values,
    required this.trend,
    this.aiSummary,
  });

  factory ParameterComparison.fromJson(Map<String, dynamic> json) {
    var list = json['values'] as List;
    List<LabValuePoint> valuesList = list.map((i) => LabValuePoint.fromJson(i)).toList();
    
    return ParameterComparison(
      parameter: json['parameter'] as String,
      unit: json['unit'] as String,
      referenceRange: json['reference_range'] as String,
      values: valuesList,
      trend: json['trend'] as String,
      aiSummary: json['ai_summary'] as String?,
    );
  }
}

class ReportComparisonResult {
  final List<String> reportIds;
  final List<ParameterComparison> comparisons;
  final DateTime generatedAt;

  ReportComparisonResult({
    required this.reportIds,
    required this.comparisons,
    required this.generatedAt,
  });

  factory ReportComparisonResult.fromJson(Map<String, dynamic> json) {
    var list = json['comparisons'] as List;
    List<ParameterComparison> comparisonsList = list.map((i) => ParameterComparison.fromJson(i)).toList();
    
    return ReportComparisonResult(
      reportIds: List<String>.from(json['report_ids'] ?? []),
      comparisons: comparisonsList,
      generatedAt: json['generated_at'] != null 
          ? DateTime.parse(json['generated_at'] as String)
          : DateTime.now(),
    );
  }
}
