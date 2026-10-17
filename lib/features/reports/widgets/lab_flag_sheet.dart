import 'package:flutter/material.dart';
import 'package:mednarrate/l10n/app_localizations.dart';

import '../../../core/l10n/app_l10n.dart';
import '../../../core/l10n/report_ui_labels.dart';
import '../../../core/utils/lab_flag_trace.dart';

/// Flag word (High / Low / Normal / Critical) in the language of the app.
String labFlagWord(String flag) {
  final labels = bundledReportUiLabels(appLanguageCode);
  switch (flag) {
    case 'high':
      return labels['label_high'] ?? 'High';
    case 'low':
      return labels['label_low'] ?? 'Low';
    case 'normal':
      return labels['label_normal'] ?? 'Normal';
    case 'critical':
      return labels['label_critical'] ?? 'Critical';
    default:
      return labels['label_not_classified'] ?? flag;
  }
}

/// One plain-language sentence saying how [trace] produced its flag.
String labFlagSentence(AppLocalizations l, LabFlagTrace trace) {
  final unit = trace.unit.isEmpty ? '' : ' ${trace.unit}';
  final value = '${LabFlagTrace.formatNumber(trace.value)}$unit';
  String number(double? v) => '${LabFlagTrace.formatNumber(v ?? 0)}$unit';
  String percent() => (trace.distancePercent ?? 0).toStringAsFixed(1);

  if (!trace.agreesWithFlag) {
    return l.mlWhyReportMarked(labFlagWord(trace.reportedFlag));
  }
  switch (trace.rule) {
    case LabFlagRule.belowLow:
      return l.mlWhyBelow(value, number(trace.refLow), percent(), labFlagWord('low'));
    case LabFlagRule.aboveHigh:
      return l.mlWhyAbove(value, number(trace.refHigh), percent(), labFlagWord('high'));
    case LabFlagRule.withinRange:
      return l.mlWhyWithin(value, rangeText(trace), labFlagWord('normal'));
    case LabFlagRule.noRange:
      return l.mlWhyNoRange(value);
  }
}

/// "13 – 17 g/dL", "> 13 g/dL", "< 17 g/dL" or an empty string.
String rangeText(LabFlagTrace trace) {
  final unit = trace.unit.isEmpty ? '' : ' ${trace.unit}';
  final low = trace.refLow, high = trace.refHigh;
  if (low != null && high != null) {
    return '${LabFlagTrace.formatNumber(low)} – ${LabFlagTrace.formatNumber(high)}$unit';
  }
  if (low != null) return '> ${LabFlagTrace.formatNumber(low)}$unit';
  if (high != null) return '< ${LabFlagTrace.formatNumber(high)}$unit';
  return '';
}

Color labFlagColor(String flag) {
  switch (flag) {
    case 'high':
      return Colors.redAccent;
    case 'low':
      return Colors.orange;
    case 'critical':
      return const Color(0xFFD32F2F);
    case 'normal':
      return const Color(0xFF00C48C);
    default:
      return Colors.grey;
  }
}

/// Opens the "How this result was flagged" sheet for one lab value.
Future<void> showLabFlagSheet(
  BuildContext context, {
  required String testName,
  required double value,
  required String unit,
  required double? refLow,
  required double? refHigh,
  required String flag,
  required bool isProvisional,
}) {
  final trace = LabFlagTrace.compute(
    value: value,
    unit: unit,
    refLow: refLow,
    refHigh: refHigh,
    flag: flag,
  );
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    builder: (_) => LabFlagSheet(
      testName: testName,
      trace: trace,
      isProvisional: isProvisional,
    ),
  );
}

class LabFlagSheet extends StatelessWidget {
  final String testName;
  final LabFlagTrace trace;
  final bool isProvisional;

  const LabFlagSheet({
    super.key,
    required this.testName,
    required this.trace,
    required this.isProvisional,
  });

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context)!;
    final theme = Theme.of(context);
    final muted = theme.colorScheme.onSurface.withValues(alpha: 0.65);
    final color = labFlagColor(trace.agreesWithFlag ? trace.computedFlag : trace.reportedFlag);
    final unit = trace.unit.isEmpty ? '' : ' ${trace.unit}';
    final range = rangeText(trace);

    return SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(l.mlWhyTitle,
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            Text(testName, style: TextStyle(fontSize: 14, color: muted)),
            const SizedBox(height: 16),
            _row(context, l.mlWhyYourValue,
                '${LabFlagTrace.formatNumber(trace.value)}$unit'),
            if (range.isNotEmpty) _row(context, l.mlWhyRangeUsed, range),
            if (trace.markerPosition != null) ...[
              const SizedBox(height: 14),
              _RangeBar(position: trace.markerPosition!, color: color),
            ],
            const SizedBox(height: 16),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.10),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: color.withValues(alpha: 0.35)),
              ),
              child: Text(labFlagSentence(l, trace),
                  style: const TextStyle(fontSize: 15, height: 1.4, fontWeight: FontWeight.w600)),
            ),
            if (isProvisional) ...[
              const SizedBox(height: 10),
              Text(l.mlWhyProvisional, style: TextStyle(fontSize: 12.5, color: muted)),
            ],
            const SizedBox(height: 14),
            Text(l.mlWhyMethod, style: TextStyle(fontSize: 12.5, height: 1.4, color: muted)),
          ],
        ),
      ),
    );
  }

  Widget _row(BuildContext context, String label, String value) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            flex: 4,
            child: Text(label,
                style: TextStyle(
                    fontSize: 14,
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.6))),
          ),
          Expanded(
            flex: 5,
            child: Text(value,
                textAlign: TextAlign.end,
                style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
          ),
        ],
      ),
    );
  }
}

/// Shows where the value sits relative to the normal range (the shaded middle).
class _RangeBar extends StatelessWidget {
  final double position;
  final Color color;
  const _RangeBar({required this.position, required this.color});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return SizedBox(
      height: 22,
      child: LayoutBuilder(builder: (context, c) {
        final w = c.maxWidth;
        return Stack(
          clipBehavior: Clip.none,
          children: [
            Positioned.fill(
              top: 8,
              bottom: 8,
              child: Container(
                decoration: BoxDecoration(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.08),
                  borderRadius: BorderRadius.circular(4),
                ),
              ),
            ),
            Positioned(
              left: w * 0.25,
              width: w * 0.5,
              top: 8,
              bottom: 8,
              child: Container(
                decoration: BoxDecoration(
                  color: const Color(0xFF00C48C).withValues(alpha: 0.35),
                  borderRadius: BorderRadius.circular(4),
                ),
              ),
            ),
            Positioned(
              left: w * position - 6,
              top: 3,
              child: Container(
                width: 12,
                height: 16,
                decoration: BoxDecoration(
                  color: color,
                  borderRadius: BorderRadius.circular(4),
                  border: Border.all(color: theme.cardColor, width: 2),
                ),
              ),
            ),
          ],
        );
      }),
    );
  }
}
