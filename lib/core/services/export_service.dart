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

/// ExportService — generates a professional, structured PDF from a ReportAnalysisModel.
/// Export PDF  → direct download, NO print dialog.
/// Print/Preview → opens system/browser print dialog ONLY.
class ExportService {
  ExportService._();
  static final ExportService instance = ExportService._();

  // ─── Colour palette ────────────────────────────────────────────────────────
  static const _primary   = PdfColor.fromInt(0xFF1A73E8);
  static const _danger    = PdfColor.fromInt(0xFFE53935);
  static const _warning   = PdfColor.fromInt(0xFFE65100);
  static const _success   = PdfColor.fromInt(0xFF1B8A5A);
  static const _textDark  = PdfColor.fromInt(0xFF0D1117);
  static const _textMuted = PdfColor.fromInt(0xFF5A6472);
  static const _divider   = PdfColor.fromInt(0xFFE0E6EF);
  static const _rowOdd    = PdfColor.fromInt(0xFFF5F8FC);
  static const _headerBg  = PdfColor.fromInt(0xFF1A73E8);
  static const _dangerBg  = PdfColor.fromInt(0xFFFFF0EE);
  static const _dangerBdr = PdfColor.fromInt(0xFFFFCDD2);
  static const _warnBg    = PdfColor.fromInt(0xFFFFF8E1);
  static const _warnBdr   = PdfColor.fromInt(0xFFFFE082);
  static const _normalBg  = PdfColor.fromInt(0xFFE8F5E9);
  static const _normalBdr = PdfColor.fromInt(0xFFA5D6A7);

  // ─── Flag colour lookup ────────────────────────────────────────────────────
  PdfColor _flagColor(String flag) {
    switch (flag.toLowerCase()) {
      case 'high':
      case 'critical':
        return _danger;
      case 'low':
        return _warning;
      case 'normal':
        return _success;
      default:
        return _textMuted;
    }
  }

  PdfColor _flagBg(String flag) {
    switch (flag.toLowerCase()) {
      case 'high':
      case 'critical':
        return _dangerBg;
      case 'low':
        return _warnBg;
      case 'normal':
        return _normalBg;
      default:
        return _rowOdd;
    }
  }

  PdfColor _flagBorder(String flag) {
    switch (flag.toLowerCase()) {
      case 'high':
      case 'critical':
        return _dangerBdr;
      case 'low':
        return _warnBdr;
      case 'normal':
        return _normalBdr;
      default:
        return _divider;
    }
  }

  // ─── Safe text helper ─────────────────────────────────────────────────────
  /// Sanitizes a string for PDF rendering (Helvetica/WinAnsi safe).
  static String _s(String? raw) => Helpers.sanitizePdfText(raw ?? '');

  // ─── Markdown-to-PDF widgets ──────────────────────────────────────────────
  /// Converts AI-generated Markdown text into structured pw.Widget list.
  /// Handles: ### headings, ## headings, bullet lists (- * •), bold **text**, paragraphs.
  List<pw.Widget> _mdWidgets(
    String rawText,
    pw.TextStyle base,
    pw.TextStyle bold,
    pw.Font fontBold,
  ) {
    // Full sanitization first
    final sanitized = _s(rawText);
    if (sanitized.isEmpty) return [];

    final lines = sanitized.split('\n');
    final out = <pw.Widget>[];
    bool prevWasEmpty = true;

    for (var rawLine in lines) {
      final line = rawLine.trimRight();
      final trimmed = line.trim();

      if (trimmed.isEmpty) {
        if (!prevWasEmpty) out.add(pw.SizedBox(height: 5));
        prevWasEmpty = true;
        continue;
      }
      prevWasEmpty = false;

      // ── Numbered section heading: "1. Section Title" or "2. Key Findings"
      final numberedMatch = RegExp(r'^(\d+)\.\s+(.+)$').firstMatch(trimmed);
      if (numberedMatch != null) {
        final num = numberedMatch.group(1)!;
        final title = _inlineBold(numberedMatch.group(2)!, fontBold, base);
        out.add(pw.Padding(
          padding: const pw.EdgeInsets.only(top: 12, bottom: 4),
          child: pw.Row(
            crossAxisAlignment: pw.CrossAxisAlignment.center,
            children: [
              pw.Container(
                width: 22,
                height: 22,
                decoration: pw.BoxDecoration(
                  color: _primary,
                  shape: pw.BoxShape.circle,
                ),
                child: pw.Center(
                  child: pw.Text(num,
                      style: pw.TextStyle(
                          font: fontBold, fontSize: 9, color: PdfColors.white)),
                ),
              ),
              pw.SizedBox(width: 8),
              pw.Expanded(child: pw.RichText(text: title)),
            ],
          ),
        ));
        continue;
      }

      // ── Bullet point: "- text" or "* text" or "• text"
      if (trimmed.startsWith('- ') ||
          trimmed.startsWith('* ') ||
          trimmed.startsWith('- ')) {
        final content = trimmed.substring(2).trim();
        out.add(pw.Padding(
          padding: const pw.EdgeInsets.only(left: 12, bottom: 3),
          child: pw.Row(
            crossAxisAlignment: pw.CrossAxisAlignment.start,
            children: [
              pw.Padding(
                padding: const pw.EdgeInsets.only(top: 5, right: 7),
                child: pw.Container(
                  width: 4,
                  height: 4,
                  decoration: pw.BoxDecoration(
                      color: _textMuted, shape: pw.BoxShape.circle),
                ),
              ),
              pw.Expanded(
                  child: pw.RichText(text: _inlineBold(content, fontBold, base))),
            ],
          ),
        ));
        continue;
      }

      // ── All-caps short line → treat as subheading
      if (trimmed == trimmed.toUpperCase() &&
          trimmed.length > 3 &&
          trimmed.length < 60 &&
          RegExp(r'^[A-Z\s\-]+$').hasMatch(trimmed)) {
        out.add(pw.Padding(
          padding: const pw.EdgeInsets.only(top: 8, bottom: 3),
          child: pw.Text(trimmed,
              style: pw.TextStyle(
                  font: fontBold,
                  fontSize: 10,
                  color: _primary,
                  letterSpacing: 0.5)),
        ));
        continue;
      }

      // ── Regular paragraph
      out.add(pw.Padding(
        padding: const pw.EdgeInsets.only(bottom: 3),
        child: pw.RichText(text: _inlineBold(trimmed, fontBold, base)),
      ));
    }
    return out;
  }

  /// Converts inline **bold** into pw.TextSpan.
  pw.TextSpan _inlineBold(String text, pw.Font boldFont, pw.TextStyle base) {
    final spans = <pw.TextSpan>[];
    final exp = RegExp(r'\*\*(.*?)\*\*');
    int last = 0;
    for (final m in exp.allMatches(text)) {
      if (m.start > last) {
        spans.add(pw.TextSpan(text: text.substring(last, m.start), style: base));
      }
      spans.add(pw.TextSpan(
          text: m.group(1) ?? '',
          style: base.copyWith(font: boldFont, fontWeight: pw.FontWeight.bold)));
      last = m.end;
    }
    if (last < text.length) {
      spans.add(pw.TextSpan(text: text.substring(last), style: base));
    }
    return pw.TextSpan(children: spans, style: base);
  }

  // ─── Section header widget ────────────────────────────────────────────────
  pw.Widget _sectionHeader(String title, pw.Font fontBold) => pw.Column(
        crossAxisAlignment: pw.CrossAxisAlignment.start,
        children: [
          pw.SizedBox(height: 18),
          pw.Text(title,
              style: pw.TextStyle(
                  font: fontBold, fontSize: 13, color: _primary)),
          pw.SizedBox(height: 4),
          pw.Divider(color: _divider, thickness: 1),
          pw.SizedBox(height: 8),
        ],
      );

  // ─── Flag badge ───────────────────────────────────────────────────────────
  pw.Widget _flagBadge(String flag, pw.Font fontBold) {
    final color = _flagColor(flag);
    final label = flag.toUpperCase();
    if (label.isEmpty) return pw.SizedBox();
    return pw.Container(
      padding: const pw.EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: pw.BoxDecoration(
        color: color,
        borderRadius: const pw.BorderRadius.all(pw.Radius.circular(3)),
      ),
      child: pw.Text(label,
          style: pw.TextStyle(
              font: fontBold, fontSize: 7.5, color: PdfColors.white)),
    );
  }

  // ─── Abnormal finding card ────────────────────────────────────────────────
  pw.Widget _findingCard(
    Map<String, dynamic> f,
    pw.TextStyle base,
    pw.TextStyle bold,
    pw.Font fontBold,
  ) {
    final name = _s(f['test_name']?.toString() ?? f['parameter']?.toString() ?? 'Finding');
    final val  = f['value']?.toString() ?? '';
    final unit = _s(f['unit']?.toString() ?? '');
    final flag = f['flag']?.toString() ?? 'normal';
    final refLow  = f['ref_low'] ?? f['refLow'];
    final refHigh = f['ref_high'] ?? f['refHigh'];

    String refText = '';
    if (refLow != null && refHigh != null) {
      refText = 'Reference Range: $refLow - $refHigh';
    } else if (refLow != null) {
      refText = 'Reference Range: > $refLow';
    } else if (refHigh != null) {
      refText = 'Reference Range: < $refHigh';
    }

    final bgColor  = _flagBg(flag);
    final bdrColor = _flagBorder(flag);

    return pw.Container(
      margin: const pw.EdgeInsets.only(bottom: 8),
      padding: const pw.EdgeInsets.all(10),
      decoration: pw.BoxDecoration(
        color: bgColor,
        border: pw.Border.all(color: bdrColor, width: 1),
        borderRadius: const pw.BorderRadius.all(pw.Radius.circular(5)),
      ),
      child: pw.Column(
        crossAxisAlignment: pw.CrossAxisAlignment.start,
        children: [
          pw.Row(
            mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
            children: [
              pw.Expanded(
                child: pw.Text(name,
                    style: bold.copyWith(fontSize: 10.5)),
              ),
              _flagBadge(flag, fontBold),
            ],
          ),
          pw.SizedBox(height: 4),
          pw.Text(
            '$val ${unit.isNotEmpty ? unit : ''}'.trim(),
            style: base.copyWith(fontSize: 11, font: fontBold, color: _flagColor(flag)),
          ),
          if (refText.isNotEmpty) ...[
            pw.SizedBox(height: 2),
            pw.Text(refText, style: base.copyWith(fontSize: 8.5, color: _textMuted)),
          ],
        ],
      ),
    );
  }

  // ─── Lab table row data ───────────────────────────────────────────────────
  List<List<String>> _labTableData(List<LabValue> labResults) {
    return labResults.map((lv) {
      final name  = _s(lv.testName);
      final val   = lv.value % 1 == 0
          ? lv.value.toInt().toString()
          : lv.value.toStringAsFixed(2);
      final unit  = _s(lv.unit);
      final range = (lv.refLow != null && lv.refHigh != null)
          ? '${lv.refLow} - ${lv.refHigh}'
          : (lv.refLow != null ? '> ${lv.refLow}' : (lv.refHigh != null ? '< ${lv.refHigh}' : '-'));
      final flag  = lv.flag.toUpperCase();
      return [name, val, unit, range, flag];
    }).toList();
  }

  // ─── Doctor discussion points ─────────────────────────────────────────────
  List<String> _discussionPoints(
    List<Map<String, dynamic>> abnormal,
    List<Map<String, dynamic>> meds,
  ) {
    final points = <String>[];
    for (final f in abnormal.take(4)) {
      final name = f['test_name']?.toString() ?? f['parameter']?.toString() ?? '';
      final val  = f['value']?.toString() ?? '';
      final unit = f['unit']?.toString() ?? '';
      final flag = (f['flag']?.toString() ?? '').toUpperCase();
      if (name.isNotEmpty) {
        points.add(
          'Discuss your $flag $name result ($val $unit) and whether any follow-up is needed.');
      }
    }
    if (meds.isNotEmpty) {
      final medNames =
          meds.map((m) => m['medication_name']?.toString() ?? '').where((n) => n.isNotEmpty).take(3).join(', ');
      if (medNames.isNotEmpty) {
        points.add('Confirm dosage and frequency for: $medNames.');
      }
    }
    if (points.isEmpty) {
      points.add('Review your complete test results with your doctor to establish a baseline.');
    }
    points.add('Ask whether a follow-up test or re-check is recommended.');
    points.add('Discuss any symptoms you have been experiencing alongside these findings.');
    return points;
  }

  // ─── Curated medical terms ────────────────────────────────────────────────
  /// Returns unique, clean medical term names from entities — excluding raw NLP category labels.
  List<String> _curatedTerms(List<Map<String, dynamic>> entities) {
    const categoriesIncluded = {
      'Lab_value',
      'Diagnosis',
      'Medication',
      'Sign_symptom',
      'Procedure',
    };
    const skipWords = {
      'high', 'low', 'normal', 'result', 'test', 'blood', 'lab', 'report',
      'value', 'range', 'mg', 'dl', 'ml', 'fl', 'g', '%', 'no', 'not',
    };

    final seen = <String>{};
    final terms = <String>[];
    for (final e in entities) {
      final group = (e['entity_group'] ?? e['category'] ?? '').toString();
      final word  = _s(e['word']?.toString() ?? '').trim();
      if (word.isEmpty) continue;
      if (word.length < 3) continue;
      if (skipWords.contains(word.toLowerCase())) continue;
      // Only include clinically meaningful categories
      final included = categoriesIncluded.contains(group) ||
          (!group.contains('_') && group.isNotEmpty);
      if (!included) continue;
      final key = word.toLowerCase();
      if (seen.contains(key)) continue;
      seen.add(key);
      terms.add(word);
      if (terms.length >= 12) break;
    }
    return terms;
  }

  // ─── Document builder ─────────────────────────────────────────────────────
  Future<pw.Document> _buildDocument({
    required ReportAnalysisModel analysis,
    required String reportTitle,
    required String reportDate,
    String reportType = '',
  }) async {
    final doc      = pw.Document();
    final font     = pw.Font.helvetica();
    final fontBold = pw.Font.helveticaBold();

    // Typography scale
    final base  = pw.TextStyle(font: font,     fontSize: 9.5,  color: _textDark, lineSpacing: 1.5);
    final bold  = pw.TextStyle(font: fontBold, fontSize: 9.5,  color: _textDark, lineSpacing: 1.5);
    final muted = pw.TextStyle(font: font,     fontSize: 8.5,  color: _textMuted, lineSpacing: 1.4);

    final cleanTitle = _s(reportTitle);
    final cleanDate  = _s(reportDate);
    final cleanType  = _s(reportType);

    // Partition lab values: metadata vs. actual lab results
    final metadataItems = <LabValue>[];
    final labResults    = <LabValue>[];
    for (final lv in analysis.structuredLabValues) {
      if (Helpers.isMetadataParameter(lv.testName)) {
        metadataItems.add(lv);
      } else {
        labResults.add(lv);
      }
    }

    // Partition findings: abnormal vs normal (non-metadata only)
    final abnormalFindings = analysis.abnormalFindings
        .where((f) {
          final name = f['test_name']?.toString() ??
              f['parameter']?.toString() ?? '';
          return !Helpers.isMetadataParameter(name);
        })
        .toList();

    final normalFindings = labResults
        .where((lv) =>
            lv.flag.toLowerCase() == 'normal' ||
            lv.flag.toLowerCase() == 'not_classified')
        .toList();

    final abnormalLabRows = labResults
        .where((lv) =>
            lv.flag.toLowerCase() != 'normal' &&
            lv.flag.toLowerCase() != 'not_classified')
        .toList();

    // Doctor discussion points
    final discussPoints = _discussionPoints(abnormalFindings, analysis.medications);

    // Curated medical terms
    final medTerms = _curatedTerms(analysis.entities);

    // ── Page Header ────────────────────────────────────────────────────────
    pw.Widget pageHeader(pw.Context ctx) => pw.Column(
          crossAxisAlignment: pw.CrossAxisAlignment.start,
          children: [
            pw.Row(
              mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
              children: [
                pw.Text('MedNarrate',
                    style: pw.TextStyle(
                        font: fontBold, fontSize: 15, color: _primary)),
                pw.Text('Medical Report Summary',
                    style: muted),
              ],
            ),
            pw.SizedBox(height: 5),
            pw.Row(
              mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
              children: [
                pw.Expanded(
                  child: pw.Text(cleanTitle,
                      style: pw.TextStyle(
                          font: fontBold, fontSize: 11, color: _textDark)),
                ),
                pw.Column(
                  crossAxisAlignment: pw.CrossAxisAlignment.end,
                  children: [
                    pw.Text('Date: $cleanDate', style: muted),
                    if (cleanType.isNotEmpty)
                      pw.Text('Type: $cleanType', style: muted),
                  ],
                ),
              ],
            ),
            pw.SizedBox(height: 4),
            pw.Divider(color: _primary, thickness: 1.5),
            pw.SizedBox(height: 8),
          ],
        );

    // ── Page Footer ────────────────────────────────────────────────────────
    pw.Widget pageFooter(pw.Context ctx) => pw.Column(
          mainAxisSize: pw.MainAxisSize.min,
          children: [
            pw.Divider(color: _divider, thickness: 0.8),
            pw.SizedBox(height: 4),
            pw.Row(
              mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
              children: [
                pw.Text('MedNarrate — For informational purposes only',
                    style: muted.copyWith(fontSize: 7.5)),
                pw.Text(
                    'Page ${ctx.pageNumber} of ${ctx.pagesCount}',
                    style: muted.copyWith(fontSize: 7.5)),
              ],
            ),
          ],
        );

    doc.addPage(
      pw.MultiPage(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.symmetric(vertical: 40, horizontal: 48),
        header: pageHeader,
        footer: pageFooter,
        build: (ctx) => [

          // ── SECTION 1: Patient / Report Metadata ──────────────────────
          if (metadataItems.isNotEmpty) ...[
            _sectionHeader('Patient & Report Information', fontBold),
            pw.TableHelper.fromTextArray(
              headers: ['Field', 'Value'],
              data: metadataItems.map((m) => [
                _s(m.testName),
                _s('${m.value == 0 ? '' : m.value} ${m.unit}'.trim()),
              ]).toList(),
              headerStyle:
                  pw.TextStyle(font: fontBold, fontSize: 8.5, color: PdfColors.white),
              cellStyle: base,
              headerDecoration:
                  const pw.BoxDecoration(color: _headerBg),
              oddRowDecoration:
                  const pw.BoxDecoration(color: _rowOdd),
              columnWidths: {0: const pw.FixedColumnWidth(140), 1: const pw.FlexColumnWidth()},
              cellPadding:
                  const pw.EdgeInsets.symmetric(horizontal: 8, vertical: 5),
            ),
          ],

          // ── SECTION 2: Plain Language Summary ─────────────────────────
          if ((analysis.patientSummary ?? '').trim().isNotEmpty) ...[
            _sectionHeader('Plain Language Summary', fontBold),
            ..._mdWidgets(analysis.patientSummary!, base, bold, fontBold),
          ],

          // ── SECTION 3: Key Findings (Abnormal) ────────────────────────
          _sectionHeader('Key Findings', fontBold),
          if (abnormalLabRows.isEmpty && abnormalFindings.isEmpty)
            pw.Padding(
              padding: const pw.EdgeInsets.only(bottom: 6),
              child: pw.Text(
                  'No out-of-range laboratory results were identified for this report.',
                  style: muted),
            )
          else ...[
            pw.Text('ABNORMAL FINDINGS',
                style: pw.TextStyle(
                    font: fontBold,
                    fontSize: 9,
                    color: _danger,
                    letterSpacing: 0.5)),
            pw.SizedBox(height: 6),
            // Use structured abnormal findings if available; fall back to lab rows
            if (abnormalFindings.isNotEmpty)
              ...abnormalFindings.map((f) =>
                  _findingCard(f, base, bold, fontBold))
            else
              ...abnormalLabRows.map((lv) => _findingCard({
                    'test_name': lv.testName,
                    'value': lv.value,
                    'unit': lv.unit,
                    'flag': lv.flag,
                    'ref_low': lv.refLow,
                    'ref_high': lv.refHigh,
                  }, base, bold, fontBold)),

            if (normalFindings.isNotEmpty) ...[
              pw.SizedBox(height: 10),
              pw.Text('NORMAL FINDINGS',
                  style: pw.TextStyle(
                      font: fontBold,
                      fontSize: 9,
                      color: _success,
                      letterSpacing: 0.5)),
              pw.SizedBox(height: 6),
              ...normalFindings.map((lv) => pw.Container(
                    margin: const pw.EdgeInsets.only(bottom: 4),
                    padding:
                        const pw.EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                    decoration: pw.BoxDecoration(
                      color: _normalBg,
                      border: pw.Border.all(color: _normalBdr, width: 0.8),
                      borderRadius:
                          const pw.BorderRadius.all(pw.Radius.circular(4)),
                    ),
                    child: pw.Row(
                      mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
                      children: [
                        pw.Expanded(
                          child: pw.Text(_s(lv.testName),
                              style: base.copyWith(font: fontBold)),
                        ),
                        pw.Text(
                          '${lv.value % 1 == 0 ? lv.value.toInt() : lv.value.toStringAsFixed(2)} ${_s(lv.unit)}',
                          style: base.copyWith(color: _success),
                        ),
                        pw.SizedBox(width: 8),
                        _flagBadge('normal', fontBold),
                      ],
                    ),
                  )),
            ],
          ],

          // ── SECTION 4: Complete Lab Results Table ──────────────────────
          _sectionHeader('Complete Laboratory Results', fontBold),
          if (labResults.isEmpty)
            pw.Padding(
              padding: const pw.EdgeInsets.only(bottom: 6),
              child: pw.Text(
                  'No laboratory results were identified in this report.',
                  style: muted),
            )
          else
            pw.TableHelper.fromTextArray(
              headers: [
                'Test Name',
                'Result',
                'Unit',
                'Reference Range',
                'Status'
              ],
              data: _labTableData(labResults),
              headerStyle: pw.TextStyle(
                  font: fontBold, fontSize: 8.5, color: PdfColors.white),
              cellStyle: base.copyWith(fontSize: 8.5),
              headerDecoration: const pw.BoxDecoration(color: _headerBg),
              oddRowDecoration: const pw.BoxDecoration(color: _rowOdd),
              columnWidths: {
                0: const pw.FlexColumnWidth(2.5),
                1: const pw.FixedColumnWidth(48),
                2: const pw.FixedColumnWidth(42),
                3: const pw.FlexColumnWidth(1.5),
                4: const pw.FixedColumnWidth(52),
              },
              cellPadding:
                  const pw.EdgeInsets.symmetric(horizontal: 6, vertical: 5),
              cellAlignment: pw.Alignment.centerLeft,
              cellAlignments: {4: pw.Alignment.center},
            ),

          // ── SECTION 5: Medications ─────────────────────────────────────
          _sectionHeader('Reported Medications', fontBold),
          if (analysis.medications.isEmpty)
            pw.Padding(
              padding: const pw.EdgeInsets.only(bottom: 6),
              child: pw.Text(
                  'No medications were identified in the uploaded report.',
                  style: muted),
            )
          else
            pw.TableHelper.fromTextArray(
              headers: ['Medication', 'Dosage', 'Frequency', 'Notes'],
              data: analysis.medications.map((m) => [
                _s(m['medication_name']?.toString() ?? ''),
                _s(m['dosage']?.toString() ?? '-'),
                _s(m['frequency']?.toString() ?? '-'),
                _s(m['notes']?.toString() ?? m['instructions']?.toString() ?? '-'),
              ]).toList(),
              headerStyle:
                  pw.TextStyle(font: fontBold, fontSize: 8.5, color: PdfColors.white),
              cellStyle: base.copyWith(fontSize: 8.5),
              headerDecoration: const pw.BoxDecoration(color: _headerBg),
              oddRowDecoration: const pw.BoxDecoration(color: _rowOdd),
              cellPadding:
                  const pw.EdgeInsets.symmetric(horizontal: 6, vertical: 5),
            ),

          // ── SECTION 6: Clinical Executive Summary ─────────────────────
          if ((analysis.clinicianSummary ?? '').trim().isNotEmpty) ...[
            _sectionHeader('Clinical Executive Summary', fontBold),
            ..._mdWidgets(
                analysis.clinicianSummary!, base, bold, fontBold),
          ],

          // ── SECTION 7: Key Medical Terms ───────────────────────────────
          if (medTerms.isNotEmpty) ...[
            _sectionHeader('Key Medical Terms Identified', fontBold),
            pw.Wrap(
              spacing: 6,
              runSpacing: 5,
              children: medTerms.map((term) => pw.Container(
                    padding: const pw.EdgeInsets.symmetric(
                        horizontal: 8, vertical: 4),
                    decoration: pw.BoxDecoration(
                      color: _rowOdd,
                      border: pw.Border.all(color: _divider, width: 0.8),
                      borderRadius:
                          const pw.BorderRadius.all(pw.Radius.circular(4)),
                    ),
                    child: pw.Text(term,
                        style: base.copyWith(fontSize: 8.5)),
                  )).toList(),
            ),
          ],

          // ── SECTION 8: What to Discuss With Your Doctor ────────────────
          _sectionHeader('What to Discuss With Your Doctor', fontBold),
          ...discussPoints.map((point) => pw.Padding(
                padding: const pw.EdgeInsets.only(left: 8, bottom: 5),
                child: pw.Row(
                  crossAxisAlignment: pw.CrossAxisAlignment.start,
                  children: [
                    pw.Padding(
                      padding: const pw.EdgeInsets.only(top: 5, right: 7),
                      child: pw.Container(
                        width: 4,
                        height: 4,
                        decoration: pw.BoxDecoration(
                            color: _primary, shape: pw.BoxShape.circle),
                      ),
                    ),
                    pw.Expanded(child: pw.Text(point, style: base)),
                  ],
                ),
              )),

          // ── DISCLAIMER ─────────────────────────────────────────────────
          pw.SizedBox(height: 20),
          pw.Container(
            padding: const pw.EdgeInsets.all(12),
            decoration: pw.BoxDecoration(
              color: const PdfColor.fromInt(0xFFFFF8E1),
              border: pw.Border.all(
                  color: const PdfColor.fromInt(0xFFFFCC80), width: 1),
              borderRadius:
                  const pw.BorderRadius.all(pw.Radius.circular(5)),
            ),
            child: pw.Text(
              'DISCLAIMER: This summary is generated by MedNarrate AI for educational and informational purposes only. '
              'It does not constitute medical advice, diagnosis, or treatment. '
              'Please consult a qualified healthcare professional before making any health decisions.',
              style: base.copyWith(fontSize: 8, color: _textMuted),
            ),
          ),
        ],
      ),
    );

    return doc;
  }

  // ─── Public API ───────────────────────────────────────────────────────────

  /// EXPORT PDF — generates and DIRECTLY DOWNLOADS the PDF. No print dialog.
  Future<void> exportReportPdf({
    required ReportAnalysisModel analysis,
    required String reportTitle,
    required String reportDate,
    String reportType = '',
  }) async {
    final doc = await _buildDocument(
      analysis: analysis,
      reportTitle: reportTitle,
      reportDate: reportDate,
      reportType: reportType,
    );
    final bytes = await doc.save();

    final safeTitle =
        reportTitle.replaceAll(RegExp(r'[^a-zA-Z0-9_\-]'), '_');
    final filename = 'MedNarrate_${safeTitle}_$reportDate.pdf';

    if (kIsWeb) {
      await downloadPdfWeb(bytes, filename);
      return;
    }

    final dir  = await getTemporaryDirectory();
    final file = File('${dir.path}/$filename');
    await file.writeAsBytes(bytes);
    await Share.shareXFiles(
      [XFile(file.path, mimeType: 'application/pdf')],
      subject: 'MedNarrate — $reportTitle Summary',
    );
  }

  /// PRINT / PREVIEW — opens the system/browser print dialog ONLY.
  Future<void> previewReportPdf({
    required ReportAnalysisModel analysis,
    required String reportTitle,
    required String reportDate,
    String reportType = '',
  }) async {
    final doc = await _buildDocument(
      analysis: analysis,
      reportTitle: reportTitle,
      reportDate: reportDate,
      reportType: reportType,
    );
    final bytes = await doc.save();
    await Printing.layoutPdf(onLayout: (_) async => bytes);
  }
}
