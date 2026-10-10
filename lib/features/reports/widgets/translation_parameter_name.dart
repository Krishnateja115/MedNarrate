import '../../../core/services/api_models.dart';

String _parameterKey(String value) =>
    value.toLowerCase().replaceAll(RegExp(r'[^a-z0-9]'), '');

const Map<String, Map<String, String>> _commonLabNameTranslations = {
  'hi': {
    'hemoglobin': 'हीमोग्लोबिन',
    'neutrophils': 'न्यूट्रोफिल्स',
    'eosinophils': 'इयोसिनोफिल्स',
    'monocytes': 'मोनोसाइट्स',
    'basophils': 'बेसोफिल्स',
    'platelets': 'प्लेटलेट्स',
    'totalrbccount': 'कुल आरबीसी काउंट',
    'hematocritvaluehct': 'हीमाटोक्रिट मान',
  },
  'ta': {
    'hemoglobin': 'ஹீமோகுளோபின்',
    'neutrophils': 'நியூட்ரோபில்கள்',
    'eosinophils': 'ஈசினோபில்கள்',
    'monocytes': 'மோனோசைட்டுகள்',
    'basophils': 'பேசோபில்கள்',
    'platelets': 'பிளேட்லெட்டுகள்',
    'totalrbccount': 'மொத்த சிவப்பு இரத்த அணுக்களின் எண்ணிக்கை',
    'hematocritvaluehct': 'ஹீமாடோக்ரிட் மதிப்பு',
  },
  'te': {
    'hemoglobin': 'హిమోగ్లోబిన్',
    'neutrophils': 'న్యూట్రోఫిల్స్',
    'eosinophils': 'ఈసినోఫిల్స్',
    'monocytes': 'మోనోసైట్స్',
    'basophils': 'బాసోఫిల్స్',
    'platelets': 'ప్లేట్‌లెట్లు',
    'totalrbccount': 'మొత్తం ఆర్‌బీసీ సంఖ్య',
    'hematocritvaluehct': 'హెమటోక్రిట్ విలువ',
  },
  'kn': {
    'hemoglobin': 'ಹಿಮೋಗ್ಲೋಬಿನ್',
    'neutrophils': 'ನ್ಯೂಟ್ರೋಫಿಲ್ಸ್',
    'eosinophils': 'ಈಸಿನೋಫಿಲ್ಸ್',
    'monocytes': 'ಮೋನೋಸೈಟ್ಸ್',
    'basophils': 'ಬೇಸೋಫಿಲ್ಸ್',
    'platelets': 'ಪ್ಲೇಟ್‌ಲೆಟ್‌ಗಳು',
    'totalrbccount': 'ಒಟ್ಟು ಆರ್‌ಬಿಸಿ ಎಣಿಕೆ',
    'hematocritvaluehct': 'ಹೆಮಟೋಕ್ರಿಟ್ ಮೌಲ್ಯ',
  },
  'ml': {
    'hemoglobin': 'ഹീമോഗ്ലോബിൻ',
    'neutrophils': 'ന്യൂട്രോഫിൽസ്',
    'eosinophils': 'ഈസിനോഫിൽസ്',
    'monocytes': 'മോണോസൈറ്റുകൾ',
    'basophils': 'ബാസോഫിൽസ്',
    'platelets': 'പ്ലേറ്റ്ലെറ്റുകൾ',
    'totalrbccount': 'ആകെ ആർബിസി എണ്ണം',
    'hematocritvaluehct': 'ഹീമറ്റോക്രിറ്റ് മൂല്യം',
  },
  'bn': {
    'hemoglobin': 'হিমোগ্লোবিন',
    'neutrophils': 'নিউট্রোফিল',
    'eosinophils': 'ইওসিনোফিল',
    'monocytes': 'মনোসাইট',
    'basophils': 'বেসোফিল',
    'platelets': 'প্লেটলেট',
    'totalrbccount': 'মোট আরবিসি গণনা',
    'hematocritvaluehct': 'হেমাটোক্রিট মান',
  },
  'mr': {
    'hemoglobin': 'हिमोग्लोबिन',
    'neutrophils': 'न्यूट्रोफिल्स',
    'eosinophils': 'इओसिनोफिल्स',
    'monocytes': 'मोनोसाइट्स',
    'basophils': 'बेसोफिल्स',
    'platelets': 'प्लेटलेट्स',
    'totalrbccount': 'एकूण आरबीसी संख्या',
    'hematocritvaluehct': 'हिमॅटोक्रिट मूल्य',
  },
};

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

  final language = translation?.language.toLowerCase().split(RegExp(r'[-_]')).first;
  final common = _commonLabNameTranslations[language];
  final fallback = common?[normalized];
  if (fallback != null) return fallback;

  return parameterName;
}
