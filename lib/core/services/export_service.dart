import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:path_provider/path_provider.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:printing/printing.dart';
import 'package:share_plus/share_plus.dart';
import '../services/api_models.dart';
import '../utils/helpers.dart';

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
    final clean = Helpers.sanitizePdfText(text);
    if (clean.isEmpty) return [];
    
    final lines = clean.split('\n');
    final widgets = <pw.Widget>[];

    for (var i = 0; i < lines.length; i++) {
      var line = lines[i].trim();
      if (line.isEmpty) {
        widgets.add(pw.SizedBox(height: 6));
        continue;
      }

      // Headers (numbered or markdown headers)
      bool isHeading = line.startsWith(RegExp(r'^\d+\.\s+')) || line.startsWith(RegExp(r'^[A-Z][a-zA-Z\s]{2,30}:'));
      if (isHeading) {
        widgets.add(pw.Padding(
          padding: const pw.EdgeInsets.only(top: 10, bottom: 4),
          child: pw.Text(
            line,
            style: pw.TextStyle(font: fontBold, fontSize: 11, color: _primary),
          ),
        ));
        continue;
      }

      bool isBullet = line.startsWith('- ') || line.startsWith('* ');
      if (isBullet) {
        line = line.substring(2).trim();
        widgets.add(pw.Padding(
          padding: const pw.EdgeInsets.only(left: 8, bottom: 4),
          child: pw.Row(
            crossAxisAlignment: pw.CrossAxisAlignment.start,
            children: [
              pw.Container(
                margin: const pw.EdgeInsets.only(top: 4, right: 6),
                width: 3,
                height: 3,
                decoration: pw.BoxDecoration(color: textColor, shape: pw.BoxShape.circle),
              ),
              pw.Expanded(child: pw.Text(line, style: baseStyle)),
            ],
          ),
        ));
        continue;
      }

      widgets.add(pw.Padding(
        padding: const pw.EdgeInsets.only(bottom: 4),
        child: pw.Text(line, style: baseStyle),
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

    final baseStyle = pw.TextStyle(font: font, fontSize: 9.5, color: _textDark, lineSpacing: 1.4);
    final mutedStyle = pw.TextStyle(font: font, fontSize: 8.5, color: _textMuted);
    final boldStyle = pw.TextStyle(font: fontBold, fontSize: 9.5, color: _textDark, lineSpacing: 1.4);
    final headStyle = pw.TextStyle(font: fontBold, fontSize: 13, color: _primary);

    pw.Widget sectionHeader(String title) => pw.Column(
          crossAxisAlignment: pw.CrossAxisAlignment.start,
          children: [
            pw.SizedBox(height: 16),
            pw.Text(title, style: headStyle),
            pw.SizedBox(height: 3),
            pw.Divider(color: _divider, thickness: 1),
            pw.SizedBox(height: 8),
          ],
        );

    pw.Widget flagBadge(String flag) {
      final color = _flagColor(flag);
      final label = Helpers.sanitizePdfText(flag.toUpperCase());
      return pw.Container(
        padding: const pw.EdgeInsets.symmetric(horizontal: 6, vertical: 2),
        decoration: pw.BoxDecoration(
          color: color,
          borderRadius: const pw.BorderRadius.all(pw.Radius.circular(3)),
        ),
        child: pw.Text(
          label.isEmpty ? 'NORMAL' : label,
          style: pw.TextStyle(font: fontBold, fontSize: 7.5, color: PdfColors.white),
        ),
      );
    }

    // Separate lab values into actual lab results vs patient metadata
    final metadataItems = <LabValue>[];
    final labResults = <LabValue>[];

    for (final lv in analysis.structuredLabValues) {
      if (Helpers.isMetadataParameter(lv.testName)) {
        metadataItems.add(lv);
      } else {
        labResults.add(lv);
      }
    }

    final cleanTitle = Helpers.sanitizePdfText(reportTitle);
    final cleanDate = Helpers.sanitizePdfText(reportDate);

    doc.addPage(
      pw.MultiPage(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.symmetric(vertical: 36, horizontal: 44),
        header: (context) => pw.Column(
          crossAxisAlignment: pw.CrossAxisAlignment.start,
          children: [
            pw.Row(
              mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
              children: [
                pw.Text('MedNarrate', style: pw.TextStyle(font: fontBold, fontSize: 16, color: _primary)),
                pw.Text('Medical Report Summary', style: pw.TextStyle(font: font, fontSize: 9, color: _textMuted)),
              ],
            ),
            pw.SizedBox(height: 6),
            pw.Row(
              mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
              children: [
                pw.Text(cleanTitle, style: pw.TextStyle(font: fontBold, fontSize: 11, color: _textDark)),
                pw.Text('Report Date: $cleanDate', style: mutedStyle),
              ],
            ),
            pw.SizedBox(height: 4),
            pw.Divider(color: _primary, thickness: 1.5),
            pw.SizedBox(height: 10),
          ],
        ),
        footer: (context) => pw.Column(
          mainAxisSize: pw.MainAxisSize.min,
          children: [
            pw.SizedBox(height: 10),
            pw.Divider(color: _divider, thickness: 1),
            pw.SizedBox(height: 6),
            pw.Row(
              mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
              children: [
                pw.Text(
                  'MedNarrate - Educational & Informational Summary',
                  style: pw.TextStyle(font: font, fontSize: 7.5, color: _textMuted),
                ),
                pw.Text(
                  'Page ${context.pageNumber} of ${context.pagesCount}',
                  style: pw.TextStyle(font: font, fontSize: 7.5, color: _textMuted),
                ),
              ],
            ),
          ],
        ),
        build: (context) => [
          // 1. Patient / Report Metadata Card
          if (metadataItems.isNotEmpty) ...[
            sectionHeader('Patient & Report Information'),
            pw.TableHelper.fromTextArray(
              headers: ['Parameter', 'Value'],
              data: metadataItems.map((m) => [
                Helpers.sanitizePdfText(m.testName),
                Helpers.sanitizePdfText('${m.value} ${m.unit}'.trim()),
              ]).toList(),
              headerStyle: pw.TextStyle(font: fontBold, fontSize: 8.5, color: PdfColors.white),
              cellStyle: baseStyle,
              headerDecoration: const pw.BoxDecoration(color: _primary),
              oddRowDecoration: const pw.BoxDecoration(color: PdfColors.grey100),
              cellPadding: const pw.EdgeInsets.symmetric(horizontal: 6, vertical: 4),
            ),
          ],

          // 2. Patient Summary
          if (analysis.patientSummary != null && analysis.patientSummary!.trim().isNotEmpty) ...[
            sectionHeader('Plain Language Summary'),
            ..._buildMarkdown(analysis.patientSummary!, baseStyle, boldStyle, _textDark, fontBold),
          ],

          // 3. Clinical Executive Summary
          if (analysis.clinicianSummary != null && analysis.clinicianSummary!.trim().isNotEmpty) ...[
            sectionHeader('Clinical Executive Summary'),
            ..._buildMarkdown(analysis.clinicianSummary!, baseStyle, boldStyle, _textDark, fontBold),
          ],

          // 4. Lab Results Table
          sectionHeader('Complete Laboratory Results'),
          if (labResults.isEmpty)
            pw.Padding(
              padding: const pw.EdgeInsets.only(bottom: 8),
              child: pw.Text('No laboratory results were identified in this report.', style: mutedStyle),
            )
          else
            pw.TableHelper.fromTextArray(
              headers: ['Test Name', 'Result Value', 'Unit', 'Ref Low', 'Ref High', 'Status'],
              data: labResults.map((lv) {
                final name = Helpers.sanitizePdfText(lv.testName);
                final val = lv.value.toString();
                final unit = Helpers.sanitizePdfText(lv.unit);
                final low = lv.refLow?.toString() ?? '-';
                final high = lv.refHigh?.toString() ?? '-';
                final flag = Helpers.sanitizePdfText(lv.flag.toUpperCase());
                return [name, val, unit, low, high, flag];
              }).toList(),
              headerStyle: pw.TextStyle(font: fontBold, fontSize: 8.5, color: PdfColors.white),
              cellStyle: baseStyle,
              headerDecoration: const pw.BoxDecoration(color: _primary),
              oddRowDecoration: const pw.BoxDecoration(color: PdfColors.grey100),
              cellPadding: const pw.EdgeInsets.all(5),
              cellAlignment: pw.Alignment.centerLeft,
            ),

          // 5. Abnormal Findings
          sectionHeader('Abnormal Findings'),
          if (analysis.abnormalFindings.isEmpty)
            pw.Padding(
              padding: const pw.EdgeInsets.only(bottom: 8),
              child: pw.Text('No abnormal laboratory results were identified based on the reported reference ranges.', style: mutedStyle),
            )
          else
            ...analysis.abnormalFindings.where((f) => !Helpers.isMetadataParameter(f['test_name']?.toString() ?? '')).map((f) {
              final name = Helpers.sanitizePdfText(f['test_name']?.toString() ?? 'Finding');
              final val = f['value']?.toString() ?? '';
              final unit = Helpers.sanitizePdfText(f['unit']?.toString() ?? '');
              final flag = f['flag']?.toString() ?? 'normal';
              return pw.Container(
                margin: const pw.EdgeInsets.only(bottom: 6),
                padding: const pw.EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                decoration: pw.BoxDecoration(
                  border: pw.Border.all(color: _divider, width: 1),
                  borderRadius: const pw.BorderRadius.all(pw.Radius.circular(4)),
                  color: PdfColors.grey50,
                ),
                child: pw.Row(
                  mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
                  children: [
                    pw.Expanded(
                      child: pw.Text(
                        '$name: $val $unit',
                        style: boldStyle,
                      ),
                    ),
                    flagBadge(flag),
                  ],
                ),
              );
            }),

          // 6. Medications
          sectionHeader('Reported Medications'),
          if (analysis.medications.isEmpty)
            pw.Padding(
              padding: const pw.EdgeInsets.only(bottom: 8),
              child: pw.Text('No medications were identified in this report.', style: mutedStyle),
            )
          else
            pw.TableHelper.fromTextArray(
              headers: ['Medication', 'Dosage', 'Frequency', 'Notes'],
              data: analysis.medications.map((m) => [
                Helpers.sanitizePdfText(m['medication_name']?.toString() ?? ''),
                Helpers.sanitizePdfText(m['dosage']?.toString() ?? '-'),
                Helpers.sanitizePdfText(m['frequency']?.toString() ?? '-'),
                Helpers.sanitizePdfText(m['notes']?.toString() ?? '-'),
              ]).toList(),
              headerStyle: pw.TextStyle(font: fontBold, fontSize: 8.5, color: PdfColors.white),
              cellStyle: baseStyle,
              headerDecoration: const pw.BoxDecoration(color: _primary),
              oddRowDecoration: const pw.BoxDecoration(color: PdfColors.grey100),
              cellPadding: const pw.EdgeInsets.all(5),
            ),

          // 7. Medical Entities
          if (analysis.entities.isNotEmpty) ...[
            sectionHeader('Extracted Medical Terms'),
            pw.TableHelper.fromTextArray(
              headers: ['Term / Finding', 'Category'],
              data: analysis.entities.map((e) {
                final word = Helpers.sanitizePdfText(e['word']?.toString() ?? '');
                var group = Helpers.sanitizePdfText(e['entity_group']?.toString() ?? e['category']?.toString() ?? 'General');
                group = group.replaceAll('_', ' ');
                return [word, group];
              }).toList(),
              headerStyle: pw.TextStyle(font: fontBold, fontSize: 8.5, color: PdfColors.white),
              cellStyle: baseStyle,
              headerDecoration: const pw.BoxDecoration(color: _primary),
              oddRowDecoration: const pw.BoxDecoration(color: PdfColors.grey100),
              cellPadding: const pw.EdgeInsets.all(5),
            ),
          ],

          pw.SizedBox(height: 20),
          pw.Container(
            padding: const pw.EdgeInsets.all(12),
            decoration: pw.BoxDecoration(
              color: PdfColors.orange50,
              border: pw.Border.all(color: _warning, width: 1),
              borderRadius: const pw.BorderRadius.all(pw.Radius.circular(6)),
            ),
            child: pw.Text(
              'DISCLAIMER: This report summary is generated by MedNarrate AI for educational and informational purposes only. '
              'It does not constitute medical advice, diagnosis, or treatment. Please consult a qualified healthcare professional before making health decisions.',
              style: pw.TextStyle(font: font, fontSize: 8, color: _textDark, lineSpacing: 1.3),
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

