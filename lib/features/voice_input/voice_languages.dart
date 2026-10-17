/// Languages that can be spoken into the chat box: the ones the app translates
/// into, plus English. The codes are the ones the server and Whisper use.
class VoiceLanguage {
  final String code;
  final String name;
  final String nativeName;

  const VoiceLanguage(this.code, this.name, this.nativeName);
}

const List<VoiceLanguage> kVoiceLanguages = [
  VoiceLanguage('en', 'English', 'English'),
  VoiceLanguage('hi', 'Hindi', 'हिन्दी'),
  VoiceLanguage('ta', 'Tamil', 'தமிழ்'),
  VoiceLanguage('te', 'Telugu', 'తెలుగు'),
  VoiceLanguage('kn', 'Kannada', 'ಕನ್ನಡ'),
  VoiceLanguage('ml', 'Malayalam', 'മലയാളം'),
  VoiceLanguage('bn', 'Bengali', 'বাংলা'),
  VoiceLanguage('mr', 'Marathi', 'मराठी'),
];

VoiceLanguage voiceLanguageFor(String code) => kVoiceLanguages.firstWhere(
      (l) => l.code == code,
      orElse: () => kVoiceLanguages.first,
    );
