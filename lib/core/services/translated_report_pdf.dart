import 'package:pdf/widgets.dart' as pw;

import 'api_models.dart';
import 'export_service.dart';

/// Backward-compatible entry point backed by the structured production PDF
/// renderer, including its PdfGoogleFonts support for Indic scripts.
Future<pw.Document> buildTranslatedReportPdf({
  required ReportAnalysisModel analysis,
  required TranslationModel translation,
  required String reportTitle,
  required String reportDate,
  String reportType = '',
}) {
  return ExportService.instance.buildReportPdf(
    analysis: analysis,
    translation: translation,
    reportTitle: reportTitle,
    reportDate: reportDate,
    reportType: reportType,
  );
}
