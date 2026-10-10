import '../../../core/services/api_models.dart';

String _parameterKey(String value) =>
    value.toLowerCase().replaceAll(RegExp(r'[^a-z0-9]'), '');

/// Resolve a translated lab name across all report tabs.
///
/// Providers may return a dynamic `param_...` label, a structured finding with
/// `translated_test_name`, or a source name with different spacing/casing.
/// Keep the fallback chain local to parameter names so other translated text is
/// unaffected.
String translatedParameterName(
  String parameterName,
  TranslationModel? translation,
) {
  final labels = translation?.uiLabels ?? const <String, String>{};
  final direct = labels['param_$parameterName'];
  if (direct != null && direct.trim().isNotEmpty) return direct;

  final normalized = _parameterKey(parameterName);
  for (final finding in translation?.findingsJson ?? const []) {
    final source = finding['test_name']?.toString();
    final translated = finding['translated_test_name']?.toString().trim();
    if (source != null &&
        _parameterKey(source) == normalized &&
        translated != null &&
        translated.isNotEmpty) {
      return translated;
    }
  }
  return parameterName;
}
