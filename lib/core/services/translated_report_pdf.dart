import 'dart:ui' as ui;
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'api_models.dart';

/// Use Flutter's Indic text shaping for translated PDFs. The existing PDF text
/// renderer/Helvetica path cannot shape Indic conjuncts. Images retain the
/// displayed glyphs without transliteration or stripping Unicode characters.
Future<pw.Document> buildTranslatedReportPdf({
  required ReportAnalysisModel analysis,
  required TranslationModel translation,
  required String reportTitle,
  required String reportDate,
  String reportType = '',
}) async {
  final labels = translation.uiLabels;
  String label(String key) => labels[key] ?? '';
  final sections = <String>[
    'MedNarrate\n$reportTitle\n$reportDate\n$reportType',
    label('label_patient_report_heading'),
    translation.patientSummary,
    label('chip_lab_results'),
    ...analysis.structuredLabValues.map((lab) =>
        '${lab.testName}\n${label('label_result')}: ${lab.value} ${lab.unit}\n'
        '${label('label_reported_range')}: ${lab.refLow ?? ''} – ${lab.refHigh ?? ''} ${lab.unit}\n'
        '${label('label_status')}: ${labels['label_${lab.flag.toLowerCase()}'] ?? lab.flag}'),
    label('section_important_findings'),
    ...translation.findingsJson.map((f) =>
        '${f['test_name']}\n${f['translated_explanation'] ?? ''}'),
    label('section_reported_medications'),
    ...translation.medicationsJson.map((m) =>
        '${m['medication_name']}\n'
        '${label('label_dose')}: ${m['translated_dosage'] ?? ''}\n'
        '${label('label_frequency')}: ${m['translated_frequency'] ?? ''}\n'
        '${label('label_timing')}: ${(m['translated_times_of_day'] as List? ?? []).join(', ')}\n'
        '${m['translated_instructions'] ?? ''}'),
    label('section_what_to_discuss'),
    ...translation.doctorDiscussionPoints,
    label('label_disclaimer_patient'),
    // Retain the original clinical content explicitly, not as a translation.
    if ((analysis.clinicianSummary ?? '').isNotEmpty)
      'Original clinical summary (English)\n${analysis.clinicianSummary}',
  ];
  final images = <pw.Widget>[];
  const width = 510.0;
  const scale = 2.0;
  for (final section in sections.where((s) => s.trim().isNotEmpty)) {
    final builder = ui.ParagraphBuilder(ui.ParagraphStyle(
      textDirection: ui.TextDirection.ltr, fontSize: 12, height: 1.5,
    ))..pushStyle(ui.TextStyle(
        color: const ui.Color(0xff172033),
        fontFamilyFallback: const [
          'Nirmala UI', 'Noto Sans Telugu', 'Noto Sans Tamil',
          'Noto Sans Kannada', 'Noto Sans Malayalam',
          'Noto Sans Devanagari', 'Noto Sans Bengali',
        ],
      ))..addText(section);
    final paragraph = builder.build()..layout(const ui.ParagraphConstraints(width: width));
    final lines = paragraph.computeLineMetrics();
    // Split only at shaped line boundaries; long reports cannot clip off a page.
    for (var start = 0; start < lines.length; start += 30) {
      final end = (start + 30 < lines.length) ? start + 30 : lines.length;
      final top = start == 0 ? 0.0 : lines[start].baseline - lines[start].ascent;
      final bottom = end == lines.length ? paragraph.height : lines[end].baseline - lines[end].ascent;
      final height = bottom - top;
      final recorder = ui.PictureRecorder();
      final canvas = ui.Canvas(recorder)..scale(scale);
      canvas.drawColor(const ui.Color(0xffffffff), ui.BlendMode.src);
      canvas.clipRect(ui.Rect.fromLTWH(0, 0, width, height));
      canvas.drawParagraph(paragraph, ui.Offset(0, -top));
      final picture = recorder.endRecording();
      final image = await picture.toImage((width * scale).ceil(), (height * scale).ceil());
      final data = await image.toByteData(format: ui.ImageByteFormat.png);
      if (data == null) throw StateError('Unable to render translated report.');
      images.add(pw.Padding(
        padding: const pw.EdgeInsets.only(bottom: 8),
        child: pw.Image(pw.MemoryImage(data.buffer.asUint8List()), width: width, height: height),
      ));
      image.dispose();
      picture.dispose();
    }
    paragraph.dispose();
  }
  final document = pw.Document();
  document.addPage(pw.MultiPage(
    pageFormat: PdfPageFormat.a4,
    margin: const pw.EdgeInsets.all(36),
    maxPages: 200,
    build: (_) => images,
  ));
  return document;
}
