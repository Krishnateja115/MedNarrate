import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:path_provider/path_provider.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:printing/printing.dart';
import 'package:share_plus/share_plus.dart';
import '../services/api_models.dart';

import 'pdf_downloader/pdf_downloader.dart';

/// ExportService — generates a clean PDF from a ReportAnalysisModel
/// and either downloads it (Export) or opens the print dialog (Print/Preview).
class ExportService {
  ExportService._();
  static final ExportService instance = ExportService._();

  // Primary colors
  static const _primary = PdfColor.fromInt(0xFF1A73E8);
  static const _danger = PdfColor.fromInt(0xFFE53935);
  static const _warning = PdfColor.fromInt(0xFFF5A623);
  static const _success = PdfColor.fromInt(0xFF00C48C);
  static const _textDark = PdfColor.fromInt(0xFF0D1117);
  static const _textMuted = PdfColor.fromInt(0xFF5A6472);
  static const _divider = PdfColor.fromInt(0xFFE8ECF0);

  PdfColor _flagColor(String flag) {
    switch (flag.toLowerCase()) {
      case 'high':
        return _danger;
      case 'low':
        return _warning;
      default:
        return _success;
    }
  }

  List<pw.Widget> _buildMarkdown(
    String text,
    pw.TextStyle baseStyle,
    pw.TextStyle boldStyle,
    PdfColor textColor,
    pw.Font fontBold,
  ) {
    final lines = text.split('\n');
    final widgets = <pw.Widget>[];

    for (var i = 0; i < lines.length; i++) {
      var line = lines[i].trim();
      if (line.isEmpty) {
        widgets.add(pw.SizedBox(height: 8));
        continue;
      }

      // Filter out raw entity labels
      line = line.replaceAll(RegExp(r'\([A-Z][a-z_]+\)'), '');
      line = line.replaceAll(RegExp(r'\([a-z_]+\)'), '');
      
      // Remove known generation artifacts
      line = line.replaceAll('<INPUT_TEXT>', '').replaceAll('</INPUT_TEXT>', '');
      line = line.replaceAll('****End of Report****', '');
      
      line = line.trim();
      if (line.isEmpty || line == 'Calculated') continue; // Skip empty after cleanup

      bool isHeading = line.startsWith(RegExp(r'^#+ '));
      if (isHeading) {
        line = line.replaceAll(RegExp(r'^#+\s*'), ''); // Remove markdown heading markers
        widgets.add(pw.Paragraph(
          text: line.replaceAll('**', '').trim(),
          style: pw.TextStyle(font: fontBold, fontSize: 12, color: _primary),
          margin: const pw.EdgeInsets.only(top: 12, bottom: 6),
        ));
        continue;
      }

      bool isBullet = line.startsWith('- ') || line.startsWith('* ');
      if (isBullet) {
        line = line.substring(2).trim();
        widgets.add(pw.Padding(
          padding: const pw.EdgeInsets.only(left: 12, bottom: 6),
          child: pw.Row(
            crossAxisAlignment: pw.CrossAxisAlignment.start,
            children: [
              pw.Container(
                margin: const pw.EdgeInsets.only(top: 4, right: 8),
                width: 3,
                height: 3,
                decoration: pw.BoxDecoration(color: textColor, shape: pw.BoxShape.circle),
              ),
              pw.Expanded(child: pw.Text(line.replaceAll('**', ''), style: baseStyle)),
            ]
          )
        ));
        continue;
      }
      
      bool looksLikeHeading = line.startsWith(RegExp(r'^\d+\. ')) || line.startsWith(RegExp(r'^[A-Z][a-z ]+ Findings:?'));
      
      widgets.add(pw.Paragraph(
        text: line.replaceAll('**', ''),
        style: looksLikeHeading ? boldStyle : baseStyle,
        margin: const pw.EdgeInsets.only(bottom: 6),
      ));
    }
    return widgets;
  }

  Future<pw.Document> _buildDocument({
    required ReportAnalysisModel analysis,
    required String reportTitle,
    required String reportDate,
  }) async {
    final doc = pw.Document();
    final font = pw.Font.helvetica();
    final fontBold = pw.Font.helveticaBold();
    final fontMono = pw.Font.courier();

    final baseStyle = pw.TextStyle(font: font, fontSize: 10, color: _textDark, lineSpacing: 1.5);
    final mutedStyle = pw.TextStyle(font: font, fontSize: 9, color: _textMuted);
    final boldStyle = pw.TextStyle(font: fontBold, fontSize: 10, color: _textDark, lineSpacing: 1.5);
    final headStyle = pw.TextStyle(font: fontBold, fontSize: 14, color: _primary);
    final monoStyle = pw.TextStyle(font: fontMono, fontSize: 9, color: _textDark);

    pw.Widget sectionHeader(String title) => pw.Column(
          crossAxisAlignment: pw.CrossAxisAlignment.start,
          children: [
            pw.SizedBox(height: 24),
            pw.Text(title, style: headStyle),
            pw.SizedBox(height: 4),
            pw.Divider(color: _divider, thickness: 1),
            pw.SizedBox(height: 12),
          ],
        );

    pw.Widget flagBadge(String flag) {
      final color = _flagColor(flag);
      return pw.Container(
        padding: const pw.EdgeInsets.symmetric(horizontal: 8, vertical: 3),
        decoration: pw.BoxDecoration(
          color: color,
          borderRadius: const pw.BorderRadius.all(pw.Radius.circular(4)),
        ),
        child: pw.Text(
          flag.toUpperCase(),
          style: pw.TextStyle(font: fontBold, fontSize: 8, color: PdfColors.white),
        ),
      );
    }

    doc.addPage(
      pw.MultiPage(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.symmetric(vertical: 40, horizontal: 50),
        header: (context) => pw.Column(
          crossAxisAlignment: pw.CrossAxisAlignment.start,
          children: [
            pw.Row(
              mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
              children: [
                pw.Text('MedNarrate', style: pw.TextStyle(font: fontBold, fontSize: 18, color: _primary)),
                pw.Text('Medical Report Summary', style: pw.TextStyle(font: font, fontSize: 10, color: _textMuted)),
              ],
            ),
            pw.SizedBox(height: 8),
            pw.Text(reportTitle, style: pw.TextStyle(font: fontBold, fontSize: 12, color: _textDark)),
            pw.Text('Date: $reportDate', style: mutedStyle),
            pw.SizedBox(height: 6),
            pw.Divider(color: _primary, thickness: 1.5),
            pw.SizedBox(height: 16),
          ],
        ),
        footer: (context) => pw.Column(
          mainAxisSize: pw.MainAxisSize.min,
          children: [
            pw.SizedBox(height: 16),
            pw.Divider(color: _divider, thickness: 1),
            pw.SizedBox(height: 8),
            pw.Row(
              mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
              children: [
                pw.Text(
                  'MedNarrate • Educational / Informational Summary',
                  style: pw.TextStyle(font: font, fontSize: 8, color: _textMuted),
                ),
                pw.Text(
                  'Page ${context.pageNumber} of ${context.pagesCount}',
                  style: pw.TextStyle(font: font, fontSize: 8, color: _textMuted),
                ),
              ],
            ),
          ],
        ),
        build: (context) => [
          // Patient Summary
          if (analysis.patientSummary != null && analysis.patientSummary!.isNotEmpty) ...[
            sectionHeader('Plain Language Summary'),
            ..._buildMarkdown(analysis.patientSummary!, baseStyle, boldStyle, _textDark, fontBold),
          ],

          // Clinician Summary
          if (analysis.clinicianSummary != null && analysis.clinicianSummary!.isNotEmpty) ...[
            sectionHeader('Clinical Summary'),
            ..._buildMarkdown(analysis.clinicianSummary!, baseStyle, boldStyle, _textDark, fontBold),
          ],

          // Lab Results
          if (analysis.structuredLabValues.isNotEmpty) ...[
            sectionHeader('Lab Results'),
            pw.TableHelper.fromTextArray(
              headers: ['Test', 'Value', 'Unit', 'Ref Low', 'Ref High', 'Status'],
              data: analysis.structuredLabValues.map((lv) => [
                lv.testName,
                lv.value.toString(),
                lv.unit,
                lv.refLow?.toString() ?? '—',
                lv.refHigh?.toString() ?? '—',
                lv.flag.toUpperCase(),
              ]).toList(),
              headerStyle: pw.TextStyle(font: fontBold, fontSize: 9, color: PdfColors.white),
              cellStyle: monoStyle,
              headerDecoration: const pw.BoxDecoration(color: _primary),
              oddRowDecoration: pw.BoxDecoration(color: PdfColors.grey100),
              cellPadding: const pw.EdgeInsets.all(6),
              cellAlignment: pw.Alignment.centerLeft,
            ),
          ],

          // Abnormal Findings
          if (analysis.abnormalFindings.isNotEmpty) ...[
            sectionHeader('Abnormal Findings'),
            ...analysis.abnormalFindings.map((f) => pw.Container(
                  margin: const pw.EdgeInsets.only(bottom: 8),
                  padding: const pw.EdgeInsets.all(12),
                  decoration: pw.BoxDecoration(
                    border: pw.Border.all(color: _divider, width: 1),
                    borderRadius: const pw.BorderRadius.all(pw.Radius.circular(6)),
                    color: PdfColors.grey50,
                  ),
                  child: pw.Row(
                    mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
                    children: [
                      pw.Expanded(
                        child: pw.Text(
                          '${f['test_name']} — ${f['value']} ${f['unit']}',
                          style: boldStyle,
                        ),
                      ),
                      flagBadge(f['flag']?.toString() ?? 'normal'),
                    ],
                  ),
                )),
          ],

          // Entities - Cleaned up to a structured table
          if (analysis.entities.isNotEmpty) ...[
            sectionHeader('Medical Entities Detected'),
            pw.TableHelper.fromTextArray(
              headers: ['Entity', 'Category'],
              data: analysis.entities.map((e) {
                final word = e['word']?.toString() ?? '';
                var group = e['entity_group']?.toString() ?? '';
                group = group.replaceAll('_', ' '); // Clean up internal labels
                return [word, group];
              }).toList(),
              headerStyle: pw.TextStyle(font: fontBold, fontSize: 9, color: PdfColors.white),
              cellStyle: baseStyle,
              headerDecoration: const pw.BoxDecoration(color: _primary),
              oddRowDecoration: pw.BoxDecoration(color: PdfColors.grey100),
              cellPadding: const pw.EdgeInsets.all(6),
              cellAlignment: pw.Alignment.centerLeft,
            ),
          ],

          pw.SizedBox(height: 30),
          pw.Container(
            padding: const pw.EdgeInsets.all(16),
            decoration: pw.BoxDecoration(
              color: PdfColors.orange50,
              border: pw.Border.all(color: _warning, width: 1),
              borderRadius: const pw.BorderRadius.all(pw.Radius.circular(8)),
            ),
            child: pw.Text(
              '⚠ DISCLAIMER: This analysis is AI-generated and intended for informational '
              'and educational purposes only. It does not constitute medical advice, diagnosis, or treatment. '
              'Please consult a qualified healthcare professional before making any health decisions.',
              style: pw.TextStyle(font: font, fontSize: 9, color: _textDark, lineSpacing: 1.4),
            ),
          ),
        ],
      ),
    );

    return doc;
  }

  /// DIRECT DOWNLOAD for the "Export PDF" action. Does NOT open print dialog.
  Future<void> exportReportPdf({
    required ReportAnalysisModel analysis,
    required String reportTitle,
    required String reportDate,
  }) async {
    print('[MEDNARRATE EXPORT] EXPORT PDF BUTTON CLICKED');
    print('[MEDNARRATE EXPORT] GENERATING PDF');
    final doc = await _buildDocument(
      analysis: analysis,
      reportTitle: reportTitle,
      reportDate: reportDate,
    );
    final bytes = await doc.save();
    print('[MEDNARRATE EXPORT] PDF GENERATED');

    final safeTitle = reportTitle.replaceAll(RegExp(r'[^a-zA-Z0-9_\-]'), '_');
    final filename = 'MedNarrate_${safeTitle}_$reportDate.pdf';

    if (kIsWeb) {
      await downloadPdfWeb(bytes, filename);
      return;
    }

    final dir = await getTemporaryDirectory();
    final file = File('${dir.path}/$filename');
    await file.writeAsBytes(bytes);

    await Share.shareXFiles(
      [XFile(file.path, mimeType: 'application/pdf')],
      subject: 'MedNarrate — $reportTitle Summary',
    );
  }

  /// OPENS PRINT/PREVIEW DIALOG for the "Print / Preview" action.
  Future<void> previewReportPdf({
    required ReportAnalysisModel analysis,
    required String reportTitle,
    required String reportDate,
  }) async {
    print('[MEDNARRATE PRINT] PRINT/PREVIEW BUTTON CLICKED');
    print('[MEDNARRATE PRINT] GENERATING PDF');
    final doc = await _buildDocument(
      analysis: analysis,
      reportTitle: reportTitle,
      reportDate: reportDate,
    );
    final bytes = await doc.save();
    print('[MEDNARRATE PRINT] STARTING PRINT PREVIEW');
    // layoutPdf uses the browser/system print dialog
    await Printing.layoutPdf(onLayout: (_) async => bytes);
  }
}

