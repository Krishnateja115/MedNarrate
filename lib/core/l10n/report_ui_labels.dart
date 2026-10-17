import '../services/api_models.dart';
import 'locale_notifier.dart';
import 'report_ui_labels_data.dart';

/// Labels for the report screens (section headings, chips, column titles).
///
/// * A report that has been translated brings its own labels - they win so the
///   screen matches the language of the report text.
/// * Otherwise the labels follow the app language. English returns an empty map,
///   which makes callers use their built-in English fallback.
Map<String, String> effectiveReportUiLabels(TranslationModel? translation) {
  if (translation != null) return translation.uiLabels;
  return bundledReportUiLabels(localeModeNotifier.value.languageCode);
}

/// Labels bundled with the app for [languageCode] (empty for English/unknown).
Map<String, String> bundledReportUiLabels(String languageCode) =>
    kBundledReportUiLabels[languageCode] ?? const <String, String>{};
