/// Why a lab value carries its High / Low / Normal flag.
///
/// The app and server flag a value by comparing it with the reference range
/// printed in the report (`_classify_value` on the server). This class repeats
/// that comparison so the "Why flagged?" sheet can show it, offline and for any
/// language. When the laboratory marked the value itself (for example an "H"
/// next to a value that sits inside the range) the lab's marking wins, exactly
/// as on the server, and [agreesWithFlag] is false so the sheet says so.
library;

enum LabFlagRule { belowLow, aboveHigh, withinRange, noRange }

class LabFlagTrace {
  final double value;
  final String unit;
  final double? refLow;
  final double? refHigh;

  /// Flag shown on the card: high, low, normal, critical or not_classified.
  final String reportedFlag;
  final LabFlagRule rule;

  /// How far outside the range the value is (same unit as the value).
  final double? distance;

  /// [distance] relative to the bound it crosses, in percent.
  final double? distancePercent;

  const LabFlagTrace._({
    required this.value,
    required this.unit,
    required this.refLow,
    required this.refHigh,
    required this.reportedFlag,
    required this.rule,
    required this.distance,
    required this.distancePercent,
  });

  factory LabFlagTrace.compute({
    required double value,
    String unit = '',
    double? refLow,
    double? refHigh,
    String flag = 'not_classified',
  }) {
    LabFlagRule rule;
    double? distance;
    double? percent;
    if (refLow != null && value < refLow) {
      rule = LabFlagRule.belowLow;
      distance = refLow - value;
      percent = refLow != 0 ? distance / refLow.abs() * 100 : null;
    } else if (refHigh != null && value > refHigh) {
      rule = LabFlagRule.aboveHigh;
      distance = value - refHigh;
      percent = refHigh != 0 ? distance / refHigh.abs() * 100 : null;
    } else if (refLow != null || refHigh != null) {
      rule = LabFlagRule.withinRange;
    } else {
      rule = LabFlagRule.noRange;
    }
    return LabFlagTrace._(
      value: value,
      unit: unit,
      refLow: refLow,
      refHigh: refHigh,
      reportedFlag: flag.toLowerCase(),
      rule: rule,
      distance: distance,
      distancePercent: percent,
    );
  }

  /// The flag the range comparison alone produces.
  String get computedFlag {
    switch (rule) {
      case LabFlagRule.belowLow:
        return 'low';
      case LabFlagRule.aboveHigh:
        return 'high';
      case LabFlagRule.withinRange:
        return 'normal';
      case LabFlagRule.noRange:
        return 'not_classified';
    }
  }

  /// False when the laboratory's own marking overrides the range comparison.
  bool get agreesWithFlag =>
      reportedFlag == computedFlag || reportedFlag == 'not_classified';

  bool get hasBothBounds => refLow != null && refHigh != null;

  /// Position of the value on a bar that shows the range in its middle half,
  /// from 0 (far below) to 1 (far above). Null unless both bounds are known.
  double? get markerPosition {
    if (!hasBothBounds) return null;
    final span = refHigh! - refLow!;
    if (span <= 0) return null;
    final domainMin = refLow! - span * 0.5;
    final position = (value - domainMin) / (span * 2);
    return position.clamp(0.04, 0.96).toDouble();
  }

  /// Numbers without noise: 13, 11.2, 0.35.
  static String formatNumber(double v) {
    if (v == v.roundToDouble()) return v.round().toString();
    final s = v.toStringAsFixed(2);
    return s.replaceFirst(RegExp(r'0+$'), '').replaceFirst(RegExp(r'\.$'), '');
  }
}
